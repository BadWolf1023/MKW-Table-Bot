from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import api.api_channelbot_interface as cb_interface
from api import api_data_builder
from api.api_common import *

app = None

origins = [
    "https://mkwtablebot.vercel.app",
    "http://localhost:3000",
    "*"
]

def raise_no_table_found():
    raise HTTPException(
                status_code=404,
                detail=TABLE_ID_NOT_FOUND_ERR_MSG,
            )


def initialize(app_: FastAPI):
    global app
    app = app_
    app.mount("/css", StaticFiles(directory="./api/css"))

    

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    def home_html():
        return api_data_builder.build_home_html()

    @app.get(TEAM_SCORES_HTML_ENDPOINT + "{table_id}", response_class=HTMLResponse)
    def get_team_scores_html(
        table_id: int,
        style: Optional[str] = Query(None, max_length=15),
        background_picture: Optional[str] = Query(None),
        background_color: Optional[str] = Query(None),
        text_color: Optional[str] = Query(None),
        font: Optional[str] = Query(None),
        border_color: Optional[str] = Query(None),
        text_size: Optional[int] = Query(None),
        show_team_names: Optional[bool] = Query(True),
        sort_teams: Optional[bool] = Query(True),
        show_races_played: Optional[bool] = Query(True),
        fit_names: Optional[bool] = Query(False)
    ):
        table_bot = cb_interface.get_table_bot(table_id)
        if table_bot is None:
            raise_no_table_found()
        return api_data_builder.build_team_html(
            cb_interface.get_team_score_data(table_bot, sort_teams), 
            style, 
            background_picture, 
            background_color, 
            text_color, 
            font, 
            border_color, 
            text_size,
            include_team_names=show_team_names,
            show_races_played=show_races_played,
            fit_names=fit_names
        )

    @app.get(FULL_TABLE_HTML_ENDPOINT + "{table_id}", response_class=HTMLResponse)
    def get_full_table_html(
        table_id: int,
        show_races_played: Optional[bool] = Query(True),
        style: Optional[str] = Query(None, max_length=15),
        background_picture: Optional[str] = Query(None),
        background_color: Optional[str] = Query(None),
        text_color: Optional[str] = Query(None),
        font: Optional[str] = Query(None),
        border_color: Optional[str] = Query(None),
        text_size: Optional[int] = Query(None),
    ):
        table_bot = cb_interface.get_table_bot(table_id)
        if table_bot is None:
            raise_no_table_found()
        return api_data_builder.build_full_table_html(
            cb_interface.get_team_score_data(table_bot), show_races_played, style, background_picture, background_color, text_color, font, border_color, text_size
        )

    @app.get(TEAM_SCORES_JSON_ENDPOINT + "{table_id}")
    def get_team_scores_json(table_id: int):
        table_bot = cb_interface.get_table_bot(table_id)
        if table_bot is None:
            raise HTTPException(
                status_code=404,
                detail="Table ID not found. Either the table has been reset, or the table ID given does not exist. Table Bot gave you a table ID when you started the table. Use that.",
            )
        return cb_interface.get_team_score_data(table_bot)

    @app.get(INFO_ENDPOINT + "{table_id}", response_class=HTMLResponse)
    def info_page(table_id: int):
        return api_data_builder.build_info_page_html(table_id)

    @app.get(FULL_SCORES_PICTURE_ENDPOINT + "{table_id}", response_class=HTMLResponse)
    def get_picture_page(table_id: int):
        table_bot = cb_interface.get_table_bot(table_id)
        if table_bot is None:
            raise_no_table_found()
        return api_data_builder.get_picture_page_html()
        
    @app.get(TABLE_PICTURE_URL_JSON_ENDPOINT + "{table_id}")
    def get_picture_url_json(table_id: int):
        table_bot = cb_interface.get_table_bot(table_id)
        if table_bot is None:
            raise_no_table_found()
        return {"table_url": table_bot.get_war().get_discord_picture_url()}
    
    @app.get(STATS_ENDPOINT)
    def get_stats_json():
        return cb_interface.get_stats_data()

    