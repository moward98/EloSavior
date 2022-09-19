from array import array
from asyncio.windows_events import NULL
from time import sleep
from venv import create
import aiohttp
from aiohttp import ClientSession
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import requests
from .models import Summoner
from timeit import default_timer as timer
import asyncio
from ratelimit import limits, sleep_and_retry

from rest_framework import viewsets

from .serializers import PlayerSerializer

# Create your views here.

class TempSummoner():
    def __init__(self, summoner_data):
        self.name = summoner_data['name']
        self.summoner_id = summoner_data['summoner_id']
        self.puuid = summoner_data['puuid']
        self.level = summoner_data['level']
        self.tier = summoner_data['tier']
        self.rank = summoner_data['rank']
        self.lp = summoner_data['lp']
        self.hotstreak = summoner_data['hotstreak']
        self.divinity = summoner_data['divinity']

    def __str__(self):
        return self.name

# API Authentication
auth_token = 'api_key=RGAPI-f980e60c-ed9a-4821-94ec-851333b63e62'

# API Call Urls
summoner_by_name_url = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
summoner_stats_url = 'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/'
match_history_ids_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'
match_details_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/' 

allowed_ranks_dict = {
    "IRON"     : ["IRON", "BRONZE", "SILVER"], 
    "BRONZE"   : ["IRON", "BRONZE", "SILVER"], 
    "SILVER"   : ["IRON", "BRONZE", "SILVER", "GOLD"], 
    "GOLD"     : ["SILVER", "GOLD", "PLATINUM"],
    "PLATINUM" : ["GOLD", "PLATINUM", "DIAMOND"], 
    "DIAMOND"  : ["PLATINUM", "DIAMOND"]
    }

tiers_list = ["I", "II", "III", "IV"]

# 100 calls per 2 minutes
M_CALLS = 100
M_RATE_LIMIT = 120

@sleep_and_retry
@limits(calls=M_CALLS, period=M_RATE_LIMIT)
def check_minutes_limit():
    ''' Empty function just to check for calls to API '''
    return

# 20 calls per second
S_CALLS = 20
S_RATE_LIMIT = 1

@sleep_and_retry
@limits(calls=S_CALLS, period=S_RATE_LIMIT)
def check_seconds_limit():
    #check_minutes_limit()
    return


def save_summoner(name):

    # games_played = summoner_stats['wins'] + summoner_stats['losses']
    # winrate = (summoner_stats['wins']/games_played) * 100

    # if games_played<20:
    #     divinity=NULL
    # elif winrate>55:
    #     divinity=True
    # else:
        # divinity=False

    Summoner.objects.update_or_create(
        name = name
        #name = summoner_info['name'],
        # level = summoner_info['summonerLevel'],
        # puuid = summoner_info['puuid'],
        # summoner_id = summoner_info['id'],
        # tier = summoner_stats['tier'],
        # rank = summoner_stats['rank'],
        # lp = summoner_stats['lp'],
        # hotstreak = summoner_stats['hotstreak'],
        # divinity=divinity
    )


def create_summoner(summoner_info, summoner_stats):

    games_played = summoner_stats['wins'] + summoner_stats['losses']
    winrate = (summoner_stats['wins']/games_played) * 100

    if games_played<20:
        divinity=NULL
    elif winrate>55:
        divinity=True
    else:
        divinity=False

    return(TempSummoner(
            summoner_data = {
                'name'          : summoner_info['name'],
                'level'         : summoner_info['summonerLevel'],
                'puuid'         : summoner_info['puuid'],
                'summoner_id'   : summoner_info['id'],
                'tier'          : summoner_stats['tier'],
                'rank'          : summoner_stats['rank'],
                'lp'            : summoner_stats['lp'],
                'hotstreak'     : summoner_stats['hotstreak'],
                'divinity'      : divinity
            }))


def get_summoner_stats(summoner_id, base_url=summoner_stats_url, token=auth_token):
    check_seconds_limit()
    response = requests.get(f'{base_url}{summoner_id}?{token}')
    if response.status_code == 200:
        summoner_stats = response.json()
        for match_type in summoner_stats:
            if match_type['queueType'] == "RANKED_SOLO_5x5":
                return ({
                    'tier'  : match_type['tier'],
                    'rank'  : match_type['rank'],
                    'wins'  : match_type['wins'],
                    'losses': match_type['losses'],
                    'lp'    : match_type['leaguePoints'],
                    'hotstreak' : match_type['hotStreak']
                })
    elif response.status_code == 429:
        print("call too fast")
        sleep(1)
        return get_summoner_stats(summoner_id)    

    else:
        return 0
    

