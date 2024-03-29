import typing

all_types = ["BUG", "DARK", "DRAGON", "ELECTRIC", "FAIRY", "FIGHTING",
             "FIRE", "FLYING", "GHOST", "GRASS", "GROUND", "ICE",
             "NORMAL", "POISON", "PSYCHIC", "ROCK", "STEEL", "WATER"]

all_types_with_unknown = all_types + ["UNKNOWN"]

all_categories = ["PHYSICAL", "SPECIAL", "STATUS"]

TypeStr = str
TypeMapping = typing.Dict[TypeStr, float]

class TypeMatchupCalculator:

    def __init__(self):
        self.mapping = {"NORMAL" :   {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 0.5,
                                      "GHOST"    : 0,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "FIRE" :     {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 0.5,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 2,
                                      "ICE"      : 2,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 2,
                                      "ROCK"     : 0.5,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 0.5,
                                      "DARK"     : 1,
                                      "STEEL"    : 2,
                                      "FAIRY"    : 1},
                        "WATER" :    {"NORMAL"   : 1,
                                      "FIRE"     : 2,
                                      "WATER"    : 0.5,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 0.5,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 2,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 2,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 0.5,
                                      "DARK"     : 1,
                                      "STEEL"    : 1,
                                      "FAIRY"    : 1},
                        "ELECTRIC" : {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 2,
                                      "ELECTRIC" : 0.5,
                                      "GRASS"    : 0.5,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 0,
                                      "FLYING"   : 2,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 0.5,
                                      "DARK"     : 1,
                                      "STEEL"    : 1,
                                      "FAIRY"    : 1},
                        "GRASS" :    {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 2,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 0.5,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 0.5,
                                      "GROUND"   : 2,
                                      "FLYING"   : 0.5,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 0.5,
                                      "ROCK"     : 2,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 0.5,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "ICE" :      {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 0.5,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 2,
                                      "ICE"      : 0.5,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 2,
                                      "FLYING"   : 2,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 2,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "FIGHTING" : {"NORMAL"   : 2,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 2,
                                      "FIGHTING" : 1,
                                      "POISON"   : 0.5,
                                      "GROUND"   : 1,
                                      "FLYING"   : 0.5,
                                      "PSYCHIC"  : 0.5,
                                      "BUG"      : 0.5,
                                      "ROCK"     : 2,
                                      "GHOST"    : 0,
                                      "DRAGON"   : 1,
                                      "DARK"     : 2,
                                      "STEEL"    : 2,
                                      "FAIRY"    : 0.5},
                        "POISON" :   {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 2,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 0.5,
                                      "GROUND"   : 0.5,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 0.5,
                                      "GHOST"    : 0.5,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 0,
                                      "FAIRY"    : 2},
                        "GROUND" :   {"NORMAL"   : 1,
                                      "FIRE"     : 2,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 2,
                                      "GRASS"    : 0.5,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 2,
                                      "GROUND"   : 1,
                                      "FLYING"   : 0,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 0.5,
                                      "ROCK"     : 2,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 2,
                                      "FAIRY"    : 1},
                        "FLYING" :   {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 0.5,
                                      "GRASS"    : 2,
                                      "ICE"      : 1,
                                      "FIGHTING" : 2,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 2,
                                      "ROCK"     : 0.5,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "PSYCHIC" :  {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 2,
                                      "POISON"   : 2,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 0.5,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 1,
                                      "DARK"     : 0,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "BUG" :      {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 2,
                                      "ICE"      : 1,
                                      "FIGHTING" : 0.5,
                                      "POISON"   : 0.5,
                                      "GROUND"   : 1,
                                      "FLYING"   : 0.5,
                                      "PSYCHIC"  : 2,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 0.5,
                                      "DRAGON"   : 1,
                                      "DARK"     : 2,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 0.5},
                        "ROCK" :     {"NORMAL"   : 1,
                                      "FIRE"     : 2,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 2,
                                      "FIGHTING" : 0.5,
                                      "POISON"   : 1,
                                      "GROUND"   : 0.5,
                                      "FLYING"   : 2,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 2,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},
                        "GHOST" :    {"NORMAL"   : 0,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 2,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 2,
                                      "DRAGON"   : 1,
                                      "DARK"     : 0.5,
                                      "STEEL"    : 1,
                                      "FAIRY"    : 1},
                        "DRAGON" :   {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 2,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 0},
                        "DARK" :     {"NORMAL"   : 1,
                                      "FIRE"     : 1,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 0.5,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 2,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 2,
                                      "DRAGON"   : 1,
                                      "DARK"     : 0.5,
                                      "STEEL"    : 1,
                                      "FAIRY"    : 0.5},
                        "STEEL" :    {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 0.5,
                                      "ELECTRIC" : 0.5,
                                      "GRASS"    : 1,
                                      "ICE"      : 2,
                                      "FIGHTING" : 1,
                                      "POISON"   : 1,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 2,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 1,
                                      "DARK"     : 1,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 2},
                        "FAIRY" :    {"NORMAL"   : 1,
                                      "FIRE"     : 0.5,
                                      "WATER"    : 1,
                                      "ELECTRIC" : 1,
                                      "GRASS"    : 1,
                                      "ICE"      : 1,
                                      "FIGHTING" : 2,
                                      "POISON"   : 0.5,
                                      "GROUND"   : 1,
                                      "FLYING"   : 1,
                                      "PSYCHIC"  : 1,
                                      "BUG"      : 1,
                                      "ROCK"     : 1,
                                      "GHOST"    : 1,
                                      "DRAGON"   : 2,
                                      "DARK"     : 2,
                                      "STEEL"    : 0.5,
                                      "FAIRY"    : 1},

                            }

    def calculate(self, attacking_type, defending_type, secondary_defending_type=None) -> float:
        if secondary_defending_type is None:
            return self.mapping[attacking_type][defending_type]
        else:
            return self.mapping[attacking_type][defending_type] * self.mapping[attacking_type][secondary_defending_type]

    def defenceMapping(self, defending_type, filter_lambda=lambda x:True) -> TypeMapping:
        """Returns the mapping for a given defending type."""
        return {attacking_type:def_dict[defending_type] for attacking_type, def_dict in self.mapping.items() if filter_lambda(def_dict[defending_type])}

    def combineMappings(self, a : TypeMapping, b : TypeMapping) -> TypeMapping:
        """Combines two mappings together, multiplying common elements."""
        # First generate common elements
        common_mapping = {}
        for at,av in a.items():
            for bt,bv in b.items():
                if at == bt:
                    common_mapping[at] = av*bv
        # Then merge b onto a, then common_mapping onto that combined dict
        # This results in a mapping that is a combination of a and b, with
        # common values being multiplied together.
        return {**a, **b, **common_mapping}

    def filterResistances(self, mapping : TypeMapping) -> TypeMapping:
        """Filters a TypeMapping to contain only resistances"""
        return {k:v for k,v in mapping.items() if v < 1}

    def filterWeaknesses(self, mapping : TypeMapping) -> TypeMapping:
        """Filters a TypeMapping to contain only weaknesses"""
        return {k:v for k,v in mapping.items() if v > 1}

calculator = TypeMatchupCalculator()