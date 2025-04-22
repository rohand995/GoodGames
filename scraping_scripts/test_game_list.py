import requests
import json

STEAM_API_KEY = "your_api_key_here"  # Replace with your Steam API key

#app list can be retrieved via: https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=STEAMKEY&format=json

print("opening app list")
with open('games.json', encoding='utf-8') as f:
    print(" opened file")
    content = f.read()
    print(" read file")
    j = json.loads(content)
    print("apps:", len(j['applist']['apps']))

#get app info for some random game

app_id = '367520'

def get_app_info(app_id: str):
    url = 'https://store.steampowered.com/api/appdetails'
    params = {
        "key": STEAM_API_KEY,
        # "steamid": steam_id,
        # "appids": app_id,
        "appids": app_id,
        "format": "json",
        # "include_appinfo": True  # Get game names
    }
    response = requests.get(url, params=params)
    data = response.json()

    print(json.dumps(data, indent=2))

get_app_info(app_id)