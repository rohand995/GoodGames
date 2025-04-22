import requests
import json
import time
from typing import Optional, Union

import os

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

def get_app_info(app_id: str) -> Optional[tuple[str, object]]:
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

    if data[app_id]['success']:
        # print(json.dumps(data, indent=2))
        # print("got app info for", app_id, " -> ", data[app_id]['data']['name'], f"({data[app_id]['data']['type']})")
        item_type = data[app_id]['data']['type']
        return (data[app_id]['data']['name'], data) if (item_type == 'game') else None
    else:
        print("failed to get app info for", app_id)
        return None

################################################################################
#get reviews for a game
################################################################################

def get_reviews(app_id: str, cursor: str = None) -> Union[tuple[object, str, int], None]:
    rate_limit()

    url = 'https://store.steampowered.com/appreviews/' + app_id
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

    if data['success'] == 1:

        # print(json.dumps(data, indent=2))

        rating = -1

        if cursor is None:
            #first review page

            if 'query_summary' in data and 'review_score' in data['query_summary']:
                # print(data['query_summary'])
                rating = data['query_summary']['review_score']

            return data, data['cursor'], rating
        else:
            #other pages
            if 'query_summary' in data:
                return data, data['cursor'], -1 #keep format the same for simplicity

    return None #this means there was an error

################################################################################
#find games with ratings above 5
################################################################################

# app_id = '367520'

#this loop goes through each app in the list, checks if it's a game, checks its rating, and if it's above 5, adds it to a secondary list for further scraping
# print("Updating app list...")
# with open("apps_checked.txt", 'a+') as f1:
#     f1.seek(0)
#     apps_checked: set[int] = set([int(line.strip()) for line in f1.readlines()])
#     with open("apps_good.txt", 'a') as f2:
#         #
#         for app_id in apps:
#             #
#             if app_id in apps_checked:
#                 # print("skipping", app_id)
#                 continue
#             #
#             appid = str(app_id)
#             app_name, _ = get_app_info(appid) #only returns name if query was successful and this app is a game
#             if app_name is not None:
#                 result = get_reviews(appid)
#                 if result is None:
#                     print(" app", appid, "name", f'"{app_name}"', "rating unknown")
#                 else:
#                     _, _, rating = result
#                     print(" app", appid, "name", f'"{app_name}"', "rating", rating)
#                     if rating > 5:
#                         print(" adding to list")
#                         f2.write(appid + ' ' + str(rating) + '\n')
#             #
#             apps_checked.add(app_id)
#             f1.write(appid + '\n')
# print(" done")

# print("Checking app categories...")
# with open("apps_good.txt") as f:
#     apps_ = [[int(x.strip()) for x in line.split()] for line in f.readlines()]
#     apps_ = sorted(apps_, key = lambda x: -x[1]) #sort descending by rating

#     all_categories: set[tuple[int, str]] = set()

#     for app_id, rating in apps_:
#             appid = str(app_id)
#             app_name, app_data = get_app_info(appid) #only returns name if query was successful and this app is a game
#             categories = app_data[appid]["data"]["categories"]
#             # print(categories)
#             for category in categories:
#                 c_id = category['id']
#                 c_name = category['description']
#                 all_categories.add((c_id, c_name))

#             print("CATEGORIES:")
#             for id, name in sorted(all_categories):
#                 print('', id, name)
# print(" done")

#select some games based on multi-player tags (ie, "categories")
#these are the steam ids of the tags
'''
this is all of the categories I got from the first few games:
 1 Multi-player
 2 Single-player
 8 Valve Anti-Cheat enabled
 9 Co-op
 13 Captions available
 14 Commentary available
 15 Stats
 16 Includes Source SDK
 17 Includes level editor
 18 Partial Controller Support
 22 Steam Achievements
 23 Steam Cloud
 24 Shared/Split Screen
 25 Steam Leaderboards
 27 Cross-Platform Multiplayer
 28 Full controller support
 29 Steam Trading Cards
 30 Steam Workshop
 31 VR Support
 32 Steam Turn Notifications
 35 In-App Purchases
 36 Online PvP
 37 Shared/Split Screen PvP
 38 Online Co-op
 39 Shared/Split Screen Co-op
 40 SteamVR Collectibles
 41 Remote Play on Phone
 42 Remote Play on Tablet
 43 Remote Play on TV
 44 Remote Play Together
 47 LAN PvP
 48 LAN Co-op
 49 PvP
 51 Steam Workshop
 52 Tracked Controller Support
 53 VR Supported
 54 VR Only
 61 HDR available
 62 Family Sharing
 63 Steam Timeline
'''

