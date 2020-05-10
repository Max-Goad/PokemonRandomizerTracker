import PySimpleGUI as gui
import typing
import uuid

from src import pokemon

class TeamDisplayElement:
    def __init__(self, index):
        self.uuid = uuid.uuid4().hex
        self.index = index
        self.empty = True
        self.current_pokemon = None
        self.on_update = lambda: None

        self.clear_button = gui.Button("X", key=f"team_display_element_clear_{self.uuid}", size=(2,1), metadata=self, disabled=True)
        self.title = gui.Text(f"", key=f"team_display_element_title_{self.uuid}", size=(10, 1), font="Impact 14", enable_events=True)
        self.primary_type_button = pokemon.Type.createButton(f"team_display_element_type_primary_{self.uuid}")
        self.secondary_type_button = pokemon.Type.createButton(f"team_display_element_type_secondary_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"team_display_element_attribute_name_{attr_name}_{self.uuid}", size=(3, 1)), gui.Text("", key=f"team_display_element_attribute_value_{attr_name}_{self.uuid}", size=(3, 1)), pokemon.Stats.Attribute.createGraph(f"team_display_element_attribute_bar_{attr_name}_{self.uuid}")]

    def update(self, pkmn : pokemon.Pokemon):
        self.current_pokemon = pkmn
        self.clear_button.update(disabled=False)
        self.title.update(f"{pkmn.name}")
        pkmn.type.updateButtons(self.primary_type_button, self.secondary_type_button, subsample=7)

        for attr_name, row_elements in self.attribute_rows.items():
            aname, avalue, agraph = row_elements
            attribute = getattr(pkmn.stats, attr_name)
            aname.update(attribute.short_name)
            avalue.update(attribute.value)
            agraph.update()
            attribute.drawOn(agraph)

        self.empty = False
        self.on_update()

    def clear(self):
        self.current_pokemon = None
        self.clear_button.update(disabled=True)
        self.title.update("")
        self.primary_type_button.update(image_filename="")
        self.secondary_type_button.update(image_filename="")
        for row_elements in self.attribute_rows.values():
            aname, avalue, agraph = row_elements
            aname.update("")
            avalue.update("")
            agraph.erase()

        self.empty = True
        self.on_update()


    def layout(self):
        return  [ [self.clear_button, self.title, self.primary_type_button, self.secondary_type_button] ,
                  *self.attribute_rows.values(),
                ]
