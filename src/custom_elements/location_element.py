import collections
import PySimpleGUI as gui
from   typing import Mapping, List
import uuid

from src import element, pokemon
from src.external import utils

class SublocationDisplayElement(element.Element):
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.set_num_element = gui.Text("", size=(8, 1))
        self.wild_occurrences_element = gui.Text("", size=(100, 1))

    def update(self, sublocation : pokemon.Sublocation):
        self.set_num_element.update(sublocation.set_num)
        wo_texts = [f"{wo.pkmn_name} {wo.condensedLevelStr()}" for wo in sublocation.wild_occurrences]
        self.wild_occurrences_element.update(" | ".join(wo_texts))

    def clear(self):
        self.set_num_element.update("")
        self.wild_occurrences_element.update("")

    def layout(self):
        return [self.set_num_element, self.wild_occurrences_element]

class LocationElement(element.Element):
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"location_element_title_{self.uuid}", size=(25, 1), font="Impact 20")
        self.tab_elements : Mapping[str, List[SublocationDisplayElement]] = {}
        self.tabs : Mapping[str, gui.Tab] = {}
        for classification in pokemon.Sublocation.classifications():
            self.tab_elements[classification] = [SublocationDisplayElement() for i in range(20)]
            self.tabs[classification] = gui.Tab(classification, [slde.layout() for slde in self.tab_elements[classification]])

    def update(self, location : pokemon.Location):
        self.title.update(f"{location.name}")
        iter_mapping = self.tab_element_iterators()
        for sl in location.sublocations:
            element_to_fill : SublocationDisplayElement = next(iter_mapping[sl.classification])
            element_to_fill.update(sl)
        self.clear_tab_elements(iter_mapping)

    def tab_element_iterators(self):
        iter_mapping = {}
        for classification, display_elements in self.tab_elements.items():
            iter_mapping[classification] = iter(display_elements)
        return iter_mapping

    def clear_tab_elements(self, iter_mapping):
        for it in iter_mapping.values():
            slde = next(it, None)
            while slde is not None:
                slde.clear()
                slde = next(it, None)




    def layout(self):
        return  [ [self.title],
                  [gui.TabGroup([[*self.tabs.values()]])]
                ]