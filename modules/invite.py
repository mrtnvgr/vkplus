from module import Module


class InviteModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inviteHandler(self, event):
        if event.text[0] in self.master.config["aliases"]["invite"]:

            # Check if any arguments specified
            if len(event.text) > 1:

                # Get user info
                user_id, user_name = self.master.getmentioninfo(event)

                # Check if user exists
                if user_id != None:

                    # Send chat invite to user
                    self.master.method(
                        "messages.addChatUser",
                        {"chat_id": event.chat_id, "user_id": user_id},
                    )

                    # Send reply message
                    self.master.sendreply(event, f"{user_name} добавлен.")
