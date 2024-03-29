import PySimpleGUI as gui
import uuid

from src import element, pokemon

class MoveElement(element.Element):
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"move_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.type_button = pokemon.Type.createButton(f"move_element_type_{self.uuid}")
        self.category_button = pokemon.Type.createButton(f"move_element_category_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in pokemon.Move.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"move_element_attribute_name_{attr_name}_{self.uuid}", size=(12, 1)), gui.Text("", size=(3, 1)), pokemon.Stats.Attribute.createGraph(f"move_element_attribute_bar_{attr_name}_{self.uuid}")]

    def update(self, move : pokemon.Move):
        self.title.update(f"{move.name}")
        move.type.updateButtons(self.type_button)
        move.category.updateButtons(self.category_button)

        for attr_name in pokemon.Move.ALL_ATTR_NAMES:
            aname, avalue, agraph = self.attribute_rows[attr_name]
            attribute = getattr(move, attr_name)
            aname.update(attribute.name)
            avalue.update(attribute.value)
            attribute.drawOn(agraph)

    def layout(self):
        return  [ [self.title, self.type_button, self.category_button],
                  *self.attribute_rows.values()
                ]
