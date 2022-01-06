from courses.planet_wars.player_bots.data_campers.best_bot_in_galaxy import BestBotInGalaxy
from courses.planet_wars.player_bots.ender.EnderBot import EnderBot
from courses.planet_wars.player_bots.kong_fu_pandas.baseline_bot import KongFuSyrianPandas
from courses.planet_wars.player_bots.rocket_league.baseline_bot import rocket_league_bot
from courses.planet_wars.player_bots.rubber_ducks.Bot1 import Bot1
from courses.planet_wars.player_bots.space_pirates.baseline_bot import Firstroundstrategy
from courses.planet_wars.player_bots.under_the_hood.baseline_bot import UnderTheHoodBot
import random
from typing import Iterable, List
from operator import itemgetter
import math

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


class NerdBot(Player):

    NAME = "Fun With Flags"

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:

        try:
            if game.turns == 0:
                home = game.get_planets_by_owner(1)
                neutrals  = game.get_planets_by_owner(0)
                closest = self.dis_home(neutrals, home[0])
                if closest.num_ships + 10 <= home[0].num_ships // 2:
                    return [Order(home[0], closest, closest.num_ships + 10)]

            planet_scores = self.get_planet_score(game)
            our_planet_scores = [i for i in planet_scores if i[0].owner == 1]
            str_plts_num = math.ceil(len(our_planet_scores) * 0.3)
            str_plts = self.get_str_plts(our_planet_scores, str_plts_num)

            order_list = []
            cur_max_index = -1
            cur_max = planet_scores[cur_max_index][0]
            total = self.sum_ships(str_plts)
            cur_need = cur_max.num_ships + 25
            while(total):

                while(cur_need and (total >= cur_need)):
                    source = self.dis_list(str_plts, cur_max)
                    if cur_need >= str_plts[source][1]:
                        order = Order(str_plts[source][0], cur_max, str_plts[source][1])
                        total -= str_plts[source][1]
                        cur_need -= str_plts[source][1]
                        str_plts.pop(source)
                    else:
                        order = Order(str_plts[source][0], cur_max, cur_need)
                        total -= cur_need
                        str_plts[source][1] -= cur_need
                    order_list.append(order)
                cur_max_index -= 1
                cur_max = planet_scores[cur_max_index][0]
                cur_need = cur_max.num_ships + 25
                if cur_max_index == -len(planet_scores) // 3:
                    break
            return order_list


        except:
            print("error")
            return []

    def dis_list(self, str_plts, planet):
        min = Planet.distance_between_planets(str_plts[0][0], planet)
        p = 0
        for i in range(1, len(str_plts)):
            if Planet.distance_between_planets(str_plts[i][0], planet) < min:
                min = Planet.distance_between_planets(str_plts[i][0], planet)
                p = i
        return p

    def dis_home(self, list, planet):
        min = Planet.distance_between_planets(list[0], planet)
        p = list[0]
        for i in range(1, len(list)):
            if Planet.distance_between_planets(list[i], planet) < min:
                min = Planet.distance_between_planets(list[i], planet)
                p = list[i]
        return p

    def sum_ships(self, str_plts):
        sum = 0
        for p in str_plts:
            sum += p[1]
        return sum

    def get_planet_score(self, game):
        planet_scores = []
        for planet in game.planets:
            deno = planet.num_ships
            if planet.owner == 1:
                for fleet in game.fleets:
                    if fleet.destination_planet_id == planet.planet_id:
                        if fleet.owner == 1:
                            deno += fleet.num_ships
                        else:
                            deno -= fleet.num_ships
            else:
                for fleet in game.fleets:
                    if fleet.destination_planet_id == planet.planet_id:
                        if fleet.owner == 1:
                            deno -= fleet.num_ships
                        else:
                            deno += fleet.num_ships
            if deno == 0:
                deno = 1
            if planet.owner == 0:
                deno *= 4
            if planet.owner == 1:
                deno *= 4
            score = abs(planet.growth_rate / deno)
            planet_scores.append([planet, score])
        planet_scores = sorted(planet_scores, key = itemgetter(1))
        return planet_scores

    def get_str_plts(self, our_planets, num):
        str_plts = []
        for i in range(num):
            str_plts.append([our_planets[i][0], our_planets[i][0].num_ships // 2])
        return str_plts




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
    run_and_view_battle(AttackWeakestPlanetFromStrongestBot(), AttackEnemyWeakestPlanetFromStrongestBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = NerdBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[

    EnderBot(), rocket_league_bot(), UnderTheHoodBot(),
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
    #for i in range(1,13):
    #tester.view_battle(5)


if __name__ == "__main__":
    test_bot()
    #view_bots_battle()
