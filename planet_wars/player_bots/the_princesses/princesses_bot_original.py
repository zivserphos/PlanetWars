import random
from typing import Iterable, List
from math import ceil, sqrt

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


class PrincessesBot(Player):
    """
    Example of very simple bot - it send flee from its strongest planet to the weakest enemy/neutral planet
    """

    # def get_planets_to_attack(self, game: PlanetWars) -> List[Planet]:
    #     """
    #     :param game: PlanetWars object representing the map
    #     :return: The planets we need to attack
    #     """
    #     return [p for p in game.planets if p.owner != PlanetWars.ME]

    def distance_between_planets(self, source_planet: Planet, destination_planet: Planet) -> int:
        """
        Returns the distance between the two given planets. Fleet from source_planet will reach destination_planet
        after 'distance' turns. (Fleet speed is 1 distance per turn)
        """
        dx = source_planet.x - destination_planet.x
        dy = source_planet.y - destination_planet.y
        return int(ceil(sqrt(dx * dx + dy * dy)))

    def closest_enemy_dist(self, game: PlanetWars, neutral_planet: Planet):
        if len(game.get_planets_by_owner(PlanetWars.ENEMY)) == 0 :
            return -1
        return min([self.distance_between_planets(neutral_planet, enemy_planet) for enemy_planet in game.get_planets_by_owner(PlanetWars.ENEMY)])


    def planet_ships_when_arrive(self, game: PlanetWars, source_planet: Planet, dest_planet: Planet, is_enemy = True):
        dist = self.distance_between_planets(source_planet, dest_planet)
        rate = dest_planet.growth_rate
        num_ships_cur = dest_planet.num_ships
        enemy_fleets = [fleet for fleet in game.get_fleets_by_owner(PlanetWars.ENEMY) if fleet.destination_planet_id == dest_planet.planet_id and fleet.turns_remaining <= dist]
        num_ships_arriving = sum([fleet.num_ships for fleet in enemy_fleets])
        total_num_ships = num_ships_cur + num_ships_arriving
        #if not(is_enemy):
            #print("ships cur: ",num_ships_cur, "\nships arriving: " , num_ships_arriving)
        if is_enemy:
            total_num_ships += rate*dist
        return total_num_ships

    def ships_matrix(self, game: PlanetWars):
        my_planets = game.get_planets_by_owner(PlanetWars.ME)
        enemy_planets = game.get_planets_by_owner(PlanetWars.ENEMY)
        neutral_planets = game.get_planets_by_owner(PlanetWars.NEUTRAL)
        min_ships_to_enemy_planets = pd.DataFrame(0, columns = enemy_planets, index = my_planets)
        min_ships_to_neutral_planets = pd.DataFrame(0, columns=neutral_planets, index=my_planets)
        for my_planet in my_planets:
            for enemy_planet in enemy_planets:
                min_ships_to_enemy_planets.loc[my_planet, enemy_planet] = self.planet_ships_when_arrive(game, my_planet, enemy_planet) +1
            for neutral_planet in neutral_planets:
                min_ships_to_neutral_planets.loc[my_planet, neutral_planet] = self.planet_ships_when_arrive(game, my_planet, neutral_planet, is_enemy=False) + 1
        return min_ships_to_enemy_planets, min_ships_to_neutral_planets

    def get_close_planets(self,game: PlanetWars, source_planet: Planet, min_ships_to_enemy_planets, min_ships_to_neutral_planets):
        close=game.get_planets_by_owner(PlanetWars.ENEMY)
        close = [planet for planet in close if min_ships_to_enemy_planets.loc[source_planet, planet]< source_planet.num_ships]
        for neutral_planet in game.get_planets_by_owner(PlanetWars.NEUTRAL):
            dist = self.distance_between_planets(source_planet, neutral_planet)
            enemy_dist = self.closest_enemy_dist(game, neutral_planet)
            if ((dist < enemy_dist) or (enemy_dist == -1)) and (min_ships_to_neutral_planets.loc[source_planet, neutral_planet]< source_planet.num_ships):
                close.append(neutral_planet)
        return close

    def best_close_planet(self, close_planets: List[Planet]):
        if len(close_planets)==0:
            return
        return max(close_planets, key = lambda planet : planet.growth_rate)


    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        """
        See player.play_turn documentation.
        :param game: PlanetWars object representing the map - use it to fetch all the planets and flees in the map.
        :return: List of orders to execute, each order sends ship from a planet I own to other planet.
        """
        orders = []
        min_ships_to_enemy_planets, min_ships_to_neutral_planets = self.ships_matrix(game)
        #print(min_ships_to_neutral_planets)
        for source_planet in game.get_planets_by_owner(owner=PlanetWars.ME):
            close_planets = self.get_close_planets(game, source_planet, min_ships_to_enemy_planets, min_ships_to_neutral_planets)
            #print(close_planets)
            dest_plent = self.best_close_planet(close_planets)
            if dest_plent!=None:
                if dest_plent.owner == PlanetWars.ENEMY:
                    ships_to_send = min_ships_to_enemy_planets.loc[source_planet, dest_plent]
                else:
                    ships_to_send = min_ships_to_neutral_planets.loc[source_planet, dest_plent]
                orders.append(Order(source_planet, dest_plent, ships_to_send))
        return orders
