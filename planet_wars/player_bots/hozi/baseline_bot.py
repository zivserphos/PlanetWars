import random
from typing import Iterable, List

from planet_wars.planet_wars import Player, PlanetWars, Order, Planet, Fleet
from planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd
import numpy as np


class HoziBot(Player):

    NAME = "Hozi"


    def calc_distance(self, source_x, source_y, destination_x, destination_y):
        return np.ceil(np.sqrt(((source_x - destination_x) ** 2) + ((source_y - destination_y) ** 2)))


    def next_enemy_conquer(self, game: PlanetWars, source: Planet, planets) -> Planet:
        enemy_planets = planets[planets['owner'] == PlanetWars.ENEMY]
        if enemy_planets.shape[0] == 0:
            return enemy_planets
        enemy_planets.loc[:, 'distance'] = self.calc_distance(source.x, source.y, enemy_planets['x'], enemy_planets['y'])
        enemy_planets.loc[:, 'cost'] = enemy_planets['num_ships'] + enemy_planets['growth_rate'] * enemy_planets['distance']
        enemy_planets = enemy_planets[enemy_planets['cost'] < source.num_ships]
        return enemy_planets.sort_values(by='cost', ascending=False)


    def next_neutral_conquer(self, game: PlanetWars, source: Planet, planets) -> Planet:
        neutral_planets = planets[planets['owner'] == PlanetWars.NEUTRAL]
        neutral_planets.loc[:, 'cost'] = neutral_planets['num_ships']
        if neutral_planets.shape[0] == 0:
            return neutral_planets
        neutral_planets.loc[:, 'distance'] = self.calc_distance(source.x, source.y, neutral_planets['x'], neutral_planets['y'])
        neutral_planets = neutral_planets[neutral_planets['cost'] < source.num_ships]
        return neutral_planets.sort_values(by='cost', ascending=False)


    def run(self, game: PlanetWars, source: Planet, planets) -> Order:
        next_enemy_conquer_df = self.next_enemy_conquer(game, source, planets)
        if next_enemy_conquer_df.shape[0] > 0:
            next_conquer = next_enemy_conquer_df['planet_id'].iloc[0]
            planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] = 0
            return Order(source, next_conquer, source.num_ships)
        else:
            next_neutral_conquer_df = self.next_neutral_conquer(game, source, planets)
            if next_neutral_conquer_df.shape[0] > 0:
                next_conquer = next_neutral_conquer_df['planet_id'].iloc[0]
                planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] = 0
                return Order(source, next_conquer, source.num_ships)
            else:
                return None

    def attack(self, game: PlanetWars, source: Planet, planets) -> Order:
        next_enemy_conquer_df = self.next_enemy_conquer(game, source, planets)
        if next_enemy_conquer_df.shape[0] > 0:
            next_enemy_conquer_df = next_enemy_conquer_df[next_enemy_conquer_df['cost'] < (source.num_ships // 2)]
            if next_enemy_conquer_df.shape[0] > 0:
                next_conquer = next_enemy_conquer_df['planet_id'].iloc[0]
                planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] -= (source.num_ships // 2)
                return Order(source, next_conquer, (source.num_ships // 2))
        else:
            next_neutral_conquer_df = self.next_neutral_conquer(game, source, planets)
            next_neutral_conquer_df = next_neutral_conquer_df[next_neutral_conquer_df['cost'] < (source.num_ships // 2)]
            if next_neutral_conquer_df.shape[0] > 0:
                next_conquer = next_neutral_conquer_df['planet_id'].iloc[0]
                planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] -= (source.num_ships // 2)
                return Order(source, next_conquer, (source.num_ships // 2))
            else:
                return None

    def snip(self, game: PlanetWars, destination: Planet, enemy_fleet: Fleet, planets) -> Order:
        # send +10 ships from the ships of the closest planet
        our_planets = planets[planets['owner'] == PlanetWars.ME]
        our_planets.loc[:, 'distance'] = self.calc_distance(destination.x, destination.y, our_planets['x'], our_planets['y'])
        our_planets.loc[:, 'cost'] = enemy_fleet.num_ships + (our_planets['distance'] - enemy_fleet.turns_remaining) * destination.growth_rate
        our_planets = our_planets[(our_planets['num_ships'] > (our_planets['cost'] + 10)) & (our_planets['distance'] > enemy_fleet.turns_remaining)]
        our_planets.sort_values(by='cost', ascending=True, inplace=True)
        if our_planets.shape[0] > 0:
            source = our_planets.iloc[0]
            planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] -= source.cost + 10
            return Order(source.planet_id, destination, source.cost + 10)
        else:
            return None


    def get_help(self, game: PlanetWars, destination: Planet, enemy_fleet: Fleet, planets) -> Order:
        our_planets = planets[planets['owner'] == PlanetWars.ME]
        our_planets.loc[:, 'distance'] = self.calc_distance(destination.x, destination.y, our_planets['x'], our_planets['y'])
        help_needed = enemy_fleet.num_ships - (destination.num_ships + enemy_fleet.turns_remaining * destination.growth_rate)
        if help_needed <= 0:
            return None
        our_planets = our_planets[(our_planets['distance'] < enemy_fleet.turns_remaining) & (our_planets['num_ships'] > help_needed)]
        if our_planets.shape[0] > 0:
            source = our_planets.iloc[0]
            planets.loc[planets['planet_id'] == source.planet_id, 'num_ships'] -= help_needed
            return Order(source.planet_id, destination, help_needed)


    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        orders = []
        planets = game.get_planets_data_frame().copy()
        enemy_fleets = game.get_fleets_by_owner(PlanetWars.ENEMY)
        for fleet in enemy_fleets:
            destination = game.get_planet_by_id(fleet.destination_planet_id)
            if destination.owner == PlanetWars.ME:
                our_ships = destination.num_ships + destination.growth_rate * fleet.turns_remaining
                if our_ships < fleet.num_ships:
                    if fleet.turns_remaining <= 1:
                        order = self.run(game, destination, planets)
                        orders.append(order) if order is not None else None
                    else:
                        order = self.get_help(game, destination, fleet, planets)
                        orders.append(order) if order is not None else None
            elif destination.owner == PlanetWars.NEUTRAL:
                order = self.snip(game, destination, fleet, planets)
                orders.append(order) if order is not None else None
        our_planets = planets[planets['owner'] == PlanetWars.ME]
        if our_planets.shape[0] > 0:
            source_id = our_planets.sort_values(by='num_ships', ascending=False)['planet_id'].iloc[0]
            source = game.get_planet_by_id(source_id)
            order = self.attack(game, source, planets)
            orders.append(order) if order is not None else None
        return orders

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
    run_and_view_battle(AttackWeakestPlanetFromStrongestBot(), HoziBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = HoziBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            AttackEnemyWeakestPlanetFromStrongestBot(), AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot(), AttackWeakestPlanetFromStrongestBot()
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
    # tester.view_battle(4)


if __name__ == "__main__":
    # test_bot()
    view_bots_battle()
