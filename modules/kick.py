from module import Module


class KickModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):
        if event.text[0] in self.master.config["aliases"]["kick"]:

            # Check if user is specified
            if len(event.text) > 1:

                # Get user info
                user_id, _ = self.master.getmentioninfo(event)

                # If user exists
                if user_id != None:

                    # Get full user data
                    user = self.master.getUser(user_id)[0]

                    # Kick user from chat
                    self.master.method(
                        "messages.removeChatUser",
                        {"chat_id": event.chat_id, "user_id": user["id"]},
                    )

                    # Send reply message
                    self.master.sendreply(
                        event,
                        text=f"{user['first_name']} {user['last_name']} исключен.",
                    )

            return True
