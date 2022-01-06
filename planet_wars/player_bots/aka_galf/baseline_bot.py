import random
from typing import Iterable, List

from planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


class FirstBot(Player):

    @staticmethod
    def get_distance_by_DF(planet, planet_id ,game):
        return Planet.distance_between_planets(planet, game.get_planet_by_id(planet_id))

    @staticmethod
    def set_num_ships(planet):
        if planet['owner'] == 2:
            return planet['growth_rate'] * planet['dist'] + planet.num_ships
        else:
            return planet.num_ships

    @staticmethod
    def set_rates(otherPlanetsDF, planet, game):
        growth_weight = 1
        ships_weight = 1
        dist_weight = 10

        planetsDF = otherPlanetsDF.copy()
        # print(planetsDF.apply(lambda x: FirstBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1))
        planetsDF['dist'] = planetsDF.apply(lambda x: FirstBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1)
        planetsDF['reqships'] = planetsDF.apply(lambda x: FirstBot.set_num_ships(x), axis = 1)
        #planetsDF = planetsDF[planetsDF['reqships'] < planet.num_ships]
        planetsDF['rank'] = planetsDF['growth_rate'] * growth_weight - planetsDF['reqships'] * ships_weight - planetsDF['dist'] * dist_weight
        return planetsDF

    @staticmethod
    def set_order_to_kill_only_first(df, source_planet):
        if len(df) == 0:
            return None
        best_option = df.iloc[0]
        return Order(
            source_planet,
            int(best_option['planet_id']),
            source_planet.num_ships // 2
        )

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # self.__count_turn += 1
        # Get and devide DF

        allPlanetsDF = game.get_planets_data_frame()
        allPlanetsDF = allPlanetsDF[allPlanetsDF['growth_rate'] > 0]
        ourPlanetsDF = game.get_planets_by_owner(1)
        # for p in ourPlanetsDF:
        #     print(p.num_ships)

        otherPlanetsDF = allPlanetsDF[allPlanetsDF['owner'] != 1]
        if len(otherPlanetsDF) == 0:
            return []
        orders = []
        # Todo: set rates to DF according to assafs algorithm
        for planet in ourPlanetsDF:
            if planet.num_ships < 30:
                continue
            df = otherPlanetsDF.copy()
            currDF = FirstBot.set_rates(df, planet, game)
            currDF.sort_values(by = 'rank', ascending = False, inplace = True)
            currOrder = FirstBot.set_order_to_kill_only_first(currDF, planet)
            #print(currDF)
            if currOrder != None:
                orders.append(currOrder)

        # maybe later Todo: split our planets to different attacks
        # listOfGroupPlanets = split_planets(ourPlanetsDF)
        # maybe later Todo: attack enemy by groups of our planets

        return orders

