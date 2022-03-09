import TableBot
import ScoreKeeper


table_bots = None

def get_table_bot(table_id :int) -> bool:
    if table_bots is None:
        return None
    for server_id, channel_id in table_bots.items():
        if table_bots[server_id][channel_id].is_table_loaded() and table_bots[server_id][channel_id].get_room().get_event_id() == table_id:
            return table_bots[server_id][channel_id]
    return None

def get_team_score_data(table_bot: TableBot.ChannelBot):
    _, table_sorted_data = ScoreKeeper.get_war_table_DCS(table_bot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, missingRacePts=table_bot.dc_points, server_id=table_bot.server_id, discord_escape=False)
    return table_sorted_data


def initialize(table_bots_):
    global table_bots
    table_bots = table_bots_
