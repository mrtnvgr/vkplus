#!/usr/bin/env python3
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id
import vk_api, json, time, re, shlex
from random import choice
import requests

class Main:
    def __init__(self):
        self.version = "0.0.0-3"
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
            payload = {"chat_id": event.chat_id, "random_id": get_random_id(), "message": text, "attachment": ",".join(attachment)}
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

    def getPhotoUrl(self, q=None, purity=None):
        params = {"q": self.config["photos"]["query"], "categories": self.config["photos"]["categories"], 
                  "purity": self.config["photos"]["purity"], "sorting": "relevance", 
                  "seed": abs(get_random_id()), "page": self.photos_page}

        url = "https://wallhaven.cc/api/v1/search"
        if self.config["photos"]["token"]:
            url += f"?apikey={self.config['photos']['token']}"

        if q!=None or purity!=None:
            if q!=None:
                params["q"] = q
            if purity!=None:
                params["purity"] = purity
            params["page"] = 1
            response = requests.Session().get(url, params=params).json()
            if response["data"]!=[]:
                return choice(response["data"])["path"]
            else:
                return None
            
        if self.photos==[]:
            self.photos_page += 1
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
                if event.from_chat:
                    self.eventHandler(event)

    def eventHandler(self, event):
        if hasattr(event, "text"):
            event.text = list(shlex.split(event.text.replace("&quot;",'"')))
        if self.config["restrictions"]:
            self.restrictionsHandler(event)
        self.cmdHandler(event)
        # NOTE: self.animebanHandler()...

    def cmdHandler(self, event):
        if hasattr(event, "text"):
            if event.from_me:
                self.restrictionSwitchHandler(event)
                self.silentSwitchHandler(event)
                self.muteHandler(event)
                self.unMuteHandler(event)
                self.statusHandler(event)
                self.helpHandler(event)
            if event.user_id in self.config["perms"]["pics"] or event.from_me:
                self.picsHandler(event)

    def restrictionSwitchHandler(self, event):
        if event.text[0] in ("!вкл", "!он", "!on", "!включить"):
            self.config["restrictions"] = True
            self.saveConfig()
            self.sendme(event, "Ограничения включены.")
        elif event.text[0] in ("!выкл", "!офф", "!оф", "!off", "!выключить"):
            self.config["restrictions"] = False
            self.saveConfig()
            self.sendme(event, "Ограничения выключены.")

    def silentSwitchHandler(self, event):
        if event.text[0] in ("!silent", "!сайлент", "!тихо"):
            self.config["silent"] = True
            self.saveConfig()
            self.deleteMessage(event.message_id)
        elif event.text[0] in ("!unsilent", "!ансайлент", "!громко"):
            self.config["silent"] = False
            self.saveConfig()

    def muteHandler(self, event):
        if event.text[0] in ("!мут", "!молчи", "!помолчи", "!молчать",
                       "!терпи", "!потерпи", "!завали", "!заткнись",
                       "!mute", "!mut"):
            chat_id = str(event.chat_id)
            if len(event.text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if len(event.text)==3:
                    time = event.text[2]
                    event.text[2] = self.gettime(event.text[2])
                else:
                    event.text.append(-1)
                    time = event.text[2]
                if user_name!="$all":
                    if f"{chat_id}|{user_id}" not in self.config["users"]:
                        self.config["users"][f"{chat_id}|{user_id}"] = {}
                    self.config["users"][f"{chat_id}|{user_id}"]["mute"] = {"time": event.text[2]}
                    self.saveConfig()
                    self.sendreply(event, f"{user_name} замучен на {time}.")
                else:
                    if chat_id not in self.config["users"]:
                        self.config["users"][chat_id] = {}
                    self.config["users"][chat_id]["mute"] = {"time": event.text[2]}
                    self.saveConfig()
                    self.sendreply(event, f"Все замучены на {time}.")

    def unMuteHandler(self, event):
        if event.text[0] in ("!размут", "!анмут", "!unmute", "!unmut"):
            chat_id = str(event.chat_id)
            if len(event.text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if user_name!="$all":
                    if f"{chat_id}|{user_id}" in self.config["users"]:
                        self.config["users"][f"{chat_id}|{user_id}"].pop("mute")
                        self.sendreply(event, f"{user_name} размучен.")
                        self.saveConfig()
                        return
            if chat_id in self.config["users"]:
                if "mute" in self.config["users"][chat_id]:
                    self.config["users"][chat_id].pop("mute")
            for user in self.config["users"]:
                if user.split("|")[0]==chat_id:
                    self.config["users"][user].pop("mute")
            self.saveConfig()
            self.sendreply(event, "Все размучены.")

    def helpHandler(self, event):
        if event.text[0] in ("!хелп", "!help", "!помощь", "!справка"):
            self.sendme(event, self.gethelptext())

    def statusHandler(self, event):
        if event.text[0] in ("!status", "!статус"):
            self.sendme(event, self.getstatusinfo(event))

    def picsHandler(self, event):
        if event.text[0] in ("!картиночки", "!картинки", "!картиночка", "!картинка", "!pic", "!пикча"):
            if len(event.text)>1 and (event.user_id in self.config["perms"]["customPics"] or event.from_me):
                if len(event.text)>2:
                    purity = event.text[2]
                else:
                    purity = None
                photo_url = self.getPhotoUrl(q=event.text[1], purity=purity)
            else:
                photo_url = self.getPhotoUrl()
            if photo_url!=None:
                attachment = self.uploadPhoto(photo_url)
                self.sendreply(event, "", attachment=[f"photo{attachment['owner_id']}_{attachment['id']}_{attachment['access_key']}"])
            else:
                self.sendreply(event, "Нету такого.")

    def restrictionsHandler(self, event):
        self.mutedUserHandler(event)

    def mutedUserHandler(self, event):
        chat_id = str(event.chat_id)
        user_id = str(event.user_id)

        user = None
        if f"{chat_id}|{user_id}" in self.config["users"]:
            user = self.config["users"][f"{chat_id}|{user_id}"]
        elif chat_id in self.config["users"]:
            user = self.config["users"][chat_id]
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
            splitted = event.text[1].split("|")
            user_id = splitted[0].removeprefix("[id")
            user_name = splitted[1].removesuffix("]")
            return user_id, user_name
        except:
            for var in ("@all", "@все", "@everyone"):
                if var in event.text:
                    return None, "$all"
            return None, None

    def gethelptext(self):
        text = []
        text.append(f"VKPlus v{self.version} (github.com/mrtnvgr/vkplus)")
        text.append("Команды:")
        text.append("   !мут (!молчи, !помолчи, !молчать, !терпи, !потерпи, !завали, !заткнись, !mute, !mut) - мут")
        text.append("   !анмут (!размут, !unmute, !unmut) - анмут")
        text.append("   !включить (!вкл, !on, !он) - включить ограничения")
        text.append("   !выключить (!выкл, !офф, !оф, !off) - выключить ограничения")
        text.append("   !silent (!сайлент, !тихо) - включить тихий режим")
        text.append("   !unsilent (!ансайлент, !громко) - выключить тихий режим")
        text.append("   !pic (!пикча, !картиночка, !картиночки, !картинка, !картинки) - картинки")
        #TODO: text.append("   !антивыход(!ануобратно, !назад) ([on/off],[вкл/выкл],[он/офф(оф)]) - запретить выход из беседы")
        text.append("   !статус (!status) - статус свитчей")
        text.append("   !помощь (!хелп, !help, !справка) - справка в избранное")
        return "\n".join(text)

    def getstatusinfo(self, event):
        chat_id = str(event.chat_id)
        text = []
        text.append(f"Restrictions: {self.config['restrictions']}")
        text.append(f"Silent mode: {self.config['silent']}")
        text.append(f"Muted users: ")
        if chat_id in self.config["users"]:
            if "mute" in self.config["users"][chat_id]:
                text[-1] = text[-1] + "all"
        else:
            for elem in self.config["users"]:
                if chat_id in elem: # TODO: add time (сколько еще осталось bantime-curtime/60 минут)
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
