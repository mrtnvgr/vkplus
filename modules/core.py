from utils import run
import tempfile, os
import urllib, json

class CoreModule:
    def __init__(self, master):
        self.master = master
        self.reset()
        self.speed = {"nc": "1.35",
                      "snc": "1.17",

                      "dc": "0.70",
                      "sdc": "0.85"}

    def reset(self):
        self.stuff = {}
        self.objs = {}

    def getCoreType(self, event):
        self.typecore_default = True
        self.typecore = None
        if len(event.text)==1:
            if event.text[0] in ("nightcore", "nc", "нк",
                                 "найткор", "найткоре"):
                event.text.append(self.speed["nc"])
                self.typecore = "nightcore"
            elif event.text[0] in ("softnightcore", "snightcore",
                                   "softnc", "snc", "снк",
                                   "софтнайткор", "софтнайткоре"):
                event.text.append(self.speed["snc"])
                self.typecore = "soft nightcore"
            elif event.text[0] in ("daycore", "dc", "дк",
                                   "дейкор", "дэйкор",
                                   "дейкоре", "дэйкоре"):
                event.text.append(self.speed["dc"])
                self.typecore = "daycore"
            elif event.text[0] in ("softdaycore", "sdaycore",
                                   "softdc", "sdc", "сдк",
                                   "софтдейкор", "софтдэйкор",
                                   "софтдейкоре", "софтдэйкоре"):
                event.text.append(self.speed["sdc"])
                self.typecore = "soft daycore"
            elif event.text[0] in ("core", "коре", "кор"):
                event.text.append(self.speed["nc"])
                self.typecore = "nightcore"
            else:
                self.typecore_default = False
        else:
            if not event.text[1].replace(".","",1).isdigit():
                return
            speed = float(event.text[1])
            if speed<=float(self.speed["dc"]):
                self.typecore = "daycore"
            elif speed<=float(self.speed["sdc"]):
                self.typecore = "soft daycore"
            elif speed<=float(self.speed["snc"]):
                self.typecore = "soft nightcore"
            elif speed<=float(self.speed["nc"]):
                self.typecore = "nightcore"

    def coreHandler(self, event):
        if event.user_id in self.master.config["perms"]["core"] or event.from_me:
            self.getCoreType(event)
            if event.attachments!={}:
                if not event.from_me:
                    if float(event.text[1])<0.50 or float(event.text[1])>1.50:
                        self.master.sendreply(event, "Ограничения скорости 0.5-1.5")
                        return
                self.reset()
                self.getAudios(event)
                self.getReplyAttachments(event)
                if self.stuff=={} and self.objs=={}: return
                self.parseAudios(event)
                attachments = self.uploadObjs(event)
                self.master.sendreply(event, None, attachments)
                #self.cleanAttachments(attachments)

    def getAudios(self, event):
        for i in range(len(event.attachments)):
            if event.attachments.get(f"attach{i+1}_type","")=="audio":
                audio = event.attachments[f"attach{i+1}"]
                if len(audio.split("_"))==2:
                    response = self.master.method("audio.getById", 
                                                 {"audios": audio})
                    if type(response) is int:
                        self.master.sendreply(event, "Не удалось получить аудиозапись.")
                        continue
                    else:
                        if "access_key" in response:
                            audio += f"_{response['access_key']}"
                self.stuff = self.add(self.stuff, "audio", audio)

    def getReplyAttachments(self, event):
        if "reply" in event.attachments:
            ids = json.loads(event.attachments["reply"])["conversation_message_id"]
            response = self.master.method("messages.getByConversationMessageId",
                                   {"peer_id": event.peer_id,
                                    "conversation_message_ids": ids})
            for item in response["items"]:
                for attachment in item["attachments"]:
                    if attachment["type"]=="audio":
                        audio = attachment["audio"]
                        self.stuff = self.add(self.stuff, "audio", f"{audio['owner_id']}_{audio['id']}_{audio['access_key']}")
                    elif attachment["type"]=="audio_message":
                        audio = attachment["audio_message"]
                        self.objs = self.add(self.objs, "audio_message", audio)

    def parseAudios(self, event):
        if "audio" not in self.stuff: return
        response = self.master.method("audio.getById",
                                     {"audios": ",".join(self.stuff["audio"])})
        for audio in response:
            if not event.from_me:
                if audio["duration"]>300:
                    self.master.sendreply(event, "Ограничения времени 0-300")
                    continue
            self.objs = self.add(self.objs, "audio", audio)

    def uploadObjs(self, event):
        attachments = []
        artist = "ᵖ¹³ᵈ³ᶻ"
        for name in self.objs:
            for obj in self.objs[name]:
                if name=="audio":
                    url = obj["url"]
                    title = f'{obj["title"]}'
                elif name=="audio_message":
                    name = "audio"
                    url = obj["link_mp3"]
                    if "transcript" in obj:
                        title = obj["transcript"]
                    else:
                        title = "Голосовое сообщение"
                title += f" +| {self.typecore}"
                data = speed_change(url,
                                    float(event.text[1]))
                new = self.master.uploadAudio(data, artist, title)
                if not self.typecore_default: title += f" x{event.text[1]}"
                attachments.append(f"{name}{new['owner_id']}_{new['id']}_{new['access_key']}")
        return attachments

    def cleanAttachments(self, attachments):
        for attachment in attachments:
            if attachment.startswith("audio"):
                audio = attachment.removeprefix("audio").split("_")
                self.master.method("audio.delete", {"owner_id": audio[0],
                                                    "audio_id": audio[1]})

    def add(self, where, group, data):
        if group not in where:
            where[group] = []
        where[group].append(data)
        return where

def speed_change(url, speed=1.0):
    file = urllib.request.urlopen(url).read()
    with tempfile.NamedTemporaryFile(prefix="core_", suffix=".mp3") as inputf:
        output = os.path.join(os.path.dirname(inputf.name), "out_"+os.path.basename(inputf.name))
        inputf.seek(0)
        inputf.write(file)
        stream = json.loads(utils.check_output(["ffprobe", "-hide_banner", "-loglevel", "panic", "-show_streams", "-of", "json", inputf.name]))
        sample_rate = stream["streams"][0]["sample_rate"]
        utils.run(["ffmpeg", "-i", inputf.name, "-ab", "320k", "-filter:a", f"asetrate={speed}*{sample_rate},aresample=resampler=soxr:precision=24:osf=s32:tsf=s32p:osr={sample_rate}", output])
        sound = open(output, "rb").read()
    os.remove(output)
    return sound
