class InviteModule:
    def __init__(self, master):
        self.master = master

    def inviteHandler(self, event):
        if event.text[0] in self.config["aliases"]["invite"]:
            if len(event.text)>1:
                user_id, _ = self.master.getmentioninfo(event)
                if user_id!=None:
                    user = self.master.getUser(user_id)[0]
                    self.master.method("messages.addChatUser",
                                      {"chat_id": event.chat_id,
                                       "user_id": user["id"]})
                    self.master.sendreply(event, text=f"{user['first_name']} {user['last_name']} добавлен.")
