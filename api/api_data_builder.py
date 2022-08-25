from asyncio import create_task
from bs4 import BeautifulSoup
import codecs
import re
from datetime import timedelta
from typing import List, Union, Tuple

import UtilityFunctions    
from api import api_common



API_DATA_PATH = "api/"
HTML_DATA_PATH = f"html/"
CSS_DATA_PATH = f"css/"
TEAM_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}team_score_builder.html"
TEAM_STYLE_FILE = f"{CSS_DATA_PATH}team_score_base.css"
FULL_TABLE_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}full_table_builder.html"
FULL_TABLE_STYLE_FILE = f"{CSS_DATA_PATH}full_scores_base.css"
QUICK_INFO_HTML_BUILDER_FILE = f"{HTML_DATA_PATH}quick_info.html"
TABLE_PICTURE_HTML_FILE = f"{HTML_DATA_PATH}picture_builder.html"

TEAM_STYLES = {"rainbow": f"{CSS_DATA_PATH}team_score_rainbow.css",
               "pastel": f"{CSS_DATA_PATH}team_score_pastel.css",
               "orange": f"{CSS_DATA_PATH}team_score_orange.css",
               "neon": f"{CSS_DATA_PATH}team_score_neon.css",
               "verticalblue": f"{CSS_DATA_PATH}team_score_vertical_blue.css"
}

FULL_TABLE_STYLES = {"rainbow": f"{CSS_DATA_PATH}full_scores_rainbow.css",
               "pastel": f"{CSS_DATA_PATH}full_scores_pastel.css",
               "orange": f"{CSS_DATA_PATH}full_scores_orange.css",
               "neon": f"{CSS_DATA_PATH}full_scores_neon.css",
               "verticalblue": f"{CSS_DATA_PATH}full_scores_vertical_blue.css"
}

def build_table_styling(html_type, style, table_background_picture_url: Union[None, str], table_background_color: Union[None, str], table_text_color: Union[None, str], table_font: Union[None, str], border_color: Union[None, str], text_size: Union[None, int]) -> str:
    styling = ""
    if table_background_picture_url is not None:
        styling_segment = """#tablebot_table {
    background-image: url(%s) !important;""" % table_background_picture_url
        styling_segment += "\nbackground-size: 100% 100% !important;\n}"
        styling += styling_segment + "\n\n"
    
    if table_background_color is not None:
        styling_segment = """#tablebot_table {
    background-color: %s !important;
}""" % table_background_color
        styling += styling_segment + "\n\n"

    if table_text_color is not None:
        styling_segment = """#tablebot_table {
    color: %s !important;
}""" % table_text_color
        styling += styling_segment + "\n\n"

    if text_size is not None:
        styling_segment = """#tablebot_table {
    font-size: %ipx !important;
}""" % text_size
        styling += styling_segment + "\n\n"

    if table_font is not None:
        styling_segment = """#tablebot_table {
    font-family: %s !important;
}""" % table_font
        styling += styling_segment + "\n\n"
    if border_color is not None:
        styling_segment = """#tablebot_table, .team_name_box, .score_box {
    border-color: %s !important;
}""" % border_color
        styling += styling_segment + "\n\n"

    return styling


