import PySimpleGUI as gui
import uuid

from src import pokemon
from src.external.parsers import getGroups

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
        # Held Items
        self.held_items_title_text = gui.Text(f"", key=f"pokemon_display_element_held_items_title_{self.uuid}", size=(10,1), font="Arial 16")
        self.held_items_rows = []
        for i in range(3):
            # One text for the item (which is clickable!), and one for the occurrence rate
            self.held_items_rows.append((gui.Text(f"", key=f"pokemon_display_element_held_items_name_{i}_{self.uuid}", size=(15,1), font="Consolas 12", enable_events=True),
                                         gui.Text(f"", key=f"pokemon_display_element_held_items_rate_{i}_{self.uuid}", size=(7,1), font="Consolas 12")))

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

        # Held Items
        self.held_items_title_text.update("Held Items:")
        for i, (name_elem, rate_elem) in enumerate(self.held_items_rows):
            if i < len(pkmn.items):
                item_name, item_rate = getGroups(r"(.+) [(]([\w\d%]+)[)]", pkmn.items[i].strip())
                name_elem.update(item_name)
                rate_elem.update(item_rate)
            else:
                name_elem.update("")
                rate_elem.update("")

        # Moveset
        self.moveset_title_text.update("Moveset:")
        for i in range(len(self.moveset_rows)):
            if i < len(pkmn.moveset.level_move_mappings):
                level, move_name = pkmn.moveset.level_move_mappings[i]
                self.moveset_rows[i][0].update(f"Level{level: >3} -")
                self.moveset_rows[i][1].update(f"{move_name}")
            else:
                self.moveset_rows[i][0].update("")
                self.moveset_rows[i][1].update("")

        # Wild Occurrences
        self.wild_occurrence_title_text.update("Locations:")
        for i in range(len(self.wild_occurrence_rows)):
            if i < len(pkmn.wild_occurrences):
                wo = pkmn.wild_occurrences[i]
                self.wild_occurrence_rows[i][0].update(wo.location.displayName())
                self.wild_occurrence_rows[i][1].update(wo.condensedLevelStr())
            else:
                self.wild_occurrence_rows[i][0].update("")
                self.wild_occurrence_rows[i][1].update("")


    def layout(self):
        summary_column = gui.Column([ [self.title, self.primary_type_button, self.secondary_type_button] ,
                                      *self.attribute_rows.values()
                                    ])
        held_items_column = gui.Column([ [self.held_items_title_text],
                                         *[[x, y] for x, y in self.held_items_rows],
                                       ])
        moveset_column = gui.Column([ [self.moveset_title_text],
                                      *[[x, y] for x, y in self.moveset_rows],
                                    ])
        wild_occurrence_column = gui.Column([ [self.wild_occurrence_title_text],
                                              *[[x, y] for x, y in self.wild_occurrence_rows],
                                            ])
        return  [ [summary_column, held_items_column],
                  [moveset_column, wild_occurrence_column],
                ]
