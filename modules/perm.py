class PermissionsModule:
    def __init__(self, master):
        self.master = master

    def permHandler(self, event):
        if event.text[0] in ("perm", "перм", "perk", "перк", "разрешение", "права"):
            if len(event.text)==4:
                user_id, user_name = self.master.getmentioninfo(event)
                if event.text[1] in ("добавить", "дать", "add"):
                    if event.text[3] in self.master.config["perms"]:
                        self.master.config["perms"][event.text[3]].append(int(user_id))
                        self.master.saveConfig()
                        self.master.sendreply(event, f"{user_name} теперь может использовать {event.text[3]}.")
                elif event.text[1] in ("удалить", "забрать", "убрать", "delete", "del"):
                    if event.text[3] in self.master.config["perms"]:
                        for id in self.master.config["perms"][event.text[3]]:
                            if id==user_id:
                                self.master.config["perms"][event.text[3]].remove(int(id))
                                self.master.saveConfig()
                                self.master.sendreply(event, f"{user_name} теперь нельзя использовать {event.text[3]}.")
            if len(event.text)>=2:
                if event.text[1].lower() in ("list", "лист", "список"):
                    if len(event.text)==2:
                        self.master.sendreply(event, f"Perks: {', '.join(self.master.config['perms'])}")
                    elif len(event.text)==3:
                        user_id, user_name = self.master.getmentioninfo(event)
                        if user_id==None:
                            users = []
                            for user_id in self.master.config['perms'][event.text[2]]:
                                user = self.master.getUser(user_id)[0]
                                users.append(f"{user['first_name']} {user['last_name']}")
                            self.master.sendreply(event, f"Perk {event.text[2]} users: {', '.join(users)}")
                        else:
                            perks = []
                            for perk in self.master.config["perms"]:
                                if int(user_id) in self.master.config["perms"][perk]:
                                    perks.append(perk)
                            if perks==[]: perks = ["None"]
                            self.master.sendreply(event, f"{user_name} perks: {', '.join(perks)}")
