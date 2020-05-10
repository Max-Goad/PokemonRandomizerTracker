import PySimpleGUI as gui
import uuid

from src import pokemon

class PokemonDisplayElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        # Header
        self.title = gui.Text(f"", key=f"pokemon_display_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.primary_type_button = pokemon.Type.createButton(f"pokemon_display_element_type_primary_{self.uuid}")
        self.secondary_type_button = pokemon.Type.createButton(f"pokemon_display_element_type_secondary_{self.uuid}")
        # Attributes
        self.attribute_rows = {}
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"pokemon_display_element_attribute_name_{attr_name}_{self.uuid}", size=(12, 1)), gui.Text("", key=f"pokemon_display_element_attribute_value_{attr_name}_{self.uuid}", size=(3, 1)), pokemon.Stats.Attribute.createGraph(f"pokemon_display_element_attribute_bar_{attr_name}_{self.uuid}")]
        # Moveset
        self.moveset_title_text = gui.Text(f"", key=f"pokemon_display_element_moveset_title_{self.uuid}", size=(8,1), font="Arial 14")
        self.moveset_rows = []
        for i in range(20):
            # One text for the level ("Level 50 - "), and one for the actual move name (which is clickable!)
            self.moveset_rows.append((gui.Text(f"", key=f"pokemon_display_element_moveset_level_{i}_{self.uuid}", size=(10,1), font="Consolas 10"),
                                      gui.Text(f"", key=f"pokemon_display_element_moveset_move_name_{i}_{self.uuid}", size=(40,1), font="Consolas 10", enable_events=True)))
        # Wild Occurrences
        self.wild_occurrence_title_text = gui.Text(f"", key=f"pokemon_display_element_wild_occurrence_title_{self.uuid}", size=(8,1), font="Arial 14")
        self.wild_occurrence_rows = []
        for i in range(10):
            # One text for the location (which is clickable!), and one for the levels
            self.wild_occurrence_rows.append((gui.Text(f"", key=f"pokemon_display_element_wild_occurrence_location_{i}_{self.uuid}", size=(30,1), font="Consolas 10", enable_events=True),
                                               gui.Text(f"", key=f"pokemon_display_element_wild_occurrence_levels_{i}_{self.uuid}", size=(20,1), font="Consolas 10")))

    def update(self, pkmn : pokemon.Pokemon):
        # Header
        self.title.update(f"{pkmn.name}")
        pkmn.type.updateButtons(self.primary_type_button, self.secondary_type_button)

        # Attributes
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            aname, avalue, agraph = self.attribute_rows[attr_name]
            attribute = getattr(pkmn.stats, attr_name)
            aname.update(attribute.name)
            avalue.update(attribute.value)
            attribute.drawOn(agraph)

        # Moveset
        self.moveset_title_text.update("Moveset:")
        for i in range(20):
            if i < len(pkmn.moveset.level_move_mappings):
                level, move_name = pkmn.moveset.level_move_mappings[i]
                self.moveset_rows[i][0].update(f"Level{level: >3} -")
                self.moveset_rows[i][1].update(f"{move_name}")
            else:
                self.moveset_rows[i][0].update("")
                self.moveset_rows[i][1].update("")

        # Wild Occurrences
        self.wild_occurrence_title_text.update("Locations:")
        for i in range(5):
            if i < len(pkmn.wild_occurrences):
                wo = pkmn.wild_occurrences[i]
                self.wild_occurrence_rows[i][0].update(wo.location)
                self.wild_occurrence_rows[i][1].update(wo.condensedLevelStr())
            else:
                self.wild_occurrence_rows[i][0].update("")
                self.wild_occurrence_rows[i][1].update("")


    def layout(self):
        moveset_column = gui.Column([ [self.moveset_title_text],
                                      *[[x, y] for x, y in self.moveset_rows],
                                    ])
        wild_occurrence_column = gui.Column([ [self.wild_occurrence_title_text],
                                              *[[x, y] for x, y in self.wild_occurrence_rows],
                                            ])
        return  [ [self.title, self.primary_type_button, self.secondary_type_button] ,
                  *self.attribute_rows.values(),
                  [moveset_column, wild_occurrence_column],
                ]