class StrongGrowthBot(Player):

    @staticmethod
    def get_distance_by_DF(planet, planet_id, game):
        return Planet.distance_between_planets(planet, game.get_planet_by_id(planet_id))

    @staticmethod
    def set_num_ships(planet):
        if planet['owner'] == 2:
            return planet['growth_rate'] * planet['dist'] + planet.num_ships
        else:
            return planet.num_ships

    @staticmethod
    def set_rates(otherPlanetsDF, planet, game):
        growth_weight = game.turns + 1000 / (game.turns+1)
        ships_weight = 1
        dist_weight = 50

        planetsDF = otherPlanetsDF.copy()
        # print(planetsDF.apply(lambda x: FirstBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1))
        planetsDF['dist'] = planetsDF.apply(lambda x: StrongGrowthBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1)
        planetsDF['reqships'] = planetsDF.apply(lambda x: StrongGrowthBot.set_num_ships(x), axis=1)
        # planetsDF = planetsDF[planetsDF['reqships'] < planet.num_ships]
        planetsDF['rank'] = planetsDF['growth_rate'] * growth_weight - planetsDF['reqships'] * ships_weight - planetsDF[
            'dist'] * dist_weight
        return planetsDF

    @staticmethod
    def set_order_to_kill_only_first(df, source_planet):
        if len(df) == 0 or source_planet.num_ships < 50:
            return None
        best_option = df.iloc[0]
        return Order(
            source_planet,
            int(best_option['planet_id']),
            source_planet.num_ships // 2
        )

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # self.__count_turn += 1
        # Get and devide DF
        allPlanetsDF = game.get_planets_data_frame()
        allPlanetsDF = allPlanetsDF[allPlanetsDF['growth_rate'] > 0]
        ourPlanetsDF = game.get_planets_by_owner(1)
        # for p in ourPlanetsDF:
        #     print(p.num_ships)

        otherPlanetsDF = allPlanetsDF[allPlanetsDF['owner'] != 1]
        if len(otherPlanetsDF) == 0:
            return []
        orders = []
        # Todo: set rates to DF according to assafs algorithm
        for planet in ourPlanetsDF:
            df = otherPlanetsDF.copy()
            currDF = StrongGrowthBot.set_rates(df, planet, game)
            currDF.sort_values(by='rank', ascending=False, inplace=True)
            currOrder = StrongGrowthBot.set_order_to_kill_only_first(currDF, planet)
            # print(currDF)
            if currOrder != None:
                orders.append(currOrder)

        # maybe later Todo: split our planets to different attacks
        # listOfGroupPlanets = split_planets(ourPlanetsDF)
        # maybe later Todo: attack enemy by groups of our planets

        return orders

