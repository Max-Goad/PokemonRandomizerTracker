import collections
import difflib
import gzip
from   matplotlib import pyplot
import numpy
import pathlib
from   pprint import pprint
import PySimpleGUI as gui
import random
import re as regex
from   scipy.signal import savgol_filter
from   scipy import interpolate, optimize, stats
import statistics
import typing
import uuid

from src import parsers, pokemon, types
from src.elements import PokemonDisplayElement, MoveElement, SearchableListBox, TeamDisplayElement, TeamAnalysisElement
from src.external import utils

####################################################
## Globals / Defaults
####################################################
default_browse_text = "X:/Games/Emulators/Pokemon Randomizer/roms/Pokemon Platinum Randomizer 2020.nds.log"
all_pokemon = []
all_moves = []

def sortByNum(pkmn_name):
    [pkmn] = [p for p in all_pokemon if p.name == pkmn_name]
    return int(pkmn.num)

def sortByOverall(pkmn_name):
    [pkmn] = [p for p in all_pokemon if p.name == pkmn_name]
    theoretical_max = (pokemon.Stats.Attribute.ATTR_MAX * len(pokemon.Stats.ALL_ATTR_NAMES))
    # We subtract the actual from the theoretical max so the list is sorted in descending order
    return theoretical_max - sum([int(getattr(pkmn.stats, attr_name).value) for attr_name in pokemon.Stats.ALL_ATTR_NAMES])

def sortByAttr(attr_name):
    def innerSort(pkmn_name):
        [pkmn] = [p for p in all_pokemon if p.name == pkmn_name]
        theoretical_max = pokemon.Stats.Attribute.ATTR_MAX
        # We subtract the actual from the theoretical max so the list is sorted in descending order
        return theoretical_max - int(getattr(pkmn.stats, attr_name).value)
    return innerSort

def filterByType(expected_type):
    def innerFilter(pkmn_name):
        [pkmn] = [p for p in all_pokemon if p.name == pkmn_name]
        return pkmn.type.primary == expected_type or pkmn.type.secondary == expected_type
    return innerFilter


