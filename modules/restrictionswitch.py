from module import Module


class RestrictionSwitchModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):

        # Turn on command
        if event.text[0] in self.master.config["aliases"]["restSwitch"]["on"]:

            # Turn switch on
            self.master.config["restrictions"] = True

            # Save configuration
            self.master.saveConfig()

            # Send reply message
            self.master.sendme(event, "Ограничения включены.")

        # Turn off command
        elif event.text[0] in self.master.config["aliases"]["restSwitch"]["off"]:

            # Turn switch off
            self.master.config["restrictions"] = False

            # Save configuration
            self.master.saveConfig()

            # Send reply message
            self.master.sendme(event, "Ограничения выключены.")
