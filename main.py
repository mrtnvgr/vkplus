#!/usr/bin/env python3
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id
import vk_api, json, time, re, shlex
from random import shuffle
import requests

from requests.exceptions import ConnectionError, ReadTimeout
from vk_api.exceptions import ApiError

from modules.core import CoreModule
from modules.restrictionswitch import RestrictionSwitchModule
from modules.silentswitch import SilentSwitchModule
from modules.perm import PermissionsModule
from modules.invite import InviteModule
from modules.kick import KickModule
from modules.update import UpdateModule
from modules.mute import MuteModule
from modules.prefix import PrefixModule
from modules.roll import RollModule

import config

class Main:
    def __init__(self):
        self.reload()
        self.listen()

    def reload(self):
        config.Config(self, "config.json")
        self.saveConfig()
        self.photos = []
        self.photos_page = 0
        self.initVkApi()
        self.loadModules()

    def loadModules(self):
        self.core_mod = CoreModule(self)
        self.restriction_switch_mod = RestrictionSwitchModule(self)
        self.silent_switch_mod = SilentSwitchModule(self)
        self.perm_mod = PermissionsModule(self)
        self.update_mod = UpdateModule(self)
        self.invite_mod = InviteModule(self)
        self.kick_mod = KickModule(self)
        self.mute_mod = MuteModule(self)
        self.prefix_mod = PrefixModule(self)
        self.roll_mod = RollModule(self)

    def initVkApi(self):
        self.vk = vk_api.VkApi(token=self.config["token"])
        self.longpoll = VkLongPoll(self.vk)

    def saveConfig(self):
        """ Save config """
        return json.dump(self.config, open("config.json", "w"), indent=4, ensure_ascii=False)

    def sendreply(self, event, text, attachment=[], reply=True):
        if not self.config["silent"]:
            payload = {"peer_id": event.peer_id, "random_id": get_random_id(), "attachment": ",".join(attachment)}
            if reply:
                payload["reply_to"] = event.message_id
            if text!=None:
                payload["message"] = text
            return self.method("messages.send", payload)
        else:
            return self.deleteMessage(event.message_id)

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

    def uploadAudio(self, data, artist, title):
        session = requests.Session()
        server = self.method("audio.getUploadServer")["upload_url"]
        response = session.post(server,
                                files={"file": ("music.mp3", data)}).json()
        audio = self.method("audio.save", {"artist": artist,
                                           "title": title,
                                           "server": response["server"],
                                           "audio": response["audio"],
                                           "hash": response["hash"]})
        return audio

    def getUrlContent(self, url):
        response = requests.Session().get(url)
        name = response.url.split("/")[-1].split("?")[0]
        return {"name": name, "content": response.content}

    def getPhotoUrl(self, q=None, purity=None, categories=None):
        params = {"q": self.config["photos"]["query"], "categories": self.config["photos"]["categories"], 
                  "purity": self.config["photos"]["purity"], "sorting": "views", 
                  "seed": abs(get_random_id()), "page": self.photos_page} # NOTE: if photo q changes => page = 0

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
                return self.checkPhotoRepeat(response["data"])
            else:
                return None
        else:
            if self.photos==[]:
                self.photos_page += 1
                params["page"] = self.photos_page
                response = requests.Session().get(url, params=params).json()
                shuffle(response["data"])
                self.photos = response["data"]
            if self.photos!=[]:
                return self.checkPhotoRepeat(self.photos)
            else:
                return None

    def checkPhotoRepeat(self, photos):
        for photo in photos:
            if photo["id"] not in self.config["photos"]["ids"]:
                self.config["photos"]["ids"].append(photo["id"])
                self.saveConfig()
                photos.remove(photo)
                return photo["path"]
        return False

    def deleteMessage(self, message_id):
        self.method("messages.delete", {"message_ids": message_id, "delete_for_all": 1})
    
    def getUser(self, user_id):
        return self.method("users.get", {"user_ids": user_id})

    def listen(self):
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW: # NOTE: handle message edits
                        self.eventHandler(event)
                break
            except (ConnectionError, ReadTimeout, ApiError):
                continue

    def eventHandler(self, event):
        if hasattr(event, "text"):
            if event.text!="":
                event.text = list(shlex.split(event.text.replace("&quot;",'"'), posix=False))
                event.text[0] = event.text[0].lower()
                if self.config["mention"]!="":
                    if event.text[0]==self.config["mention"]:
                        event.text.pop(0)
                else:
                    if event.text[0].startswith(self.config["prefix"]):
                        event.text[0] = event.text[0].removeprefix(self.config["prefix"])
                        if event.from_chat or event.from_user:
                            self.cmdHandler(event)
                if event.from_chat:
                    if self.config["restrictions"]:
                        self.restrictionsHandler(event)

    def cmdHandler(self, event):
        if hasattr(event, "text"):

            admin_modules = ()
            
            # Check if event is from admin
            if event.from_me:

                # Add admin modules
                admin_modules = (
                    self.restriction_switch_mod.handler,
                    self.silent_switch_mod.handler,
                    self.mute_mod.muteHandler,
                    self.mute_mod.unMuteHandler,
                    self.kick_mod.handler,
                    self.perm_mod.permHandler,
                    self.update_mod.updateHandler,
                    self.invite_mod.inviteHandler,
                    self.statusHandler
                )

            # Add modules
            modules = (
                self.picsHandler,
                self.core_mod.coreHandler,
                self.prefix_mod.handler,
                self.roll_mod.handler,
                self.helpHandler
            )

            # Check for modules
            for module in admin_modules+modules:
                
                # Do not check other modules if one already worked
                response = module(event)

                if response != None:
                    break

    def helpHandler(self, event):
        if event.text[0] in self.config["aliases"]["help"]:
            if not event.from_me:
                self.sendreply(event, self.gethelptext(event))
            else:
                self.sendme(event, self.gethelptext(event))

    def statusHandler(self, event):
        if event.text[0] in self.config["aliases"]["status"]:
            self.sendme(event, self.getstatusinfo(event))

    def picsHandler(self, event):
        if event.text[0] in self.config["aliases"]["pics"]:
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

    def restrictionsHandler(self, event):
        self.mutedUserHandler(event)

    def mutedUserHandler(self, event):
        peer_id = str(event.peer_id)
        user_id = str(event.user_id)
        
        user_elem = None
        if f"{peer_id}|{user_id}" in self.config["users"]:
            user_elem = f"{peer_id}|{user_id}"
        elif peer_id in self.config["users"]:
            user_elem = peer_id
        if user_elem!=None:
            user = self.config["users"][user_elem]
            if "mute" in user:
                if "time" in user["mute"]:
                    if int(time.time())>=user["mute"]["time"] and user["mute"]["time"]>0:
                        self.config["users"][user_elem].pop("mute")
                        self.saveConfig()
                    else:
                        self.deleteMessage(event.message_id)

    @staticmethod
    def gettime(st):
        cur = int(time.time())
        num = re.findall(r"\d+", st)[0]
        st = st.removeprefix(num)
        num = int(num)
        if st in ("м","мин", "m", "min"):
            num *= 60
        elif st in ("ч", "h"):
            num *= 3600
        elif st in ("д", "d"):
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
        permhelp = {"pics":       f"       {pr}pic ({pr}пик, {pr}пикча, {pr}картиночка, {pr}картиночки, {pr}картинка, {pr}картинки) - картинки",
                    "customPics": f"       {pr}pic ({pr}пик, {pr}пикча, {pr}картиночка, {pr}картиночки, {pr}картинка, {pr}картинки) (query)* (purity)* (categories)* - картинки",
                    "core":       f"       {pr}core (кор, коре)/(nightcore, nc, нк, найткор, найткоре)/(softnightcore, snightcore, softnc, snc, снк, софтнайткор, софтнайткоре)/(daycore, dc, дк, дейкор, дэйкор, дейкоре, дэйкоре)/(softdaycore, sdaycore, softdc, sdc, сдк, софтдейкор, софтдэйкор, софтдейкоре, софтдэйкоре) (speed)* - изменить скорость аудиозаписи"}
        text = []
        text.append(f"VKPlus (github.com/mrtnvgr/vkplus)")
        text.append("Команды:")
        if event.from_me:
            text.append("   Админкие:")
            text.append(f"       {pr}мут ({pr}молчи, {pr}помолчи, {pr}молчать, {pr}терпи, {pr}потерпи, {pr}завали, {pr}заткнись, {pr}mute, {pr}mut) (user) - мут")
            text.append(f"       {pr}анмут ({pr}размут, {pr}unmute, {pr}unmut) (user) - анмут")
            text.append(f"       {pr}кик (kick, пнуть, ануотсюда, кыш, пшел, пшёл, вон, исключить) - кик")
            text.append(f"       {pr}инвайт (invite, заходи, пригласить) - пригласить пользователя в беседу")
            text.append(f"       {pr}включить ({pr}вкл, {pr}on, {pr}он) - включить ограничения")
            text.append(f"       {pr}выключить ({pr}выкл, {pr}офф, {pr}оф, {pr}off) - выключить ограничения")
            text.append(f"       {pr}silent ({pr}сайлент, {pr}тихо) - включить тихий режим")
            text.append(f"       {pr}unsilent ({pr}ансайлент, {pr}громко) - выключить тихий режим")
            text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (добавить,дать,add) (user) (perk) - дать права")
            text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (удалить,забрать,убрать,delete,del) (perk/user)* - забрать права")
            text.append(f"       {pr}префикс ({pr}prefix) (change,поменять,изменить,set,поставить) - изменение префикса")
            text.append(f"       {pr}префикс ({pr}prefix) (view,посмотреть,глянуть,current,текущий) - текущий префикс")
            text.append(f"       {pr}апдейт (апдэйт, update) - обновить (требуется установка из git репозитория)")
            text.append(f"       {pr}статус ({pr}status) - статус свитчей")
        text.append("   Доступны вам:")
        for perm in self.config["perms"]:
            if event.user_id in self.config["perms"][perm] or event.from_me:
                text.append(permhelp[perm])
        text.append("   Общедоступные:")
        text.append(f"       {pr}перм ({pr}perm, {pr}perk, {pr}перк, {pr}разрешение, {pr}права) (list,лист,список) (perk/user)* - показать права")
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
        text.append(f"Muted users: ") # TODO: add perms
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
