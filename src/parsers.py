import collections
import itertools
import pprint
from   typing import Mapping, List

from src import pokemon
from src.external import parsers, utils
from src.external.parsers import InvalidFormatError, RegexNotFoundError

class RandomizerLogParser(parsers.FileParser):
    """ TODO: Documentation
    """
    RANDOMIZER_VERSION_HEADER = r"Randomizer Version: (\d+).(\d+).(\d+)"
    POKEMON_VERSION_HEADER = r"Randomization of Pokemon (\w+(?: \d)?).+completed"
    POKEMON_DISPLAY_HEADER = r"Pokemon Base Stats & Types"
    POKEMON_MOVE_HEADER = r"--Move Data--"
    POKEMON_MOVESET_HEADER = r"Pokemon Movesets"
    LOCATION_HEADER = r"Wild Pokemon"
    WILD_POKEMON_HEADER = r"Wild Pokemon"
    STATIC_POKEMON_HEADER = r"Static Pokemon"

    def __init__(self, file):
        super().__init__(file)
        if not self._valid():
            raise parsers.InvalidFormatError
        pass

    def _header_regexes(self):
        return [self.POKEMON_DISPLAY_HEADER]

    def _valid(self):
        try:
            self.find(*self._header_regexes())
            return True
        except parsers.RegexNotFoundError:
            return False

    def extractRandomizerVersion(self):
        self.reset()
        try:
            return self.moveAndGetGroups(self.RANDOMIZER_VERSION_HEADER)
        except RegexNotFoundError:
            return "0","0","0"

    def extractPokemonVersion(self) -> pokemon.Version:
        self.reset()
        version_str = self.moveAndGetGroups(self.POKEMON_VERSION_HEADER)
        return pokemon.Version.parse(version_str)


    def extractPokemon(self, zx = False):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_DISPLAY_HEADER)

        # Move past headers
        self.current_line += 2

        extracted_pkmn = {}

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            pkmn_pieces = [x.strip() for x in line.split("|")]


            if len(pkmn_pieces) == 12:
                num_abilities = 2
            elif len(pkmn_pieces) == 13:
                num_abilities = 3
            else:
                assert len(pkmn_pieces) in (12,13), f"Expected(12/13) vs Actual({len(pkmn_pieces)})"

            num = pkmn_pieces[0]
            name = pokemon.fix_unicode_name(pkmn_pieces[1])
            types = pkmn_pieces[2].split("/")
            stats = pkmn_pieces[3:9]
            # MAX TODO: It's a bit ugly to do it this way. Gotta find a better way.
            #           But it's also ugly to change the god damn order of the stats output, damn it!
            if zx:
                # Reorder stats
                # From: HP, AT, DE, SA, SD, SP
                # To:   HP, AT, DE, SP, SA, SD
                stats[:] = [stats[i] for i in [0, 1, 2, 5, 3, 4]]
            abilities = [a for a in pkmn_pieces[9:9+num_abilities] if a != '-']
            items = [i for i in pkmn_pieces[9+num_abilities].split(",") if i]

            new_pkmn = pokemon.Pokemon(num, name, types, stats, abilities, items)
            extracted_pkmn[new_pkmn.name] = new_pkmn
            self.current_line += 1
        return extracted_pkmn

    def extractMoves(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_MOVE_HEADER)

        # Move past headers
        self.current_line += 2

        extracted_moves = {}

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

            new_move = pokemon.Move(num, name, pokemon.Type([move_type]), power, accuracy, pp, pokemon.Type([category]))
            extracted_moves[new_move.name] = new_move
            self.current_line += 1
        return extracted_moves

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
            pkmn_name = pokemon.fix_unicode_name(pkmn[4:].strip())

            curr_moveset = pokemon.Moveset(pkmn_name)
            for learned_move_string in raw_moveset.split(','):
                learned_move_string = learned_move_string.strip()
                move_name, level = learned_move_string.strip().split("at level")
                curr_moveset.addMapping(int(level), move_name.strip())
            movesets.append(curr_moveset)

            self.current_line += 1
        return movesets

    def extractMovesetsZX(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_MOVESET_HEADER)

        # Move past headers
        self.current_line += 1

        movesets = []

        while True:
            # Find next pokemon
            line = self.lines[self.current_line]
            pkmn = parsers.getGroups(r"^\d+\s(.+)\s-> .+", line)
            if pkmn is None:
                break
            pkmn_name = pokemon.fix_unicode_name(pkmn.strip())

            # Move past stats (why the fuck are they even here to begin with)
            self.current_line += 7

            # Extract moves until empty line encountered
            curr_moveset = pokemon.Moveset(pkmn_name)
            while True:
                line = self.lines[self.current_line]
                if not line.strip():
                    break
                level, move_name = line[6:].strip().split(":")
                curr_moveset.addMapping(int(level), move_name.strip())
                self.current_line += 1
            movesets.append(curr_moveset)
            self.current_line += 1
        return movesets

    def extractLocations(self) -> Mapping[str, pokemon.Location]:
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.WILD_POKEMON_HEADER)

        # Move past headers
        self.current_line += 1

        locations : Mapping[str, pokemon.Location] = {}

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            # set_num is currently unused
            set_num, raw_location, raw_pkmn_list = line.split(' - ')
            # rate is currently unused
            raw_location_name, rate = parsers.getGroups(r"(.+)[(]rate=(\d+)[)]", raw_location.strip())

            # seperate the actual name from the classification
            location_regex = fr"\s*(.+)\s+({'|'.join(pokemon.Sublocation.classifications())})"
            location_name, location_classification = parsers.getGroups(location_regex, raw_location_name.strip())

            location_name = pokemon.fix_unicode_name(location_name)

            if location_name not in locations:
                locations[location_name] = pokemon.Location(location_name)

            # create a sublocation instance
            sl = pokemon.Sublocation(set_num, location_name, location_classification)
            locations[location_name].sublocations.add(sl)

            # Extract mapping from list of raw pokemon/level pairs
            raw_pkmn = raw_pkmn_list.split(',')
            pkmn_level_mapping = collections.defaultdict(set)
            for raw in raw_pkmn:
                # Pokemon Level Mappings can come in 2 forms:
                #   1) "Bulbasaur Lvs XX-YY"
                #   2) "Bulbasaur LvXX"
                # In any case, we must compile all these occurrences together into one mapping:
                #   { "Bulbasaur" : (XX, YY) }
                # where XX is the min, and YY is the max
                if "Lvs" in raw:
                    pkmn_name, lvl_range = raw.split(" Lvs ")
                    pkmn_name = pokemon.fix_unicode_name(pkmn_name.strip())
                    min_level, max_level = (int(l) for l in lvl_range.split('-'))
                    pkmn_level_mapping[pkmn_name].update(range(min_level, max_level+1))
                elif "Lv" in raw:
                    pkmn_name, level = raw.split(" Lv")
                    pkmn_name = pokemon.fix_unicode_name(pkmn_name.strip())
                    pkmn_level_mapping[pkmn_name].add(int(level.strip()))

            for pkmn_name, levels in pkmn_level_mapping.items():
                sl.wild_occurrences.append(pokemon.WildOccurrence(pkmn_name, sl, levels))

            self.current_line += 1

        # Platinum has these unknown locations for some reason
        # We have to get rid of them or they muck up the data.
        if "? Unknown ?" in locations:
            del locations["? Unknown ?"]

        return dict(sorted(locations.items()))

    def extractLocationsZX(self, version : pokemon.Version) -> Mapping[str, pokemon.Location]:
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.WILD_POKEMON_HEADER)

        # Move past headers
        self.current_line += 1

        locations : Mapping[str, pokemon.Location] = {}

        # Location Loop
        while True:
            line = self.lines[self.current_line]

            location_values = parsers.getGroups(r"^Set #(\d+) - (.+)[(]rate=(\d+)[)]", line)
            if location_values is None:
                break
            elif len(location_values) != 3:
                break
            # rate currently unused
            set_num, raw_location, rate = location_values

            # seperate the actual name from the classification
            joined_sublocation_str = '|'.join(pokemon.Sublocation.classifications(version))
            location_regex = fr"\s*(.+)\s+({joined_sublocation_str})"
            print(f"Location Name = {raw_location.strip()}")
            location_name, location_classification = parsers.getGroups(location_regex, raw_location.strip())
            location_name = pokemon.fix_unicode_name(location_name)

            if location_name not in locations:
                locations[location_name] = pokemon.Location(location_name)

            # create a sublocation instance
            sl = pokemon.Sublocation(set_num, location_name, location_classification)
            locations[location_name].sublocations.add(sl)

            # collect all pokemon instances at this location
            pkmn_level_mapping = collections.defaultdict(set)
            while True:
                self.current_line += 1
                line = self.lines[self.current_line]
                if not line.strip():
                    break

                raw_pkmn = parsers.getGroups(r"(.+)\s+HP.+", line)
                if raw_pkmn is None:
                    print(f"Error parsing line as wild occurrence: ''{line}''")
                    break
                # Pokemon Level Mappings can come in 2 forms:
                #   1) "Bulbasaur Lvs XX-YY"
                #   2) "Bulbasaur LvXX"
                # In any case, we must compile all these occurrences together into one mapping:
                #   { "Bulbasaur" : (XX, YY) }
                # where XX is the min, and YY is the max
                if "Lvs" in raw_pkmn:
                    pkmn_name, lvl_range = raw_pkmn.split(" Lvs ")
                    pkmn_name = pokemon.fix_unicode_name(pkmn_name.strip())
                    min_level, max_level = (int(l) for l in lvl_range.split('-'))
                    pkmn_level_mapping[pkmn_name].update(range(min_level, max_level+1))
                elif "Lv" in raw_pkmn:
                    pkmn_name, level = raw_pkmn.split(" Lv")
                    pkmn_name = pokemon.fix_unicode_name(pkmn_name.strip())
                    pkmn_level_mapping[pkmn_name].add(int(level.strip()))

            for pkmn_name, levels in pkmn_level_mapping.items():
                sl.wild_occurrences.append(pokemon.WildOccurrence(pkmn_name, sl, levels))

            self.current_line += 1

        # Platinum has these unknown locations for some reason
        # We have to get rid of them or they muck up the data.
        if "? Unknown ?" in locations:
            del locations["? Unknown ?"]

        return dict(sorted(locations.items()))

    def extractStaticOccurrences(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.STATIC_POKEMON_HEADER)

        # Move past headers
        self.current_line += 1

        static_pkmn_occurrences = dict()

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            # old_num is to differentiate between different occurrences of the same static pokemon.
            # It is currently unused.
            old, old_num, new = parsers.getGroups(r"(\w+)([(]\d[)])? [=][>] (\w+)", line)
            static_pkmn_occurrences[new] = pokemon.WildOccurrence(new, pokemon.StaticSublocation(old), [])
            self.current_line += 1

        return static_pkmn_occurrences


    def extractStaticOccurrencesZX(self, pokemon_version : pokemon.Version):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.STATIC_POKEMON_HEADER)

        # Move past headers
        self.current_line += 1

        static_pkmn_occurrences = dict()

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            if pokemon_version is pokemon.Version.HEARTGOLD or pokemon.Version.SOULSILVER:
                regex = r"^([\w.-]+|Mr. Mime)(?:\(\d\)| \(egg\))? => ([\w.-]+|Mr. Mime)(?:\(\d\)| \(egg\))?"
            else:
                regex = r"(\w+),? (?:Lv\d+(?:[(]\d[)])?|[(]egg[)]) [=][>] (\w+),? (?:Lv\d+|[(]egg[)])"

            print(f"line = {line.strip()}")
            old, new = parsers.getGroups(regex, line.strip())
            static_pkmn_occurrences[new] = pokemon.WildOccurrence(new, pokemon.StaticSublocation(old), [])
            self.current_line += 1

        return static_pkmn_occurrences