def build_neon_text_js_injection(table_text_color):
    if table_text_color.startswith("0x"):
        table_text_color = table_text_color[2:]
    if UtilityFunctions.is_hex(table_text_color):
        table_text_color = "#"+table_text_color.upper()
    lighten_color_func = """const pSBC=(p,c0,c1,l)=>{
    let r,g,b,P,f,t,h,i=parseInt,m=Math.round,a=typeof(c1)=="string";
    if(typeof(p)!="number"||p<-1||p>1||typeof(c0)!="string"||(c0[0]!='r'&&c0[0]!='#')||(c1&&!a))return null;
    if(!this.pSBCr)this.pSBCr=(d)=>{
        let n=d.length,x={};
        if(n>9){
            [r,g,b,a]=d=d.split(","),n=d.length;
            if(n<3||n>4)return null;
            x.r=i(r[3]=="a"?r.slice(5):r.slice(4)),x.g=i(g),x.b=i(b),x.a=a?parseFloat(a):-1
        }else{
            if(n==8||n==6||n<4)return null;
            if(n<6)d="#"+d[1]+d[1]+d[2]+d[2]+d[3]+d[3]+(n>4?d[4]+d[4]:"");
            d=i(d.slice(1),16);
            if(n==9||n==5)x.r=d>>24&255,x.g=d>>16&255,x.b=d>>8&255,x.a=m((d&255)/0.255)/1000;
            else x.r=d>>16,x.g=d>>8&255,x.b=d&255,x.a=-1
        }return x};
    h=c0.length>9,h=a?c1.length>9?true:c1=="c"?!h:false:h,f=this.pSBCr(c0),P=p<0,t=c1&&c1!="c"?this.pSBCr(c1):P?{r:0,g:0,b:0,a:-1}:{r:255,g:255,b:255,a:-1},p=P?p*-1:p,P=1-p;
    if(!f||!t)return null;
    if(l)r=m(P*f.r+p*t.r),g=m(P*f.g+p*t.g),b=m(P*f.b+p*t.b);
    else r=m((P*f.r**2+p*t.r**2)**0.5),g=m((P*f.g**2+p*t.g**2)**0.5),b=m((P*f.b**2+p*t.b**2)**0.5);
    a=f.a,t=t.a,f=a>=0||t>=0,a=f?a<0?t:t<0?a:a*P+t*p:0;
    if(h)return"rgb"+(f?"a(":"(")+r+","+g+","+b+(f?","+m(a*1000)/1000:"")+")";
    else return"#"+(4294967296+r*16777216+g*65536+b*256+(f?m(a*255):0)).toString(16).slice(1,f?undefined:-2)
}
    function from_rule(color){
        return "0% { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px " + color + ", 0 0 20px " + color + ", 0 0 30px " + color + ", 0 0 40px " + color + ", 0 0 50px " + color + "; }"
    }
    function to_rule(color){
        var c = pSBC ( 0.15, color );
        return "100% { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px " + c + ", 0 0 20px " + c + ", 0 0 30px " + c + ", 0 0 40px " + c + ", 0 0 50px " + c + "; }"
    }
"""

    return lighten_color_func + """
    
    // search the CSSOM for a specific -webkit-keyframe rule
function findKeyframesRule(rule)
    {
        // gather all stylesheets into an array
        var ss = document.styleSheets;
        // loop through the stylesheets
        for (var i = 0; i < ss.length; ++i) {
            // loop through all the rules
            for (var j = 0; j < ss[i].cssRules.length; ++j) {
                // find the -webkit-keyframe rule whose name matches our passed over parameter and return that rule
                if (ss[i].cssRules[j].name == rule)
                    return ss[i].cssRules[j];
            }
        }
        
        // rule not found
        return null;
    }

// remove old keyframes and add new ones
function GlowColorInjection()
    {
        // find our -webkit-keyframe rule
        var keyframes = findKeyframesRule("glow");
        
        // remove the existing from and to rules
        keyframes.deleteRule("from");
        keyframes.deleteRule("to");
        var fr = from_rule("%s");
        var tr = to_rule("%s");

        keyframes.appendRule(fr);
        keyframes.appendRule(tr);
        

    }""" % (table_text_color, table_text_color)


def team_name_score_generator(team_data) -> Tuple[str, str]:
    if len(team_data["teams"]) == 1 and "No Tag" in team_data["teams"]:
        players = team_data["teams"]["No Tag"]["players"]
        for player_data in players.values():
            yield player_data["table_name"], str(player_data["total_score"])
    else:
        for team_tag, team_data in team_data["teams"].items():
            yield team_tag, str(team_data["total_score"])

