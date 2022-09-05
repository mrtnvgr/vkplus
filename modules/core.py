from pydub import AudioSegment
from io import BytesIO
import urllib, json

class CoreModule:
    def __init__(self, master):
        self.master = master

    def coreHandler(self, event):
        default = True
        typecore = None
        if len(event.text)==1:
            if event.text[0] in ("nightcore", "nc", "нк",
                                 "найткор", "найткоре"):
                event.text.append("1.35")
                typecore = "nightcore"
            elif event.text[0] in ("softnightcore", "snightcore",
                                   "softnc", "snc", "снк",
                                   "софтнайткор", "софтнайткоре"):
                event.text.append("1.17")
                typecore = "soft nightcore"
            elif event.text[0] in ("daycore", "dc", "дк",
                                   "дейкор", "дэйкор",
                                   "дейкоре", "дэйкоре"):
                event.text.append("0.70")
                typecore = "daycore"
            elif event.text[0] in ("softdaycore", "sdaycore",
                                   "softdc", "sdc", "сдк",
                                   "софтдейкор", "софтдэйкор",
                                   "софтдейкоре", "софтдэйкоре"):
                event.text.append("0.85")
                typecore = "soft daycore"
            elif event.text[0] in ("core", "коре", "кор"):
                event.text.append("1.35")
                typecore = "nightcore"
            else:
                default = False
        else:
            if not event.text[1].replace(".","",1).isdigit():
                return
            speed = float(event.text[1])
            if speed<=0.70:
                typecore = "daycore"
            elif speed<=0.85:
                typecore = "soft daycore"
            elif speed<=1.17:
                typecore = "soft nightcore"
            elif speed<=1.35:
                typecore = "nightcore"

        if event.user_id in self.master.config["perms"]["core"] or event.from_me:
            if event.attachments!={}:
                if not event.from_me:
                    if float(event.text[1])<0.50 or float(event.text[1])>1.50:
                        self.master.sendreply(event, "Ограничения скорости 0.5-1.5")
                        return
                audios = []
                for i in range(len(event.attachments)):
                    if event.attachments.get(f"attach{i+1}_type","")=="audio":
                        audios.append(event.attachments[f"attach{i+1}"])
                if "reply" in event.attachments:
                    ids = json.loads(event.attachments["reply"])["conversation_message_id"]
                    response = self.master.method("messages.getByConversationMessageId",
                                           {"peer_id": event.peer_id,
                                            "conversation_message_ids": ids})
                    for item in response["items"]:
                        for attachment in item["attachments"]:
                            if attachment["type"]=="audio":
                                audio = attachment["audio"]
                                audios.append(f"{audio['owner_id']}_{audio['id']}_{audio['access_key']}")
                response = self.master.method("audio.getById",
                                      {"audios": ",".join(audios)})
                attachments = []
                for audio in response:
                    if not event.from_me:
                        if audio["duration"]>300:
                            self.master.sendreply(event, "Ограничения времени 0-300")
                            return
                    data = speed_change(audio["url"],
                                                float(event.text[1]))
                    artist = "`×{¤ 𝔭13𝔡3𝔷 ¤}~"
                    title = f'{audio["title"]} +| {typecore}'
                    if not default: title += f" x{event.text[1]}"
                    newAudio = self.master.uploadAudio(data, artist, title)
                    attachments.append(f"audio{newAudio['owner_id']}_{newAudio['id']}_{newAudio['access_key']}")
                self.master.sendreply(event, None, attachments)

def speed_change(url, speed=1.0):
    file = urllib.request.urlopen(url).read()
    sound = AudioSegment.from_file(BytesIO(file))
    sound2 = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    sound2 = sound2.set_frame_rate(sound.frame_rate)
    buf = BytesIO()
    sound2.export(buf)
    return buf.getvalue()
