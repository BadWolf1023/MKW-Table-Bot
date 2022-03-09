from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
import api_channelbot_interface as cb_interface
import api_data_builder


app = FastAPI()

@app.get("/api/html/team_scores", response_class=HTMLResponse)
def read_item(table_id: int, style: Optional[str] = Query(None, max_length=50)):
    table_bot = cb_interface.get_table_bot(table_id)
    if table_bot is None:
        raise HTTPException(status_code=404, detail="Table ID not found. Either the table has been reset, or the table ID given does not exist. Table Bot gave you a table ID when you started the table. Use that.")
    return api_data_builder.build_team_html(cb_interface.get_team_score_data(table_bot), style)