class SmartSendBot(Player):

    @staticmethod
    def get_distance_by_DF(planet, planet_id, game):
        return Planet.distance_between_planets(planet, game.get_planet_by_id(planet_id))

    @staticmethod
    def set_num_ships(planet):
        if planet['owner'] == 2:
            return planet['growth_rate'] * planet['dist'] + planet.num_ships
        else:
            return planet.num_ships

    @staticmethod
    def set_rates(otherPlanetsDF, planet, game):
        growth_weight = 1
        ships_weight = 1
        dist_weight = 1000000

        planetsDF = otherPlanetsDF.copy()
        # print(planetsDF.apply(lambda x: FirstBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1))
        planetsDF['dist'] = planetsDF.apply(lambda x: SmartSendBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1)
        planetsDF['reqships'] = planetsDF.apply(lambda x: SmartSendBot.set_num_ships(x), axis=1)
        # planetsDF = planetsDF[planetsDF['reqships'] < planet.num_ships]
        planetsDF['rank'] = planetsDF['growth_rate'] * growth_weight - planetsDF['reqships'] * ships_weight - planetsDF[
            'dist'] * dist_weight
        return planetsDF

    @staticmethod
    def set_order_to_kill_only_first(df, source_planet, index, negShips):
        if len(df) == 0 or source_planet.num_ships - negShips < df.iloc[index].reqships + 2:
            return None
        best_option = df.iloc[index]
        return Order(
            source_planet,
            int(best_option['planet_id']),
            best_option.num_ships + 1
        )

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # self.__count_turn += 1
        # Get and devide DF

        allPlanetsDF = game.get_planets_data_frame().copy()
        allPlanetsDF = allPlanetsDF[allPlanetsDF['growth_rate'] > 0]
        ourPlanetsDF = game.get_planets_by_owner(1)
        # for p in ourPlanetsDF:
        #     print(p.num_ships)
        fleets = [fleet.destination_planet_id for fleet in game.get_fleets_by_owner(1)]
        allPlanetsDF['fleets'] = allPlanetsDF.apply(lambda x: x.planet_id in fleets, axis=1)
        otherPlanetsDF = allPlanetsDF[(allPlanetsDF['owner'] != 1) & (allPlanetsDF['fleets'] == False)]
        if len(otherPlanetsDF) == 0:
            return []
        orders = []
        # Todo: set rates to DF according to assafs algorithm

        for planet in ourPlanetsDF:
            negShips = 0
            if planet.num_ships - negShips < 30:
                continue
            counter = 0
            df = otherPlanetsDF.copy()
            while counter < (len(df) // 2):
                currDF = SmartSendBot.set_rates(df, planet, game)
                currDF.sort_values(by='rank', ascending=False, inplace=True)
                currOrder = SmartSendBot.set_order_to_kill_only_first(currDF, planet, counter, negShips)
                counter += 1

            # print(currDF)
                if currOrder != None:
                    orders.append(currOrder)
                    negShips += currOrder.num_ships


        # maybe later Todo: split our planets to different attacks
        # listOfGroupPlanets = split_planets(ourPlanetsDF)
        # maybe later Todo: attack enemy by groups of our planets

        return orders

class galfFinals(Player):

    @staticmethod
    def get_distance_by_DF(planet, planet_id, game):
        return Planet.distance_between_planets(planet, game.get_planet_by_id(planet_id))

    @staticmethod
    def set_num_ships(planet):
        if planet['owner'] == 2:
            return planet['growth_rate'] * planet['dist'] + planet.num_ships
        else:
            return planet.num_ships

    @staticmethod
    def set_rates(otherPlanetsDF, planet, game):
        growth_weight = 1
        ships_weight = 1
        dist_weight = 1000000

        planetsDF = otherPlanetsDF.copy()
        # print(planetsDF.apply(lambda x: FirstBot.get_distance_by_DF(planet, x['planet_id'], game), axis=1))
        planetsDF['dist'] = planetsDF.apply(lambda x: galfFinals.get_distance_by_DF(planet, x['planet_id'], game), axis=1)
        planetsDF['reqships'] = planetsDF.apply(lambda x: SmartSendBot.set_num_ships(x), axis=1)
        # planetsDF = planetsDF[planetsDF['reqships'] < planet.num_ships]
        planetsDF['rank'] = planetsDF['growth_rate'] * growth_weight - planetsDF['reqships'] * ships_weight - planetsDF[
            'dist'] * dist_weight
        return planetsDF

    @staticmethod
    def set_order_to_kill_only_first(df, source_planet, index, negShips):
        if len(df) == 0 or source_planet.num_ships - negShips < df.iloc[index].reqships + 2:
            return None
        best_option = df.iloc[index]
        return Order(
            source_planet,
            int(best_option['planet_id']),
            best_option.num_ships + 1
        )

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        # self.__count_turn += 1
        # Get and devide DF

        allPlanetsDF = game.get_planets_data_frame().copy()
        allPlanetsDF = allPlanetsDF[allPlanetsDF['growth_rate'] > 0]
        ourPlanetsDF = game.get_planets_by_owner(1)
        # for p in ourPlanetsDF:
        #     print(p.num_ships)
        fleets = [fleet.destination_planet_id for fleet in game.get_fleets_by_owner(1)]
        allPlanetsDF['fleets'] = allPlanetsDF.apply(lambda x: x.planet_id in fleets, axis=1)
        otherPlanetsDF = allPlanetsDF[(allPlanetsDF['owner'] != 1) & (allPlanetsDF['fleets'] == False)]
        if len(otherPlanetsDF) == 0:
            return []
        orders = []
        # Todo: set rates to DF according to assafs algorithm

        for planet in ourPlanetsDF:
            negShips = 0
            if planet.num_ships - negShips < 30:
                continue
            counter = 0
            df = otherPlanetsDF.copy()
            while counter < (len(df) // 2):
                currDF = SmartSendBot.set_rates(df, planet, game)
                currDF.sort_values(by='rank', ascending=False, inplace=True)
                currOrder = SmartSendBot.set_order_to_kill_only_first(currDF, planet, counter, negShips)
                counter += 1

            # print(currDF)
                if currOrder != None:
                    orders.append(currOrder)
                    negShips += currOrder.num_ships


        # maybe later Todo: split our planets to different attacks
        # listOfGroupPlanets = split_planets(ourPlanetsDF)
        # maybe later Todo: attack enemy by groups of our planets

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
    # run_and_view_battle(PLAYER_BOTS[3], SmartSendBot(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = AttackWeakestPlanetFromStrongestBot()
    tester = TestBot(
        player=player_bot_to_test,
        competitors=[
            AttackEnemyWeakestPlanetFromStrongestBot(), AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot()
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
    #test_bot()
    view_bots_battle()
