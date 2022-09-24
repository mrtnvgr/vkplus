from module import Module


class PrefixModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):
        if event.text[0] in self.master.config["aliases"]["prefix"]["prefix"]:

            # 1 argument commands
            if len(event.text) == 2:

                # Current prefix command
                if event.text[1] in self.master.config["aliases"]["prefix"]["current"]:

                    # Get prefix
                    prefix = self.master.config["prefix"]

                    # Send prefix reply message
                    self.master.sendreply(event, f"Текущий префикс: ({prefix})")

            # 2 argument commands
            elif len(event.text) == 3:

                # Admin-only commands
                if event.from_me:

                    # Change current prefix command
                    if (
                        event.text[1]
                        in self.master.config["aliases"]["prefix"]["change"]
                    ):

                        # Check if prefix is not in invalid prefixes list
                        if (
                            event.text[2]
                            not in self.master.config["aliases"]["prefix"][
                                "invalidlist"
                            ]
                        ):

                            # Change current prefix
                            self.master.config["prefix"] = event.text[2]

                            # Save configuration
                            self.master.saveConfig()

                            # Send reply message
                            self.master.sendreply(
                                event, f"Префикс изменён на ({event.text[2]})"
                            )

                        else:

                            # Send error
                            self.master.sendreply(
                                event, f"Префикс нельзя изменить на ({event.text[2]})"
                            )

            return True
