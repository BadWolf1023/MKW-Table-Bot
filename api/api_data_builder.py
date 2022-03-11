from asyncio import create_task
from bs4 import BeautifulSoup
import codecs
import re
from datetime import timedelta
from typing import List, Union, Tuple

if __name__ == "__main__":
    import sys
    import os
    # insert at 1, 0 is the script path (or '' in REPL)
    sys.path.insert(1, '.')
    
from api import api_common



API_DATA_PATH = "api/"
HTML_DATA_PATH = f"html/"
CSS_DATA_PATH = f"css/"
TEAM_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}team_score_builder.html"
TEAM_STYLE_FILE = f"{CSS_DATA_PATH}team_score_base.css"
FULL_TABLE_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}full_table_builder.html"
FULL_TABLE_STYLE_FILE = f"{CSS_DATA_PATH}team_score_base.css"
QUICK_INFO_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}quick_info.html"

TEAM_STYLES = {"rainbow": f"{CSS_DATA_PATH}team_score_rainbow.css",
               "pastel": f"{CSS_DATA_PATH}team_score_pastel.css",
               "orange": f"{CSS_DATA_PATH}team_score_orange.css",
               "neon": f"{CSS_DATA_PATH}team_score_neon.css",
               "verticalblue": f"{CSS_DATA_PATH}team_score_vertical_blue.css"
}

FULL_TABLE_STYLES = {
}

def build_table_styling(table_background_picture_url: Union[None, str], table_background_color: Union[None, str], table_text_color: Union[None, str], table_font: Union[None, str]) -> str:
    styling = ""
    if table_background_picture_url is not None:
        styling_segment = """table {
    background-image: url(%s) !important;""" % table_background_picture_url
        styling_segment += "\nbackground-size: 100% 100% !important;\n}"
        styling += styling_segment + "\n\n"
    
    if table_background_color is not None:
        styling_segment = """table {
    background-color: %s !important;
}""" % table_background_color
        styling += styling_segment + "\n\n"

    if table_text_color is not None:
        styling_segment = """table, td, th {
    color: %s !important;
}""" % table_text_color
        styling += styling_segment + "\n\n"
    if table_font is not None:
        styling_segment = """table, td, th {
    font-family: %s !important;
}""" % table_font
        styling += styling_segment + "\n\n"

    return styling


def team_name_score_generator(team_data) -> Tuple[str, str]:
    if len(team_data["teams"]) == 1 and "No Tag" in team_data["teams"]:
        players = team_data["teams"]["No Tag"]["players"]
        for player_data in players.values():
            yield player_data["table_name"], str(player_data["total_score"])
    else:
        for team_tag, team_data in team_data["teams"].items():
            yield team_tag, str(team_data["total_score"])

def build_full_table_html(table_data: dict, style=None, table_background_picture_url=None, table_background_color=None, table_text_color=None, table_font=None):
    '''
    table_data is what is returned by ScoreKeeper.get_war_table_DCS 
    '''
    soup = None
    with codecs.open(f"{API_DATA_PATH}{FULL_TABLE_HTML_BUILDER_FILE}", "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        soup.style.string = build_table_styling(table_background_picture_url, table_background_color, table_text_color, table_font)
        # Add style sheets for base css styling and custom styling if it was specified
        soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"{FULL_TABLE_STYLE_FILE}"}))
        if style in FULL_TABLE_STYLES:
            soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"{FULL_TABLE_STYLES[style]}"}))

        for id_index, (team_tag, team_data) in enumerate(table_data["teams"].items(), 1):
            tbody_element = soup.new_tag('tbody')
            team_players = [p for p in team_data["players"].values() if not p["subbed_out"]]
            num_team_players = len(team_players)
            team_name_header_element = soup.new_tag('th', attrs={"class": "team_name", "id": f"team_name_{id_index}", "rowspan": f"{num_team_players}", "scope": "rowgroup"})
            team_name_header_element.string = team_tag
            team_score_header_element = soup.new_tag('th', attrs={"class": "team_score", "id": f"team_score_{id_index}", "rowspan": f"{num_team_players}", "scope": "rowgroup"})
            team_score_header_element.string = str(team_data["total_score"])
            for player_data in team_players:
                tr_element = soup.new_tag('tr')
                player_name_header_element = soup.new_tag('th', attrs={"class": "player_name", "scope": "row"})
                player_name_header_element.string = player_data["table_name"]
                tr_element.append(player_name_header_element)
                for gp_num, gp_score_chunk in enumerate(player_data["gp_scores"], 1):
                    player_score_element = soup.new_tag('td', attrs={"class": f"player_score GP_{gp_num}"})
                    player_score_element.string = str(sum(gp_score_chunk))
                    tr_element.append(player_score_element)
                tbody_element.append(tr_element)
                
            first_tr = tbody_element.find_all("tr")[0]
            first_tr.insert(0, team_name_header_element)
            first_tr.append(team_score_header_element)
            soup.table.append(tbody_element)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()

def style_equal_width(html_tag_attrs, num_boxes):
    html_tag_attrs.update({"style": f"width:{(1/num_boxes):.2%};"})

def build_team_html(table_data: dict, style=None, table_background_picture_url=None, table_background_color=None, table_text_color=None, table_font=None):
    '''
    table_data is what is returned by ScoreKeeper.get_war_table_DCS 
    '''    
    # Build the team HTML
    soup = None
    with codecs.open(f"{API_DATA_PATH}{TEAM_HTML_BUILDER_FILE}", "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        soup.style.string = build_table_styling(table_background_picture_url, table_background_color, table_text_color, table_font)
        # Add style sheets for base css styling and custom styling if it was specified
        soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{TEAM_STYLE_FILE}"}))
        if style in TEAM_STYLES:
            soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{TEAM_STYLES[style]}"}))

        num_teams = sum(1 for _ in team_name_score_generator(table_data))
        for id_index, (team_tag, score) in enumerate(team_name_score_generator(table_data), 1):
            # Add the team tag at the top of the HTML table:
            html_tag_attrs = {"class": "team_name", "id": f"team_name_{id_index}"}
            style_equal_width(html_tag_attrs, num_teams)
            team_name_html_tag = soup.new_tag('th', attrs=html_tag_attrs)
            team_name_html_tag.string = team_tag
            soup.body.table.thead.tr.append(team_name_html_tag)
            # Add the team score at the bottom of the HTML table:
            html_tag_attrs = {"class": "team_score", "id": f"team_score_{id_index}"}
            team_score_html_tag = soup.new_tag('td', attrs=html_tag_attrs)
            team_score_html_tag.string = score
            soup.body.table.tbody.tr.append(team_score_html_tag)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()


def build_info_page_html(table_id: int):
    table_id = str(table_id)
    with codecs.open(f"{API_DATA_PATH}{QUICK_INFO_HTML_BUILDER_FILE}", "r", "utf-8") as fp:
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
    BadWolfBot.data_init()
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
    html = build_team_html(table_sorted_data, style="verticalblue").replace("""setTimeout("location.reload(true);", t);""", "")
    with open(f"{API_DATA_PATH}result.html", "w") as file:
        file.write(html)