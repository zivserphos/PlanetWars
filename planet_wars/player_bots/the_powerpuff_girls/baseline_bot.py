import random
from typing import Iterable, List

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

class PowerPuff(Player):
    def __init__(self):
        self.turns_until_end = 200

    def whos_planet(self, planet, enemy_fleets, my_fleets):
        """
        :param planet: a planet object
        :param enemy_fleets: a list of enemy fleet objects
        :param my_fleets:  a list of my fleet objects
        :return:
        """
        # Retreive only fleets flying towards relevant planet
        enemy_fleets = [fleet for fleet in enemy_fleets if fleet.destination_planet_id == planet.planet_id]
        enemy_fleets = sorted(enemy_fleets, key=lambda f: f.turns_remaining)

        my_fleets = [fleet for fleet in my_fleets if fleet.destination_planet_id == planet.planet_id]
        my_fleets = sorted(my_fleets, key=lambda f: f.turns_remaining)

        all_fleets = sorted(enemy_fleets + my_fleets, key=lambda f: f.turns_remaining)

        cur_ships = planet.num_ships
        cur_ownership = planet.owner

        # Edge case
        if len(all_fleets) == 0:
            return 0, cur_ownership
        if len(all_fleets) == 1:
            cur_ships = cur_ships - all_fleets[0].num_ships
            if cur_ships < 0:
                cur_ownership = all_fleets[0].owner
            return all_fleets[0].num_ships, cur_ownership

        cur_turn = 0
        idx = 0
        """
        Dealing with neutral planets
        """
        if cur_ownership == PlanetWars.NEUTRAL:  # neutral
            for idx, f in enumerate(all_fleets):
                cur_turn = f.turns_remaining
                cur_ships -= f.num_ships
                if cur_ships < 0:
                    cur_ownership = f.owner
                    cur_ships = -cur_ships
                    # Reached the end of all fleets
                    if idx == len(all_fleets) - 1:
                        return planet.num_ships - cur_ships, cur_ownership
                    break

        if idx == 0:
            if all_fleets[idx].owner == cur_ownership:
                cur_ships += all_fleets[0].num_ships
            else:
                cur_ships -= all_fleets[0].num_ships
            if cur_ships < 0:
                cur_ownership = all_fleets[0].owner

        # Ownership is of enemy or myself
        while idx + 1 < len(all_fleets):
            # Planet switched from neutral to enemy or was enemy from the beggining
            if cur_ownership == PlanetWars.ENEMY:
                idx += 1
                f = all_fleets[idx]
                if f.owner == PlanetWars.ENEMY:  # Reinforcing
                    cur_ships = cur_ships + f.num_ships + (
                                planet.growth_rate * (f.turns_remaining - all_fleets[idx - 1].turns_remaining))
                else:  # Im attacking
                    cur_ships = cur_ships - f.num_ships + (
                                planet.growth_rate * (f.turns_remaining - all_fleets[idx - 1].turns_remaining))
                    if cur_ships < 0:
                        cur_ownership == PlanetWars.ME
                        cur_ships = -cur_ships
            else:
                idx += 1
                f = all_fleets[idx]
                if f.owner == PlanetWars.ME:  # Reinforcing
                    cur_ships = cur_ships + f.num_ships + (
                                planet.growth_rate * (f.turns_remaining - all_fleets[idx - 1].turns_remaining))
                else:  # Im attacking
                    cur_ships = cur_ships - f.num_ships + (
                                planet.growth_rate * (f.turns_remaining - all_fleets[idx - 1].turns_remaining))
                    if cur_ships < 0:
                        cur_ownership == PlanetWars.ENEMY
                        cur_ships = -cur_ships
        return planet.num_ships - cur_ships, cur_ownership

    def get_planet_score(self, game: PlanetWars, planet, dis):
        enemy_fleets = game.get_fleets_by_owner(owner=PlanetWars.ENEMY)
        my_fleets = game.get_fleets_by_owner(owner=PlanetWars.ME)
        planet_after_fleets = self.whos_planet(planet, enemy_fleets, my_fleets)
        if planet_after_fleets[1] == PlanetWars.ME:
            planet_after_fleets_score = -planet_after_fleets[0]
        else:
            planet_after_fleets_score = planet_after_fleets[0]

        if planet.owner == PlanetWars.NEUTRAL:
            score = (planet.growth_rate * self.turns_until_end) - planet.num_ships - planet_after_fleets_score
            return score
        elif planet.owner == PlanetWars.ENEMY:
            score = planet.growth_rate * (self.turns_until_end - dis) - planet.num_ships - planet_after_fleets_score
            return score
        score = planet.growth_rate * (self.turns_until_end - dis) - planet.num_ships - planet_after_fleets_score
        return -score

    def get_lst_scores(self, game: PlanetWars):
        dic_scores = {}
        for planet in game.planets:
            score = -float('inf')
            source = None
            for my_planet in game.get_planets_by_owner(owner=PlanetWars.ME):
                dis = Planet.distance_between_planets(planet, my_planet)
                temp_score = self.get_planet_score(game,planet, dis)
                if temp_score > score:
                    score = temp_score
                    source = my_planet
            dic_scores[planet] = [score, source]
        return dic_scores

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        self.turns_until_end -= 1
        score_dict = self.get_lst_scores(game)
        # Dict is empty


        # Sort Dictionary
        #score_dict = dict(sorted(score_dict.items(), key=lambda item: item[0], reverse=True))
        keylist = sorted(score_dict.keys(), key=lambda x: score_dict[x][0], reverse=True)
        score_dict = {k: score_dict[k] for k in keylist}

        order_counter = 0
        order_list = []
        try:
            for dest_planet, tup in score_dict.items():
                owner = self.whos_planet(dest_planet,game.get_fleets_by_owner(PlanetWars.ENEMY),game.get_fleets_by_owner(PlanetWars.ME))[1]
                if owner == PlanetWars.ME:
                    continue
                num_ships = dest_planet.num_ships + 1
                if dest_planet.owner == PlanetWars.ENEMY:
                    num_ships += dest_planet.growth_rate*Planet.distance_between_planets(dest_planet, tup[1])
                if num_ships <= tup[1].num_ships:
                    order_list.append(Order(source_planet=tup[1].planet_id,destination_planet=dest_planet.planet_id, num_ships=tup[1].num_ships))
                    order_counter += 1
        except:
            return []
        return order_list




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
    run_and_view_battle(AttackEnemyWeakestPlanetFromStrongestBot(), PowerPuff(), map_str)


def test_bot():
    """
    Test AttackWeakestPlanetFromStrongestBot against the 2 other bots.
    Print the battle results data frame and the PlayerScore object of the tested bot.
    So is AttackWeakestPlanetFromStrongestBot worse than the 2 other bots? The answer might surprise you.
    """
    maps = [get_random_map(), get_random_map()]
    player_bot_to_test = PowerPuff()
    tester = TestBot(
        player=player_bot_to_test,
        # competitors=PLAYER_BOTS[2:5],
        #     AttackEnemyWeakestPlanetFromStrongestBot(), AttackWeakestPlanetFromStrongestSmarterNumOfShipsBot()
        # ],
        competitors=[],
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
    #tester.view_battle(4)


if __name__ == "__main__":
    test_bot()
    #view_bots_battle()
