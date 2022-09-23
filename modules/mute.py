from module import Module


class MuteModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def muteHandler(self, event):
        if event.text[0] in self.master.config["aliases"]["mute"]["mute"]:

            peer_id = str(event.peer_id)

            if len(event.text) > 1:

                # Get user data
                user_id, user_name = self.master.getmentioninfo(event)

                # If mute time is specified, than get this time in seconds
                # Time variable will be send to user (user-friendly info)
                if len(event.text) == 3:
                    time = event.text[2]
                    event.text[2] = self.master.gettime(event.text[2])

                # If mute time is not specified, than set infinity seconds
                else:
                    event.text.append(-1)
                    time = event.text[2]

                # Mute only one user
                if user_name != "$all":

                    # Set user dict if it does not exists
                    if f"{peer_id}|{user_id}" not in self.master.config["users"]:
                        self.master.config["users"][f"{peer_id}|{user_id}"] = {}

                    # Mute user
                    self.master.config["users"][f"{peer_id}|{user_id}"]["mute"] = {
                        "time": event.text[2]
                    }

                    # Save configuration
                    self.master.saveConfig()

                    # Send reply message
                    self.master.sendreply(event, f"{user_name} замучен на {time}.")

                # Mute all users from chat
                else:

                    # Set chat dict if it does not exists
                    if peer_id not in self.master.config["users"]:
                        self.master.config["users"][peer_id] = {}

                    # Mute all users from chat
                    self.master.config["users"][peer_id]["mute"] = {
                        "time": event.text[2]
                    }

                    # Save configuration
                    self.master.saveConfig()

                    # Send reply message
                    self.master.sendreply(event, f"Все замучены на {time}.")

    def unMuteHandler(self, event):
        if event.text[0] in self.master.config["aliases"]["mute"]["unmute"]:

            peer_id = str(event.peer_id)

            # If user is specified
            if len(event.text) > 1:

                # Get user data
                user_id, user_name = self.master.getmentioninfo(event)

                # Check if mention is actually user
                if user_name != "$all":

                    # Check if user is currently muted
                    if f"{peer_id}|{user_id}" in self.master.config["users"]:

                        # Unmute user
                        self.master.config["users"][f"{peer_id}|{user_id}"].pop("mute")

                        # Save configuration
                        self.master.saveConfig()

                        # Send reply message
                        self.master.sendreply(event, f"{user_name} размучен.")

                # If mention is @all (or any all users ping)
                else:

                    # Check if chat exists in users dict
                    if peer_id in self.master.config["users"]:

                        # Check if chat is muted
                        if "mute" in self.master.config["users"][peer_id]:

                            # Unmute chat
                            self.master.config["users"][peer_id].pop("mute")

                    # Iterate through all users
                    for user in self.master.config["users"]:

                        # Check if user is in requested chat
                        if user.split("|")[0] == peer_id:

                            # Unmute user
                            self.master.config["users"][user].pop("mute")

                    # Save configuration
                    self.master.saveConfig()

                    # Send reply message
                    self.master.sendreply(event, "Все размучены.")
