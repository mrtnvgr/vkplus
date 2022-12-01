import tempfile, os
import urllib, json
import utils

from module import Module


class CoreModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

        # Speed values
        self.speed = {
            "daycore": "0.70",
            "soft daycore": "0.85",
            "soft nightcore": "1.17",
            "nightcore": "1.35",
        }

        # Link core to nightcore
        self.speed["core"] = self.speed["nightcore"]

    def reset(self):
        """Reset stuff"""
        self.stuff = {}
        self.objs = {}

    def getCoreType(self, event):
        """Get core type"""

        # Reset variables
        self.speed_default = True
        self.typecore = None

        # Speed is not specified
        if len(event.text) == 1:

            # Iterate through all core types
            for core in self.master.config["aliases"]["core"]:

                if event.text[0] in self.master.config["aliases"]["core"][core]:

                    # Add speed to event text
                    event.text.append(self.speed[core])

                    # Set typecore
                    self.typecore = core

        # Speed is specified
        else:

            # Check if speed is digit
            if not event.text[1].replace(".", "", 1).isdigit():
                return

            # Iterate through speeds
            for speed in self.speed:

                # Get speed value
                speed_value = float(self.speed[speed])

                # Check if user speed <= speed
                if float(event.text[1]) <= speed_value:

                    # Set core type
                    self.typecore = speed

            # Speed is not default
            self.speed_default = False

    def coreHandler(self, event):
        # Check if user have perm core or is admin
        if event.user_id in self.master.config["perms"]["core"] or event.from_me:

            # Get core type
            self.getCoreType(event)

            # Check for core type
            if self.typecore == None:
                return

            # Check if message have attachments
            if event.attachments != {}:

                # Check if message is not from me
                if not event.from_me:

                    # Check for speed violation
                    if float(event.text[1]) < 0.50 or float(event.text[1]) > 1.50:

                        # Send error message
                        self.master.sendreply(event, "Ограничения скорости 0.5-1.5")
                        return

                # Reset variables
                self.reset()

                # Get audios from message
                self.getAudios(event)

                # Get reply audios from message
                self.getReplyAttachments(event)

                # Check if any audios was found
                if self.stuff == {} and self.objs == {}:
                    return

                # Parse audios to objects
                self.parseAudios(event)

                # Upload audios to vk servers
                attachments = self.uploadObjs(event)

                # Send audios
                self.master.sendreply(event, None, attachments)
                # self.cleanAttachments(attachments)

                return True

    def getAudios(self, event):

        # Iterate through message attachments
        for i in range(len(event.attachments)):

            # Check if attachment type is audio
            if event.attachments.get(f"attach{i+1}_type", "") == "audio":

                # Get audio attachment
                audio = event.attachments[f"attach{i+1}"]

                # Check if audio has not access_key
                if len(audio.split("_")) == 2:

                    # Get audio info by id
                    response = self.master.method("audio.getById", {"audios": audio})

                    # Audio get error
                    if type(response) is int:
                        self.master.sendreply(
                            event,
                            f"Не удалось получить аудиозапись. Код ошибки: {response}",
                        )
                        continue
                    else:

                        # Check for access key in response
                        if "access_key" in response:

                            # Append access key to audio
                            audio += f"_{response['access_key']}"

                # Add audio to stuff
                self.stuff = self.add(self.stuff, "audio", audio)

    def getReplyAttachments(self, event):

        # Check if reply is in attachments
        if "reply" in event.attachments:

            # Get conversation message id
            ids = json.loads(event.attachments["reply"])["conversation_message_id"]

            # Get message by conv. message id
            response = self.master.method(
                "messages.getByConversationMessageId",
                {"peer_id": event.peer_id, "conversation_message_ids": ids},
            )

            # Iterate through message
            for item in response["items"]:

                # Iterate through attachments
                for attachment in item["attachments"]:

                    # Check if attachment type is audio
                    if attachment["type"] == "audio":

                        audio = attachment["audio"]

                        audioline = f"{audio['owner_id']}_{audio['id']}"

                        if "access_key" in audio:
                            audioline += f"_{audio['access_key']}"

                        # Add audio to stuff
                        self.stuff = self.add(
                            self.stuff,
                            "audio",
                            audioline,
                        )

                    # Check if attachment type is audio message
                    elif attachment["type"] == "audio_message":

                        audio = attachment["audio_message"]

                        # Add audio message to stuff
                        self.objs = self.add(self.objs, "audio_message", audio)

    def parseAudios(self, event):

        # Check if audio is in stuff
        if "audio" not in self.stuff:
            return

        # Get audios data
        audios = ",".join(self.stuff["audio"])
        response = self.master.method("audio.getById", {"audios": audios})

        # Iterate through audios response
        for audio in response:

            # Check if message is not from me
            if not event.from_me:

                # Check for audio duration violation
                if audio["duration"] > 300:

                    # Send error message
                    self.master.sendreply(event, "Ограничения времени 0-300")
                    continue

            # Add audio to objects
            self.objs = self.add(self.objs, "audio", audio)

    def uploadObjs(self, event):

        attachments = []

        # Set result audio artist name
        artist = "ᵖ¹³ᵈ³ᶻ"

        # Iterate through object groups
        for name in self.objs:

            # Iterate through objects
            for obj in self.objs[name]:

                # Object group is audio
                if name == "audio":

                    # Set url from object url
                    url = obj["url"]

                    # Set title from object title
                    title = f'{obj["title"]}'

                # Object group is audio message
                elif name == "audio_message":

                    # Overwrite name to audio
                    name = "audio"

                    # Set url from object link_mp3
                    url = obj["link_mp3"]

                    # Check if audio transcript is available
                    if "transcript" in obj:

                        # Set title from object transcript
                        title = obj["transcript"]

                    else:

                        # Set default audio name
                        title = "Голосовое сообщение"

                # Add core type to title
                title += f" +| {self.typecore}"

                # Generate new audio
                data = speed_change(url, float(event.text[1]))

                # Upload new audio to vk servers
                new = self.master.uploadAudio(data, artist, title)

                # Add core speed to name if speed is not default
                if not self.speed_default:
                    title += f" x{event.text[1]}"

                # Append new audio to attachments
                attachments.append(
                    f"{name}{new['owner_id']}_{new['id']}_{new['access_key']}"
                )

        # Return attachments
        return attachments

    def cleanAttachments(self, attachments):
        # NOTE: this function is currently deprecated.
        # NOTE: we can use playlists as audio containers in future

        # Iterate through attachments
        for attachment in attachments:

            # Check if attachment type is audio
            if attachment.startswith("audio"):

                # Get audio info
                audio = attachment.removeprefix("audio").split("_")

                # Delete audio from servers
                self.master.method(
                    "audio.delete", {"owner_id": audio[0], "audio_id": audio[1]}
                )

    def add(self, where, group, data):
        if group not in where:
            where[group] = []
        where[group].append(data)
        return where


