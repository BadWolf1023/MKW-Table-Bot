import TableBot
import ScoreKeeper
from typing import Union, Dict


get_table_bots = None

def get_table_bot(table_id: Union[int, str]) -> Union[TableBot.ChannelBot, bool]:
    table_bots:Dict[int, Dict[int, TableBot.ChannelBot]] = get_table_bots()
    if table_bots is None:
        return None
    for channel_bots in table_bots.values():
        for table_bot in channel_bots.values():
            if table_bot.is_table_loaded() and table_bot.get_room().get_event_id() == table_id:
                return table_bot
    return None

def get_team_score_data(table_bot: TableBot.ChannelBot, sort_teams = True):
    _, table_sorted_data = ScoreKeeper.get_war_table_DCS(table_bot, sort_teams=sort_teams, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, missingRacePts=table_bot.dc_points, server_id=table_bot.server_id, discord_escape=False)
    return table_sorted_data


def initialize(get_table_bots_func):
    global get_table_bots
    get_table_bots = get_table_bots_func
