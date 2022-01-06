from planet_wars.player_bots.aka_galf.baseline_bot import galfFinals
from planet_wars.player_bots.data_campers.best_bot_in_galaxy import BestBotInGalaxy
from planet_wars.player_bots.dont_be_mean.dont_be_mean_bot import DontBeMean
from planet_wars.player_bots.ender.EnderBot import EnderBot
from planet_wars.player_bots.hozi.baseline_bot import HoziBot
from planet_wars.player_bots.kong_fu_pandas.baseline_bot import KongFuSyrianPandas
from planet_wars.player_bots.rocket_league.baseline_bot import rocket_league_bot
from planet_wars.player_bots.rubber_ducks.Bot1 import Bot1
from planet_wars.player_bots.space_pirates.baseline_bot import Firstroundstrategy
from planet_wars.player_bots.the_princesses.princesses_bot import PrincessesBot
from planet_wars.player_bots.under_the_hood.baseline_bot import UnderTheHoodBot
from planet_wars.tournament import Tournament
import warnings
import pandas as pd
from planet_wars.player_bots.fun_with_flags.baseline_bot import NerdBot
from planet_wars.player_bots.spaceNinjas.baseline_bot import spaceNinjas
from planet_wars.player_bots.arrakis.baseline_bot import BestBot
from planet_wars.player_bots.the_powerpuff_girls.baseline_bot import PowerPuff

# Insert Your bot object here, as BotObject(). Don't forget to set BotObject.NAME to your team name
PLAYER_BOTS = [
    Firstroundstrategy(), NerdBot(), Bot1(), EnderBot(), UnderTheHoodBot(),
    KongFuSyrianPandas(), BestBotInGalaxy(), spaceNinjas(), BestBot(), PowerPuff(), PrincessesBot(), galfFinals(),
    DontBeMean(), HoziBot()
]

# rocket_league_bot(),  too slow sorry

ROUND1_MAP = """P 13 13 0 36 4
P 3.7820839879289565 12.57131994383198 1 100 5
P 14.566680518832031 22.09391303829458 2 100 5
P 6.714699700365638 20.23041089459612 0 81 4
P 5.471494067341194 21.660555378506636 0 35 1
P 24.735601688020807 8.489327141914504 0 8 3
P 16.0229442973115 0.7962168001927417 0 8 3
P 6.436172310561731 2.873730227972443 0 73 5
P 23.861041702180607 18.259557640715546 0 73 5
P 23.01027681820345 8.585404917274749 0 95 2
P 16.14122363806936 2.5201619393657797 0 95 2
P 20.862860436292834 11.056744855024498 0 6 2
P 13.954777609541708 4.957039443375921 0 6 2
P 8.420223458807161 8.169133999180557 0 35 5
P 18.360731572897127 16.94641311680333 0 35 5
P 21.431433058369393 14.134653557437993 0 50 2
P 10.830154961442174 4.773927144632324 0 50 2"""

ROUND2_MAP = """P 15 15 0 43 1
P 11.114072097364033 22.64553445227421 1 100 5
P 18.885927902635963 7.35446554772579 2 100 5
P 6.930398156851366 11.06419220434527 0 73 1
P 23.069601843148636 18.935807795654732 0 73 1
P 8.464341714844089 11.812346466598989 0 43 1
P 21.53565828515591 18.18765353340101 0 43 1
P 17.007871967271754 15.321010314082814 0 36 5
P 12.992128032728246 14.678989685917188 0 36 5
P 25.438481257658367 20.22656069592056 0 59 3
P 4.561518742341633 9.77343930407944 0 59 3
P 11.090851907463446 12.780335591321368 0 65 4
P 18.909148092536558 17.21966440867863 0 65 4
P 12.907703910648491 7.052178765948909 0 75 1
P 17.09229608935151 22.94782123405109 0 75 1
P 11.780774009384144 27.339326702495185 0 20 4
P 18.21922599061583 2.6606732975048075 0 20 4"""

ROUND3_MAP = """P 15 15 0 28 5
P 5.775092167744024 9.945603402585451 1 100 5
P 22.37817840199747 7.502778318212037 2 100 5
P 14.290337764612119 10.51936898641209 0 24 3
P 22.46690378782811 25.34395609840424 0 28 4
P 10.828859132954104 27.056270725628874 0 28 4
P 29.719061395649952 12.827948188216832 0 63 2
P 0.27908809793287226 17.159474522554415 0 63 2
P 10.47859056018009 1.5413863220861614 0 60 3
P 15.453365415599462 0.8094438004086548 0 60 3
P 7.574366009785828 18.33206150202184 0 74 3
P 23.070675767779797 16.052077307640506 0 74 3
P 6.415718558715152 16.065026550738125 0 88 5
P 23.52725636556483 13.547392588171654 0 88 5
P 16.824572305027687 20.46843969316639 0 90 1
P 14.827804297343912 20.762225734389318 0 90 1
P 26.458323098955336 10.225402744498432 0 85 5
P 2.65204212371734 13.728039514039232 0 85 5
P 11.902922340652648 18.59937175982182 0 52 1
P 19.00254557026323 17.554798632259995 0 52 1
P 13.36863369359301 16.594772135863842 0 90 3
P 17.021569641837495 16.057312808117224 0 90 3
P 28.612742363253513 15.11549391205284 0 58 5
P 1.9973978593244741 19.03143039916831 0 58 5
P 4.780026960670561 23.75546342198531 0 34 3
P 27.308681116906314 20.44080488720715 0 34 3
P 4.9777283436208375 21.254835473405894 0 37 5
P 26.399110666795405 18.10309071085411 0 37 5
P 18.571498861103997 7.520667608856594 0 80 3
P 9.425606478373874 8.866309919948126 0 80 3"""

if __name__ == '__main__':
    # Display options
    warnings.simplefilter(action='ignore')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('expand_frame_repr', False)

    tournament = Tournament(PLAYER_BOTS, [ROUND3_MAP])
    battle_results = tournament.run_tournament()
    player_scores_df = tournament.get_player_scores_data_frame()
    battle_results_df = tournament.get_battle_results_data_frame()
    print(player_scores_df)
    print(battle_results_df)

    player_scores_df.to_parquet("./player_scores_df.parquet")
    battle_results_df.to_parquet("./battle_results_df.parquet")
    player_scores_df.to_csv("./player_scores_df.csv")
    battle_results_df.to_csv("./battle_results_df.csv")
    # TODO commit the saved df so all players can see the battle results