from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
from steam_api import get_owned_games

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
def get_recommendations(steam_ids: List[str]):
    recommendations = {}
    
    for steam_id in steam_ids:
        owned_games = get_owned_games(steam_id)
        recommended_games = owned_games[:5]  # Just the top 5 games
        recommendations[steam_id] = recommended_games
    
    return JSONResponse(content={"recommendations": recommendations})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
