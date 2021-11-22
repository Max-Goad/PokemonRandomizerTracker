from   typing import Mapping, List, Set
import uuid

import PySimpleGUI as gui

from src import element, pokemon


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
            self.tab_elements[classification] = [SublocationDisplayElement() for i in range(35)]
            self.tabs[classification] = gui.Tab(classification, [[gui.Column([slde.layout() for slde in self.tab_elements[classification]], scrollable=True, vertical_scroll_only=True)]], visible=False)

    def update(self, location : pokemon.Location):
        self.title.update(f"{location.name}")
        self.set_tab_visibility({sl.classification for sl in location.sublocations})
        iter_mapping = self.tab_element_iterators()
        for sl in sorted(location.sublocations):
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

    def set_tab_visibility(self, visible_tabs : Set[str]):
        all_classifications = set(pokemon.Sublocation.classifications())
        for classification in all_classifications:
            if classification in visible_tabs:
                self.tabs[classification].update(visible=True)
                self.tabs[classification].set_focus()
            else:
                self.tabs[classification].update(visible=False)


    def layout(self):
        return  [ [self.title],
                  [gui.TabGroup([[*self.tabs.values()]])]
                ]
