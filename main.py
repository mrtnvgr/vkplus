#!/usr/bin/env python3
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id
import vk_api, json, time, re, shlex
from random import choice, shuffle
import requests

class Main:
    def __init__(self):
        self.version = "0.0.0-5"
        self.reload()
        self.listen()

    def reload(self):
        self.config = json.load(open("config.json"))
        self.photos = []
        self.photos_page = 0
        self.initVkApi()
        self.checkConfigHealth()
        self.saveConfig()

    def checkConfigHealth(self):
        if "prefix" not in self.config:
            self.config["prefix"] = "./"
        if "mention" not in self.config:
            self.config["mention"] = ""


        if "users" not in self.config:
            self.config["users"] = {}
        if "restrictions" not in self.config:
            self.config["restrictions"] = True
        if "silent" not in self.config:
            self.config["silent"] = False

        if "photos" not in self.config:
            self.config["photos"] = {}
        if "token" not in self.config["photos"]:
            self.config["photos"]["token"] = ""
        if "query" not in self.config["photos"]:
            self.config["photos"]["query"] = ""
        if "categories" not in self.config["photos"]:
            self.config["photos"]["categories"] = "010"
        if "purity" not in self.config["photos"]:
            self.config["photos"]["purity"] = "100"
        if "ids" not in self.config["photos"]:
            self.config["photos"]["ids"] = []
        self.checkPermsHealth()

    def checkPermsHealth(self):
        if "perms" not in self.config:
            self.config["perms"] = {}
        if "pics" not in self.config["perms"]:
            self.config["perms"]["pics"] = []
        if "customPics" not in self.config["perms"]:
            self.config["perms"]["customPics"] = []

        for perm in self.config["perms"]:
            for i,elem in enumerate(self.config["perms"][perm]):
                if type(elem) is str:
                    self.config["perms"][perm][i] = self.getUser(elem)[0]["id"]
                    

    def saveConfig(self):
        json.dump(self.config, fp=open("config.json", "w"), indent=4)

    def initVkApi(self):
        self.vk = vk_api.VkApi(token=self.config["token"])
        self.longpoll = VkLongPoll(self.vk)

    def sendreply(self, event, text, attachment=[], reply=True):
        if not self.config["silent"]:
            payload = {"peer_id": event.peer_id, "random_id": get_random_id(), "message": text, "attachment": ",".join(attachment)}
            if reply:
                payload["reply_to"] = event.message_id
            self.method("messages.send", payload)
        else:
            self.deleteMessage(event.message_id)

    def sendme(self, event, text):
        if self.config["silent"]:
            self.deleteMessage(event.message_id)
        payload = {"user_id": event.user_id, "random_id": get_random_id(), "message": text}
        self.method("messages.send", payload)

    def uploadPhoto(self, url):
        session = requests.Session()
        server = self.method("photos.getMessagesUploadServer", {})["upload_url"]
        photo = self.getUrlContent(url)
        response = session.post(server, files={"photo": (photo["name"], photo["content"])}).json()
        attachment = self.method("photos.saveMessagesPhoto", response)[0]
        return attachment

    def getUrlContent(self, url):
        response = requests.Session().get(url)
        name = response.url.split("/")[-1].split("?")[0]
        return {"name": name, "content": response.content}

    def getPhotoUrl(self, q=None, purity=None, categories=None):
        params = {"q": self.config["photos"]["query"], "categories": self.config["photos"]["categories"], 
                  "purity": self.config["photos"]["purity"], "sorting": "relevance", 
                  "seed": abs(get_random_id()), "page": self.photos_page}

        url = "https://wallhaven.cc/api/v1/search"
        if self.config["photos"]["token"]:
            url += f"?apikey={self.config['photos']['token']}"

        if q!=None or purity!=None or categories!=None:
            if q!=None:
                params["q"] = q
            if purity!=None:
                params["purity"] = purity
            if categories!=None:
                params["categories"] = categories
            params["page"] = 1
            response = requests.Session().get(url, params=params).json()
            if response["data"]!=[]:
                shuffle(response["data"])
                for photo in response["data"]:
                    if photo["id"] not in self.config["photos"]["ids"]:
                        self.config["photos"]["ids"].append(photo["id"])
                        self.saveConfig()
                        return photo["path"]
                return False
            else:
                return None
        else:
            if self.photos==[]:
                self.photos_page += 1
                params["page"] = self.photos_page
                response = requests.Session().get(url, params=params).json()
                self.photos = response["data"]
            photo = choice(self.photos)
            self.photos.remove(photo)
            return photo["path"]

    def deleteMessage(self, message_id):
        self.method("messages.delete", {"message_ids": message_id, "delete_for_all": 1})
    
    def getUser(self, user_id):
        return self.method("users.get", {"user_ids": user_id})

    def listen(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW: # NOTE: handle message edits
                self.eventHandler(event)

    def eventHandler(self, event):
        if hasattr(event, "text"):
            if event.text!="":
                event.text = list(shlex.split(event.text.replace("&quot;",'"'), posix=False))
                if self.config["mention"]!="":
                    if event.text[0]==self.config["mention"]:
                        event.text.pop(0)
                else:
                    if event.text[0].startswith(self.config["prefix"]):
                        event.text[0] = event.text[0].removeprefix(self.config["prefix"])
                if event.from_chat:
                    if self.config["restrictions"]:
                        self.restrictionsHandler(event)
                if event.from_chat or event.from_user:
                    self.cmdHandler(event)
            # NOTE: self.animebanHandler()...

    def cmdHandler(self, event):
        if hasattr(event, "text"):
            if event.from_me:
                self.restrictionSwitchHandler(event)
                self.silentSwitchHandler(event)
                self.muteHandler(event)
                self.unMuteHandler(event)
                self.permHandler(event)
                self.prefixHandler(event)
                self.statusHandler(event)
            if event.user_id in self.config["perms"]["pics"] or event.from_me:
                self.picsHandler(event)
            self.helpHandler(event)

    def restrictionSwitchHandler(self, event):
        if event.text[0] in ("вкл", "он", "on", "включить"):
            self.config["restrictions"] = True
            self.saveConfig()
            self.sendme(event, "Ограничения включены.")
        elif event.text[0] in ("выкл", "офф", "оф", "off", "выключить"):
            self.config["restrictions"] = False
            self.saveConfig()
            self.sendme(event, "Ограничения выключены.")

    def silentSwitchHandler(self, event):
        if event.text[0] in ("silent", "сайлент", "тихо"):
            self.config["silent"] = True
            self.saveConfig()
            self.deleteMessage(event.message_id)
        elif event.text[0] in ("unsilent", "ансайлент", "громко"):
            self.config["silent"] = False
            self.saveConfig()

    def muteHandler(self, event):
        if event.text[0] in ("мут", "молчи", "помолчи", "молчать",
                       "терпи", "потерпи", "завали", "заткнись",
                       "mute", "mut"):
            peer_id = str(event.peer_id)
            if len(event.text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if len(event.text)==3:
                    time = event.text[2]
                    event.text[2] = self.gettime(event.text[2])
                else:
                    event.text.append(-1)
                    time = event.text[2]
                if user_name!="$all":
                    if f"{peer_id}|{user_id}" not in self.config["users"]:
                        self.config["users"][f"{peer_id}|{user_id}"] = {}
                    self.config["users"][f"{peer_id}|{user_id}"]["mute"] = {"time": event.text[2]}
                    self.saveConfig()
                    self.sendreply(event, f"{user_name} замучен на {time}.")
                else:
                    if peer_id not in self.config["users"]:
                        self.config["users"][peer_id] = {}
                    self.config["users"][peer_id]["mute"] = {"time": event.text[2]}
                    self.saveConfig()
                    self.sendreply(event, f"Все замучены на {time}.")

    def unMuteHandler(self, event):
        if event.text[0] in ("размут", "анмут", "unmute", "unmut"):
            peer_id = str(event.peer_id)
            if len(event.text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if user_name!="$all":
                    if f"{peer_id}|{user_id}" in self.config["users"]:
                        self.config["users"][f"{peer_id}|{user_id}"].pop("mute")
                        self.sendreply(event, f"{user_name} размучен.")
                        self.saveConfig()
                        return
            if peer_id in self.config["users"]:
                if "mute" in self.config["users"][peer_id]:
                    self.config["users"][peer_id].pop("mute")
            for user in self.config["users"]:
                if user.split("|")[0]==peer_id:
                    self.config["users"][user].pop("mute")
            self.saveConfig()
            self.sendreply(event, "Все размучены.")

    def helpHandler(self, event):
        if event.text[0] in ("хелп", "help", "помощь", "справка"):
            if not event.from_me:
                self.sendreply(event, self.gethelptext(event))
            else:
                self.sendme(event, self.gethelptext(event))

    def statusHandler(self, event):
        if event.text[0] in ("status", "статус"):
            self.sendme(event, self.getstatusinfo(event))

    def picsHandler(self, event):
        if event.text[0] in ("картиночки", "картинки", "картиночка", "картинка", "pic", "пикча", "пик"):
            if len(event.text)>1 and (event.user_id in self.config["perms"]["customPics"] or event.from_me):
                if len(event.text)>2:
                    purity = event.text[2]
                else:
                    purity = None
                if len(event.text)>3:
                    categories = event.text[3]
                else:
                    categories = None
                photo_url = self.getPhotoUrl(q=event.text[1], purity=purity, categories=categories)
            else:
                photo_url = self.getPhotoUrl()
            if photo_url==None:
                self.sendreply(event, "Нету такого.")
            elif photo_url==False:
                self.sendreply(event, "По этому запросу закончились картиночки.")
            else:
                attachment = self.uploadPhoto(photo_url)
                self.sendreply(event, "", attachment=[f"photo{attachment['owner_id']}_{attachment['id']}_{attachment['access_key']}"])

    def permHandler(self, event):
        if event.text[0] in ("perm", "перм", "perk", "перк", "разрешение", "права"): # TODO: $all handling
            if len(event.text)==4:
                user_id, user_name = self.getmentioninfo(event)
                if event.text[1] in ("добавить", "дать", "add"):
                    if event.text[3] in self.config["perms"]:
                        self.config["perms"][event.text[3]].append(int(user_id))
                        self.saveConfig()
                        self.sendreply(event, f"{user_name} теперь может использовать {event.text[3]}.")
                elif event.text[1] in ("удалить", "забрать", "убрать", "delete", "del"):
                    if event.text[3] in self.config["perms"]:
                        for id in self.config["perms"][event.text[3]]:
                            if id==user_id:
                                self.config["perms"][event.text[3]].remove(int(id))
                                self.saveConfig()
                                self.sendreply(event, f"{user_name} теперь нельзя использовать {event.text[3]}.")
            if len(event.text)>=2:
                if event.text[1].lower() in ("list", "лист", "список"):
                    if len(event.text)==2:
                        self.sendreply(event, f"Perks: {', '.join(self.config['perms'])}")
                    elif len(event.text)==3:
                        user_id, user_name = self.getmentioninfo(event)
                        if user_id==None:
                            pass # send perk users TODO
                            # self.sendreply(event, f"Perk {event.text[2]} users: {', '.join(self.config['perms'][event.text[2]])}")
                        else:
                            perks = []
                            for perk in self.config["perms"]:
                                if int(user_id) in self.config["perms"][perk]:
                                    perks.append(perk)
                            if perks==[]: perks = ["None"]
                            self.sendreply(event, f"{user_name} perks: {', '.join(perks)}")

    def prefixHandler(self, event):
        if event.text[0] in ("префикс", "prefix"):
            if len(event.text)==2:
                if event.text[1] in ("view","посмотреть","глянуть","current","текущий"):
                    self.sendreply(event, f"Текущий префикс: ({self.config['prefix']})")
            elif len(event.text)==3:
                if event.text[1] in ("change","поменять","изменить","set","поставить"):
                    if event.text[2]!="\\":
                        self.config["prefix"] = event.text[2]
                        self.saveConfig()
                        self.sendreply(event, f"Префикс изменён на ({event.text[2]})")

    def restrictionsHandler(self, event):
        self.mutedUserHandler(event)

    def mutedUserHandler(self, event):
        peer_id = str(event.peer_id)
        user_id = str(event.user_id)

        user = None
        if f"{peer_id}|{user_id}" in self.config["users"]:
            user = self.config["users"][f"{peer_id}|{user_id}"]
        elif peer_id in self.config["users"]:
            user = self.config["users"][peer_id]
        if user!=None:
            if "mute" in user:
                if "time" in user["mute"]:
                    if int(time.time())>=user["mute"]["time"]:
                        self.deleteMessage(event.message_id)
                    else:
                        user.pop("mute")

    @staticmethod
    def gettime(st):
        cur = int(time.time())
        num = re.findall(r"\d+", st)[0]
        st = st.removeprefix(num)
        num = int(num)
        if st in ("м","мин"):
            num *= 60
        elif st=="ч":
            num *= 3600
        elif st=="д":
            num *= 86400
        return cur+int(num)

    @staticmethod
    def getmentioninfo(event):
        try:
            splitted = " ".join(event.text).split("|")
            user_id = splitted[0].split("[id")[1]
            user_name = splitted[1].split("]")[0]
            return user_id, user_name
        except:
            for var in ("@all", "@все", "@everyone"):
                if var in event.text:
                    return None, "$all"
            return None, None

    def getmention(self):
        user = self.getUser(self.config["name"])[0]
        return f"[id{user['id']}|@{self.config['name']}]"

    def gethelptext(self, event):
        pr = self.config["prefix"]
        text = []
        text.append(f"VKPlus v{self.version} (github.com/mrtnvgr/vkplus)")
        text.append("Команды:")
        if event.from_me:
            text.append("   Админкие:")
            text.append(f"       {pr}мут ({pr}молчи, {pr}помолчи, {pr}молчать, {pr}терпи, {pr}потерпи, {pr}завали, {pr}заткнись, {pr}mute, {pr}mut) (user) - мут")
            text.append(f"       {pr}анмут ({pr}размут, {pr}unmute, {pr}unmut) (user) - анмут")
            text.append(f"       {pr}включить ({pr}вкл, {pr}on, {pr}он) - включить ограничения")
            text.append(f"       {pr}выключить ({pr}выкл, {pr}офф, {pr}оф, {pr}off) - выключить ограничения")
            text.append(f"       {pr}silent ({pr}сайлент, {pr}тихо) - включить тихий режим")
            text.append(f"       {pr}unsilent ({pr}ансайлент, {pr}громко) - выключить тихий режим")
            text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (добавить,дать,add) (user) (perk) - дать права")
            text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (удалить,забрать,убрать,delete,del) (perk/user)* - забрать права")
            text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (list,лист,список) (perk/user)* - показать права")
            text.append(f"       {pr}префикс ({pr}prefix) (change,поменять,изменить,set,поставить) - изменение префикса")
            text.append(f"       {pr}префикс ({pr}prefix) (view,посмотреть,глянуть,current,текущий) - текущий префикс")
            text.append(f"       {pr}статус ({pr}status) - статус свитчей")
        text.append("   Требуются права:")
        text.append(f"       {pr}pic ({pr}пик, {pr}пикча, {pr}картиночка, {pr}картиночки, {pr}картинка, {pr}картинки) (query)* (purity)* (categories)* - картинки")
        text.append("   Общедоступные:")
        text.append(f"       {pr}помощь ({pr}хелп, {pr}help, {pr}справка) - справка")
        text.append("* - Optional argument")
        #TODO: text.append("   !антивыход(!ануобратно, !назад) ([on/off],[вкл/выкл],[он/офф(оф)]) - запретить выход из беседы")
        return "\n".join(text)

    def getstatusinfo(self, event):
        peer_id = str(event.peer_id)
        text = []
        text.append(f"Prefix: ({self.config['prefix']})")
        text.append(f"Restrictions: {self.config['restrictions']}")
        text.append(f"Silent mode: {self.config['silent']}")
        text.append(f"Muted users: ") # TODO: add perms and current prefix
        if peer_id in self.config["users"]:
            if "mute" in self.config["users"][peer_id]:
                text[-1] = text[-1] + "all"
        else:
            for elem in self.config["users"]:
                if peer_id in elem: # TODO: add time (сколько еще осталось bantime-curtime/60 минут)
                    user = elem.split("|")[1]
                    user_data = self.getUser(user)[0]
                    if text[-1]!="Muted users: ":
                        text[-1] += ","
                    text[-1] = f"{text[-1]}{user_data['first_name']} {user_data['last_name']}"
        return "\n".join(text)

    def method(self, *args, **kwargs):
        try:
            return self.vk.method(*args, **kwargs)
        except vk_api.exceptions.ApiError as error:
            if error.code not in (11, 15, 5):
                print(error)
            return error.code

if __name__=="__main__":
    Main()
