from module import Module
import random

class RollModule(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handler(self, event):
        if event.text[0] in self.master.config["aliases"]["roll"]:

            value = None

            if len(event.text) == 1:

                event.text.append("1-100")

            if event.text[1].count("-") == 1:

                ranges = event.text[1].split("-")

                if ranges[0].isdigit() and ranges[1].isdigit():
                    
                    value = random.randint(*map(int, ranges))

            if event.text[1].count(",") != 0 or len(event.text) > 2:

                values = []

                if event.text[1].count(",") != 0:
                    
                    values.extend(event.text[1].split(","))

                if len(event.text) > 2:
                    
                    values.extend(event.text[1:])

                value = random.choice(values)
            
            self.master.sendreply(event, value)
