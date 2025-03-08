import requests

STEAM_API_KEY = "your_api_key_here"  # Replace with your Steam API key

def get_owned_games(steam_id):
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id,
        "format": "json",
        "include_appinfo": True  # Get game names
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if "response" in data and "games" in data["response"]:
        return [game["name"] for game in data["response"]["games"]]
    return []