####################################################
## Reusable Containers
####################################################
class MainWindowLayout:
    def __init__(self, wrapper):
        # Home
        self.file_ingested = False
        self.ingest_button = gui.Button("Ingest", key="button_ingest")
        self.home_tab = gui.Tab("Home", [ [gui.InputText(key="input_text_file", default_text=default_browse_text), gui.FileBrowse(button_text="Browse For Log File")] ,
                                          [self.ingest_button, gui.Text(self.file_ingested, key="text_ingested_boolean")],
                                          [gui.Button("Stat Averages", key="stat_averages"), gui.Button("Close"), gui.Button("???")],
                                        ])

        # Summary
        self.pokemon_display_slb = SearchableListBox(PokemonDisplayElement())
        self.display_add_to_team_builder_button = gui.Button("Add To Team Builder", key="pokemon_display_add_to_team_builder_button", metadata=self.pokemon_display_slb)

        self.pokemon_display_slb.registerSort("Num", sortByNum)
        self.pokemon_display_slb.registerSort("Overall", sortByOverall)
        for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
            self.pokemon_display_slb.registerSort(pokemon.Stats.short_name(attr_name), sortByAttr(attr_name))

        for type_name in types.all_types:
            self.pokemon_display_slb.registerFilter(type_name, filterByType(type_name))

        self.display_tab = gui.Tab("Display", [ [gui.Column(self.pokemon_display_slb.element.layout()), gui.Column([ *self.pokemon_display_slb.layout(),
                                                                                                                     [self.display_add_to_team_builder_button],
                                                                                                                    ], justification="right")],
                                              ])

        # Moves
        self.pokemon_move_slb = SearchableListBox(MoveElement())
        self.moves_tab = gui.Tab("Moves", [ [gui.Column(self.pokemon_move_slb.element.layout()), gui.Sizer(500, 0), gui.Column(self.pokemon_move_slb.layout(), justification="right")],
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
        self.theme_slb = SearchableListBox(ThemeChangingElement(wrapper))
        self.options_tab = gui.Tab("Options", [ [gui.Text("Select A Theme:", font="Arial 16"), gui.Text(f"[Currently: {gui.theme()}]", font="Arial 16")],
                                                *self.theme_slb.layout()
                                              ]
                                            , element_justification="right")

        self.tab_group = gui.TabGroup([[self.home_tab, self.display_tab, self.moves_tab, self.team_builder_tab, self.options_tab]]
                                    , key=f"main_window_layout_tab_group_{uuid.uuid4().hex}"
                                    , font="Impact 12")

    def layout(self):
        return [[self.tab_group]]

    def populateThemes(self):
        self.theme_slb.populate(gui.theme_list())

    def expandButtons(self):
        # TODO: Can we do this is a more elegant way?
        self.pokemon_display_slb.expandButtons()
        self.pokemon_move_slb.expandButtons()
        self.theme_slb.expandButtons()

class WindowWrapper:
    def __init__(self, title, **kwargs):
        self.title = title
        self.main = None
        self.window = None
        self.kwargs = kwargs


    def new(self, location=(None, None)):
        self.main = MainWindowLayout(self)
        self.window = gui.Window(self.title, self.main.layout(), location=location, **self.kwargs)
        self.main.populateThemes()
        self.main.expandButtons()
        # TEMP
        self.main.ingest_button.click()

    def change_theme(self, theme_name):
        old_window = self.window
        gui.theme(theme_name)
        self.new(self.window.current_location())
        old_window.close()
        self.window.bring_to_front()


####################################################
## Custom Elements
####################################################
class ThemeChangingElement:
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def update(self, theme_name):
        self.wrapper.change_theme(theme_name)

####################################################
## Other (Temp?)
####################################################
def popupStatAverages(all_pokemon: typing.List[pokemon.Pokemon]):
    # Group raw stats by attribute
    grouped_raw_stats = {}
    grouped_raw_stats : typing.Dict[str, int]
    for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
        grouped_raw_stats[attr_name] = []
        for pkmn in all_pokemon:
            grouped_raw_stats[attr_name].append(getattr(pkmn.stats,attr_name).value)

    # Covert raw counts into Counter objects
    grouped_counters = {}
    grouped_counters : typing.Dict[str, collections.Counter]
    for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
        grouped_counters[attr_name] = collections.Counter(grouped_raw_stats[attr_name])

    for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
        ## Plot splined curve over data
        cdict = dict(sorted(dict(grouped_counters[attr_name]).items()))
        (xs, ys) = list(cdict.keys()), list(cdict.values())
        #pyplot.scatter(xs, ys)
        spline = interpolate.UnivariateSpline(xs, ys, s=400)
        xs2 = numpy.linspace(0, 255, 1000)
        xs2 = numpy.linspace(min(xs), max(xs), 1000)
        ys2 = spline(xs2)
        plotted_curves = pyplot.plot(xs2, ys2, label=attr_name)

        ## Plot median line
        median_value = statistics.median(grouped_raw_stats[attr_name])
        print(f"median of {attr_name} is {median_value}")
        pyplot.axvline(x=median_value, color=plotted_curves[-1].get_color(), lw=1, ls="dashed")

    pyplot.title("Stat Distribution (with 50th percentile)")
    pyplot.legend(loc="best")
    pyplot.show(block=False)



def main():
    gui.theme("Topanga")

    global all_pokemon
    currently_selected_pokemon = None
    currently_selected_pokemon : pokemon.Pokemon

    global all_moves
    currently_selected_move = None
    currently_selected_move : pokemon.Move

    movesets = []


    # Define window and layout
    wrapper = WindowWrapper("My Test Application", return_keyboard_events=True, use_default_focus=False, finalize=True)
    wrapper.new()

    while True:
        event, values = wrapper.window.read()
        if event is not None:
            encoded_event = event.encode('utf-8') # Necessary for capturing \r

        # TEMP

        ################################################################################
        if event in (None, "Close"):
            break
        ################################################################################
        # Check for ENTER key
        elif encoded_event in (b'\r',):
            print("==== Event: Enter Key ====")
            current_tab_key = wrapper.main.tab_group.Get()
            if current_tab_key == "Home":
                wrapper.window["button_ingest"].Click()
            elif current_tab_key == "Display":
                wrapper.main.pokemon_display_slb.button.Click()
            elif current_tab_key == "Moves":
                wrapper.main.pokemon_move_slb.button.Click()
            elif current_tab_key == "Team Builder":
                pass
            elif current_tab_key == "Options":
                wrapper.main.theme_slb.button.Click()
            else:
                assert True == False, "Enter key not handled for this tab"
        ################################################################################
        # Check for all other keyboard events
        elif len(event) == 1 or event.startswith("Shift")\
                             or event.startswith("Ctrl")\
                             or event.startswith("Control")\
                             or event.startswith("Alt")\
                             or event.startswith("MouseWheel")\
                             or event.startswith("BackSpace")\
                             or event.startswith("Delete")\
                             or event.startswith("Left")\
                             or event.startswith("Right")\
                             or event.startswith("Down")\
                             or event.startswith("Up"):
            pass
        ################################################################################
        elif event in ("button_ingest",):
            print("==== Event: Ingest Button ====")
            input_text_file = values["input_text_file"]
            if not input_text_file:
                continue

            try:
                ingester = parsers.RandomizerLogParser(pathlib.Path(input_text_file))
            except parsers.InvalidFormatError:
                gui.popup_error("Ingested file doesn't have a valid format!")
                continue

            all_pokemon = ingester.extractPokemon()
            print(f"Extracted {len(all_pokemon)} pokemon")

            all_moves = ingester.extractMoves()
            print(f"Extracted {len(all_moves)} moves")

            movesets = ingester.extractMovesets()
            # Add movesets to pokemon
            for moveset in movesets:
                for pkmn in all_pokemon:
                    if moveset.pkmn_name == pkmn.name:
                        pkmn.addMoveset(moveset)
            print(f"Extracted movesets for {len(movesets)} pokemon")

            wild_pokemon_occurrences = ingester.extractWildOccurrences()
            # Add wild occurrences to pokemon
            for pkmn in all_pokemon:
                pkmn.addWildOccurrences(*wild_pokemon_occurrences[pkmn.name])
            print(f"Extracted wild occurrences for {len(wild_pokemon_occurrences)} pokemon")

            static_pokemon_occurrences = ingester.extractStaticOccurrences()
            # Add static occurrences to pokemon
            for pkmn in all_pokemon:
                if pkmn.name in static_pokemon_occurrences:
                    pkmn.addWildOccurrences(static_pokemon_occurrences[pkmn.name])
            print(f"Extracted static occurrences for {len(static_pokemon_occurrences)} pokemon")

            # Update Team Builder Screen
            wrapper.main.team_analysis_element.update()

            # Update text
            file_ingested = True
            wrapper.window['text_ingested_boolean'].update(file_ingested)

            # Update combo boxs
            wrapper.main.pokemon_display_slb.populate([p.name for p in all_pokemon])
            wrapper.main.pokemon_move_slb.populate([m.name for m in all_moves])

        ################################################################################
        elif event in wrapper.main.pokemon_display_slb.eventKeys():
            if len(all_pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            if event == wrapper.main.pokemon_display_slb.button.Key:
                print("==== Event: Display Chooser Button ====")
                # Find closest match and update the selection
                names = [pkmn.name for pkmn in all_pokemon]
                name_snippet = values[wrapper.main.pokemon_display_slb.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.pokemon_display_slb.setSelection(name_to_search)
            else:
                print("==== Event: Display Chooser Click ====")

            [selected_name] = wrapper.main.pokemon_display_slb.currentlySelected()
            print(selected_name)
            currently_selected_pokemon = next((pkmn for pkmn in all_pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None
            wrapper.main.pokemon_display_slb.update(currently_selected_pokemon)

        ################################################################################
        elif event in wrapper.main.pokemon_move_slb.eventKeys():
            if len(all_pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            if event == wrapper.main.pokemon_move_slb.button.Key:
                print("==== Event: Moves Chooser Button ====")
                # Find closest match and update the selection
                names = [move.name for move in all_moves]
                name_snippet = values[wrapper.main.pokemon_move_slb.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.pokemon_move_slb.setSelection(name_to_search)
            else:
                print("==== Event: Moves Chooser Click ====")

            [selected_name] = wrapper.main.pokemon_move_slb.currentlySelected()
            currently_selected_move = next((move for move in all_moves if move.name == selected_name), None)
            assert currently_selected_move is not None
            wrapper.main.pokemon_move_slb.update(currently_selected_move)

        ################################################################################
        elif event in wrapper.main.theme_slb.eventKeys():
            # TODO: Fix copy-paste code!
            if event == wrapper.main.theme_slb.button.Key:
                print("==== Event: Theme Chooser Button ====")
                # Find closest match and update the selection
                names = gui.theme_list()
                name_snippet = values[wrapper.main.theme_slb.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.theme_slb.setSelection(name_to_search)
            else:
                print("==== Event: Theme Chooser Click ====")

            [selected_name] = wrapper.main.theme_slb.currentlySelected()
            wrapper.main.theme_slb.update(selected_name)

            #[selected_name] = pokemon_display_slb.currentlySelected()
            #currently_selected_pokemon = next((pkmn for pkmn in all_pokemon if pkmn.name == selected_name), None)
            #assert currently_selected_pokemon is not None
            #pokemon_display_slb.update(currently_selected_pokemon)

        ################################################################################
        elif event in ("stat_averages",):
            print("==== Event: Stat Averages ====")
            if len(all_pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            popupStatAverages(all_pokemon)

        ################################################################################
        elif event in ("listbox_theme",):
            print("==== Event: Theme Chooser ====")
            [new_theme] = values["listbox_theme"]
            gui.theme(new_theme)

        ################################################################################
        elif event.startswith("pokemon_display_element_moveset_move_name_"):
            print("==== Event: Display Moveset Click ====")
            # Simulate a Move Selection search given the move clicked on
            wrapper.main.pokemon_move_slb.input_text.update(wrapper.window[event].DisplayText)
            wrapper.main.pokemon_move_slb.button.click()

            # Finally, switch tabs to the Moves tab
            wrapper.main.moves_tab.select()

        ################################################################################
        elif event.startswith("pokemon_display_add_to_team_builder_button"):
            print("=== Event: Add Pokemon To Team Builder ===")
            display_slb : SearchableListBox = wrapper.window[event].metadata
            [selected_name] = display_slb.currentlySelected()
            currently_selected_pokemon : pokemon.Pokemon = next((pkmn for pkmn in all_pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None

            for team_builder_element in wrapper.main.team_builder_elements:
                if team_builder_element.empty:
                    team_builder_element.update(currently_selected_pokemon)
                    print(f"Added {currently_selected_pokemon.name} to the team builder")
                    break
            else:
                print(f"Warning: {currently_selected_pokemon} cannot be added to Team Builder as the team is already full!")

        ################################################################################
        elif event.startswith("SearchableListBox_SortButton"):
            print("=== Event: Sort Searchable List Box ===")
            sort_lambda = wrapper.window[event].metadata
            sort_lambda()

        ################################################################################
        elif event.startswith("SearchableListBox_FilterButton"):
            print("=== Event: Filter Searchable List Box ===")
            filter_lambda = wrapper.window[event].metadata
            filter_lambda()

        ################################################################################
        elif event.startswith("team_display_element_clear"):
            print("=== Event: Clear Team Display ")
            team_display_element = wrapper.window[event].metadata
            team_display_element.clear()

        ################################################################################
        elif event.startswith("team_display_element_title"):
            print("=== Event: Clear Team Display ===")
            selected_name = wrapper.window[event].DisplayText
            currently_selected_pokemon : pokemon.Pokemon = next((pkmn for pkmn in all_pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None
            wrapper.main.pokemon_display_slb.update(currently_selected_pokemon)

            # Finally, switch tabs to the Display tab
            wrapper.main.display_tab.select()

        ################################################################################
        elif event in ("team_builder_randomize_team_button"):
            print("=== Event: Randomize Team ===")
            if len(all_pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in wrapper.main.team_builder_elements:
                elem.update(all_pokemon[random.randint(0,len(all_pokemon)-1)])

        ################################################################################
        elif event in ("team_builder_randomize_remaining_button"):
            print("=== Event: Randomize Remaining ===")
            if len(all_pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in wrapper.main.team_builder_elements:
                if elem.empty:
                    elem.update(all_pokemon[random.randint(0,len(all_pokemon)-1)])

        ################################################################################
        elif event in ("team_builder_clear_team_button"):
            print("=== Event: Clear Team ===")
            for elem in wrapper.main.team_builder_elements:
                elem.clear()



        ################################################################################
        elif event.startswith("explanation_button_"):
            explanation = wrapper.window[event].metadata
            gui.popup(explanation, title="Explanation")

        ################################################################################
        else:
            print(f"==== Event: UNKNOWN ({event}) ====")
            pprint(values)
            print(f"==== Event: UNKNOWN ({event}) ====")
    wrapper.window.close()

if __name__ == "__main__":
    main()
