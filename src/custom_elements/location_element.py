import PySimpleGUI as gui
import uuid

from src import pokemon

class LocationElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"location_element_title_{self.uuid}", size=(25, 1), font="Impact 20")
        self.sublocation_rows = []
        for i in range(10):
            self.sublocation_rows.append([gui.Text(f"", key=f"location_element_sublocation_set_num_{i}_{self.uuid}", size=(8,1), font="Consolas 10"),
                                          gui.Text(f"", key=f"location_element_sublocation_classification_{i}_{self.uuid}", size=(20,1), font="Consolas 10"),
                                         ])

    def update(self, location : pokemon.Location):
        self.title.update(f"{location.name}")

        # Sublocations?
        for i in range(len(self.sublocation_rows)):
            if i < len(location.sublocations):
                sl = location.sublocations[i]
                self.sublocation_rows[i][0].update(sl.set_num)
                self.sublocation_rows[i][1].update(sl.classification)
            else:
                self.sublocation_rows[i][0].update("")
                self.sublocation_rows[i][1].update("")

    def layout(self):
        return  [ [self.title],
                  *[x for x in self.sublocation_rows]
                ]
