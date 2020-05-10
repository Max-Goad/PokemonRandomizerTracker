import collections
import colorsys
import difflib
from   functools import reduce
import gzip
import itertools
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

from src import types, utils
from src.pokemon import Pokemon

def getLatestFileFrom(directory_path, glob_filter='*.log'):
    """Gets the latest file from the directory specified.

    Latest is specified by name, not creation date.

    TODO: Should use either creation or modification date instead of name.
    """
    file_matches = list(directory_path.glob(glob_filter))
    file_matches.sort(reverse=True)
    if len(file_matches) == 0: raise Exception(f"No files matching glob filter {glob_filter} could be found in directory {directory_path.name}")
    return str(file_matches[0])

def getLinesFromFile(file, custom_strip_fn=lambda x: x):
    """Returns the file as a list of strings (lines).

    Can read from either regular or gzipped files.

    Can specify a function (custom_strip_fn) to run
    on each line while building the list.
    """
    if '.gz' in file.suffixes:
        open_fn = lambda x: gzip.open(x,'rt')
    else:
        open_fn = lambda x: open(x,'r')

    with open_fn(file) as f:
        return [custom_strip_fn(line) for line in f]

def getGroups(pattern, line):
    """Gets regex groups listed in pattern from line (as a tuple).

    If only one group found, returns value (not tuple).

    If no groups are found, returns None.
    """
    groups = None
    match = regex.search(pattern, line)
    if match:
        groups = match.groups()
        if len(groups) == 1:
            groups = groups[0]
    return groups

def stripBracketBlocks(line):
    """A common function that can be used in lambdas to get rid of
    the [Something] blocks commonly found at the beginning of logs

    Also strips leading/trailing spaces/tabs/newlines.
    """
    return regex.sub(r'\[[\w:]+\]', "", line).strip(' \t\n')

class RegexNotFoundError(Exception):
    """ Exception raised when the LogParser can't find a specified regex string """
    pass

class InvalidFormatError(Exception):
    """ Exception raised when the file passed to the file parser is not in a valid format """
    pass

class StringParser:
    """A class meant to ease the process of searching
    programmatically through a list of strings "line-by-line".

    Keeps an internal "current line marker" to help you
    progress through the lines, can extract regex groups
    from a line match, and can even return entire sections
    specified by a start and end regex.
    """

    def __init__(self, lines):
        self.lines = lines
        self.current_line = -1

    def reset(self):
        """Sets the current line marker back to the
        beginning of the list.
        """
        self.current_line = -1

    def moveAndGetGroups(self, regex_str, end_regex=None):
        """Helper function that finds a specified regex_str,
        moves the internal current line marker to that line,
        and returns the capture groups specified in the regex.

        Can specify an end_regex to tell the function when to
        stop looking for the regex_str; By default it searches
        until the end of the file.

        Throws RegexNotFoundError if regex_str not found.
        """
        index = self.current_line + 1
        while index < len(self.lines):

            if end_regex and regex.search(end_regex, self.lines[index]):
                raise RegexNotFoundError

            groups = getGroups(regex_str, self.lines[index])
            #print(f"index = {index}, len = {len(self.lines)}, groups = {groups}")
            if groups is not None:
                self.current_line = index
                return groups
            index += 1
        raise RegexNotFoundError

    def consumeUntil(self, regex_str):
        """Helper function that consumes, collects, and returns all lines following
        the current index until the first line that matches the regex_str.

        Does not change internal current line marker.

        Throws RegexNotFoundError if end of file reached (no matches found).
        """
        index = self.current_line + 1
        consumed_lines = []
        while index < len(self.lines):
            if regex.search(regex_str, self.lines[index]):
                return consumed_lines
            consumed_lines.append(self.lines[index])
            index += 1
        raise RegexNotFoundError

    def consumeRemaining(self):
        """Helper function that consumes, collects, and returns all lines
        following the current line until the end of the file.

        Does not change internal current line marker.
        """
        return self.lines[self.current_line+1:]

    def extractSection(self, begin_regex, end_regex):
        """Helper function that extracts all lines from the specified
        begin regex to the specified end_regex.

        Changes internal current line marker to beginning of section.

        Throws RegexNotFoundError if any matches not found.

        """
        self.moveAndGetGroups(begin_regex)
        return self.consumeUntil(end_regex)


    def find(self, *regex_strings):
        """Finds and returns the contents of the first line which
        contains any of the specified 'regex_strings'.

        Throws RegexNotFoundError if no matches found.
        """
        return_line_fn = lambda i, s: self.lines[i] if regex.search(s, self.lines[i]) else None
        return self._findBase(return_line_fn, *regex_strings)

    def findGroups(self, *regex_strings):
        """Finds and returns the regex capture groups
        of the first line which contains any of the
        specified 'regex_strings' as a tuple.

        Throws RegexNotFoundError if no matches found.
        """
        return_groups_fn = lambda i, s: getGroups(s, self.lines[i])
        return self._findBase(return_groups_fn, *regex_strings)

    def findIndex(self, *regex_strings):
        """Finds and returns the index of the first line which
        contains any of the specified 'regex_strings'.

        Throws RegexNotFoundError if no matches found.
        """
        return_index_fn = lambda i, s: i if regex.search(s, self.lines[i]) else None
        return self._findBase(return_index_fn, *regex_strings)

    def _findBase(self, for_each_fn, *regex_strings):
        """The private base function for all find operations.
        """
        index = 0
        while index < len(self.lines):
            for regex_str in regex_strings:
                result = for_each_fn(index, regex_str)
                if result:
                    return result
            index += 1
        raise RegexNotFoundError

