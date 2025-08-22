import json
import os

import requests
from dotenv import load_dotenv

from logs import logger

load_dotenv()
APPLICATION_ID = os.environ.get("APPLICATION_ID")
logger = logger.getChild("api")
region_list = ["ASIA", "EU", "NA"]
TLD = {"ASIA": "asia", "EU": "eu", "NA": "com"}

async def wows_user_clan(account_id):
    """WoWSクラン情報の取得"""
    url = f"https://api.worldofwarships.asia/wows/clans/accountinfo/"
    params = {"application_id": APPLICATION_ID, "account_id": account_id}
    res = requests.get(url, params=params)
    data = json.loads(res.text)
    clan = data["data"][f"{account_id}"]
    if clan is None:
        return "ERROR_ACCOUNT_NOT_FOUND"
    clan_id = clan["clan_id"]
    if clan_id is None:
        return "ERROR_NOT_JOINED_CLAN"
    return clan_id

async def wows_clan_search(clan_id):
    """WoWSクラン情報の取得"""
    url = f"https://api.worldofwarships.asia/wows/clans/info/"
    params = {"application_id": APPLICATION_ID, "clan_id": clan_id}
    res = requests.get(url, params=params)
    data = json.loads(res.text)
    clan = data["data"][f"{clan_id}"]
    if clan is None:
        return "ERROR"
    clan_tag = clan["tag"]
    clan_name = clan["name"]
    leader = clan["leader_name"]
    clan_dict = {"clan_id": clan_id, "clan_tag": clan_tag, "clan_name": clan_name, "leader": leader}
    return clan_dict


async def wows_account_search(account_id, nickname):
    """WoWS情報の取得"""
    for region in region_list:
        url = f"https://api.worldofwarships.{TLD[region]}/wows/account/list/"
        params = {"application_id": APPLICATION_ID, "search": nickname, "type": "exact"}
        res = requests.get(url, params=params)
        data = json.loads(res.text)
        if not data["data"]:
            continue
        return_account_id = str(data["data"][0]["account_id"])
        if return_account_id == account_id:
            return region
    else:
        return "ERROR"


async def wows_info(account_id, region):
    """WG APIの呼び出し"""
    url = f"https://api.worldofwarships.{TLD[region]}/wows/account/info/"
    params = {"application_id": APPLICATION_ID, "account_id": account_id,
              "fields": "account_id, hidden_profile, nickname, statistics.pvp.battles"}
    res = requests.get(url, params=params)
    data = json.loads(res.text)
    user = data["data"][account_id]
    if user is None:
        nickname = "ERROR"
        battles = "ERROR"
        return nickname, battles
    else:
        nickname = data["data"][account_id]["nickname"]
        private = data["data"][account_id]["hidden_profile"]
        if private is True:
            battles = "private"
            return nickname, battles
        else:
            battles = data["data"][account_id]["statistics"]["pvp"]["battles"]
            return nickname, battles
