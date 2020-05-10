import PySimpleGUI as gui

from src import types, utils

class Pokemon:
    def __init__(self, num, name, types, stats, abilities, items):
        self.num = num
        self.name = name
        self.type = Pokemon.Type(types)
        self.stats = Pokemon.Stats(*stats)
        self.abilities = abilities
        self.items = items
        self.moves = {}

    def add_moveset(self, moveset):
        self.moveset = moveset

    @staticmethod
    def fix_unicode_name(name : str):
        return name.replace("â™€", "♀").replace("â™‚", "♂").replace("â€™", "'")

    def debug_print(self):
        print(f"==========")
        print(f"Pokemon #{self.num}: {self.name}")
        print(f"==========")
        print(f"Type      = {self.type}")
        print(f"Stats     = {self.stats}")
        print(f"Abilities = {self.abilities}")
        print(f"Items     = {self.items}")
        print(f"==========")

    def __repr__(self):
        return f"Pokemon[{self.name}]"

    ####################################################
    class Stats:
        ALL_ATTR_NAMES=("hp", "attack", "defence", "special_attack", "special_defence", "speed")

        def __init__(self, hp, p_atk, p_def, speed, s_atk, s_def):
            self.hp = Pokemon.Stats.Attribute("hp", "hp", int(hp), maximum=255)
            self.attack = Pokemon.Stats.Attribute("attack", "atk", int(p_atk), maximum=255)
            self.defence = Pokemon.Stats.Attribute("defence", "def", int(p_def), maximum=255)
            self.special_attack = Pokemon.Stats.Attribute("special_attack", "satk", int(s_atk), maximum=255)
            self.special_defence = Pokemon.Stats.Attribute("special_defence", "sdef", int(s_def), maximum=255)
            self.speed = Pokemon.Stats.Attribute("speed", "spd", int(speed), maximum=255)

        def __str__(self):
            return f"[{self.hp}, {self.attack}, {self.defence}, {self.special_attack}, {self.special_defence}, {self.speed}]"

        ####################################################
        class Attribute:
            GRAPH_MAX=255

            def __init__(self, name, short_name, value, maximum):
                assert value <= self.GRAPH_MAX, f"attribute value ({value}) must be <= {self.GRAPH_MAX}"
                self.name = name
                self.short_name = short_name
                self.value = value
                self.maximum = maximum

            @staticmethod
            def create_graph(key=None):
                return gui.Graph(canvas_size=(Pokemon.Stats.Attribute.GRAPH_MAX, 10), graph_bottom_left=(0,0), graph_top_right=(Pokemon.Stats.Attribute.GRAPH_MAX, 10), key=key)

            def draw_on(self, graph: gui.Graph):
                graph.erase()
                scaled_value = (self.value*(self.GRAPH_MAX/self.maximum))
                graph.draw_rectangle((0, 10), (scaled_value, 0), fill_color=self._colour(scaled_value))

            def _colour(self, value):
                # We adjust the hue scale so it's 0.00 - ~0.72 instead of 0.00 - 1.00
                # This prevents us from having colour rollover, where really low and
                # really high values end up having similar colours.
                h = value/(self.GRAPH_MAX + 100)
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

        def defence_mapping(self):
            if self.secondary is None:
                return types.calculator.defence_mapping(self.primary)
            else:
                a = types.calculator.defence_mapping(self.primary)
                b = types.calculator.defence_mapping(self.secondary)
                return types.calculator.combine_mappings(a, b)

        @staticmethod
        def create_button(key=None):
            return gui.Button("", key=key, button_color=(gui.theme_background_color(), gui.theme_background_color()), border_width=0, image_filename="", disabled=True)

        @staticmethod
        def update_button(button, type_str, subsample=5):
            if type_str is not None:
                button.update(image_filename=utils.resource(f"types/{type_str.lower()}.png"), image_size=(500/subsample,160/subsample), image_subsample=subsample, disabled=False)
            else:
                button.update(image_filename="", disabled=True)


        def update_buttons(self, primary_button, secondary_button=None, subsample=5):
            self.update_button(primary_button, self.primary, subsample=subsample)
            if secondary_button is not None:
                self.update_button(secondary_button, self.secondary, subsample=subsample)


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
            self.power = Pokemon.Stats.Attribute("power", "pow", int(power), maximum=150)
            self.accuracy = Pokemon.Stats.Attribute("accuracy", "acc", int(accuracy), maximum=100)
            self.pp = Pokemon.Stats.Attribute("pp", "pp", int(pp), maximum=40)
            self.category = category

    ####################################################
    class Moveset:
        def __init__(self, pkmn_name):
            self.pkmn_name = pkmn_name
            self.level_move_mappings = []

        def add_mapping(self, level, move_name):
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