class FileParser(StringParser):
    """A wrapper that converts the file's contents into a
    list of strings compatible with StringParser.

    (See doc for StringParser for more information)

    Can optionally take a "custom_strip_fn" to apply to
    each line as it is processed and converted to a string.
    """
    def __init__(self, file, custom_strip_fn=lambda x: x):
        super().__init__(getLinesFromFile(file, custom_strip_fn=custom_strip_fn))
        self.file = file

class RandomizerLogParser(FileParser):
    """
    TODO: Documentation
    """
    POKEMON_SUMMARY_HEADER = r"Pokemon Base Stats & Types"
    POKEMON_MOVE_HEADER = r"Move Data"
    POKEMON_MOVESET_HEADER = r"Pokemon Movesets"
    WILD_POKEMON_HEADER = r"Wild Pokemon"

    def __init__(self, file):
        super().__init__(file)


        if not self._valid():
            raise InvalidFormatError
        pass

    def _header_regexes(self):
        return [self.POKEMON_SUMMARY_HEADER]

    def _valid(self):
        try:
            self.find(*self._header_regexes())
            return True
        except RegexNotFoundError:
            return False

    def extractPokemon(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_SUMMARY_HEADER)

        # Move past headers
        self.current_line += 2

        pokemon = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            pkmn_pieces = [x.strip() for x in line.split("|")]

            assert len(pkmn_pieces) == 12, f"Expected(12) vs Actual({len(pkmn_pieces)})"

            num = pkmn_pieces[0]
            name = Pokemon.fix_unicode_name(pkmn_pieces[1])
            types = pkmn_pieces[2].split("/")
            stats = pkmn_pieces[3:9]
            abilities = [a for a in pkmn_pieces[9:11] if a != '-']
            items = [i for i in pkmn_pieces[11].split(",") if i]

            pokemon.append(Pokemon(num, name, types, stats, abilities, items))
            self.current_line += 1
        return pokemon

    def extractMoves(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_MOVE_HEADER)

        # Move past headers
        self.current_line += 2

        moves = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            move_pieces = [x.strip() for x in line.split("|")]

            assert len(move_pieces) == 7, f"Expected(7) vs Actual({len(move_pieces)})"

            [num, name, move_type, power, accuracy, pp, category] = move_pieces
            # We use the move type string to ingest the proper image,
            # but we can't name an image '???.png' so we use 'unknown.png' instead.
            if move_type == "???":
                move_type = "unknown"
            moves.append(Pokemon.Move(num, name, Pokemon.Type([move_type]), power, accuracy, pp, Pokemon.Type([category])))
            self.current_line += 1
        return moves

    def extractMovesets(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_MOVESET_HEADER)

        # Move past headers
        self.current_line += 1

        movesets = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            pkmn, raw_moveset = line.split(':')
            pkmn_name = Pokemon.fix_unicode_name(pkmn[4:].strip())

            curr_moveset = Pokemon.Moveset(pkmn_name)
            for learned_move_string in raw_moveset.split(','):
                learned_move_string = learned_move_string.strip()
                move_name, level = learned_move_string.strip().split("at level")
                curr_moveset.add_mapping(int(level), move_name.strip())
            movesets.append(curr_moveset)

            self.current_line += 1
        return movesets

    def extractWildPokemon(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.WILD_POKEMON_HEADER)

        # Move past headers
        self.current_line += 1

        wild_pokemon_locations = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            set_num, raw_location, raw_pokemon_list = line.split('-')
            # Rate is currently unused
            location_name, rate = getGroups(r"([\w\s?]+)[(]rate=(\d+)[)]", raw_location.strip())
            raw_pokemon = raw_pokemon_list.split(',')

            # TODO

            self.current_line += 1
        return wild_pokemon_locations