def calc_eligible_ranks(summoner_name: str, ranks_dict=allowed_ranks_dict, tiers_list=tiers_list) -> list:
#     summoner = Summoner.objects.get(name=summoner_name)

#     elig_ranks = ranks_dict[summoner.rank]

#     if summoner.rank=="PLATINUM":

#     elif
#     else:
#         elig_tiers = tiers_list

#     return elig_ranks
    pass


async def get_eligible_participants(session, match_id: str, main_summoner: object, potential_players: array, base_url=match_details_url, token=auth_token) -> array:
    check_seconds_limit()
    
    player_list = []
    eligible_players = []

    #eligible_ranks = calc_eligible_ranks(summoner_name)


    async with session.get(f'{base_url}{match_id}?{token}') as response:
        match_details = await response.json()

        for player in match_details["info"]['participants']: 
            if player['summonerName'] != main_summoner.name:
                if player['deaths'] == 0:
                    kda = (player['kills']+player['assists'])
                else:
                    kda = (player['kills']+player['assists']) / player['deaths']

                if kda>2.3:
                    player_list.append(player['summonerName']) 

        tasks = []
        for player in player_list:
            tasks.append(asyncio.ensure_future(async_get_summoner_info(session, main_summoner, player, eligible_players, potential_players)))

        await asyncio.gather(*tasks)

            # if created:
                # player = potential_players[-1]

                # if player.divinity is not NULL and player.divinity is not main_summoner.divinity:
                #     eligible_players.append(player.name)

        return eligible_players


def get_summoner_match_history(summoner_puuid: str, base_url=match_history_ids_url, type='ranked', start='0', count='5', token=auth_token) -> array:
    check_seconds_limit()
    response = requests.get(f'{base_url}{summoner_puuid}/ids?type={type}&start={start}&count={count}&{token}')
    match_id_list = response.json()

    return match_id_list


async def async_get_summoner_info(session, main_summoner: str, summoner_name: str, eligible_players: array, potential_players: array, base_url=summoner_by_name_url, token=auth_token): 
    check_seconds_limit()
    async with session.get(f'{base_url}{summoner_name}?{token}') as resp:
        if resp.status == 200:
            summoner_info = await resp.json()
            summoner_stats = get_summoner_stats(summoner_info['id'])
            if summoner_stats != 0:
                if summoner_name not in potential_players:
                    potential_player = create_summoner(summoner_info, summoner_stats)

                    if potential_player.divinity is not NULL and potential_player.divinity is not main_summoner.divinity:
                        eligible_players.append(potential_player.name)


def get_summoner_info(summoner_name: str, potential_players: array, base_url=summoner_by_name_url, token=auth_token):    
    check_seconds_limit()
    response = requests.get(f'{base_url}{summoner_name}?{token}')
    if response.status_code == 200:
        summoner_info = response.json()
        summoner_stats = get_summoner_stats(summoner_info['id'])
        if summoner_stats != 0:
            if summoner_name not in potential_players:
                potential_players.append(create_summoner(summoner_info, summoner_stats))


async def main(matches, main_summoner, potential_players):

    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for match in matches:
            tasks.append(asyncio.ensure_future(get_eligible_participants(session, match, main_summoner, potential_players)))
        player_suggestions = await asyncio.gather(*tasks)
        return player_suggestions


def resp(request: HttpRequest, summoner_name: str, base_url=summoner_by_name_url, token=auth_token) -> HttpResponse:
    start = timer()
    potential_players = []
    
    # Create Summoner that made request on site
    get_summoner_info(summoner_name, potential_players)  
    
    main_summoner = potential_players[0]
    matches = get_summoner_match_history(main_summoner.puuid)
    player_suggestions = asyncio.run(main(matches, main_summoner, potential_players))
    for player in player_suggestions:
        save_summoner(player)
    end = timer() - start
    return render(request, 'simple.html', {"suggestions" : player_suggestions})


class PlayerViewSet(viewsets.ModelViewSet):
    potential_players = []
    player_list = []
    summoner_name = 'xDIDLOxDANESx'
    
    # Create Summoner that made request on site
    get_summoner_info(summoner_name, potential_players)  
    
    main_summoner = potential_players[0]
    matches = get_summoner_match_history(main_summoner.puuid)
    player_suggestions = asyncio.run(main(matches, main_summoner, potential_players))

    for match_players in player_suggestions:
        for player in match_players:
            save_summoner(player)
            player_list.append(player)

    queryset = Summoner.objects.filter(name__in=player_list)
    serializer_class = PlayerSerializer


