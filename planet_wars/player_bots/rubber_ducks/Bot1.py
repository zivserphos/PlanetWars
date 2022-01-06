import random
from typing import Iterable, List

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd


class Bot1(Player):
    NAME = "Rubber_Ducks"

    def help_planets_need_help(self, game: PlanetWars) -> Iterable[Order]:
        orders = []

        planets_need_help = []

        for planet in game.get_planets_by_owner(PlanetWars.ME):
            # already sent help
            for fleet in game.get_fleets_by_owner(PlanetWars.ME):
                if fleet.destination_planet_id == planet.planet_id:
                    continue

            attack_size = 0
            turns_to_first_attack = 10000
            for fleet in game.get_fleets_by_owner(PlanetWars.ENEMY):
                if fleet.destination_planet_id == planet.planet_id:
                    attack_size += fleet.num_ships
                    turns_to_first_attack = min(turns_to_first_attack, fleet.turns_remaining)

            if attack_size == 0:
                continue

            planet_size_at_first_attack = turns_to_first_attack * planet.growth_rate + planet.num_ships
            planet_need = attack_size - planet_size_at_first_attack

            if planet_need <= 0:
                continue

            planets_need_help.append((planet, planet_need, turns_to_first_attack))

        for need_help, planet_need, turns_to_first_attack in planets_need_help:
            helpers = []
            size_of_help = 0

            for help_planet in game.get_planets_by_owner(PlanetWars.ME):
                if help_planet in planets_need_help:
                    continue
                if Planet.distance_between_planets(help_planet, need_help) >= turns_to_first_attack:
                    continue

                percent = 0.65
                helpers.append((help_planet, min(int(percent * help_planet.num_ships), planet_need)))
                size_of_help += min(int(percent * help_planet.num_ships), planet_need)
                if size_of_help > planet_need * 1.25:
                    continue


            if size_of_help >= planet_need:
                for help_planet, amount in helpers:
                    orders.append(Order(help_planet, need_help, amount))

        return orders


    def elusive(self, game:PlanetWars):
        orders = []
        for my_planet in game.get_planets_by_owner(PlanetWars.ME):
            is_attacked = False
            attack_force = 0
            for attacking_fleet in game.get_fleets_by_owner(PlanetWars.ENEMY):
                if attacking_fleet.destination_planet_id == my_planet.planet_id and attacking_fleet.turns_remaining <= 1:
                    is_attacked = True
                    attack_force += attacking_fleet.num_ships

            if not is_attacked or attack_force <= my_planet.num_ships + my_planet.growth_rate:
                return []

            for incoming_help in game.get_fleets_by_owner(game.ME):
                if incoming_help.destination_planet_id == my_planet.planet_id:
                    return []

            for run_to in game.get_planets_by_owner(PlanetWars.ME):
                if my_planet == run_to:
                    continue
                else:
                    orders.append(Order(my_planet, run_to, my_planet.num_ships))
        return orders

    def go_to_closest(self, game: PlanetWars, defensive_planets) ->Iterable[Order]:

        minimum_in_planet = 20
        planets_i_sent_to = [f.destination_planet_id for f in game.get_fleets_by_owner(owner=PlanetWars.ME)]
        planets = game.get_planets_by_owner(owner=PlanetWars.NEUTRAL) + game.get_planets_by_owner(
            owner=PlanetWars.ENEMY)
        planets = [p for p in planets if p.planet_id not in planets_i_sent_to]

        my_planets = [p for p in game.get_planets_by_owner(owner=PlanetWars.ME) if p.num_ships > minimum_in_planet and p.planet_id not in defensive_planets]

        orders = []
        for mp in my_planets:
            to_delete = set()
            free_ships = mp.num_ships - minimum_in_planet
            planets.sort(key=lambda p: p.num_ships * (5 - Planet.distance_between_planets(mp, p)), reverse=True)
            for p in planets:
                neutral = p.owner == PlanetWars.NEUTRAL
                threshold = p.num_ships if neutral else p.num_ships + (Planet.distance_between_planets(mp, p) * p.growth_rate)
                if threshold < free_ships:
                    free_ships -= threshold + 1
                    orders.append(Order(
                        mp,
                        p,
                        threshold + 1)
                    )
                    planets_i_sent_to.append(p.planet_id)
                    to_delete.add(p)
            planets = list(set(planets) - to_delete)
        return orders

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        orders = []
        orders += self.help_planets_need_help(game)

        elusive_orders = self.elusive(game)
        defensive_planets = [order.destination_planet_id for order in orders] + [order.source_planet_id for order in orders] + [order.source_planet_id for order in elusive_orders]
        orders += elusive_orders
        orders += self.go_to_closest(game, defensive_planets)

        return orders