def build_full_table_html(table_data: dict, style=None, table_background_picture_url=None, table_background_color=None, table_text_color=None, table_font=None, border_color=None, text_size=None):
    '''
    table_data is what is returned by ScoreKeeper.get_war_table_DCS 
    '''
    soup = None
    with codecs.open(f"{API_DATA_PATH}{FULL_TABLE_HTML_BUILDER_FILE}", "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        soup.style.string = build_table_styling("full", style, table_background_picture_url, table_background_color, table_text_color, table_font, border_color, text_size)
        # Add style sheets for base css styling and custom styling if it was specified
        soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{FULL_TABLE_STYLE_FILE}"}))
        if style in FULL_TABLE_STYLES:
            soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{FULL_TABLE_STYLES[style]}"}))

        player_number = 0
        for id_index, (team_tag, team_data) in enumerate(table_data["teams"].items(), 1):
            # Build the elements related to the team name/tag
            team_wrapper = soup.new_tag('div', attrs={"class": "team_wrapper", "id": f"team_{id_index}_wrapper"})
            team_name_wrapper = soup.new_tag('div', attrs={"class": "team_name_wrapper"})
            team_name_div = soup.new_tag('div', attrs={"class": "team_name", "id": f"team_{id_index}_name"})
            team_name_div.string = team_tag
            team_name_wrapper.append(team_name_div)
            team_wrapper.append(team_name_wrapper)

            # Build the elements related to the team players and their scores
            team_players = [p for p in team_data["players"].values() if not p["subbed_out"]]
            team_players_wrapper = soup.new_tag('div', attrs={"class": "team_players_wrapper"})
            for player_data in team_players:
                player_number += 1
                player_wrapper = soup.new_tag('div', attrs={"class": "player_wrapper"})
                # Build the elements related to the player's name
                player_name_wrapper = soup.new_tag('div', attrs={"class": "player_name_wrapper"})
                player_name_div = soup.new_tag('div', attrs={"class": "player_name", "id": f"player_{player_number}_name"})
                player_name_div.string = player_data["table_name"]
                player_name_wrapper.append(player_name_div)
                player_wrapper.append(player_name_wrapper)

                #Build the elements related to the player's GP scores
                gp_scores_wrapper = soup.new_tag('div', attrs={"class": "gp_scores_wrapper"})
                for gp_num, gp_score_chunk in enumerate(player_data["gp_scores"], 1):
                    score_wrapper = soup.new_tag('div', attrs={"class": "score_wrapper"})
                    score_div = soup.new_tag('div', attrs={"class":"score", "id": f"player_{player_number}_score_{gp_num}"})
                    score_div.string = str(sum(gp_score_chunk))
                    score_wrapper.append(score_div)
                    gp_scores_wrapper.append(score_wrapper)
                player_wrapper.append(gp_scores_wrapper)

                #Build the elements related to the player's total score
                player_total_wrapper = soup.new_tag('div', attrs={"class": "player_total_wrapper"})
                player_total_div = soup.new_tag('div', attrs={"class": "player_total", "id": f"player_{player_number}_total"})
                player_total_div.string = str(player_data["total_score"])
                player_total_wrapper.append(player_total_div)
                player_wrapper.append(player_total_wrapper)

                team_players_wrapper.append(player_wrapper)
            team_wrapper.append(team_players_wrapper)

            # Build the elements related to the team total
            team_score_wrapper = soup.new_tag('div', attrs={"class": "team_score_wrapper"})
            team_score_div = soup.new_tag('div', attrs={"class": "team_score", "id": f"team_{id_index}_total"})
            team_score_div.string = str(team_data["total_score"])
            team_score_wrapper.append(team_score_div)
            team_wrapper.append(team_score_wrapper)

            soup.find(id="tablebot_table").append(team_wrapper)
        return str(soup)
    finally:
        if soup is not None:
            soup.decompose()

def style_equal_width(html_tag_attrs, num_boxes):
    html_tag_attrs.update({"style": f"width:{(1/num_boxes):.2%};"})
def style_equal_height(html_tag_attrs, num_boxes):
    html_tag_attrs.update({"style": f"height:{(1/num_boxes):.2%};"})

def build_team_html(table_data: dict, style=None, table_background_picture_url=None, table_background_color=None, table_text_color=None, table_font=None, border_color=None, text_size=None, include_team_names=True):
    '''
    table_data is what is returned by ScoreKeeper.get_war_table_DCS 
    '''    
    # Build the team HTML
    soup = None
    with codecs.open(f"{API_DATA_PATH}{TEAM_HTML_BUILDER_FILE}", "r", "utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
    try:
        soup.style.string = build_table_styling("team", style, table_background_picture_url, table_background_color, table_text_color, table_font, border_color, text_size)
        # Add style sheets for base css styling and custom styling if it was specified
        soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{TEAM_STYLE_FILE}"}))
        if style in TEAM_STYLES:
            soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": f"/{TEAM_STYLES[style]}"}))
            if style == "neon" and table_text_color is not None:
                soup.head.script.string += build_neon_text_js_injection(table_text_color)
        
        for id_index, (team_tag, score) in enumerate(team_name_score_generator(table_data), 1):
            if include_team_names:
                # Add the team name divs:
                team_name_box = soup.new_tag('div', attrs={"class": "team_name_box"})
                team_name_div = soup.new_tag('div', attrs={"class": "team_name", "id": f"team_name_{id_index}"})
                team_name_div.string = team_tag
                team_name_box.append(team_name_div)

            team_score_box = soup.new_tag('div', attrs={"class": "score_box"})
            team_score_div = soup.new_tag('div', attrs={"class": "team_score", "id": f"team_score_{id_index}"})
            team_score_div.string = score
            team_score_box.append(team_score_div)

            if include_team_names:
                soup.find(id="team_names_box").append(team_name_box)
            else:
                if team_names_container := soup.find(id="team_names_box"):
                    team_names_container.decompose()
                    
            soup.find(id="scores_box").append(team_score_box)
            
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

def get_picture_page_html():
    with codecs.open(f"{API_DATA_PATH}{TABLE_PICTURE_HTML_FILE}", "r", "utf-8") as fp:
        return str(BeautifulSoup(fp.read(), "html.parser"))

def generate_table_picture(table_sorted_data, table_image_path):
    table_html = build_full_table_html(table_sorted_data, style="orange")