####################################################
## Global Defaults
####################################################
default_browse_text = "X:/Games/Emulators/Pokemon Randomizer/roms/Pokemon Platinum Randomizer 2020.nds.log"


####################################################
## Pokemon Custom Types
####################################################


####################################################
## Reusable Containers
####################################################
class SearchableListBox:

    def __init__(self, element, size=(30,25)):
        self.uuid = uuid.uuid4().hex
        self.element = element
        self.list_box = gui.Listbox([], key=f"SearchableListBox_ListBox_{self.uuid}", size=size, font="Arial 16", enable_events=True, select_mode="single")
        self.input_text = gui.InputText(key=f"SearchableListBox_InputText_{self.uuid}", size=(22, 1), font="Arial 16")
        self.button = gui.Button("Search", key=f"SearchableListBox_Button_{self.uuid}", size=(8, 1), font="Arial 16")

    def populate(self, values):
        self.list_box.update(values=values)

    def set_selection(self, name):
        name_index = self.list_box.get_list_values().index(name)
        self.list_box.update(set_to_index=name_index, scroll_to_index=name_index)

    def update(self, values):
        self.input_text.update("")
        self.element.update(values)

    def currently_selected(self):
        return self.list_box.get()

    def event_keys(self):
        return (self.list_box.Key, self.button.Key)

    def layout(self):
        return [[self.input_text, self.button],
                [self.list_box]]


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
        self.summary_search_listbox = SearchableListBox(PokemonSummaryElement())
        self.summary_add_to_team_builder_button = gui.Button("Add To Team Builder", key="pokemon_summary_add_to_team_builder_button", metadata=self.summary_search_listbox)
        self.summary_tab = gui.Tab("Summary", [ [gui.Column(self.summary_search_listbox.element.layout()), gui.Sizer(300, 0), gui.Column([*self.summary_search_listbox.layout(),
                                                                                                                       [self.summary_add_to_team_builder_button]], justification="right")],
                                              ])

        # Moves
        self.moves_search_listbox = SearchableListBox(MoveElement())
        self.moves_tab = gui.Tab("Moves", [ [gui.Column(self.moves_search_listbox.element.layout()), gui.Sizer(300, 0), gui.Column(self.moves_search_listbox.layout())],
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
        self.theme_search_listbox = SearchableListBox(ThemeChangingElement(wrapper))
        self.options_tab = gui.Tab("Options", [ [gui.Text("Select A Theme:", font="Arial 16"), gui.Text(f"[Currently: {gui.theme()}]", font="Arial 16")],
                                                *self.theme_search_listbox.layout()
                                              ]
                                            , element_justification="right")

        self.tab_group = gui.TabGroup([[self.home_tab, self.summary_tab, self.moves_tab, self.team_builder_tab, self.options_tab]]
                                    , key=f"main_window_layout_tab_group_{uuid.uuid4().hex}"
                                    , font="Impact 12")

    def layout(self):
        return [[self.tab_group]]

    def populate_themes(self):
        self.theme_search_listbox.populate(gui.theme_list())


class WindowWrapper:
    def __init__(self, title, **kwargs):
        self.title = title
        self.main = None
        self.window = None
        self.kwargs = kwargs


    def new(self, location=(None, None)):
        self.main = MainWindowLayout(self)
        self.window = gui.Window(self.title, self.main.layout(), location=location, **self.kwargs)
        self.main.populate_themes()
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
    def __init__(self, wrapper : WindowWrapper):
        self.wrapper = wrapper

    def update(self, theme_name):
        self.wrapper.change_theme(theme_name)


class PokemonSummaryElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"pokemon_summary_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.primary_type_button = Pokemon.Type.create_button(f"pokemon_summary_element_type_primary_{self.uuid}")
        self.secondary_type_button = Pokemon.Type.create_button(f"pokemon_summary_element_type_secondary_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"pokemon_summary_element_attribute_name_{attr_name}_{self.uuid}", size=(12, 1)), gui.Text("", key=f"pokemon_summary_element_attribute_value_{attr_name}_{self.uuid}", size=(3, 1)), Pokemon.Stats.Attribute.create_graph(f"pokemon_summary_element_attribute_bar_{attr_name}_{self.uuid}")]
        self.moveset_title_text = gui.Text(f"", key=f"pokemon_summary_element_moveset_title_{self.uuid}", size=(8,1), font="Arial 14")
        self.moveset_rows = []
        for i in range(20):
            # One text for the level ("Level 50 - "), and one for the actual move name (which is clickable!)
            self.moveset_rows.append((gui.Text(f"", key=f"pokemon_summary_element_moveset_level_{i}_{self.uuid}", size=(10,1), font="Consolas 10"),
                                      gui.Text(f"", key=f"pokemon_summary_element_moveset_move_name_{i}_{self.uuid}", size=(40,1), font="Consolas 10", enable_events=True)))

    def update(self, pkmn : Pokemon):
        self.title.update(f"{pkmn.name}")
        pkmn.type.update_buttons(self.primary_type_button, self.secondary_type_button)

        for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
            aname, avalue, agraph = self.attribute_rows[attr_name]
            attribute = getattr(pkmn.stats, attr_name)
            aname.update(attribute.name)
            avalue.update(attribute.value)
            attribute.draw_on(agraph)

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


class MoveElement:
    def __init__(self):
        self.uuid = uuid.uuid4().hex
        self.title = gui.Text(f"", key=f"move_element_title_{self.uuid}", size=(13, 1), font="Impact 20")
        self.type_button = Pokemon.Type.create_button(f"move_element_type_{self.uuid}")
        self.category_button = Pokemon.Type.create_button(f"move_element_category_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in Pokemon.Move.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"move_element_attribute_name_{attr_name}_{self.uuid}", size=(12, 1)), gui.Text("", size=(3, 1)), Pokemon.Stats.Attribute.create_graph(f"move_element_attribute_bar_{attr_name}_{self.uuid}")]

    def update(self, move : Pokemon.Move):
        self.title.update(f"{move.name}")
        move.type.update_buttons(self.type_button)
        move.category.update_buttons(self.category_button)

        for attr_name in Pokemon.Move.ALL_ATTR_NAMES:
            aname, avalue, agraph = self.attribute_rows[attr_name]
            attribute = getattr(move, attr_name)
            aname.update(attribute.name)
            avalue.update(attribute.value)
            attribute.draw_on(agraph)

    def layout(self):
        return  [ [self.title, self.type_button, self.category_button],
                  *self.attribute_rows.values()
                ]


class TeamDisplayElement:
    def __init__(self, index):
        self.uuid = uuid.uuid4().hex
        self.index = index
        self.empty = True
        self.current_pokemon = None
        self.on_update = lambda: None

        self.clear_button = gui.Button("X", key=f"team_display_element_clear_{self.uuid}", size=(2,1), metadata=self, disabled=True)
        self.title = gui.Text(f"", key=f"team_display_element_title_{self.uuid}", size=(10, 1), font="Impact 14", enable_events=True)
        self.primary_type_button = Pokemon.Type.create_button(f"team_display_element_type_primary_{self.uuid}")
        self.secondary_type_button = Pokemon.Type.create_button(f"team_display_element_type_secondary_{self.uuid}")
        self.attribute_rows = {}
        for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
            self.attribute_rows[attr_name] = [gui.Text("", key=f"team_display_element_attribute_name_{attr_name}_{self.uuid}", size=(3, 1)), gui.Text("", key=f"team_display_element_attribute_value_{attr_name}_{self.uuid}", size=(3, 1)), Pokemon.Stats.Attribute.create_graph(f"team_display_element_attribute_bar_{attr_name}_{self.uuid}")]

    def update(self, pkmn : Pokemon):
        self.current_pokemon = pkmn
        self.clear_button.update(disabled=False)
        self.title.update(f"{pkmn.name}")
        pkmn.type.update_buttons(self.primary_type_button, self.secondary_type_button, subsample=7)

        for attr_name, row_elements in self.attribute_rows.items():
            aname, avalue, agraph = row_elements
            attribute = getattr(pkmn.stats, attr_name)
            aname.update(attribute.short_name)
            avalue.update(attribute.value)
            agraph.update()
            attribute.draw_on(agraph)

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

        self.team_weakness_type_buttons = [Pokemon.Type.create_button(f"team_analysis_element_weakness_button_{i}_{self.uuid}") for i in range(len(types.all_types))]
        self.team_resistance_type_buttons = [Pokemon.Type.create_button(f"team_analysis_element_resistance_button_{i}_{self.uuid}") for i in range(len(types.all_types))]
        self.team_missing_type_buttons = [Pokemon.Type.create_button(f"team_analysis_element_missing_button_{i}_{self.uuid}") for i in range(len(types.all_types))]


    def update(self):
        pokemon = [element.current_pokemon for element in self.team_elements if element.current_pokemon is not None]
        pokemon : typing.List[Pokemon]

        combined_mappings = {}
        if len(pokemon) != 0:
            combined_mappings = reduce(lambda x,y: types.calculator.combine_mappings(x, y), [pkmn.type.defence_mapping() for pkmn in pokemon])
        team_weaknesses = set(types.calculator.filter_weaknesses(combined_mappings).keys())
        team_resistances = set(types.calculator.filter_resistances(combined_mappings).keys())
        combined_individual_resistances = set(utils.flatten([types.calculator.filter_resistances(pkmn.type.defence_mapping()).keys() for pkmn in pokemon]))
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
            Pokemon.Type.update_button(self.team_weakness_type_buttons[i], next(w_iter, None), subsample=subsample)
            Pokemon.Type.update_button(self.team_resistance_type_buttons[i], next(r_iter, None), subsample=subsample)
            Pokemon.Type.update_button(self.team_missing_type_buttons[i], next(m_iter, None), subsample=subsample)


    def calculate_type_vulnerabilities(self, pokemon : typing.List[Pokemon]):
        pass

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

####################################################
## Other (Temp?)
####################################################
def popup_stat_averages(pokemon: typing.List[Pokemon]):
    # Group raw stats by attribute
    grouped_raw_stats = {}
    grouped_raw_stats : typing.Dict[str, int]
    for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
        grouped_raw_stats[attr_name] = []
        for pkmn in pokemon:
            grouped_raw_stats[attr_name].append(getattr(pkmn.stats,attr_name).value)

    # Covert raw counts into Counter objects
    grouped_counters = {}
    grouped_counters : typing.Dict[str, collections.Counter]
    for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
        grouped_counters[attr_name] = collections.Counter(grouped_raw_stats[attr_name])

    for attr_name in Pokemon.Stats.ALL_ATTR_NAMES:
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

    pokemon = []
    currently_selected_pokemon = None

    moves = []
    currently_selected_move = None

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
            elif current_tab_key == "Summary":
                wrapper.main.summary_search_listbox.button.Click()
            elif current_tab_key == "Moves":
                wrapper.main.moves_search_listbox.button.Click()
            elif current_tab_key == "Options":
                wrapper.main.theme_search_listbox.button.Click()
            else:
                assert True == False, "Enter key not handled for this tab"
        ################################################################################
        # Check for all other keyboard events
        elif len(event) == 1 or event.startswith("Shift")\
                             or event.startswith("Ctrl")\
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
                ingester = RandomizerLogParser(pathlib.Path(input_text_file))
            except InvalidFormatError:
                gui.popup_error("Ingested file doesn't have a valid format!")
                continue

            pokemon = ingester.extractPokemon()
            print(f"Extracted {len(pokemon)} pokemon")

            moves = ingester.extractMoves()
            print(f"Extracted {len(moves)} moves")

            movesets = ingester.extractMovesets()
            print(f"Extracted {len(movesets)} movesets")

            # Add movesets to pokemon
            for moveset in movesets:
                for pkmn in pokemon:
                    if moveset.pkmn_name == pkmn.name:
                        pkmn.add_moveset(moveset)

            # Update Team Builder Screen
            wrapper.main.team_analysis_element.update()

            # Update text
            file_ingested = True
            wrapper.window['text_ingested_boolean'].update(file_ingested)

            # Update combo boxs
            wrapper.main.summary_search_listbox.populate([p.name for p in pokemon])
            wrapper.main.moves_search_listbox.populate([m.name for m in moves])

        ################################################################################
        elif event in wrapper.main.summary_search_listbox.event_keys():
            if len(pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            if event == wrapper.main.summary_search_listbox.button.Key:
                print("==== Event: Summary Chooser Button ====")
                # Find closest match and update the selection
                names = [pkmn.name for pkmn in pokemon]
                name_snippet = values[wrapper.main.summary_search_listbox.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.summary_search_listbox.set_selection(name_to_search)
            else:
                print("==== Event: Summary Chooser Click ====")

            [selected_name] = wrapper.main.summary_search_listbox.currently_selected()
            print(selected_name)
            currently_selected_pokemon = next((pkmn for pkmn in pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None
            wrapper.main.summary_search_listbox.update(currently_selected_pokemon)

        ################################################################################
        elif event in wrapper.main.moves_search_listbox.event_keys():
            if len(pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            if event == wrapper.main.moves_search_listbox.button.Key:
                print("==== Event: Moves Chooser Button ====")
                # Find closest match and update the selection
                names = [move.name for move in moves]
                name_snippet = values[wrapper.main.moves_search_listbox.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.moves_search_listbox.set_selection(name_to_search)
            else:
                print("==== Event: Moves Chooser Click ====")

            [selected_name] = wrapper.main.moves_search_listbox.currently_selected()
            currently_selected_move = next((move for move in moves if move.name == selected_name), None)
            assert currently_selected_move is not None
            wrapper.main.moves_search_listbox.update(currently_selected_move)

        ################################################################################
        elif event in wrapper.main.theme_search_listbox.event_keys():
            # TODO: Fix copy-paste code!
            if event == wrapper.main.theme_search_listbox.button.Key:
                print("==== Event: Theme Chooser Button ====")
                # Find closest match and update the selection
                names = gui.theme_list()
                name_snippet = values[wrapper.main.theme_search_listbox.input_text.Key]
                [name_to_search] = difflib.get_close_matches(name_snippet, names, n=1, cutoff=0)
                print(f"'{name_snippet}' found the match '{name_to_search}'")
                wrapper.main.theme_search_listbox.set_selection(name_to_search)
            else:
                print("==== Event: Theme Chooser Click ====")

            [selected_name] = wrapper.main.theme_search_listbox.currently_selected()
            wrapper.main.theme_search_listbox.update(selected_name)

            #[selected_name] = summary_search_listbox.currently_selected()
            #currently_selected_pokemon = next((pkmn for pkmn in pokemon if pkmn.name == selected_name), None)
            #assert currently_selected_pokemon is not None
            #summary_search_listbox.update(currently_selected_pokemon)

        ################################################################################
        elif event in ("stat_averages",):
            print("==== Event: Stat Averages ====")
            if len(pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            popup_stat_averages(pokemon)

        ################################################################################
        elif event in ("listbox_theme",):
            print("==== Event: Theme Chooser ====")
            [new_theme] = values["listbox_theme"]
            gui.theme(new_theme)

        ################################################################################
        elif event.startswith("pokemon_summary_element_moveset_move_name_"):
            print("==== Event: Summary Moveset Click ====")
            # Simulate a Move Selection search given the move clicked on
            wrapper.main.moves_search_listbox.input_text.update(wrapper.window[event].DisplayText)
            wrapper.main.moves_search_listbox.button.click()

            # Finally, switch tabs to the Moves tab
            wrapper.main.moves_tab.select()

        ################################################################################
        elif event.startswith("pokemon_summary_add_to_team_builder_button"):
            print("=== Event: Add Pokemon To Team Builder ===")
            summary_listbox : SearchableListBox = wrapper.window[event].metadata
            [selected_name] = summary_listbox.currently_selected()
            currently_selected_pokemon : Pokemon = next((pkmn for pkmn in pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None

            for team_builder_element in wrapper.main.team_builder_elements:
                if team_builder_element.empty:
                    team_builder_element.update(currently_selected_pokemon)
                    print(f"Added {currently_selected_pokemon.name} to the team builder")
                    break
            else:
                print(f"Warning: {currently_selected_pokemon} cannot be added to Team Builder as the team is already full!")

        ################################################################################
        elif event.startswith("team_display_element_clear"):
            print("=== Event: Clear Team Display ")
            team_display_element = wrapper.window[event].metadata
            team_display_element.clear()

        ################################################################################
        elif event.startswith("team_display_element_title"):
            print("=== Event: Clear Team Display ===")
            selected_name = wrapper.window[event].DisplayText
            currently_selected_pokemon : Pokemon = next((pkmn for pkmn in pokemon if pkmn.name == selected_name), None)
            assert currently_selected_pokemon is not None
            wrapper.main.summary_search_listbox.update(currently_selected_pokemon)

            # Finally, switch tabs to the Summary tab
            wrapper.main.summary_tab.select()

        ################################################################################
        elif event in ("team_builder_randomize_team_button"):
            print("=== Event: Randomize Team ===")
            if len(pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in wrapper.main.team_builder_elements:
                elem.update(pokemon[random.randint(0,len(pokemon)-1)])

        ################################################################################
        elif event in ("team_builder_randomize_remaining_button"):
            print("=== Event: Randomize Remaining ===")
            if len(pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in wrapper.main.team_builder_elements:
                if elem.empty:
                    elem.update(pokemon[random.randint(0,len(pokemon)-1)])

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
