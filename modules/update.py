import utils

from module import Module

class UpdateModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def updateHandler(self, event):
        if event.text[0] in self.master.config["aliases"]["update"]:
            if event.from_me:
                utils.update()
