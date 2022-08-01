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
        if "mutedUsers" not in self.config:
            self.config["mutedUsers"] = {}
        if "restrictions" not in self.config:
            self.config["restrictions"] = True

    def saveConfig(self):
        json.dump(self.config, fp=open("config.json", "w"), indent=4)

    def initVkApi(self):
        self.vk = vk_api.VkApi(token=self.config["token"])
        self.longpoll = VkLongPoll(self.vk)

    def sendreply(self, event, text, reply=True):
        payload = {"chat_id": event.chat_id, "random_id": get_random_id(), "message": text}
        if reply:
            payload["reply_to"] = event.message_id
        self.method("messages.send", payload)

    def sendme(self, event, text):
        payload = {"user_id": event.user_id, "random_id": get_random_id(), "message": text}
        self.method("messages.send", payload)

    def listen(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW: # TODO: message edit
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
                self.restrictionSwitchHandler(event)
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

    def muteHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!мут", "!молчи", "!помолчи", "!молчать",
                       "!терпи", "!потерпи", "!завали", "!заткнись",
                       "!mute", "!mut"):
            if len(text)>1:
                chat_id = str(event.chat_id)
                user_id, user_name = self.getmentioninfo(event)
                # NOTE: implement mute all
                # TODO: make independent function for getting user_id and user_name
                if len(text)==3:
                    time = text[2]
                    text[2] = self.gettime(text[2])
                else:
                    text.append(-1)
                    time = text[2]
                if chat_id not in self.config["mutedUsers"]: self.config["mutedUsers"][chat_id] = {}
                self.config["mutedUsers"][chat_id][user_id] = {"time": text[2]}
                self.saveConfig()
                self.sendreply(event, f"{user_name} замучен на {time}.")
            else:
                pass # TODO: all

    def unMuteHandler(self, event):
        text = event.text.split(" ")
        if text[0] in ("!размут", "!анмут", "!unmute", "!unmut"):
            chat_id = str(event.chat_id)
            if len(text)>1:
                user_id, user_name = self.getmentioninfo(event)
                if chat_id in self.config["mutedUsers"]:
                    if user_id in self.config["mutedUsers"][chat_id]:
                        self.config["mutedUsers"][chat_id].pop(user_id)
                        self.sendreply(event, f"{user_name} размучен.")
                        self.saveConfig()
            else:
                self.config["mutedUsers"].pop(chat_id)
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
        if chat_id in self.config["mutedUsers"]:
            chat = self.config["mutedUsers"][chat_id]
            if user_id in chat:
                user = chat[user_id]
                if int(time.time())>=user["time"] and user["time"]!=-1:
                    chat.pop(user_id)
                else:
                    self.method("messages.delete", {"message_ids": event.message_id, "delete_for_all": 1})

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
        text.append("   !помощь (!хелп, !help, !справка) - справка в избранное")
        return "\n".join(text)

    def method(self, *args, **kwargs):
        try:
            self.vk.method(*args, **kwargs)
        except vk_api.exceptions.ApiError as error:
            if error.code not in (11, 15, 100): # cannot reply to message
                print(error)

if __name__=="__main__":
    Main()
