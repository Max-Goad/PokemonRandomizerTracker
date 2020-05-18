import PySimpleGUI as gui

from src.custom_elements import WindowElement

class Controller:
    def __init__(self):
        self.element_class = WindowElement
        self.window = None
        self.current_element = None

    def read(self):
        event, values = self.window.read()
        encoded_event = event.encode('utf-8') if event is not None else None
        return event, encoded_event, values

    def newWindow(self, title, location=(None, None)):
        self.current_element = self.element_class()
        self.window = gui.Window(title, self.current_element.layout(), location=location, return_keyboard_events=True, use_default_focus=False, finalize=True)
        self.current_element.populateThemes()
        self.current_element.expandButtons()
        # TODO: This auto-ingest is temporary to speed up dev (could it be a setting?)
        self.current_element.ingest_button.click()

    def changeTheme(self, new_theme):
        old_window = self.window
        gui.theme(new_theme)
        self.newWindow(old_window.Title, old_window.current_location())
        old_window.close()
        self.window.bring_to_front()

instance = Controller()