def speed_change(url, speed=1.0):
    # Get file content
    file = urllib.request.urlopen(url).read()

    # Create temp file
    with tempfile.NamedTemporaryFile(prefix="core_", suffix=".mp3") as inputf:

        # Get output path
        output = os.path.join(
            os.path.dirname(inputf.name), "out_" + os.path.basename(inputf.name)
        )

        # Seek file to 0
        inputf.seek(0)

        # Write file to temp file
        inputf.write(file)

        # Get file info
        stream = json.loads(
            utils.check_output(
                [
                    "ffprobe",
                    "-hide_banner",
                    "-loglevel",
                    "panic",
                    "-show_streams",
                    "-of",
                    "json",
                    inputf.name,
                ]
            )
        )

        # Get file sample rate
        sample_rate = stream["streams"][0]["sample_rate"]

        # Generate filters
        filters = []

        # Add speed filter

        # Check if speed is not default
        if speed != 1.0:

            # Add speed filter
            filters.append(f"asetrate={speed}*{sample_rate}")

        # Add resampler filter
        filters.append(
            f"aresample=resampler=soxr:precision=24:osf=s32:tsf=s32p:osr={sample_rate}"
        )

        # Join filters
        filters = ",".join(filters)

        # Run ffmpeg with filters
        utils.run(
            ["ffmpeg", "-i", inputf.name, "-ab", "320k", "-filter:a", filters, output]
        )

        # Read new audio data
        sound = open(output, "rb").read()

    # Clean output file
    os.remove(output)

    # Return new audio data
    return sound
