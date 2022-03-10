from bs4 import BeautifulSoup
import codecs
import re
from datetime import timedelta
from typing import List, Union, Tuple
from api import api_common



API_DATA_PATH = "api/"
HTML_DATA_PATH = f"{API_DATA_PATH}html/"
CSS_DATA_PATH = f"{API_DATA_PATH}css/"
TEAM_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}team_score_builder.html"
TEAM_STYLE_FILE = f"{CSS_DATA_PATH}team_score_base.css"
TABLE_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}full_table_builder.html"
QUICK_INFO_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}quick_info.html"

TEAM_STYLES = {"rainbow": f"{CSS_DATA_PATH}team_score_rainbow.css",
               "pastel": f"{CSS_DATA_PATH}team_score_pastel.css",
               "orange": f"{CSS_DATA_PATH}team_score_orange.css",
               "neon": f"{CSS_DATA_PATH}team_score_neon.css",
               "verticalblue": f"{CSS_DATA_PATH}team_score_vertical_blue.css"
}


def restructure_if_needed(team_data):
    '''If it's an FFA, the data is restructured so that the team names are the player names'''
    
    if len(team_data) == 1 and team_data[0][0] == "No Tag":
        new_team_data = []
        for fc, player_data in team_data[0][1]:
            new_team_data.append((player_data[3], [(fc, player_data)]))
        return new_team_data
    else:
        return team_data

