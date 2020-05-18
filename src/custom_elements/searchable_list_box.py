import difflib
from   typing import Mapping, TypeVar
import uuid

import PySimpleGUI as gui

from src.element import Element

T = TypeVar('T')

class SearchableListBox(Element):
    def __init__(self, element : Element, size=(30,25)):
        self.uuid = uuid.uuid4().hex
        self.element = element
        self.original_data = {}
        self.list_box = gui.Listbox([], key=f"SearchableListBox_ListBox_{self.uuid}_callback_available", size=size, font="Arial 16", enable_events=True, select_mode="single", metadata=self.onListSelection)
        self.input_text = gui.InputText(key=f"SearchableListBox_InputText_{self.uuid}", size=(22, 1), font="Arial 16")
        self.button = gui.Button("Search", key=f"SearchableListBox_Button_{self.uuid}_callback_available", size=(8, 1), font="Arial 16", metadata=self.onSearchButton)
        self.sort_buttons = []
        self.filter_buttons = []

    def onSearchButton(self):
        snippet = self.input_text.get()
        [closest_match] = difflib.get_close_matches(snippet, self.list_box.Values, n=1, cutoff=0) or [None]
        if closest_match is None:
            return
        assert closest_match in self.original_data, f"{closest_match} not found in data passed to slb-{self.uuid}"
        self.update(self.original_data[closest_match])

    def onListSelection(self):
        [selected] = self.currentlySelected()
        if selected is None:
            return
        assert selected in self.original_data, f"{selected} not found in data passed to slb-{self.uuid}"
        self.update(self.original_data[selected])

    def populate(self, data : Mapping[str, T]):
        self.original_data = data
        self.list_box.update(values=list(data.keys()))

    def setSelection(self, name):
        name_index = self.list_box.get_list_values().index(name)
        self.list_box.update(set_to_index=name_index, scroll_to_index=name_index)

    def update(self, obj):
        self.input_text.update("")
        self.element.update(obj)

    def currentlySelected(self):
        return self.list_box.get() or [None]

    def eventKeys(self):
        return (self.list_box.Key, self.button.Key)

    def registerSort(self, name, sort_lambda):
        key = f"SearchableListBox_SortButton_{len(self.sort_buttons)}_{self.uuid}_callback_available"
        def createSortLambda(sort_lambda):
            def sort():
                self.list_box.update(sorted(self.list_box.Values, key=sort_lambda))
            return sort

        button = gui.Button(name, key=key, metadata=createSortLambda(sort_lambda))
        self.sort_buttons.append(button)
        return button

    def registerFilter(self, name, filter_lambda):
        def createFilterLambda(filter_lambda):
            def filt():
                self.list_box.update(list(filter(filter_lambda, list(self.original_data.keys()))))
            return filt

        if len(self.filter_buttons) == 0:
            key = f"SearchableListBox_FilterButton_{len(self.filter_buttons)}_{self.uuid}_callback_available"
            self.filter_buttons.append(gui.Button("All", key=key, metadata=createFilterLambda(lambda x:x)))

        key = f"SearchableListBox_FilterButton_{len(self.filter_buttons)}_{self.uuid}_callback_available"
        button = gui.Button(name.title(), key=key, metadata=createFilterLambda(filter_lambda))
        self.filter_buttons.append(button)
        return button

    def expandButtons(self):
        for button in self.sort_buttons:
            button.expand(expand_x=True, expand_y=True)
        for button in self.filter_buttons:
            button.expand(expand_x=True, expand_y=True)


    def layout(self):
        layout = [gui.Column([  [self.input_text, self.button],
                                [self.list_box],
                             ])]
        if len(self.sort_buttons) > 0:
            layout.append(gui.Column([ [gui.Text("Sort By:")], *[[x] for x in self.sort_buttons]]))
        if len(self.filter_buttons) > 0:
            layout.append(gui.Column([ [gui.Text("Filter By:")], *[[x] for x in self.filter_buttons]]))
        return [layout]
