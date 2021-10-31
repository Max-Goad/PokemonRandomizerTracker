import collections
import pathlib
from   typing import List, Mapping

from src import pokemon

default_source_location = "X:/Games/Emulators/Pokemon Randomizer/roms/Pokemon Black 2 Randomizer 2021.nds.log"
default_theme = "Topanga"

class Database:
    def __init__(self):
        # TODO: Default should be ingested from file
        self.source_location : pathlib.Path = None
        self.theme : str = "Topanga"
        self.version : pokemon.Version = None
        self.pokemon : Mapping[str, pokemon.Pokemon] = {}
        self.moves : Mapping[str, pokemon.Move] = {}
        self.locations : Mapping[str, pokemon.Location] = {}

    def setVersion(self, version : pokemon.Version):
        self.version = version

    def addPokemon(self, pkmn : List[pokemon.Pokemon]):
        for p in pkmn:
            self.pokemon[p.name] = p

    def addMoves(self, moves : List[pokemon.Move]):
        for m in moves:
            self.moves[m.name] = m

    def addMovesets(self, movesets : List[pokemon.Moveset]):
        for ms in movesets:
            assert ms.pkmn_name in self.pokemon, f"{ms.pkmn_name} not found in {len(self.pokemon)} pokemon ingested into database"
            self.pokemon[ms.pkmn_name].addMoveset(ms)

    def addLocations(self, locations : List[pokemon.Location]):
        for l in locations:
            self.locations[l.name] = l

    def addWildOccurrencesToPokemon(self):
        # 1) Extract occurrences into map of [pkmn_name, wo]
        wild_occurrences : Mapping[str, List[pokemon.WildOccurrence]] = collections.defaultdict(list)
        wo_counter = 0
        for location in self.locations.values():
            for sublocation in location.sublocations:
                for wild_occurrence in sublocation.wild_occurrences:
                    wild_occurrences[wild_occurrence.pkmn_name] += [wild_occurrence]
                    wo_counter += 1
        # 2) Apply all wild occurrences to list of all pokemon
        for pkmn in self.pokemon.values():
            pkmn.addWildOccurrences(*wild_occurrences[pkmn.name])
        # TODO: Is the print really in the right place/necessary?
        print(f"Applied {wo_counter} wild occurrences to {len(self.pokemon)} pokemon")

    def addStaticPokemonEncounters(self, encounters : Mapping[str, pokemon.WildOccurrence]):
        for pkmn in self.pokemon.values():
            if pkmn.name in encounters:
                pkmn.addWildOccurrences(encounters[pkmn.name])
        # TODO: Is the print really in the right place/necessary?
        print(f"Extracted static occurrences for {len(encounters)} pokemon")

instance = Database()
