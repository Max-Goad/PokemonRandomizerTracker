import collections
import pathlib
from   pprint import pprint
import random
import statistics
from   typing import Mapping, List

from   matplotlib import pyplot
import numpy
import PySimpleGUI as gui
from   scipy import interpolate

from src import controller, database, parsers, pokemon
from src.custom_elements import SearchableListBox

####################################################
## Other (Temp?)
####################################################
def popupStatAverages(all_pokemon: List[pokemon.Pokemon]):
    # Group raw stats by attribute
    grouped_raw_stats = {}
    grouped_raw_stats : Mapping[str, int]
    for attr_name in pokemon.Stats.ALL_ATTR_NAMES:
        grouped_raw_stats[attr_name] = []
        for pkmn in all_pokemon:
            grouped_raw_stats[attr_name].append(getattr(pkmn.stats,attr_name).value)

    # Covert raw counts into Counter objects
    grouped_counters = {}
    grouped_counters : Mapping[str, collections.Counter]
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
    gui.theme(database.default_theme)

    controller.instance.newWindow("Some Title")

    while True:
        event, encoded_event, values = controller.instance.read()

        ################################################################################
        if event in (None, "Close"):
            break
        ################################################################################
        # Check for ENTER key
        elif encoded_event in (b'\r',):
            print("==== Event: Enter Key ====")
            current_tab_key = controller.instance.current_element.tab_group.Get()
            if current_tab_key == "Home":
                controller.instance.window["button_ingest"].Click()
            elif current_tab_key == "Summary":
                controller.instance.current_element.summary_slb.button.Click()
            elif current_tab_key == "Moves":
                controller.instance.current_element.move_slb.button.Click()
            elif current_tab_key == "Team Builder":
                pass
            elif current_tab_key == "Options":
                controller.instance.current_element.theme_slb.button.Click()
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

            # TODO: Ingester should just return list
            database.instance.addPokemon(list(ingester.extractPokemon().values()))
            # TODO: Move prints into ingester
            print(f"Extracted {len(database.instance.pokemon)} pokemon")

            # TODO: Ingester should just return list
            database.instance.addMoves(list(ingester.extractMoves().values()))
            # TODO: Move prints into ingester
            print(f"Extracted {len(database.instance.moves)} moves")

            movesets = ingester.extractMovesets()
            database.instance.addMovesets(movesets)
            print(f"Extracted movesets for {len(movesets)} pokemon")

            # TODO: Ingester should just return list
            database.instance.addLocations(list(ingester.extractLocations().values()))
            print(f"Extracted {len(database.instance.locations)} locations")

            # Add wild occurrences to pokemon
            database.instance.addWildOccurrencesToPokemon()

            # Add static encounters to pokemon
            database.instance.addStaticPokemonEncounters(ingester.extractStaticOccurrences())

            # Update Team Builder Screen
            controller.instance.current_element.team_analysis_element.update()

            # Update text
            file_ingested = True
            controller.instance.window['text_ingested_boolean'].update(file_ingested)

            # Update combo boxs
            controller.instance.current_element.summary_slb.populate(database.instance.pokemon)
            controller.instance.current_element.move_slb.populate(database.instance.moves)
            controller.instance.current_element.location_slb.populate(database.instance.locations)

        ################################################################################
        elif event.endswith("_callback_available"):
            controller.instance.window[event].metadata()

        ################################################################################
        elif event in ("stat_averages",):
            print("==== Event: Stat Averages ====")
            if len(database.instance.pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            popupStatAverages(database.instance.pokemon.values())

        ################################################################################
        elif event in ("listbox_theme",):
            print("==== Event: Theme Chooser ====")
            [new_theme] = values["listbox_theme"]
            gui.theme(new_theme)

        ################################################################################
        elif event.startswith("summary_element_moveset_move_name_"):
            print("==== Event: Display Moveset Click ====")
            # Simulate a Move Selection search given the move clicked on
            controller.instance.current_element.move_slb.input_text.update(controller.instance.window[event].DisplayText)
            controller.instance.current_element.move_slb.button.click()

            # Finally, switch tabs to the Moves tab
            controller.instance.current_element.moves_tab.select()

        ################################################################################
        elif event.startswith("summary_add_to_team_builder_button"):
            print("=== Event: Add Pokemon To Team Builder ===")
            display_slb : SearchableListBox = controller.instance.window[event].metadata
            [selected_name] = display_slb.currentlySelected()
            assert selected_name in database.instance.pokemon
            currently_selected_pokemon : pokemon.Pokemon = database.instance.pokemon[selected_name]

            for team_builder_element in controller.instance.current_element.team_builder_elements:
                if team_builder_element.empty:
                    team_builder_element.update(currently_selected_pokemon)
                    print(f"Added {currently_selected_pokemon.name} to the team builder")
                    break
            else:
                print(f"Warning: {currently_selected_pokemon} cannot be added to Team Builder as the team is already full!")

        ################################################################################
        elif event.startswith("team_display_element_clear"):
            print("=== Event: Clear Team Display ")
            team_display_element = controller.instance.window[event].metadata
            team_display_element.clear()

        ################################################################################
        elif event.startswith("team_display_element_title"):
            print("=== Event: Clear Team Display ===")
            selected_name = controller.instance.window[event].DisplayText
            assert selected_name in database.instance.pokemon
            controller.instance.current_element.summary_slb.update(database.instance.pokemon[selected_name])

            # Finally, switch tabs to the Display tab
            controller.instance.current_element.display_tab.select()

        ################################################################################
        elif event in ("team_builder_randomize_team_button"):
            print("=== Event: Randomize Team ===")
            if len(database.instance.pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in controller.instance.current_element.team_builder_elements:
                elem.update(list(database.instance.pokemon.values())[random.randint(0,len(database.instance.pokemon)-1)])

        ################################################################################
        elif event in ("team_builder_randomize_remaining_button"):
            print("=== Event: Randomize Remaining ===")
            if len(database.instance.pokemon) == 0:
                gui.popup_error("No Pokemon have been ingested")
                continue

            for elem in controller.instance.current_element.team_builder_elements:
                if elem.empty:
                    elem.update(list(database.instance.pokemon.values())[random.randint(0,len(database.instance.pokemon)-1)])

        ################################################################################
        elif event in ("team_builder_clear_team_button"):
            print("=== Event: Clear Team ===")
            for elem in controller.instance.current_element.team_builder_elements:
                elem.clear()

        ################################################################################
        elif event.startswith("explanation_button_"):
            explanation = controller.instance.window[event].metadata
            gui.popup(explanation, title="Explanation")

        ################################################################################
        else:
            print(f"==== Event: UNKNOWN ({event}) ====")
            pprint(values)
            print(f"==== Event: UNKNOWN ({event}) ====")
    controller.instance.window.close()

if __name__ == "__main__":
    main()
