import os
import requests
import json
from time import sleep
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
RETRY_SLEEP_SECONDS = 30

PLATFORM = "euw1"
REGION = "europe"
PLATFORM_BASE_URL = f"https://{PLATFORM}.api.riotgames.com/lol"
REGION_BASE_URL = f"https://{REGION}.api.riotgames.com/lol"
endpoints = {
    "league": f"{PLATFORM_BASE_URL}/league/v4/entries", # /{queue}/{tier}/{rank}?page={page_number}
    "puuid": f"{PLATFORM_BASE_URL}/summoner/v4/summoners", # /{summonerId}
    "match_ids": f"{REGION_BASE_URL}/match/v5/matches/by-puuid", # /{puid}/ids?start={index_by_most_recent}&count={number_of_games}
    "match_stats": f"{REGION_BASE_URL}/match/v5/matches" # /{match_id}
}
headers = {"X-Riot-Token": RIOT_API_KEY}

queues = ["RANKED_SOLO_5x5"]
tiers = ["DIAMOND", "EMERALD", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
ranks = ["I", "II", "III", "IV"]

games_per_player = 10
players_stats_list = []

output_file_name = "matches_data"

# Make a request to the url passed by parameter with the headers also passed by parameter. 
# If the server returns a status code 429 (Rate Limit Exceeded), the request is retried after RETRY_SLEEP_SECONDS seconds.
def make_request(url, headers):
    while True:
        try:
            response = requests.get(url, headers = headers)
            
            if response.status_code == 429:
                print(f"Rate Limit Exceeded. Retrying after {RETRY_SLEEP_SECONDS} seconds...")
                sleep(RETRY_SLEEP_SECONDS)
                continue
            elif response.status_code == 200:
                return response
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
            
        except Exception as e:
            print(f"Error: {e}")
            return None

def get_tier_rank_combination(tier, rank):
    return (tiers.index(tier) * 4) + (ranks.index(rank) + 1)

def extract_player_stats(tier, rank, puuid, match_data):
    filtered_player_data = {}

    # Find the index of the player's puuid in the match data
    player_index = match_data["metadata"]["participants"].index(puuid)
    print(f"player index: {player_index}")
    # Get players data
    player_data = match_data["info"]["participants"][player_index]

    # Find the index of the player's team
    team_index = None
    for index, team in enumerate(match_data["info"]["teams"]):
        if team["teamId"] == player_data["teamId"]:
            team_index = index
            break

    # Sometimes riot 

    print(f"team index: {team_index}")
    print("")
    # Get player's team data
    team_data = match_data["info"]["teams"][team_index]

    # Get tier/rank combination
    tier_rank = get_tier_rank_combination(tier, rank)

    # Filter the data we want to save
    filtered_player_data = {
        # Player-related data
        "tier_rank": tier_rank,
        "kills": player_data["kills"],
        "deaths": player_data["deaths"],
        "assists": player_data["assists"],
        "killingsprees": player_data["killingSprees"],
        "champExperience": player_data["champExperience"],
        "totalDamageDealth": player_data["totalDamageDealt"],
        "totalDamageTaken": player_data["totalDamageTaken"],
        "totalMinionsKilled": player_data["totalMinionsKilled"],
        "turretTakedown": player_data["turretTakedowns"],
        "visionScore": player_data["visionScore"],

        # Team-related data
        "dragonTakedowns": team_data["objectives"]["dragon"]["kills"],
        "riftHeraldTakedowns": team_data["objectives"]["riftHerald"]["kills"],
        "baronTakedowns": team_data["objectives"]["baron"]["kills"],
        "towerTakedowns": team_data["objectives"]["tower"]["kills"],

        # Game-related data
        "gameDuration": match_data["info"]["gameDuration"]
    }

    return filtered_player_data

for queue in queues:
    for tier in tiers:
        for rank in ranks:
            print(f"Fetching data from {tier} {rank}...")
            # Get some players from each tier/rank
            url = f"{endpoints['league']}/{queue}/{tier}/{rank}?page=1"
            response = make_request(url, headers)

            if response:
                leagueEntryDTO_set = response.json()

                # Get PUUID from summonerId
                for leagueEntryDTO in leagueEntryDTO_set:
                    summoner_id = leagueEntryDTO.get("summonerId")
                    url = f"{endpoints['puuid']}/{summoner_id}"
                    response = make_request(url, headers)

                    if response:
                        summonerDTO = response.json()
                        puuid = summonerDTO.get("puuid")

                        # Get last games of each player
                        url = f"{endpoints['match_ids']}/{puuid}/ids?start=0&count={games_per_player}"
                        response = make_request(url, headers)
                            
                        if response:
                            matchIDs = response.json()

                            # Get stats from every game
                            for matchID in matchIDs:
                                url = f"{endpoints['match_stats']}/{matchID}"
                                response = make_request(url, headers)

                                if response:
                                    match_data = response.json()

                                    # Since there is not an endpoint for retrieving just Ranked Solo 5v5 games,
                                    # get stats only from games that have queueId = 420 (Ranked Solo 5v5)
                                    if match_data["info"]["queueId"] != 420: 
                                        continue

                                    print(f"match_id: {matchID}")
                                    player_tier = leagueEntryDTO["tier"]
                                    player_rank = leagueEntryDTO["rank"]
                                    player_stats = extract_player_stats(player_tier, player_rank, puuid, match_data)

                                    players_stats_list.append(player_stats)

print(f"Done. Total saved games: {len(players_stats_list)}")

# Save result into a json file
try:
    with open(f"{output_file_name}.json", 'w') as json_file:
        json.dump(players_stats_list, json_file, indent = 4)
except Exception as e:
    print(f"Error writing to file: {e}")
