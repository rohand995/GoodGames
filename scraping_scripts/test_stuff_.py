import requests
import json
import time
from typing import Optional

STEAM_API_KEY = "your_api_key_here"  # Replace with your Steam API key

with open('STEAM_KEY.txt') as f_key:
    STEAM_API_KEY = f_key.read().strip()

# print(STEAM_API_KEY)

#https://github.com/Revadike/InternalSteamWebAPI/wiki

################################################################################
#utils
################################################################################

def rate_limit():
    #steam rate limit is 100k per day, which is about 1.15 per second https://steamcommunity.com/dev/apiterms
    #another source says "most calls are limited to 200 requests every 5 minutes", which is 2 every 3 seconds
    time.sleep(1.5) #let's just start with 1 request per 1.5 seconds, ie 40/m

################################################################################
#app list
################################################################################

#fresh app list can be retrieved via: https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=STEAMKEY&format=json

#the following api requires a key, but can return just games:
# https://api.steampowered.com/IStoreService/GetAppList/v1/?include_games=true
# also see: https://steamapi.xpaw.me/#IStoreService/GetAppList

#returns the parsed list of integer app ids
def get_app_list(last_app_id: Optional[int] = None) -> Optional[list[int]]:
    rate_limit()

    url = 'https://api.steampowered.com/IStoreService/GetAppList/v1/'
    #
    params = {
        "key": STEAM_API_KEY,
        "format": "json",
        #
        "include_games": True,
        # "max_results": '10000' #so we get responses faster
        "max_results": '50000' #this is the max that steam allows per "page" of response
    }
    if last_app_id is not None:
        params['last_appid'] = last_app_id
    #
    response = requests.get(url, params=params)

    if response.status_code < 200 or response.status_code > 299:
        print("ERROR:", response.status_code)
        return None

    data = response.json()
    
    if 'response' not in data or 'apps' not in data['response']:
        return [] #done

    applist = data['response']['apps']
    return [item['appid'] for item in applist]

def get_full_app_list() -> list[int]:
    print("Retrieving app list...")

    apps = []
    last_app = None
    while True:
        apps_ = get_app_list(last_app)

        print("Received", len(apps_))
        
        print(len(apps_))
        if len(apps_) == 0:
            print(" (done)")
            break

        last_app = apps_[-1]
        apps += apps_
        print(" total:", len(apps))
        print(" last id:", last_app)
    return apps

def load_full_app_list() -> list[int]:
    print("Loading app list...")
    apps: list[int] = []
    try:
        with open('app_list.txt') as f:
            apps = [int(line.strip()) for line in f]
        print(" Loaded", len(apps), "apps from local cache")
    except:
        #file doesn't exist
        print(" Local cache not found, retrieving from API")
        apps = get_full_app_list()
        print(" Loaded", len(apps), "apps from API")
        #save for next time
        with open('app_list.txt', 'w') as f:
            for app in apps:
                f.write(str(app) + '\n')
        print(" Saved to local cache")
    return apps

apps = load_full_app_list()

################################################################################
#get app info for some random game
################################################################################

def get_app_info(app_id: str) -> Optional[str]:
    rate_limit()

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

    if response.status_code < 200 or response.status_code > 299:
        print("ERROR:", response.status_code)
        return None

    data = response.json()

    with open("tmp/app_" + app_id + "_info.json", 'w') as f:
        f.write(json.dumps(data, indent=2))

    if data[app_id]['success']:
        # print(json.dumps(data, indent=2))
        print("got app info for", app_id, " -> ", data[app_id]['data']['name'], f"({data[app_id]['data']['type']})")
        item_type = data[app_id]['data']['type']
        return (data[app_id]['data']['name']) if (item_type == 'game') else None
    else:
        print("failed to get app info for", app_id)
        return None

################################################################################
#get reviews for a game
################################################################################

def get_reviews(app_id: str, cursor: str = None) -> Optional[tuple[str, int]]:
    rate_limit()

    url = 'https://store.steampowered.com/appreviews/' + app_id + '?json=1'
    #
    params = {
        "key": STEAM_API_KEY,
        "format": "json",
        #
        "filter": 'updated',
        "num_per_page": '100' #this is the max that steam allows per "page" of response
    }
    if cursor is not None:
        params['cursor'] = cursor
    #
    response = requests.get(url, params=params)

    if response.status_code < 200 or response.status_code > 299:
        print("ERROR:", response.status_code)
        return None

    data = response.json()

    with open("tmp/app_" + app_id + "_reviews.json", 'w') as f:
        f.write(json.dumps(data, indent=2))

    if data['success'] == 1:

        # print(json.dumps(data, indent=2))

        rating = -1

        if 'query_summary' in data and 'review_score' in data['query_summary']:
            # print(data['query_summary'])
            rating = data['query_summary']['review_score']

        return data['cursor'], rating

    return None #this means there was an error

################################################################################
#find games with ratings above 5
################################################################################

# app_id = '367520'

with open("apps_checked.txt", 'a+') as f1:
    f1.seek(0)
    apps_checked: set[int] = set([int(line.strip()) for line in f1.readlines()])
    with open("apps_good.txt", 'a') as f2:
        #
        for app_id in apps:
            #
            if app_id in apps_checked:
                # print("skipping", app_id)
                continue
            #
            appid = str(app_id)
            app_name = get_app_info(appid) #only returns name if query was successful and this app is a game
            if app_name is not None:
                result = get_reviews(appid)
                if result is None:
                    print(" app", appid, "name", f'"{app_name}"', "rating unknown")
                else:
                    _, rating = result
                    print(" app", appid, "name", f'"{app_name}"', "rating", rating)
                    if rating > 5:
                        print(" adding to list")
                        f2.write(appid + ' ' + str(rating) + '\n')
            #
            apps_checked.add(app_id)
            f1.write(appid + '\n')

'''
TODO
the above loop goes through each app in the list, checks if it's a game, checks its rating, and if it's above 5, adds it to a secondary list for further scraping
but... the list already contains only games, and it looks like most of them are above a 5 in rating
so this might be a waste of time...
i'm going to run it for now, just to see, but I may need to do something a bit more efficient (e.g., scrape ratings and just drop them if the game is 5 or below)
'''