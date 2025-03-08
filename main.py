from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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

@app.get("/recommend/{steam_id}")
def get_recommendations(steam_id: str):
    owned_games = get_owned_games(steam_id)
    # Placeholder for recommendation logic
    recommended_games = owned_games[:5]  # Just return first 5 games for now
    return {"recommended_games": recommended_games}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
