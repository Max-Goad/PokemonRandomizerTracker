import typing
import PySimpleGUI as gui

from src import types
from src.external import utils

def fix_unicode_name(name : str):
    return name.replace("â™€", "♀").replace("â™‚", "♂").replace("â€™", "'")

class Pokemon:
    def __init__(self, num, name, types, stats, abilities, items):
        self.num = num
        self.name = name
        self.type = Type(types)
        self.stats = Stats(*stats)
        self.abilities = abilities
        self.items = items
        self.moves = {}
        self.moveset = []
        self.wild_occurrences : typing.List[WildOccurrence] = []

    def addMoveset(self, moveset):
        self.moveset = moveset

    def addWildOccurrences(self, *wild_occurrences):
        self.wild_occurrences.extend(wild_occurrences)

    def __repr__(self):
        return f"Pokemon[{self.name}]"

####################################################
class Stats:
    ALL_ATTR_NAMES=("hp", "attack", "defence", "special_attack", "special_defence", "speed")

    def __init__(self, hp, p_atk, p_def, speed, s_atk, s_def):
        self.hp = Stats.Attribute("hp", int(hp), maximum=Stats.Attribute.ATTR_MAX)
        self.attack = Stats.Attribute("attack", int(p_atk), maximum=Stats.Attribute.ATTR_MAX)
        self.defence = Stats.Attribute("defence", int(p_def), maximum=Stats.Attribute.ATTR_MAX)
        self.special_attack = Stats.Attribute("special_attack", int(s_atk), maximum=Stats.Attribute.ATTR_MAX)
        self.special_defence = Stats.Attribute("special_defence", int(s_def), maximum=Stats.Attribute.ATTR_MAX)
        self.speed = Stats.Attribute("speed", int(speed), maximum=Stats.Attribute.ATTR_MAX)

    @staticmethod
    def short_name(attr_name):
        if attr_name == "hp":
            return "hp"
        elif attr_name == "attack":
            return "atk"
        elif attr_name == "defence":
            return "def"
        elif attr_name == "special_attack":
            return "stak"
        elif attr_name == "special_defence":
            return "sdef"
        elif attr_name == "speed":
            return "spd"
        elif attr_name == "power":
            return "pow"
        elif attr_name == "accuracy":
            return "acc"
        elif attr_name == "pp":
            return "pp"
        else:
            return None

    def __str__(self):
        return f"[{self.hp}, {self.attack}, {self.defence}, {self.special_attack}, {self.special_defence}, {self.speed}]"

    ####################################################
    class Attribute:
        ATTR_MAX=255

        def __init__(self, name, value, maximum):
            assert value <= self.ATTR_MAX, f"attribute value ({value}) must be <= {self.ATTR_MAX}"
            self.name = name
            self.short_name = Stats.short_name(name) or name
            self.value = value
            self.maximum = maximum

        @staticmethod
        def createGraph(key=None):
            return gui.Graph(canvas_size=(Stats.Attribute.ATTR_MAX, 10), graph_bottom_left=(0,0), graph_top_right=(Stats.Attribute.ATTR_MAX, 10), key=key)

        def drawOn(self, graph: gui.Graph):
            graph.erase()
            scaled_value = (self.value*(self.ATTR_MAX/self.maximum))
            graph.draw_rectangle((0, 10), (scaled_value, 0), fill_color=self._colour(scaled_value))

        def _colour(self, value):
            # We adjust the hue scale so it's 0.00 - ~0.72 instead of 0.00 - 1.00
            # This prevents us from having colour rollover, where really low and
            # really high values end up having similar colours.
            h = value/(self.ATTR_MAX + 100)
            s = 0.75
            v = 0.8
            final_hex = utils.hsv_to_hex(h, s, v)
            return f"#{final_hex}"

        def __str__(self):
            return f"{self.name.upper()}:{self.value}"

####################################################
class Type:
    def __init__(self, types):
        if (len(types) == 1):
            [self.primary] = types
            self.secondary = None
        elif(len(types) == 2):
            self.primary, self.secondary = types
        else:
            raise Exception

    def defenceMapping(self):
        if self.secondary is None:
            return types.calculator.defenceMapping(self.primary)
        else:
            a = types.calculator.defenceMapping(self.primary)
            b = types.calculator.defenceMapping(self.secondary)
            return types.calculator.combineMappings(a, b)

    @staticmethod
    def createButton(key=None):
        return gui.Button("", key=key, button_color=(gui.theme_background_color(), gui.theme_background_color()), border_width=0, image_filename="", disabled=True)

    @staticmethod
    def updateButton(button, type_str, subsample=5):
        if type_str is not None:
            button.update(image_filename=utils.resource(f"types/{type_str.lower()}.png"), image_size=(500/subsample,160/subsample), image_subsample=subsample, disabled=False)
        else:
            button.update(image_filename="", disabled=True)


    def updateButtons(self, primary_button, secondary_button=None, subsample=5):
        self.updateButton(primary_button, self.primary, subsample=subsample)
        if secondary_button is not None:
            self.updateButton(secondary_button, self.secondary, subsample=subsample)


    def __str__(self):
        if (self.secondary):
            return f"{self.primary} / {self.secondary}"
        else:
            return self.primary

####################################################
class Move:
    ALL_ATTR_NAMES = ("power", "accuracy", "pp")
    def __init__(self, num, name, move_type, power, accuracy, pp, category):
        self.num = num
        self.name = name
        self.type = move_type
        self.power = Stats.Attribute("power", int(power), maximum=150)
        self.accuracy = Stats.Attribute("accuracy", int(accuracy), maximum=100)
        self.pp = Stats.Attribute("pp", int(pp), maximum=40)
        self.category = category

####################################################
class Moveset:
    def __init__(self, pkmn_name):
        self.pkmn_name = pkmn_name
        self.level_move_mappings = []

    def addMapping(self, level, move_name):
        self.level_move_mappings.append((level, move_name))

    def __str__(self):
        ret_str = f"{self.pkmn_name} learns the following moves:"
        for level, move_name in self.level_move_mappings:
            ret_str += r"\n"
            ret_str += f"{move_name} at level {level}"
        return ret_str

####################################################
class Location:
    def __init__(self, set_num, pkmn_name, level_min, level_max):
        self.set_num = int(set_num)
        self.pkmn_name = pkmn_name
        self.level_min = level_min
        self.level_max = level_max

####################################################
class WildOccurrence:
    def __init__(self, pkmn_name, location, levels):
        self.pkmn_name = pkmn_name
        self.location = location
        self.levels = levels

    def condensedLevelStr(self) -> str:
        # Original: [0,1,2,3,4,5,6,7,8,9,10,15,20,21,22,23,24,25]
        level_ranges_step1 = utils.to_ranges(self.levels)
        # Step 1: [(0,10), (15,15), (20,25)]
        level_ranges_step2 = []
        for x,y in level_ranges_step1:
            if x == y:
                level_ranges_step2.append(str(x))
            else:
                level_ranges_step2.append(f"{x}-{y}")
        # Step 2: ["0-10", "15", "20-25"]
        level_ranges_step3 = ", ".join(level_ranges_step2)
        # Step 3: "0-10, 15, 20-25"
        return level_ranges_step3

    def __repr__(self):
        return f"Wild Pokemon Occurrence[{self.pkmn_name},{self.location},{self.levels}]"
