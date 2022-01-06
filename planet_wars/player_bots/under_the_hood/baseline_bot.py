import random
from typing import Iterable, List

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
#from courses.planet_wars.player_bots.ender.EnderBot import EnderBot
#from courses.planet_wars.player_bots.kong_fu_pandas.baseline_bot import KongFuSyrianPandas
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd
import numpy as np


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



class UnderTheHoodBot(Player):
    """
    Chen & Roei's bot
    """

    def __init__(self):
        super(UnderTheHoodBot, self).__init__()
        self.FIRST_TURN = 1
        self.turn =0

    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner != PlanetWars.ME]

    def get_planets_to_defend(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we can defend
        """
        return [p for p in game.planets if p.owner == PlanetWars.ME]

    def ships_to_send_in_a_flee(self, source_planet: Planet, dest_planet: Planet) -> int:
        return source_planet.num_ships // 2

    def calc_distance_all_planets(self, game: PlanetWars):
        df = game.get_planets_data_frame()
        X_all = df['x'].to_numpy()
        Y_all = df['y'].to_numpy()
        dist_x = np.square(X_all - X_all[:, np.newaxis])
        dist_y = np.square(Y_all - Y_all[:, np.newaxis])
        self.distances = np.ceil(np.sqrt(dist_x + dist_y))

    def filter_possible_attacks(self, possible_attacks, our_planet):
        possible_attacks = possible_attacks.loc[False == ((possible_attacks['growth_rate'] < our_planet.growth_rate) & (possible_attacks['total_ships'] > our_planet.num_ships*0.5))]
        return possible_attacks

    def check_fleets(self, all_fleets, all_planets):
        orders = []
        if len(all_fleets):
            all_fleets = all_fleets[all_fleets['owner'] == 2]
            if len(all_fleets):
                for planet_from in all_planets:
                    sent = 0
                    for idx, row in all_fleets.iterrows():
                        temp = 20 + np.random.randint(10)
                        sent += temp
                        if planet_from.num_ships > sent+50:
                            orders.append(Order(planet_from.planet_id,
                                        row['destination_planet_id'],
                                        temp))
        return orders


    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # (-1)
        self.turn += 1
        if self.FIRST_TURN:
            self.calc_distance_all_planets(game)
            self.FIRST_TURN = 0
        # (0)
        all_planets = game.get_planets_data_frame()
        all_fleets = game.get_fleets_data_frame()

        # (1) If we currently have a fleet in flight, just do nothing.
        # if len(game.get_fleets_by_owner(owner=PlanetWars.ME)) >= 1:
        #    return []

        # (2) Find all my planets.
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        if len(my_planets) == 0:
            return []
        # my_strongest_planet = max(my_planets, key=lambda planet: planet.num_ships)

        # (3) Find the best planet to attack (for each of our planets).

        planets_to_attack = self.get_planets_to_attack(game)
        if len(planets_to_attack) == 0:
            return []

        orders = []
        # Defend
        if self.turn %2 == 1:
            self.check_fleets(all_fleets, my_planets)
        # loop over our planets
        if not orders:
            for our_planet in my_planets:
                possible_attacks = pd.DataFrame()
                for planet_to_attack in planets_to_attack:
                    # get dist from dictionary
                    dist_to_attack = self.distances[our_planet.planet_id, planet_to_attack.planet_id]

                    # get fleets by planet id
                    # reinforcements = all_fleets.loc[all_fleets['destination_planet']==planet_to_attack.planet_id]
                    total_ships = planet_to_attack.num_ships + (
                                planet_to_attack.owner * 0.5 * planet_to_attack.growth_rate * dist_to_attack)
                    if total_ships < our_planet.num_ships:
                        score = (planet_to_attack.growth_rate * (1 + (planet_to_attack.owner == 2 * 4))) / (
                                    max(dist_to_attack * total_ships, 1))
                        possible_attacks = possible_attacks.append(
                            {'dest': planet_to_attack.planet_id, 'total_ships': total_ships, 'score': score,
                             'owner': planet_to_attack.owner,
                             'growth_rate': planet_to_attack.growth_rate},
                            ignore_index=True)

                #if len(possible_attacks):
                #   possible_attacks = self.filter_possible_attacks(possible_attacks, our_planet)
                current_ships = our_planet.num_ships
                if len(possible_attacks):
                    possible_attacks.sort_values(by='score', inplace=True, ascending=False)
                    attack = possible_attacks.iloc[[0]]

                    ships_sent = min((attack['total_ships'].iloc[0] + 10, current_ships))
                    orders.append(Order(our_planet.planet_id,
                                        attack['dest'].iloc[0],
                                        ships_sent))


        return orders


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
    run_and_view_battle(UnderTheHoodBot(), EnderBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = UnderTheHoodBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            EnderBot(),
            KongFuSyrianPandas()
            #AttackEnemyWeakestPlanetFromStrongestBot()
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
    test_bot()
    #view_bots_battle()
