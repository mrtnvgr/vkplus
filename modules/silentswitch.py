from module import Module


class SilentSwitchModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):

        # Turn on command
        if event.text[0] in self.master.config["aliases"]["silentSwitch"]["on"]:

            # Turn switch on
            self.master.config["silent"] = True

            # Save configuration
            self.master.saveConfig()

            # Delete event message
            self.master.deleteMessage(event.message_id)

        # Turn off command
        elif event.text[0] in self.master.config["aliases"]["silentSwitch"]["off"]:

            # Turn switch off
            self.master.config["silent"] = False

            # Save configuration
            self.master.saveConfig()
