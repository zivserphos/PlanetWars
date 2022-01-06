import random
from typing import Iterable, List
import numpy as np
from queue import PriorityQueue
from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot
from courses.planet_wars.player_bots.data_campers.best_bot_in_galaxy import BestBotInGalaxy
from courses.planet_wars.player_bots.the_princesses.princesses_bot import PrincessesBot
from courses.planet_wars.player_bots.ender.EnderBot import EnderBot
from courses.planet_wars.player_bots.rocket_league.baseline_bot import rocket_league_bot
from courses.planet_wars.player_bots.space_pirates.baseline_bot import Firstroundstrategy
from courses.planet_wars.player_bots.under_the_hood.baseline_bot import UnderTheHoodBot
from courses.planet_wars.tournament import Tournament, get_map_by_id
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
        # if len(game.get_fleets_by_owner(owner=PlanetWars.ME)) >= 1:
        #     return []

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

class KongFuSyrianPandas(Player):
    """
    The best bot out there..
    """
    NAME = "KongFuSyrianPandas"
    IS_FIRST_TURN = True
    def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner != PlanetWars.ME]

    def get_enemy_planets(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner == PlanetWars.ENEMY]

    def get_enemy_fleets(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [f for f in game.fleets if f.owner == PlanetWars.ENEMY]

    def get_my_fleets(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [f for f in game.fleets if f.owner == PlanetWars.ME]

    def get_natural_planets(self, game: PlanetWars) -> List[Planet]:
        """
        :param game: PlanetWars object representing the map
        :return: The planets we need to attack
        """
        return [p for p in game.planets if p.owner == PlanetWars.NEUTRAL]

    def get_planet_score(self,my_planet,target_planet,num_ships_on_way):

        weights = {'growth_rate':8,'distance':-0.6,'ships':-0.4,'is_enemy':3}

        growth_rate = target_planet.growth_rate
        distance = self.get_dist(my_planet,target_planet)
        ships = target_planet.num_ships + num_ships_on_way
        is_enemy = target_planet.owner == PlanetWars.ENEMY

        temp_score = (growth_rate * weights['growth_rate'] + distance * weights['distance'] + ships * weights['ships'])
        if temp_score < 0:
            temp_score = 0
        if is_enemy:
            if temp_score > 0:
                return weights['is_enemy']*temp_score
            else:
                return temp_score / weights['is_enemy']

        return temp_score


    def get_dist(self,source_planet,target_planet):
        return int(np.linalg.norm(np.array([target_planet.x,target_planet.y]) - np.array([source_planet.x,source_planet.y])))

    def ships_to_send_in_a_fleet(self, source_planet: Planet, dest_planet: Planet,game: PlanetWars) -> int:

        expected_defence = dest_planet.num_ships + 3

        if dest_planet in self.get_enemy_planets(game):
            expected_defence += dest_planet.growth_rate * self.get_dist(source_planet,dest_planet) + 3


        if source_planet.num_ships < expected_defence:
            return None
        return int(round(min(source_planet.num_ships-5,expected_defence)))

    def calc_num_ships_on_the_way(self,dest_planet,game: PlanetWars):
        my_fleets = self.get_my_fleets(game)
        enemy_fleets =  self.get_enemy_fleets(game)
        sum_enemy_fleets_list_on_the_way =  sum([x.num_ships for x in filter(lambda x: x.destination_planet_id == dest_planet.planet_id, enemy_fleets)])
        sum_my_fleets_list_on_the_way= sum([x.num_ships for x in filter(lambda x: x.destination_planet_id == dest_planet.planet_id, my_fleets)])

        return sum_enemy_fleets_list_on_the_way - sum_my_fleets_list_on_the_way

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """

        orders = []

        # Get atributes
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        enemy_and_natural_planets = game.get_planets_by_owner(owner=PlanetWars.ENEMY) + game.get_planets_by_owner(owner=PlanetWars.NEUTRAL)
        if len(my_planets) == 0:
            return []
        my_planets.sort(key=lambda planet: planet.num_ships,reverse=True)
        my_strongest_planet = max(my_planets, key=lambda planet: planet.num_ships)
        scores = []
        PlanetDataFrame = game.get_planets_data_frame()
        fleetsDataFrame = game.get_fleets_data_frame()
        my_planets_df = PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ME]
        enemy_planets_df = PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ENEMY]
        my_total_num_of_ships = my_planets_df['num_ships'].sum()
        enemy_total_num_of_ships = enemy_planets_df['num_ships'].sum()


        if(len(self.get_enemy_planets(game)) > 0):

            enemy_strongest_planet = max(self.get_enemy_planets(game), key=lambda planet: planet.num_ships)
            if my_total_num_of_ships > 2 * enemy_strongest_planet.num_ships:
                # print("Mother Russia")
                ships_sent = 0
                for i in range(len(my_planets)):

                    Order(my_planets[i], enemy_strongest_planet, int(my_planets[i].num_ships * 0.8))
                    my_last_fleet_size = int(my_planets[i].num_ships * 0.8)
                    ships_sent += my_last_fleet_size
                    ships_to_send = self.ships_to_send_in_a_fleet(my_planets[i], enemy_strongest_planet, game)
                    if (ships_to_send != None and ships_sent > self.ships_to_send_in_a_fleet(my_planets[i],
                                                                                             enemy_strongest_planet,
                                                                                             game)):
                        break
                    my_planets[i].num_ships -= my_last_fleet_size


        if self.IS_FIRST_TURN:
            self.IS_FIRST_TURN = False
            my_planet = game.get_planet_by_id(PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ME].planet_id.values)
            enemy_planet =  game.get_planet_by_id(PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ENEMY].planet_id.values)
            if (self.get_dist(my_planet,enemy_planet) <= 1.5):
                print("We have used kamikaza")
                return Order(my_planet,enemy_planet,KAMIKAZE_FIRST_ATTACK * my_planet.num_ships)

        planets_in_danger = {}
        planets_not_in_danger = {}
        # # Calculate Fleets
        enemy_fleets_list = self.get_enemy_fleets(game)
        my_fleets_list = self.get_my_fleets(game)

        # Only address enemy fleets position if they exist
        if(len(enemy_fleets_list) > 0):
            for planet in my_planets:
                sum_attacks = sum([x.num_ships for x in filter(lambda x: x.destination_planet_id == planet.planet_id, enemy_fleets_list)])
                if (sum_attacks > planet.num_ships):
                    planets_in_danger[planet] = sum_attacks \
                                                # - planet.growth_rate
                else:
                    planets_not_in_danger[planet] = sum_attacks \
                                                    # TODO - consider looking at planet growth rate
                                                    # - planet.growth_rate

            for fleet in my_fleets_list:
                sum_counter_fleets = sum([x.num_ships for x in filter(lambda x: x.destination_planet_id == fleet.destination_planet_id, enemy_fleets_list)])
                fleet.num_ships -= sum_counter_fleets


        reinforcment_dict = {}

        for planet_to_save in planets_in_danger.keys():
            safe_planets = list(planets_not_in_danger.keys())
            safe_planets.sort(key = lambda Planet: self.get_dist(planet_to_save,Planet))
            reinforcment_needed = max(planet_to_save.num_ships - planets_in_danger[planet_to_save],0)

            for i in range(len(safe_planets)):
                Planet_of_reinforcment = safe_planets[i]
                if ((Planet_of_reinforcment.num_ships - planets_in_danger[planet_to_save]) > reinforcment_needed):
                    num_ships_on_the_way = int(self.calc_num_ships_on_the_way(planet_to_save, game))
                    score = self.get_planet_score(Planet_of_reinforcment, planet_to_save, num_ships_on_the_way)
                    scores.append([Planet_of_reinforcment,planet_to_save,score])
                    reinforcment_dict[(Planet_of_reinforcment,planet_to_save)] = reinforcment_needed


            my_planets.sort(key=lambda planet: planet.num_ships, reverse=True)
            # print(my_planets)



        for my_planet in  my_planets:
            for dest_planet in enemy_and_natural_planets:
                num_ships_on_the_way = int(self.calc_num_ships_on_the_way(dest_planet,game))
                score = self.get_planet_score(my_planet,dest_planet,num_ships_on_the_way)
                scores.append([my_planet,dest_planet,score])

        # print("orders are: ")

        while len(scores) > 0:
            best_move = max(scores, key=lambda move: move[2])
            try:
                ships_to_send = (reinforcment_dict[(best_move[0],best_move[1])])
            except:
                ships_to_send = self.ships_to_send_in_a_fleet(best_move[0], best_move[1],game)


            if (ships_to_send != None) and (ships_to_send > 0):
                # print("send {} ships from {} to {}".format(ships_to_send,best_move[0].planet_id,best_move[1].planet_id))
                orders.append(Order(
                            best_move[0],
                            best_move[1],
                            ships_to_send))
                best_move[0].num_ships -= ships_to_send
                temp_scores = []
                scores.remove(best_move)
                for score in scores:
                    if  (score[1] == best_move[1]):
                        score[2] = score[2]/10
                    temp_scores.append(score)
                scores = temp_scores
            else:
                scores.remove(best_move)

        return orders


class KongFuSyrianPandasTest(KongFuSyrianPandas):

    NAME = "KongFuSyrianPandasTest"
    IS_FIRST_TURN = True
    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """

        # Get atributes
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        enemy_and_natural_planets = game.get_planets_by_owner(owner=PlanetWars.ENEMY) + game.get_planets_by_owner(
            owner=PlanetWars.NEUTRAL)
        if len(my_planets) == 0:
            return []
        my_planets.sort(key=lambda planet: planet.num_ships, reverse=True)
        my_strongest_planet = max(my_planets, key=lambda planet: planet.num_ships)
        scores = []
        fleetsDataFrame = game.get_fleets_data_frame()
        PlanetDataFrame = game.get_planets_data_frame()
        my_planets_df = PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ME]
        my_total_num_of_ships = my_planets_df['num_ships'].sum()
        if (len(self.get_enemy_planets(game)) > 0):
            enemy_strongest_planet = max(self.get_enemy_planets(game), key=lambda planet: planet.num_ships)

            if my_total_num_of_ships > 0.5 * enemy_strongest_planet.num_ships:
                # print("Mother Russia Mode!")
                ships_sent = 0
                for i in range(len(my_planets)):

                    Order(my_planets[i], enemy_strongest_planet, my_planets[i].num_ships * 0.8)
                    my_last_fleet_size = my_planets[i].num_ships * 0.8
                    ships_sent += my_last_fleet_size
                    ships_to_send = self.ships_to_send_in_a_fleet(my_planets[i], enemy_strongest_planet, game)
                    if (ships_to_send != None and ships_sent > self.ships_to_send_in_a_fleet(my_planets[i],
                                                                                             enemy_strongest_planet,
                                                                                             game)):
                        break
                    my_planets[i].num_ships -= my_last_fleet_size

        if self.IS_FIRST_TURN:
            self.IS_FIRST_TURN = False
            my_planet = game.get_planet_by_id(
                PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ME].planet_id.values)
            enemy_planet = game.get_planet_by_id(
                PlanetDataFrame.loc[PlanetDataFrame.owner == PlanetWars.ENEMY].planet_id.values)
            if (self.get_dist(my_planet, enemy_planet) <= 1.5):
                print("We have used kamikaza")
                return Order(my_planet, enemy_planet, KAMIKAZE_FIRST_ATTACK * my_planet.num_ships)

        for my_planet in my_planets:
            for dest_planet in enemy_and_natural_planets:
                score = self.get_planet_score(my_planet, dest_planet,int(self.calc_num_ships_on_the_way(dest_planet,game)))
                scores.append([my_planet, dest_planet, score])
        # print("orders are: ")
        orders = []
        while len(scores) > 0:
            best_move = max(scores, key=lambda move: move[2])

            ships_to_send = self.ships_to_send_in_a_fleet(best_move[0], best_move[1], game)

            if ships_to_send != None:
                orders.append(Order(
                    best_move[0],
                    best_move[1],
                    ships_to_send))
                best_move[0].num_ships -= ships_to_send
            scores.remove(best_move)
        # if(len(orders) == 0):
        #     print("No orders sent")
        # print(len(orders))
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
    run_and_view_battle(KongFuSyrianPandas(), PrincessesBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = KongFuSyrianPandas()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            EnderBot(), rocket_league_bot(), UnderTheHoodBot(),
            BestBotInGalaxy(),PrincessesBot()
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
    # view_bots_battle()
