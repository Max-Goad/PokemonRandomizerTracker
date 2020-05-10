import PySimpleGUI as gui
import uuid

class SearchableListBox:
    def __init__(self, element, size=(30,25)):
        self.uuid = uuid.uuid4().hex
        self.element = element
        self.list_box = gui.Listbox([], key=f"SearchableListBox_ListBox_{self.uuid}", size=size, font="Arial 16", enable_events=True, select_mode="single")
        self.input_text = gui.InputText(key=f"SearchableListBox_InputText_{self.uuid}", size=(22, 1), font="Arial 16")
        self.button = gui.Button("Search", key=f"SearchableListBox_Button_{self.uuid}", size=(8, 1), font="Arial 16")

    def populate(self, values):
        self.list_box.update(values=values)

    def setSelection(self, name):
        name_index = self.list_box.get_list_values().index(name)
        self.list_box.update(set_to_index=name_index, scroll_to_index=name_index)

    def update(self, values):
        self.input_text.update("")
        self.element.update(values)

    def currentlySelected(self):
        return self.list_box.get()

    def eventKeys(self):
        return (self.list_box.Key, self.button.Key)

    def layout(self):
        return [[self.input_text, self.button],
                [self.list_box]]
