#!/usr/bin/env python3
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id
import vk_api, json, time, re

class Main:
    def __init__(self):
        self.version = "0.0.0-1"
        self.reloadConfig()
        self.initVkApi()
        self.listen()

    def reloadConfig(self):
        self.config = json.load(open("config.json"))
        if "users" not in self.config:
            self.config["users"] = {}
        if "restrictions" not in self.config:
            self.config["restrictions"] = True
        if "silent" not in self.config:
            self.config["silent"] = False

    def saveConfig(self):
        json.dump(self.config, fp=open("config.json", "w"), indent=4)

    def initVkApi(self):
        self.vk = vk_api.VkApi(token=self.config["token"])
        self.longpoll = VkLongPoll(self.vk)

    def sendreply(self, event, text, reply=True):
        if not self.config["silent"]:
            payload = {"chat_id": event.chat_id, "random_id": get_random_id(), "message": text}
            if reply:
                payload["reply_to"] = event.message_id
            self.method("messages.send", payload)

    def sendme(self, event, text):
        payload = {"user_id": event.user_id, "random_id": get_random_id(), "message": text}
        self.method("messages.send", payload)

    def deleteMessage(self, message_id):
        self.method("messages.delete", {"message_ids": message_id, "delete_for_all": 1})

    def listen(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW: # NOTE: handle message edits
                if event.from_chat:
                    self.eventHandler(event)

    def eventHandler(self, event):
        if self.config["restrictions"]:
            self.restrictionsHandler(event)
        self.cmdHandler(event)
        # NOTE: self.animebanHandler()...

    def cmdHandler(self, event):
        if hasattr(event, "text"):
            if event.from_me:
                if self.config["silent"]:
                    self.deleteMessage(event.message_id)
                self.restrictionSwitchHandler(event)
                self.silentSwitchHandler(event)
                self.muteHandler(event)
                self.unMuteHandler(event)
                self.helpHandler(event)
                # NOTE: self.unmuteHandler(event)...

    def restrictionSwitchHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!вкл", "!он", "!on", "!включить"):
            self.config["restrictions"] = True
            self.sendme(event, "Ограничения включены.")
        elif text[0] in ("!выкл", "!офф", "!оф", "!off", "!выключить"):
            self.config["restrictions"] = False
            self.sendme(event, "Ограничения выключены.")
        self.saveConfig()

    def silentSwitchHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!silent", "!сайлент", "!тихо"):
            self.config["silent"] = True
            self.deleteMessage(event.message_id)
        elif text[0] in ("!unsilent", "!ансайлент", "!громко"):
            self.config["silent"] = False
        self.saveConfig()

    def muteHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!мут", "!молчи", "!помолчи", "!молчать",
                       "!терпи", "!потерпи", "!завали", "!заткнись",
                       "!mute", "!mut"):
            chat_id = str(event.chat_id)
            if chat_id not in self.config["users"]: self.config["users"][chat_id] = {}
            if len(text)>1:
                user_id, user_name = self.getmentioninfo(event)
                # NOTE: implement mute all
                if len(text)==3:
                    time = text[2]
                    text[2] = self.gettime(text[2])
                else:
                    text.append(-1)
                    time = text[2]
                self.config["users"][chat_id][user_id] = {"time": text[2]}
                self.saveConfig()
                self.sendreply(event, f"{user_name} замучен на {time}.")
            else:
                self.config["users"][chat_id]["muteAll"] = True

    def unMuteHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!размут", "!анмут", "!unmute", "!unmut"):
            chat_id = str(event.chat_id)
            if len(text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if chat_id in self.config["users"]:
                    if user_id in self.config["users"][chat_id]:
                        self.config["users"][chat_id].pop(user_id)
                        self.sendreply(event, f"{user_name} размучен.")
                        self.saveConfig()
            else:
                if chat_id in self.config["users"]:
                    self.config["users"].pop(chat_id)
                    self.saveConfig()
                    self.sendreply(event, "Все размучены.")

    def helpHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!хелп", "!help", "!помощь", "!справка"):
            self.sendme(event, self.gethelptext())

    def restrictionsHandler(self, event):
        self.mutedUserHandler(event)

    def mutedUserHandler(self, event):
        chat_id = str(event.chat_id)
        user_id = str(event.user_id)
        if chat_id in self.config["users"]:
            chat = self.config["users"][chat_id]
            if user_id in chat or "muteAll" in chat:
                user = chat.get(user_id, {"time":-1})
                if (int(time.time())>=user["time"] and user["time"]!=-1) and not chat.get("muteAll", False):
                    chat.pop(user_id)
                else:
                    self.deleteMessage(event.message_id)

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
        splitted = event.text.split(" ")[1].split("|")
        user_id = splitted[0].removeprefix("[id")
        user_name = splitted[1].removesuffix("]")
        return user_id, user_name

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
        text.append("   !антивыход(!ануобратно, !назад) ([on/off],[вкл/выкл],[он/офф(оф)]) - запретить выход из беседы")
        text.append("   !помощь (!хелп, !help, !справка) - справка в избранное")
        return "\n".join(text)

    def method(self, *args, **kwargs):
        try:
            self.vk.method(*args, **kwargs)
        except vk_api.exceptions.ApiError as error:
            if error.code not in (11, 15, 100, 5):
                print(error)

if __name__=="__main__":
    Main()
