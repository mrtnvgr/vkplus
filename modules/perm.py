from module import Module


class PermissionsModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def permHandler(self, event):
        if event.text[0] in self.master.config["aliases"]["perm"]["cmd"]:

            # 3 arguments commands
            if len(event.text) == 4:

                # Get user info
                user_id, user_name = self.master.getmentioninfo(event)

                perm = event.text[3]

                # Add perm command
                if event.text[1] in self.master.config["aliases"]["perm"]["add"]:

                    # Check if perm exists
                    if perm in self.master.config["perms"]:

                        # Add permission to user
                        self.master.config["perms"][perm].append(int(user_id))

                        # Save configuration
                        self.master.saveConfig()

                        # Send reply message
                        self.master.sendreply(
                            event,
                            f"{user_name} теперь может использовать {perm}.",
                        )

                    else:

                        # Send error message
                        self.master.sendreply(event, f'Права "{perm}" не существует.')

                # Delete perm command
                elif event.text[1] in self.master.config["aliases"]["perm"]["delete"]:

                    # Check if perm exists
                    if perm in self.master.config["perms"]:

                        # Check if user in perm
                        if user_id in self.master.config["perms"][perm]:

                            # Remove perm from user
                            self.master.config["perms"][perm].remove(user_id)

                            # Save configuration
                            self.master.saveConfig()

                            # Send reply message
                            self.master.sendreply(
                                event,
                                f"{user_name} теперь нельзя использовать {event.text[3]}.",
                            )

                        else:

                            # Send error message
                            self.master.sendreply(
                                event,
                                f'У пользователя {user_name} нету права "{perm}".',
                            )

                    else:

                        # Send error message
                        self.master.sendreply(event, f"Права '{perm}' не существует.")

            # Commands with optional arguments
            if len(event.text) >= 2:

                # Permisson list commands
                if event.text[1] in self.master.config["aliases"]["perm"]["list"]:

                    # Send all existing perms (no arguments specified)
                    if len(event.text) == 2:

                        # Send reply message
                        self.master.sendreply(
                            event, f"Perks: {', '.join(self.master.config['perms'])}"
                        )

                    # 1 argument specified
                    elif len(event.text) == 3:

                        # Get user info
                        user_id, user_name = self.master.getmentioninfo(event)

                        # Send perm users (user does not exist)
                        if user_id == None:

                            perm = event.text[2]

                            users = []

                            # Iterate through perm users
                            for user_id in self.master.config["perms"][perm]:

                                # Get user info
                                user = self.master.getUser(user_id)[0]

                                # Append user name to users list
                                users.append(
                                    f"{user['first_name']} {user['last_name']}"
                                )

                            # Send reply message
                            self.master.sendreply(event, f"{perm}: {', '.join(users)}")

                        # Send user perms (user exists)
                        else:

                            perms = []

                            # Iterate through perms
                            for perm in self.master.config["perms"]:

                                # Check if user in perm
                                if int(user_id) in self.master.config["perms"][perm]:

                                    # Append perm to perms list
                                    perms.append(perm)

                            # Check if user has not any perms
                            if perms == []:

                                # Set "None" instead of empty value
                                perms = ["None"]

                            # Send reply message
                            self.master.sendreply(
                                event, f"{user_name} разрешения: {', '.join(perms)}"
                            )

            return True
