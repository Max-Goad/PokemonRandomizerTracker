import PySimpleGUI as gui
import uuid

from src.elements import SearchableListBox

class SLBSorter:
    def __init__(self, slb_to_sort : SearchableListBox, key_prefix : str):
        self.uuid = uuid.uuid4().hex
        self.slb = slb_to_sort
        self.key_prefix = key_prefix
        self.sort_buttons = []
        self.sort_lambdas = {}

    def registerSort(self, name, sort_lambda):
        key = f"{self.key_prefix}_{len(self.sort_buttons)}_{self.uuid}"
        self.sort_lambdas[key] = sort_lambda
        button = gui.Button(name, key=key, metadata=self)
        self.sort_buttons.append(button)
        return button

    def sortBy(self, key):
        sort_lambda = self.sort_lambdas[key]
        self.slb.list_box.update(sorted(self.slb.list_box.Values, key=sort_lambda, reverse=True))