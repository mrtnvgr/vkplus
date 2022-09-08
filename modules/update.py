import utils

class UpdateModule:
    def __init__(self, master):
        self.master = master

    def updateHandler(event):
        if event.text[0] in ("апдейт", "апдэйт", "update"):
            if event.from_me:
                utils.update()
