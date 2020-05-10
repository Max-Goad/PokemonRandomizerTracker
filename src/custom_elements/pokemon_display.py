import PySimpleGUI as gui
import uuid

from src import pokemon

class PokemonDisplayElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"pokemon_display_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.primary_type_button = pokemon.Type.createButton(f"pokemon_display_element_type_primary_{self.uuid}")
        self.secondary_type_button = pokemon.Type.createButton(f"pokemon_display_element_type_secondary_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"pokemon_display_element_attribute_name_{attr_name}_{self.uuid}", size=(12, 1)), gui.Text("", key=f"pokemon_display_element_attribute_value_{attr_name}_{self.uuid}", size=(3, 1)), pokemon.Stats.Attribute.createGraph(f"pokemon_display_element_attribute_bar_{attr_name}_{self.uuid}")]
        self.moveset_title_text = gui.Text(f"", key=f"pokemon_display_element_moveset_title_{self.uuid}", size=(8,1), font="Arial 14")
        self.moveset_rows = []
        for i in range(20):
            # One text for the level ("Level 50 - "), and one for the actual move name (which is clickable!)
            self.moveset_rows.append((gui.Text(f"", key=f"pokemon_display_element_moveset_level_{i}_{self.uuid}", size=(10,1), font="Consolas 10"),
                                      gui.Text(f"", key=f"pokemon_display_element_moveset_move_name_{i}_{self.uuid}", size=(40,1), font="Consolas 10", enable_events=True)))

    def update(self, pkmn : pokemon.Pokemon):
        self.title.update(f"{pkmn.name}")
        pkmn.type.updateButtons(self.primary_type_button, self.secondary_type_button)

        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            aname, avalue, agraph = self.attribute_rows[attr_name]
            attribute = getattr(pkmn.stats, attr_name)
            aname.update(attribute.name)
            avalue.update(attribute.value)
            attribute.drawOn(agraph)

        self.moveset_title_text.update("Moveset:")
        for i in range(20):
            if i < len(pkmn.moveset.level_move_mappings):
                level, move_name = pkmn.moveset.level_move_mappings[i]
                self.moveset_rows[i][0].update(f"Level{level: >3} -")
                self.moveset_rows[i][1].update(f"{move_name}")
            else:
                self.moveset_rows[i][0].update("")
                self.moveset_rows[i][1].update("")

    def layout(self):
        return  [ [self.title, self.primary_type_button, self.secondary_type_button] ,
                  *self.attribute_rows.values(),
                  [self.moveset_title_text],
                  *[[x, y] for x, y in self.moveset_rows],
                ]
