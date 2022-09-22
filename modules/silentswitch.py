from module import Module


class SilentSwitchModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):
        if event.text[0] in self.master.config["aliases"]["silentSwitch"]["on"]:
            self.master.config["silent"] = True
            self.master.saveConfig()
            self.master.deleteMessage(event.message_id)
        elif event.text[0] in self.master.config["aliases"]["silentSwitch"]["off"]:
            self.master.config["silent"] = False
            self.master.saveConfig()
