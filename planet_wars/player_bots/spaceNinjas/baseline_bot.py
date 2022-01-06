import random
from typing import Iterable, List

import numpy as np

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


class spaceNinjas(Player):
    """
    Example of very simple bot - it send flee from its strongest planet to the weakest enemy/neutral planet
    """


    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner != PlanetWars.ME]

    def ships_to_send_in_a_flee(self, source_planet: Planet, dest_planet: Planet) -> int:
        return source_planet.num_ships // 2

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        list_order = []

        planets_df = game.get_planets_data_frame()
        planets_df = planets_df[planets_df['owner'] != 1]

        for i in game.get_planets_by_owner(1):
            planets_df_copy = planets_df.copy()
            planets_df_copy['distance'] = np.sqrt((planets_df_copy.x - i.x) **2 + (planets_df_copy.y - i.y) **2)
            planets_df_copy['threshold'] = planets_df_copy['num_ships'] + planets_df_copy['distance'] * planets_df_copy['growth_rate']

            if (planets_df_copy['threshold'] >= i.num_ships).all():
                continue
            else:
                planets_df_copy = planets_df_copy.loc[planets_df_copy['threshold'] < i.num_ships]

                if 2 in planets_df_copy['owner']:
                    planets_df_copy = planets_df_copy.loc[planets_df_copy['owner'] == 2]
                    planets_df_copy = planets_df_copy.sort_values(['growth_rate'], ascending=[False])
                    planet_to_attack = planets_df_copy.head(6).tail(1)
                    planet_to_attack_id = planet_to_attack['planet_id'].iloc[0]
                    num_ships_send = planet_to_attack['threshold'].iloc[0] + 2
                    planet_to_attack_from = i.planet_id
                    list_order.append(Order(
                        planet_to_attack_from,
                        planet_to_attack_id,
                        num_ships_send
                    ))

                elif 0 in planets_df_copy['owner']:
                    planets_df_copy = planets_df_copy.loc[planets_df_copy['owner'] == 0]
                    planets_df_copy['test'] = planets_df_copy['threshold']/planets_df_copy['growth_rate']
                    planets_df_copy = planets_df_copy.sort_values(['test'], ascending=[ True])
                    planet_to_attack = planets_df_copy.head(1)

                    if len(planet_to_attack['num_ships']) == 0:
                        continue
                    if planet_to_attack['num_ships'].iloc[0] < i.num_ships+1:
                        planet_to_attack_id = planet_to_attack['planet_id'].iloc[0]
                        num_ships_send = planet_to_attack['num_ships'].iloc[0] + 2
                        planet_to_attack_from = i.planet_id
                        list_order.append(Order(
                            planet_to_attack_from,
                            planet_to_attack_id,
                            num_ships_send
                        ))

        return list_order


class AttackWeakestPlanetFromStrongestBot(Player):
    """
    Example of very simple bot - it send flee from its strongest planet to the weakest enemy/neutral planet
    """

    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner != PlanetWars.ME]

    def ships_to_send_in_a_flee(self, source_planet: Planet, dest_planet: Planet) -> int:
        return source_planet.num_ships // 2

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # (1) If we currently have a fleet in flight, just do nothing.
        if len(game.get_fleets_by_owner(owner=PlanetWars.ME)) >= 1:
            return []

        # (2) Find my strongest planet.
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        if len(my_planets) == 0:
            return []
        my_strongest_planet = max(my_planets, key=lambda planet: planet.num_ships)

        # (3) Find the weakest enemy or neutral planet.
        planets_to_attack = self.get_planets_to_attack(game)
        if len(planets_to_attack) == 0:
            return []
        enemy_or_neutral_weakest_planet = min(planets_to_attack, key=lambda planet: planet.num_ships)

        # (4) Send half the ships from my strongest planet to the weakest planet that I do not own.
        return [Order(
            my_strongest_planet,
            enemy_or_neutral_weakest_planet,
            self.ships_to_send_in_a_flee(my_strongest_planet, enemy_or_neutral_weakest_planet)
        )]


class AttackEnemyWeakestPlanetFromStrongestBot(AttackWeakestPlanetFromStrongestBot):
    """
    Same like AttackWeakestPlanetFromStrongestBot but attacks only enemy planet - not neutral planet.
    The idea is not to "waste" ships on fighting with neutral planets.

    See which bot is better using the function view_bots_battle
    """

    def get_planets_to_attack(self, game: PlanetWars):
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack - attack only enemy's planets
        """
        return game.get_planets_by_owner(owner=PlanetWars.ENEMY)


class AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot(AttackWeakestPlanetFromStrongestBot):
    """
    Same like AttackWeakestPlanetFromStrongestBot but with smarter flee size.
    If planet is neutral send up to its population + 5
    If it is enemy send most of your ships to fight!

    Will it out preform AttackWeakestPlanetFromStrongestBot? see test_bot function.
    """

    def ships_to_send_in_a_flee(self, source_planet: Planet, dest_planet: Planet) -> int:
        original_num_of_ships = source_planet.num_ships // 2
        if dest_planet.owner == PlanetWars.NEUTRAL:
            if dest_planet.num_ships < original_num_of_ships:
                return dest_planet.num_ships + 5
        if dest_planet.owner == PlanetWars.ENEMY:
            return int(source_planet.num_ships * 0.75)
        return original_num_of_ships


def get_random_map():
    """
    :return: A string of a random map in the maps directory
    """
    random_map_id = random.randrange(1, 100)
    return get_map_by_id(random_map_id)


def view_bots_battle():
    """
    Runs a battle and show the results in the Java viewer

    Note: The viewer can only open one battle at a time - so before viewing new battle close the window of the
    previous one.
    Requirements: Java should be installed on your device.
    """
    map_str = get_random_map()
    run_and_view_battle(spaceNinjas(), AttackEnemyWeakestPlanetFromStrongestBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = spaceNinjas()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            AttackWeakestPlanetFromStrongestBot(), AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot()
        ],
        maps=maps
    )
    tester.run_tournament()

    # for a nicer df printing
    pd.set_option('display.max_columns', 30)
    pd.set_option('expand_frame_repr', False)

    print(tester.get_testing_results_data_frame())
    print("\n\n")
    print(tester.get_score_object())

    # To view battle number 4 uncomment the line below
    tester.view_battle(4)


if __name__ == "__main__":
    test_bot()
    #view_bots_battle()
