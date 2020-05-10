from src import pokemon
from src.external import parsers
from src.external.parsers import InvalidFormatError

class RandomizerLogParser(parsers.FileParser):
    """
    TODO: Documentation
    """
    POKEMON_DISPLAY_HEADER = r"Pokemon Base Stats & Types"
    POKEMON_MOVE_HEADER = r"Move Data"
    POKEMON_MOVESET_HEADER = r"Pokemon Movesets"
    WILD_POKEMON_HEADER = r"Wild Pokemon"

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

    def extractPokemon(self):
        # Move marker back to start
        self.reset()

        # Find start
        self.moveAndGetGroups(self.POKEMON_DISPLAY_HEADER)

        # Move past headers
        self.current_line += 2

        extracted_pkmn = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            pkmn_pieces = [x.strip() for x in line.split("|")]

            assert len(pkmn_pieces) == 12, f"Expected(12) vs Actual({len(pkmn_pieces)})"

            num = pkmn_pieces[0]
            name = pokemon.fix_unicode_name(pkmn_pieces[1])
            types = pkmn_pieces[2].split("/")
            stats = pkmn_pieces[3:9]
            abilities = [a for a in pkmn_pieces[9:11] if a != '-']
            items = [i for i in pkmn_pieces[11].split(",") if i]

            extracted_pkmn.append(pokemon.Pokemon(num, name, types, stats, abilities, items))
            self.current_line += 1
        return extracted_pkmn

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
            moves.append(pokemon.Move(num, name, pokemon.Type([move_type]), power, accuracy, pp, pokemon.Type([category])))
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
            pkmn_name = pokemon.fix_unicode_name(pkmn[4:].strip())

            curr_moveset = pokemon.Moveset(pkmn_name)
            for learned_move_string in raw_moveset.split(','):
                learned_move_string = learned_move_string.strip()
                move_name, level = learned_move_string.strip().split("at level")
                curr_moveset.addMapping(int(level), move_name.strip())
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

        wild_pkmn_locations = []

        # Loop until empty line encountered
        while True:
            line = self.lines[self.current_line]
            if not line.strip():
                break

            set_num, raw_location, raw_pkmn_list = line.split('-')
            # Rate is currently unused
            location_name, rate = parsers.getGroups(r"([\w\s?]+)[(]rate=(\d+)[)]", raw_location.strip())
            raw_pkmn = raw_pkmn_list.split(',')

            # TODO

            self.current_line += 1
        return wild_pkmn_locations