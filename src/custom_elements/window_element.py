import uuid

import PySimpleGUI as gui

from src import database, pokemon, types
from src.element import Element
from src.custom_elements import SummaryElement, MoveElement, LocationElement, SearchableListBox, TeamAnalysisElement, TeamDisplayElement, ThemeChangeElement

# TODO: Move sorts/filters?
def sortByNum(pkmn_name):
    assert pkmn_name in database.instance.pokemon, f"can't find {pkmn_name} in ingested pokemon"
    return int(database.instance.pokemon[pkmn_name].num)

def sortByOverall(pkmn_name):
    assert pkmn_name in database.instance.pokemon, f"can't find {pkmn_name} in ingested pokemon"
    theoretical_max = (pokemon.Stats.Attribute.ATTR_MAX * len(pokemon.Stats.ALL_ATTR_NAMES))
    # We subtract the actual from the theoretical max so the list is sorted in descending order
    return theoretical_max - sum([int(getattr(database.instance.pokemon[pkmn_name].stats, attr_name).value) for attr_name in pokemon.Stats.ALL_ATTR_NAMES])

def sortByAttr(attr_name):
    def innerSort(pkmn_name):
        assert pkmn_name in database.instance.pokemon, f"can't find {pkmn_name} in ingested pokemon"
        theoretical_max = pokemon.Stats.Attribute.ATTR_MAX
        # We subtract the actual from the theoretical max so the list is sorted in descending order
        return theoretical_max - int(getattr(database.instance.pokemon[pkmn_name].stats, attr_name).value)
    return innerSort

def filterByType(expected_type):
    def innerFilter(pkmn_name):
        assert pkmn_name in database.instance.pokemon, f"can't find {pkmn_name} in ingested pokemon"
        pkmn = database.instance.pokemon[pkmn_name]
        return expected_type in (pkmn.type.primary, pkmn.type.secondary)
    return innerFilter


class WindowElement(Element):
    def __init__(self):
        # Home
        self.file_ingested = False
        self.ingest_button = gui.Button("Ingest", key="button_ingest")
        self.home_tab = gui.Tab("Home", [ [gui.InputText(key="input_text_file", default_text=database.default_source_location), gui.FileBrowse(button_text="Browse For Log File")] ,
                                          [self.ingest_button, gui.Text(self.file_ingested, key="text_ingested_boolean")],
                                          [gui.Button("Stat Averages", key="stat_averages"), gui.Button("Close"), gui.Button("???")],
                                        ])

        # Summary
        self.summary_slb = SearchableListBox(SummaryElement())
        self.summary_add_to_team_builder_button = gui.Button("Add To Team Builder", key="summary_add_to_team_builder_button", metadata=self.summary_slb)

        self.summary_slb.registerSort("Num", sortByNum)
        self.summary_slb.registerSort("Overall", sortByOverall)
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            self.summary_slb.registerSort(pokemon.Stats.short_name(attr_name), sortByAttr(attr_name))

        for type_name in types.all_types:
            self.summary_slb.registerFilter(type_name, filterByType(type_name))

        self.display_tab = gui.Tab("Summary", [ [gui.Column(self.summary_slb.element.layout()), gui.Column([ *self.summary_slb.layout(),
                                                                                                                     [self.summary_add_to_team_builder_button],
                                                                                                                    ], justification="right")],
                                              ])

        # Moves
        self.move_slb = SearchableListBox(MoveElement())
        self.moves_tab = gui.Tab("Moves", [ [gui.Column(self.move_slb.element.layout()), gui.Sizer(500, 0), gui.Column(self.move_slb.layout(), justification="right")],
                                          ])

        # Locations
        self.location_slb = SearchableListBox(LocationElement())
        self.locations_tab = gui.Tab("Locations", [ [gui.Column(self.location_slb.element.layout()), gui.Sizer(10, 0), gui.Column(self.location_slb.layout(), justification="right")],
                                                  ])

        # Team Builder
        self.team_builder_elements = [TeamDisplayElement(i) for i in range(6)]
        self.team_analysis_element = TeamAnalysisElement(self.team_builder_elements)
        tb_column1 = gui.Column([ *self.team_builder_elements[0].layout(), *self.team_builder_elements[2].layout(), *self.team_builder_elements[4].layout() ])
        tb_column2 = gui.Column([ *self.team_builder_elements[1].layout(), *self.team_builder_elements[3].layout(), *self.team_builder_elements[5].layout() ])
        left_column = gui.Column([  [ gui.Frame("Pokemon Team", [[tb_column1, tb_column2]]) ],
                                    [ gui.Button("Randomize Team", key="team_builder_randomize_team_button", size=(10,2)),
                                      gui.Button("Randomize Remaining", key="team_builder_randomize_remaining_button", size=(10,2)),
                                      gui.Button("Clear Team", key="team_builder_clear_team_button", size=(10,2)),
                                    ],
                                 ])
        right_column = gui.Column(self.team_analysis_element.layout())
        self.team_builder_tab = gui.Tab("Team Builder", [ [left_column, right_column] ]
                                                    , element_justification="top")

        # Options
        self.theme_slb = SearchableListBox(ThemeChangeElement())
        self.options_tab = gui.Tab("Options", [ [gui.Text("Select A Theme:", font="Arial 16"), gui.Text(f"[Currently: {gui.theme()}]", font="Arial 16")],
                                                *self.theme_slb.layout()
                                              ]
                                            , element_justification="right")

        self.tab_group = gui.TabGroup([[self.home_tab, self.display_tab, self.moves_tab, self.locations_tab, self.team_builder_tab, self.options_tab]]
                                    , key=f"main_window_layout_tab_group_{uuid.uuid4().hex}"
                                    , font="Impact 12")

    def update(self, obj):
        # Do Nothing (for now?)
        pass

    def layout(self):
        return [[self.tab_group]]

    def populateThemes(self):
        # SearchableListBoxes require a mapping of keys and values, so when the keys
        # ARE the values, we just convert the list [x,y] to a mapping of {x:x, y:y}.
        self.theme_slb.populate({x:x for x in gui.theme_list()})

    def expandButtons(self):
        # TODO: Can we do this is a more elegant way?
        self.summary_slb.expandButtons()
        self.move_slb.expandButtons()
        self.theme_slb.expandButtons()
