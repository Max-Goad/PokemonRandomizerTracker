from src import controller, element

class ThemeChangeElement(element.Element):
    def update(self, obj : str):
        controller.instance.changeTheme(obj)

    def layout(self):
        return [[]]
