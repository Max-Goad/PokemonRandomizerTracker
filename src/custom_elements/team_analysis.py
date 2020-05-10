from   functools import reduce
import PySimpleGUI as gui
import typing
import uuid

from src import pokemon, types
from src.custom_elements.team_display import TeamDisplayElement
from src.external import utils

class TeamAnalysisElement:
    def __init__(self, team_elements : typing.List[TeamDisplayElement]):
        self.uuid = uuid.uuid4().hex
        self.team_elements = team_elements
        for element in self.team_elements:
            element.on_update = lambda: self.update()

        wex = """\
"Weaknesses" indicate types that, on average, are more effective against your team as a whole.

The measure is calculated by taking each member's type matchups, and multiplaying them together.

Your team may still show a weakness for a certain type even if you have a Pokemon that is resistant to that type.

Example:
    If your team has 2 Pokemon that are weak to WATER, and one that's resistant to WATER,
    then the team as a whole will still be rated as "weak" to WATER.
    However, if you were to add another Pokemon that was resistant to WATER, the weakness would be removed.
"""
        self.weakness_explanation_button = gui.Button("?", key=f"explanation_button_weakness_{self.uuid}", size=(2,1), metadata=wex)

        rex = """\
"Resistances" indicate types that, on average, are less effective against your team as a whole.

The measure is calculated by taking each member's type matchups, and multiplaying them together.

Your team may still show a resistance for a certain type even if you have a Pokemon that is weak to that type.

Example:
    If your team has 2 Pokemon that are resistant to WATER, and one that's weak to WATER,
    then the team as a whole will still be rated as "resistant" to WATER.
    However, if you were to add another Pokemon that was weak to WATER, the resistance would be removed.
"""
        self.resistance_explanation_button = gui.Button("?", key=f"explanation_button_resistance_{self.uuid}", size=(2,1), metadata=rex)

        mex = """\
"Missing" indicate types that no Pokemon on your team are resistant to. If an opposing pokemon
were to use a move of that type, then all Pokemon on your team would at least take normal damage.

This is usually a sign of a non-diversely typed team, and adding a Pokemon that has a resistance
to that type will remove the type from the "Missing" list.
"""
        self.missing_explanation_button = gui.Button("?", key=f"explanation_button_resistance_{self.uuid}", size=(2,1), metadata=mex)

        self.team_weakness_type_buttons = [pokemon.Type.createButton(f"team_analysis_element_weakness_button_{i}_{self.uuid}") for i in range(len(types.all_types))]
        self.team_resistance_type_buttons = [pokemon.Type.createButton(f"team_analysis_element_resistance_button_{i}_{self.uuid}") for i in range(len(types.all_types))]
        self.team_missing_type_buttons = [pokemon.Type.createButton(f"team_analysis_element_missing_button_{i}_{self.uuid}") for i in range(len(types.all_types))]


    def update(self):
        team_pkmn = [element.current_pokemon for element in self.team_elements if element.current_pokemon is not None]
        team_pkmn : typing.List[pokemon.Pokemon]

        combined_mappings = {}
        if len(team_pkmn) != 0:
            combined_mappings = reduce(lambda x,y: types.calculator.combineMappings(x, y), [pkmn.type.defenceMapping() for pkmn in team_pkmn])
        team_weaknesses = set(types.calculator.filterWeaknesses(combined_mappings).keys())
        team_resistances = set(types.calculator.filterResistances(combined_mappings).keys())
        combined_individual_resistances = set(utils.flatten([types.calculator.filterResistances(pkmn.type.defenceMapping()).keys() for pkmn in team_pkmn]))
        missing_individual_resistances = {x for x in types.all_types if x not in combined_individual_resistances}

        # print(f"Combined mapping: {combined_mappings}")
        # print(f"Team weaknesses are: {team_weaknesses}")
        # print(f"Team resistances are: {team_resistances}")
        # print(f"Missing individual resistances: {missing_individual_resistances}")

        w_iter = iter(team_weaknesses)
        r_iter = iter(team_resistances)
        m_iter = iter(missing_individual_resistances)
        subsample = 6

        for i in range(len(types.all_types)):
            pokemon.Type.updateButton(self.team_weakness_type_buttons[i], next(w_iter, None), subsample=subsample)
            pokemon.Type.updateButton(self.team_resistance_type_buttons[i], next(r_iter, None), subsample=subsample)
            pokemon.Type.updateButton(self.team_missing_type_buttons[i], next(m_iter, None), subsample=subsample)

    def layout(self):
        return [ [gui.Column([[gui.Text("Weaknesses:", size=(10,1)), self.weakness_explanation_button],   *[[x] for x in self.team_weakness_type_buttons]]),
                  gui.Column([[gui.Text("Resistances:", size=(10,1)), self.resistance_explanation_button], *[[x] for x in self.team_resistance_type_buttons]]),
                  gui.Column([[gui.Text("Missing:", size=(10,1)), self.missing_explanation_button],   *[[x] for x in self.team_missing_type_buttons]])
                 ],
               ]
        #return  [ [gui.Text("Team Weaknesses:"),     gui.Column([*halve(self.team_weakness_type_buttons)])],
        #          [gui.Text("Team Resistances:"),    gui.Column([*halve(self.team_resistance_type_buttons)])],
        #          [gui.Text("Missing Resistances:"), gui.Column([*halve(self.team_missing_type_buttons)])],
        #        ]
