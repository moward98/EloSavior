from asyncio.windows_events import NULL
from venv import create
import winsound
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import requests
from .models import Summoner
from timeit import default_timer as timer

# Create your views here.

# API Authentication
auth_token = 'api_key=RGAPI-e2441bcd-8778-484c-a888-41a8b9cef2da'

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

def create_summoner(summoner_info, summoner_stats):

    games_played = summoner_stats['wins'] + summoner_stats['losses']
    winrate = (summoner_stats['wins']/games_played) * 100

    if games_played<20:
        divinity=NULL
    elif winrate>55:
        divinity=True
    else:
        divinity=False

    Summoner.objects.update_or_create(
        name = summoner_info['name'],
        level = summoner_info['summonerLevel'],
        puuid = summoner_info['puuid'],
        summoner_id = summoner_info['id'],
        tier = summoner_stats['tier'],
        rank = summoner_stats['rank'],
        lp = summoner_stats['lp'],
        hotstreak = summoner_stats['hotstreak'],
        divinity=divinity
    )


def get_summoner_stats(summoner_id, base_url=summoner_stats_url, token=auth_token):
    response = requests.get(f'{base_url}{summoner_id}?{token}')

    summoner_stats = response.json()
    if summoner_stats:
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
    else:
        return 0
    

# def calc_eligible_ranks(summoner_name: str, ranks_dict=allowed_ranks_dict, tiers_list=tiers_list) -> list:

#     summoner = Summoner.objects.get(name=summoner_name)

#     elig_ranks = ranks_dict[summoner.rank]

#     if summoner.rank=="PLATINUM":

#     elif
#     else:
#         elig_tiers = tiers_list

#     return elig_ranks

def get_eligible_participants(match_id_list: list, summoner_name: str, base_url=match_details_url, token=auth_token) -> list:
    
    player_list = []
    eligible_players = []

    summoner = Summoner.objects.get(name=summoner_name)

    #eligible_ranks = calc_eligible_ranks(summoner_name)

    for match_id in match_id_list:
        response = requests.get(f'{base_url}{match_id}?{token}')
        
        match_details = response.json()

        for player in match_details["info"]['participants']: 
            if player['summonerName'] != summoner_name:
                if player['deaths'] == 0:
                    kda = (player['kills']+player['assists'])
                else:
                    kda = (player['kills']+player['assists']) / player['deaths']

                if kda>2.3:
                    player_list.append(player['summonerName']) 

    for player_name in player_list:
        created = get_create_summoner_info(player_name)
        if created:
            player = Summoner.objects.get(name=player_name)

            if player.divinity is not NULL and player.divinity is not summoner.divinity:
                eligible_players.append(player.name)

    return eligible_players


def get_summoner_match_history(summoner_name: str, base_url=match_history_ids_url, type='ranked', start='0', count='2', token=auth_token) -> list:
    summoner = Summoner.objects.get(name=summoner_name)
    
    response = requests.get(f'{base_url}{summoner.puuid}/ids?type={type}&start={start}&count={count}&{token}')
    match_id_list = response.json()

    return match_id_list


def get_create_summoner_info(summoner_name: str, base_url=summoner_by_name_url, token=auth_token):
    response = requests.get(f'{base_url}{summoner_name}?{token}')
    if response.status_code == 200:
        summoner_info = response.json()
        summoner_stats = get_summoner_stats(summoner_info['id'])
        if summoner_stats != 0:
            create_summoner(summoner_info, summoner_stats)
            return 1
    else: 
        return 0


def resp(request: HttpRequest, summoner_name: str, base_url=summoner_by_name_url, token=auth_token) -> HttpResponse:
    start = timer()
    player_return_dict = {}
    
    # Create Summoner that made request on site
    get_create_summoner_info(summoner_name)  
    
    matches = get_summoner_match_history(summoner_name)

    player_suggestions = get_eligible_participants(matches, summoner_name)        
    end = timer()
    print(f"Time Elapsed: {end - start}")
    return render(request, 'simple.html', {"suggestions" : player_suggestions})