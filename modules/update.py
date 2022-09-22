import utils

class UpdateModule:
    def __init__(self, master):
        self.master = master

    def updateHandler(self, event):
        if event.text[0] in self.config["aliases"]["update"]:
            if event.from_me:
                utils.update()