'''
these are the multi-player-related ones:
 1 Multi-player
 9 Co-op
 24 Shared/Split Screen
 27 Cross-Platform Multiplayer
 36 Online PvP
 37 Shared/Split Screen PvP
 38 Online Co-op
 39 Shared/Split Screen Co-op
 44 Remote Play Together
 47 LAN PvP
 48 LAN Co-op
 49 PvP
'''

# tags: set[int] = {1, 9, 24, 27, 36, 37, 38, 39, 44, 47, 48, 49}

# print("Checking good apps...")
# with open("apps_good.txt") as f:
#     apps_ = [[int(x.strip()) for x in line.split()] for line in f.readlines()]
#     apps_ = sorted(apps_, key = lambda x: -x[1]) #sort descending by rating

#     for app_id, rating in apps_:
#             appid = str(app_id)
#             app_name, app_data = get_app_info(appid) #only returns name if query was successful and this app is a game
#             categories = app_data[appid]["data"]["categories"]
#             # print(categories)
#             for category in categories:
#                 c_id = category['id']
#                 if c_id in tags:
#                     c_name = category['description']
#                     #
#                     data, cursor, rating = get_reviews(appid)
#                     n_reviews = data['query_summary']['total_reviews']
#                     #
#                     print(f'{appid} "{app_name}" ({n_reviews})')
#                     # print(f'{appid} "{app_name}" ({n_reviews}) {c_name}')
#                     break
# print(" done")

#start with some arbitrary apps (with lots of reviews)
#our initial list of apps to scrape:
applist = [
10, #"Counter-Strike" (32613)
220, #"Half-Life 2" (79668)
240, #"Counter-Strike: Source" (41917)
550, #"Left 4 Dead 2" (207361)
620, #"Portal 2" (156703)
2200, #"Quake III Arena" (1860)
2280, #"DOOM + DOOM II" (14554)
2310, #"Quake" (9017)
2320, #"Quake II" (4913)
4000, #"Garry's Mod" (492406)
4700, #"Total War: MEDIEVAL II – Definitive Edition" (15308)
6910, #"Deus Ex: Game of the Year Edition" (9638)
8930, #"Sid Meier's Civilization® V" (75630)
32440, #"LEGO® Star Wars™ - The Complete Saga" (13450)
32470, #"STAR WARS™ Empire at War - Gold Pack" (23938)
49520, #"Borderlands 2" (112524) Multi-player
49600, #"Beat Hazard" (3445) Multi-player
105600, #"Terraria" (550250) Multi-player
204360, #"Castle Crashers®" (39894) Multi-player
221380, #"Age of Empires II (Retired)" (36005) Multi-player
227300, #"Euro Truck Simulator 2" (123943) Multi-player
230270, #"N++ (NPLUSPLUS)" (2055) Multi-player
238210, #"System Shock® 2 (Classic)" (4709) Multi-player
238460, #"BattleBlock Theater®" (22926) Multi-player
242680, #"Nuclear Throne" (8973) Multi-player
242760, #"The Forest" (168058) Multi-player
247080, #"Crypt of the NecroDancer" (11950) Multi-player
250760, #"Shovel Knight: Treasure Trove" (9671) Multi-player
250900, #"The Binding of Isaac: Rebirth" (124490) Multi-player
253230, #"A Hat in Time" (28356) Multi-player
261180, #"Lethal League" (2388) Multi-player
268910, #"Cuphead" (57060) Multi-player
270880, #"American Truck Simulator" (80859) Multi-player
284160, #"BeamNG.drive" (158436) Remote Play Together
286160, #"Tabletop Simulator" (28354) Multi-player
311690, #"Enter the Gungeon" (36740) Multi-player
312520, #"Rain World" (22441) Multi-player
322330, #"Don't Starve Together" (76709) Multi-player
346010, #"Besiege" (21720) Multi-player
362890, #"Black Mesa" (62005) Multi-player
379720, #"DOOM" (77118) Multi-player
413150, #"Stardew Valley" (344997) Multi-player
427520, #"Factorio" (104280) Multi-player
434570, #"Blood and Bacon" (12620) Multi-player
435150, #"Divinity: Original Sin 2 - Definitive Edition" (77664) Multi-player
508440, #"Totally Accurate Battle Simulator" (75074) Multi-player
]
#reviws: 32613 + 79668 + 41917 + 207361 + 156703 + 1860 + 14554 + 9017 + 4913 + 492406 + 15308 + 9638 + 75630 + 13450 + 23938 + 112524 + 3445 + 550250 + 39894 + 36005 + 123943 + 2055 + 4709 + 22926 + 8973 + 168058 + 11950 + 9671 + 124490 + 28356 + 2388 + 57060 + 80859 + 158436 + 28354 + 36740 + 22441 + 76709 + 21720 + 62005 + 77118 + 344997 + 104280 + 12620 + 77664 + 75074
#that's a total of 3664690 (3,664,690) reviews across all of those games
#at 100 reviews per file, and an avg of 70 KB per file, that's about...
# (3.6M) / (100) * (70KB) = 2.5 million KB, ie, 2.5 GB
#that'll be fine :]

