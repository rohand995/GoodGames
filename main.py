from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
from steam_api import get_owned_games
import uvicorn
import recommender

# Initialize FastAPI
app = FastAPI()

# Set up Jinja2 template rendering
templates = Jinja2Templates(directory="templates")

# Serve static files (CSS, JS, images) from the 'styles' folder
app.mount("/styles", StaticFiles(directory="styles"), name="styles")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/recommend")
async def recommend(request: Request):
    json_data = await request.json()
    steam_ids = json_data['steam_ids']
    game_ids = recommender.get_recommendations(steam_ids)
    game_info = recommender.get_game_info(game_ids)
    return JSONResponse(content={"recommendations": game_info})

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
