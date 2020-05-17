import PySimpleGUI as gui
import uuid

from src import pokemon

class LocationElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"location_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.wild_occurrence_rows = []
        for i in range(10):
            # One text for the location (which is clickable!), and one for the levels
            self.wild_occurrence_rows.append((gui.Text(f"", key=f"location_element_wild_occurrence_name_{i}_{self.uuid}", size=(30,1), font="Consolas 10", enable_events=True),
                                               gui.Text(f"", key=f"location_element_wild_occurrence_levels_{i}_{self.uuid}", size=(20,1), font="Consolas 10")))

    def update(self, location : pokemon.Location):
        self.title.update(f"{location.name}")

        # Wild Occurrences
        for i in range(len(self.wild_occurrence_rows)):
            if i < len(location.wild_occurrences):
                wo = location.wild_occurrences[i]
                self.wild_occurrence_rows[i][0].update(wo.location)
                self.wild_occurrence_rows[i][1].update(wo.condensedLevelStr())
            else:
                self.wild_occurrence_rows[i][0].update("")
                self.wild_occurrence_rows[i][1].update("")

    def layout(self):
        return  [ [self.title],
                  *[[x, y] for x, y in self.wild_occurrence_rows]
                ]
