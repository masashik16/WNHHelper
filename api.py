from dotenv import load_dotenv
import json
import os
import requests
from logs import logger

load_dotenv()
APPLICATION_ID = os.environ.get("APPLICATION_ID")
logger = logger.getChild("api")
region_list = ["ASIA", "EU", "NA"]
TLD = {"ASIA": "asia", "EU": "eu", "NA": "com"}


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
