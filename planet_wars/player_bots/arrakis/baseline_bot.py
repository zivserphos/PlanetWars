import random
from typing import Iterable, List
from planet_wars.player_bots.data_campers.best_bot_in_galaxy import BestBotInGalaxy
from planet_wars.player_bots.ender.EnderBot import EnderBot
from planet_wars.player_bots.fun_with_flags.baseline_bot import NerdBot
from planet_wars.player_bots.kong_fu_pandas.baseline_bot import KongFuSyrianPandas
from planet_wars.player_bots.rocket_league.baseline_bot import rocket_league_bot
from planet_wars.player_bots.rubber_ducks.Bot1 import Bot1
from planet_wars.player_bots.space_pirates.baseline_bot import Firstroundstrategy
from planet_wars.player_bots.under_the_hood.baseline_bot import UnderTheHoodBot
from planet_wars.tournament import Tournament, get_map_by_id

from planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


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


class BestBot(Player):
    NAME = 'Arrakis'

    '''
    def get_state(self, game: PlanetWars):
        self.num_ships = game.total_ships_by_owner(game.ME)
        self.opponent_ships = game.total_ships_by_owner(game.ENEMY)
        my_planets = game.get_planets_by_owner(game.ME)
        opponent_planets = game.get_planets_by_owner(game.ENEMY)
        self.total_growth = sum([planet.growth_rate for planet in my_planets])
        self.opponent_growth = sum([planet.growth_rate for planet in opponent_planets])
    '''

    def ships_to_send_in_a_flee(self, source_planet, dest_planet) -> int:
        if dest_planet.owner == 0:
            enemy_planet = dest_planet.num_ships
            if (source_planet.num_ships > enemy_planet):
                return enemy_planet + 1
            return 0
        if dest_planet.owner == 2:
            on_arrival = dest_planet.num_ships + Planet.distance_between_planets(source_planet,
                                                                             dest_planet) * dest_planet.growth_rate
            if source_planet.num_ships > on_arrival + 2:
                return on_arrival + 2
        return 0

    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        possible_planets = [p for p in game.planets if p.owner != PlanetWars.ME]
        possible_planets_ordered = sorted(possible_planets, key=lambda x: x.owner, reverse=True)
        fleets_omw = game.get_fleets_by_owner(game.ME)
        planets_omw = [fleet.destination_planet_id for fleet in fleets_omw]
        ans = []
        for planet in possible_planets:
            if planet.planet_id not in planets_omw:
                ans.append(planet)
        return ans

    def attacking_planet_by_radius(self, planet: Planet, radius: int):
        game = self.game
        planets = game.get_planets_by_owner(game.ME)
        for p in planets:
            dist = Planet.distance_between_planets(planet, p)
            if dist == radius:
                return p
        return None

    def stealing_neutral_planets(self, game: PlanetWars):
        fleet_data = game.get_fleets_data_frame()
        fleet_data['destination_owner'] = fleet_data['destination_planet_id'].apply(
            lambda x: (game.get_planet_by_id(x)).owner)
        fleet_data = fleet_data[fleet_data['owner'] == game.ENEMY]
        fleet_data['destination_planet'] = fleet_data['destination_planet_id'].apply(game.get_planet_by_id)
        fleet_data['destination_planet_ships'] = fleet_data['destination_planet'].apply(lambda x: x.num_ships)
        fleet_data['total_after_conquer'] = fleet_data['num_ships'] - fleet_data['destination_planet_ships']
        fleet_data.set_index('destination_planet_id', inplace=True)

        fleets_omw = game.get_fleets_by_owner(game.ME)
        planets_omw = [fleet.destination_planet_id for fleet in fleets_omw]
        res = []

        for dest_id, row in fleet_data.iterrows():

            if dest_id in planets_omw:
                continue

            dest_planet = game.get_planet_by_id(dest_id)
            radius = row['turns_remaining']
            attacking_planet = self.attacking_planet_by_radius(dest_planet, radius + 1)
            if (attacking_planet != None):
                res.append(Order(
                    attacking_planet,
                    dest_id,
                    row['total_after_conquer'] + 6))

        return res

    def match_fights(self, our_planets: List[Planet], target_plants: List[Planet]):
        res = []
        for origin_plant in our_planets:
            possible_planets_est = [[planet, planet.num_ships] for planet in target_plants]
            for planet_est in possible_planets_est:
                planet_est[1] += (4 * Planet.distance_between_planets(origin_plant, planet_est[0]))
                planet_est[1] -= (3 * planet_est[0].growth_rate)
            min_planet = min(possible_planets_est, key=lambda x: x[1])
            if min_planet[1] < origin_plant.num_ships:
                res.append([origin_plant, min_planet[0]])

        return res

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:

        self.game = game
        res = []

        if len(game.get_fleets_data_frame()) > 0:
            res += self.stealing_neutral_planets(game)

        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        planets_to_attack = self.get_planets_to_attack(game)

        # (2) Find my strongest planets.
        if len(my_planets) == 0:
            return []
        my_strongest_planet = sorted(my_planets, key=lambda planet: planet.num_ships, reverse=True)

        # (3) Find the weakest enemies or neutral planet.
        if len(planets_to_attack) == 0:
            return []
        enemy_or_neutral_weakest_planet = sorted(planets_to_attack, key=lambda planet: planet.num_ships)

        matching_attack = self.match_fights(my_strongest_planet, enemy_or_neutral_weakest_planet)

        for match in matching_attack:
            how_many = self.ships_to_send_in_a_flee(match[0], match[1])
            if how_many == 0:
                continue
            res += [Order(
                match[0], match[1], how_many)]

        return res


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
    run_and_view_battle(BestBot(), EnderBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = BestBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            NerdBot(), EnderBot(), rocket_league_bot(), UnderTheHoodBot(),
            KongFuSyrianPandas(), BestBotInGalaxy()
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

    # newest_code

if __name__ == "__main__":
    test_bot()
    view_bots_battle()