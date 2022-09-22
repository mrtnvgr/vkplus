import json, os


class Config:
    def __init__(self, master, path):
        self.master = master
        self.path = path
        self.get()
        self.master.config = self.config

    def get(self):
        """Get config"""

        if os.path.exists(self.path):
            self.config = json.load(open(self.path))
        else:
            token = input("VK ADMIN API TOKEN: ")
            self.config = {"token": token}

        self.check()

    def check(self):
        """All config checks"""

        # Default values
        self.addDefaultValue("prefix", "%")
        self.addDefaultValue("mention", "")

        self.addDefaultValue("users", {})
        self.addDefaultValue("restrictions", True)
        self.addDefaultValue("silent", False)

        self.addDefaultValue("photos", {})
        self.addDefaultValue("photos.token", "")
        self.addDefaultValue("photos.query", "")
        self.addDefaultValue("photos.categories", "010")
        self.addDefaultValue("photos.purity", "100")
        self.addDefaultValue("photos.ids", [])

        self.addDefaultValue("aliases", {})

        self.addDefaultValue("aliases.restSwitch", {})
        self.addDefaultValue("aliases.restSwitch.on", ("вкл", "он", "on", "включить"))
        self.addDefaultValue(
            "aliases.restSwitch.off", ("выкл", "офф", "оф", "off", "выключить")
        )

        self.addDefaultValue("aliases.silentSwitch", {})
        self.addDefaultValue("aliases.silentSwitch.on", ("silent", "сайлент", "тихо"))
        self.addDefaultValue(
            "aliases.silentSwitch.off", ("unsilent", "ансайлент", "громко")
        )

        self.addDefaultValue("aliases.mute", {})
        self.addDefaultValue(
            "aliases.mute.mute",
            (
                "мут",
                "молчи",
                "помолчи",
                "молчать",
                "терпи",
                "потерпи",
                "завали",
                "заткнись",
                "mute",
                "mut",
            ),
        )
        self.addDefaultValue(
            "aliases.mute.unmute", ("размут", "анмут", "unmute", "unmut")
        )

        # Default permissions
        self.checkPermissions()

    def checkPermissions(self):
        """Check permission values"""
        self.addDefaultValue("perms", {})

        for perm in ("pics", "customPics", "core"):
            self.addDefaultValue(f"perms.{perm}", [])

        # Convert user names to user ids
        for perm in self.config["perms"]:
            for index, elem in enumerate(self.config["perms"][perm]):
                if type(elem) is str:
                    self.config["perms"][perm][index] = self.master.getUser(elem)[0][
                        "id"
                    ]

    def addDefaultValue(self, keys, value):
        """Add default value to config"""

        keys = keys.split(".")
        config = self.config

        for key in keys:
            if key in config:
                config = config[key]
            else:
                # FIXME: ugly implementation
                kys = [f'["{key}"]' for key in keys]
                exec(f"self.config{''.join(kys)} = {repr(value)}")