#now, it's time to scrape some of the selected games
#the last page of reviews for a game will have [query_summary][num_reviews] = 0 and [reviews] = []

from collections import deque

# any_success = True
# while any_success:
#     any_success = False
#     print("restarting main loop")

#     #log last cursor for each game in a file and load it here
#     cursors: dict[int, str] = {id: None for id in applist}
#     with open("cursors.txt") as f:
#         for line in f:
#             id, cursor = [x.strip() for x in line.split()]
#             cursors[int(id)] = cursor

#     jobs: deque[tuple[int, Optional[str]]] = deque() #queue of (appid, cursor)

#     #initialize queue
#     for appid, cursor in cursors.items():
#         jobs.append((appid, cursor))

#     with open("cursors.txt", 'a') as f:
#         while len(jobs) > 0:
#             print("jobs:", len(jobs))

#             appid, cursor = jobs.popleft()
#             appid_ = str(appid)
#             #
#             result = get_reviews(appid_, cursor)
#             if result is None:
#                 print("got null result!", appid, cursor)
#                 continue

#             data, cursor2, rating = result
#             reviews = data['reviews']
#             # if len(reviews) > 0 or cursor2 != None:
#             if len(reviews) > 0:
#                 #this review actually has stuff
#                 any_success = True
#                 print(appid, cursor, data.keys())
#                 #dump the review data to a file
#                 if cursor is None:
#                     with open(os.path.join("reviews", "app_" + appid_ + "_initial.txt"), 'w') as f2:
#                         f2.write(json.dumps(data, indent=2))
#                 else:
#                     with open(os.path.join("reviews", "app_" + appid_ + "_" + ''.join([x for x in cursor if x.isalnum()]) + ".txt"), 'w') as f2:
#                         f2.write(json.dumps(data)) #dont waste all my storage, no indent
#                 #
#                 jobs.append((appid, cursor2))
#                 f.write(appid_ + ' ' + cursor2 + '\n')
#             else:
#                 print("done with", appid_, "?")
#                 print(json.dumps(data, indent=2))



#now re-read the review files, collect reviews for each app, and write out in one file each

# app_reviews: dict[int, list[object]] = {appid: [] for appid in applist}

# print("Loading reviews...")
# for fname in os.listdir('reviews'):
#     fpath = os.path.join('reviews', fname)
#     _, appid, _ = os.path.splitext(fname)[0].split('_')
#     appid = int(appid)
#     #
#     # print(fname)
#     #
#     with open(fpath) as f:
#         data = f.read()
#         content = json.loads(data)

#         for item in content['reviews']:
#             app_reviews[appid].append(item)
# print(" done")

# print("Storing reviews...")
# total_reviews = 0
# for appid, reviews in app_reviews.items():
#     n_reviews = len(reviews)
#     total_reviews += n_reviews
#     print("app", appid, ":", n_reviews, "reviews")
#     fpath = os.path.join('reviews_collected', 'app_' + str(appid) + '.json')
#     with open(fpath, 'w') as f:
#         f.write(json.dumps(reviews))
# print(" done")
# print("Total reviews:", total_reviews)

for appid in applist:
    appid = str(appid)
    app_name, app_data = get_app_info(appid)
    with open('appdata/app_' + appid + '_info.json', 'w') as f:
        f.write(json.dumps(app_data))