from module import Module


class RestrictionSwitchModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):
        if event.text[0] in self.master.config["aliases"]["restSwitch"]["on"]:
            self.master.config["restrictions"] = True
            self.master.saveConfig()
            self.master.sendme(event, "Ограничения включены.")
        elif event.text[0] in self.master.config["aliases"]["restSwitch"]["off"]:
            self.master.config["restrictions"] = False
            self.master.saveConfig()
            self.master.sendme(event, "Ограничения выключены.")