def build_full_table_html(team_data: List[Tuple[str, List]], style=None):
    '''team_data contains the scores for teams in the following format:
    [
        (team_1_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ]),
        (team_2_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ]),
        (team_3_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ])
    ]

    team_data is what is returned by ScoreKeeper.get_war_table_DCS
    player_data is a list that contains various information, such as the player's name, player score each GP, and player score each race    
    '''
    team_data = restructure_if_needed(team_data)
    
    # Read in base css styling and read in custom styling if it was specified
    styling = ""
    with codecs.open(TEAM_STYLE_FILE, "r", "utf-8") as fp:
        styling = fp.read() + "\n\n"
    if style in TEAM_STYLES:
        with codecs.open(TEAM_STYLES[style], "r", "utf-8") as fp:
            styling += fp.read() + "\n\n"

    # Build the team HTML
    soup = None
    with codecs.open(TEAM_HTML_BUILDER_FILE, "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        for id_index, (team_tag, players) in enumerate(team_data, 1):
            # Add the css styling:
            soup.head.style.string = styling
            # Add the team tag at the top of the HTML table:
            html_tag_attrs = {"class": "team_name", "id": f"team_name_{id_index}"}
            team_name_html_tag = soup.new_tag('th', attrs=html_tag_attrs)
            team_name_html_tag.string = team_tag
            soup.body.table.thead.tr.append(team_name_html_tag)
            # Add the team score at the bottom of the HTML table:
            html_tag_attrs = {"class": "team_score", "id": f"team_score_{id_index}"}
            team_score_html_tag = soup.new_tag('td', attrs=html_tag_attrs)
            team_score = sum(p[1][1] for p in players if not p[0].strip().startswith('#'))
            team_score_html_tag.string = str(team_score)
            soup.body.table.tbody.tr.append(team_score_html_tag)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()

def build_team_html(team_data: List[Tuple[str, List]], style=None):
    '''team_data contains the scores for teams in the following format:
    [
        (team_1_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ]),
        (team_2_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ]),
        (team_3_name, [ (fc_1, player_data_1), (fc_2, player_data_2) ])
    ]

    team_data is what is returned by ScoreKeeper.get_war_table_DCS
    player_data is a list that contains various information, such as the player's name, player score each GP, and player score each race    
    '''
    team_data = restructure_if_needed(team_data)
    
    # Read in base css styling and read in custom styling if it was specified
    styling = ""
    with codecs.open(TEAM_STYLE_FILE, "r", "utf-8") as fp:
        styling = fp.read() + "\n\n"
    if style in TEAM_STYLES:
        with codecs.open(TEAM_STYLES[style], "r", "utf-8") as fp:
            styling += fp.read() + "\n\n"

    # Build the team HTML
    soup = None
    with codecs.open(TEAM_HTML_BUILDER_FILE, "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        for id_index, (team_tag, players) in enumerate(team_data, 1):
            # Add the css styling:
            soup.head.style.string = styling
            # Add the team tag at the top of the HTML table:
            html_tag_attrs = {"class": "team_name", "id": f"team_name_{id_index}"}
            team_name_html_tag = soup.new_tag('th', attrs=html_tag_attrs)
            team_name_html_tag.string = team_tag
            soup.body.table.thead.tr.append(team_name_html_tag)
            # Add the team score at the bottom of the HTML table:
            html_tag_attrs = {"class": "team_score", "id": f"team_score_{id_index}"}
            team_score_html_tag = soup.new_tag('td', attrs=html_tag_attrs)
            team_score = sum(p[1][1] for p in players if not p[0].strip().startswith('#'))
            team_score_html_tag.string = str(team_score)
            soup.body.table.tbody.tr.append(team_score_html_tag)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()


def build_info_page_html(table_id: int):
    table_id = str(table_id)
    with codecs.open(QUICK_INFO_HTML_BUILDER_FILE, "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        team_score_html_base_url = f"{api_common.API_URL}{api_common.TEAM_SCORES_HTML_ENDPOINT}{table_id}"
        
        team_header_tag = soup.new_tag('h1')
        team_header_tag.string = f"Want a stream table overlay that automatically updates? Developing an app to interact with Table Bot? Read how below!"
        soup.body.append(team_header_tag)
        soup.body.append(soup.new_tag('br'))
        soup.body.append(soup.new_tag('br'))

        team_header_tag = soup.new_tag('h3')
        team_header_tag.string = f"Get team score HTML for an ongoing table with TableBot:"
        soup.body.append(team_header_tag)

        list_tag = soup.new_tag('ul')
        soup.body.append(list_tag)

        for style in TEAM_STYLES:
            url_tag = soup.new_tag('a', href=f"{team_score_html_base_url}?style={style}")
            url_tag.string = f"Scores with tags in {style} style"
            li_tag = soup.new_tag('li')
            li_tag.append(url_tag)
            soup.body.ul.append(li_tag)
            #soup.body.append(soup.new_tag('br'))
        
        soup.body.append(soup.new_tag('br'))
        li_tag = soup.new_tag('li')

        em_tag = soup.new_tag('b')
        em_tag.string = "Don't like any of these? You can apply your own styling in OBS by adding the URL "
        li_tag.append(em_tag)

        url_tag = soup.new_tag('a', href=f"{team_score_html_base_url}")
        url_tag.string = f"{team_score_html_base_url}"
        li_tag.append(url_tag)

        em_tag = soup.new_tag('b')
        em_tag.string = """ as a browser source, then applying your own CSS in the "Custom CSS" field."""
        li_tag.append(em_tag)

        soup.body.ul.append(li_tag)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()

def __get_testing_channel_bot__():
    import os
    import sys
    import inspect
    
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir) 
    import BadWolfBot
    BadWolfBot.initialize()
    import common
    import TableBot
    import SmartTypes
    

    import TagAIShell
    
    TagAIShell.initialize()
    war = TableBot.War.War("2v2", 6, 0, 3, ignoreLargeTimes=False, displayMiis=True)
    this_bot = TableBot.ChannelBot(war=war, server_id=1, channel_id=1)
    smart_type = SmartTypes.SmartLookupTypes("r0000001", allowed_types=SmartTypes.SmartLookupTypes.ROOM_LOOKUP_TYPES)
    status = common.run_async_function_no_loop(this_bot.load_table_smart(smart_type, war, message_id=0, setup_discord_id=0, setup_display_name="Bad Wolf"))

    players = list(this_bot.getRoom().get_fc_to_name_dict(1, 3*4).items())
    tags_player_fcs = TagAIShell.determineTags(players, this_bot.getWar().playersPerTeam)
    this_bot.getWar().set_temp_team_tags(tags_player_fcs)

    this_bot.getWar().setTeams(this_bot.getWar().getConvertedTempTeams())
    return this_bot

if __name__ == "__main__":
    this_bot = __get_testing_channel_bot__()
    import ScoreKeeper
    table_text, table_sorted_data = ScoreKeeper.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, missingRacePts=this_bot.dc_points, server_id=123, discord_escape=False)
    #print(table_sorted_data)
    html = build_team_html(table_sorted_data)
    with open(f"{API_DATA_PATH}result.html", "w") as file:
        file.write(html)