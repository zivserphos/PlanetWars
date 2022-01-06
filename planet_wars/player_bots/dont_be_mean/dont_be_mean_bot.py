import random
from typing import Iterable, List

from courses.planet_wars.planet_wars import Player, PlanetWars, Order, Planet
from courses.planet_wars.tournament import get_map_by_id, run_and_view_battle, TestBot

import pandas as pd
import math
import numpy as np

class DontBeMean(Player):

    def distance(self, planet1, planet2):
        dx = (planet1.x - planet2.x)**2
        dy = (planet1.y - planet2.y) ** 2
        return math.ceil(math.sqrt(dx+dy))


    def closest_planets(self,n, planet1,dists):
        id = planet1.planet_id
        p_dists = dists[id]
        res = p_dists.sort_values().index
        return res[1:min(n+1,len(res))]


    def center_of_the_force(self, game):
        planet_df = game.get_planets_data_frame()
        my_planets = planet_df.loc[planet_df["owner"] == 1]
        x = my_planets["x"].mean()
        y = my_planets["y"].mean()

        #create center planet
        center = Planet(my_planets.shape[0], 1, -1, -1, x, y)
        game.planets.append(center)
        planets = game.get_planets_data_frame()
        my_planets = planets.loc[planets["owner"] == 1]

        #find the closest planet
        dists = self.get_dist_mat(my_planets)
        if len(dists.iloc[-1, :-1]):
            closest_planet_id = dists.iloc[-1, :-1].idxmin()
        else:
            closest_planet_id = 1
        game.planets.pop()

        return game.get_planet_by_id(closest_planet_id)

    def play_turn(self, game: PlanetWars) -> Iterable[Order]:
        planet_df = game.get_planets_data_frame()
        fleet_df = game.get_fleets_data_frame()
        orders = []
        #get the center planet
        center_planet = self.center_of_the_force(game)

        #define my planets
        my_planets = game.get_planets_by_owner(owner=PlanetWars.ME)
        my_planets_ids = [p.planet_id for p in my_planets]

        #get matrix distances
        dists = self.get_dist_mat(planet_df)

        #defend
        if len(fleet_df):
            #fleet_df['is_attacking_me'] = fleet_df["destination_planet_id"].isin(my_planets_ids)
            #new_fleets_attacking_me = self.get_new_fleets_attacking_me(fleet_df)
            fleet_df['is_attacking_me'] = fleet_df["destination_planet_id"].isin(my_planets_ids)
            new_fleets_attacking_me = self.get_new_fleets_attacking_me(fleet_df)
            orders+= self.defense(new_fleets_attacking_me, dists, my_planets_ids, planet_df, game)

        #attack
        orders += self.attack_enemy(planet_df, center_planet, game, 3, 6)
        orders += self.attack_neutral(planet_df, center_planet, game, 2, 6)
        return orders

    def attack_enemy(self, planet_df, center,game, num_attack, num_attackers):
        orders=[]
        df_enemey = planet_df.loc[(planet_df.owner==2) | (planet_df.planet_id==center.planet_id)]
        dists = self.get_dist_mat(df_enemey)
        next_attack_list = self.closest_planets(num_attack, center, dists)
        for next_attack in next_attack_list:
        #next_attack = max(next_attack_list, key=lambda p: planet_df.iloc[p].growth_rate)
            df_mine = planet_df.loc[(planet_df.owner==1) | (planet_df.planet_id==next_attack)]
            dists = self.get_dist_mat(df_mine)
            next_attack_planet = game.get_planet_by_id(next_attack)
            attackers = list(self.closest_planets(num_attackers, next_attack_planet, dists))
            attackers.sort(key=lambda p: game.get_planet_by_id(p).num_ships, reverse=True)
            remaining_ships = planet_df.loc[planet_df.planet_id==next_attack].num_ships.iloc[0]
            if remaining_ships > 0:
                for p in attackers:
                    ships = min(remaining_ships, planet_df.num_ships.iloc[p] - 1)
                    orders.append(Order(p, next_attack, ships))
                    remaining_ships -= ships
                    planet_df.loc[planet_df.planet_id==p,'num_ships'] -= ships
        return orders

    def attack_neutral(self, planet_df, center,game, num_attack, num_attackers):
        orders=[]
        df_enemey = planet_df.loc[(planet_df.owner==0) | (planet_df.planet_id==center.planet_id)]
        dists = self.get_dist_mat(df_enemey)
        next_attack_list = self.closest_planets(num_attack, center, dists)
        for next_attack in next_attack_list:
        #next_attack = max(next_attack_list, key=lambda p: planet_df.iloc[p].growth_rate)
            df_mine = planet_df.loc[(planet_df.owner==1) | (planet_df.planet_id==next_attack)]
            dists = self.get_dist_mat(df_mine)
            next_attack_planet = game.get_planet_by_id(next_attack)
            attackers = list(self.closest_planets(num_attackers, next_attack_planet, dists))
            attackers.sort(key=lambda p: game.get_planet_by_id(p).num_ships, reverse=True)
            remaining_ships = planet_df.loc[planet_df.planet_id==next_attack].num_ships.iloc[0]
            if remaining_ships > 0:
                for p in attackers:
                    ships = min(remaining_ships, planet_df.num_ships.iloc[p] - 1)
                    orders.append(Order(p, next_attack, ships))
                    remaining_ships -= ships
                    planet_df.loc[planet_df.planet_id==p,'num_ships'] -= ships
        return orders

    def get_dist_mat(self, planet_df):
        x_diff = planet_df.x.to_numpy() - np.expand_dims(planet_df.x.to_numpy(), axis=-1)
        y_diff = planet_df.y.to_numpy() - np.expand_dims(planet_df.y.to_numpy(), axis=-1)
        df = np.ceil(np.sqrt(x_diff * x_diff + y_diff * y_diff))
        df = pd.DataFrame(df)
        df.columns = planet_df.index
        df.index = planet_df.index
        return df

    def get_new_fleets_attacking_me(self, fleet_df):
        return fleet_df.loc[
            (fleet_df.owner == 2) &
            (fleet_df.is_attacking_me == True) &
            (fleet_df.total_trip_length == fleet_df.turns_remaining + 1)]

    def defense(self, new_fleets_attacking_me, dists, my_planets_ids, planet_df, game):
        orders = []
        attacked_planets_id = pd.unique(new_fleets_attacking_me.destination_planet_id)
        not_attacked = list(set(my_planets_ids) - set(attacked_planets_id))
        for i in range(new_fleets_attacking_me.shape[0]):
            fleet = new_fleets_attacking_me.iloc[i]
            attacked = fleet['destination_planet_id']
            attacked_dists=dists[attacked]
            close_enough = attacked_dists[attacked_dists < fleet.turns_remaining].index
            close_enough_mine = list(set(not_attacked) & set(close_enough))
            close_enough_mine.sort(key=lambda p: game.get_planet_by_id(p).num_ships, reverse=True)
            remaining_ships = fleet.num_ships - game.get_planet_by_id(attacked).num_ships
            if remaining_ships > 0:
                for p in close_enough_mine:
                    ships = min(remaining_ships, planet_df.num_ships.iloc[p] - 1)
                    orders.append(Order(p, attacked, ships))
                    remaining_ships -= ships
                    planet_df.loc[planet_df.planet_id==p,'num_ships'] -= ships
        return orders