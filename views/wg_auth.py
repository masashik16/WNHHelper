import asyncio
import os
import re

import requests
from dotenv import load_dotenv
from flask import Blueprint, request, redirect, session

import api
import db
from exception import FlaskCustomError
from openid_wargaming.authentication import Authentication
from openid_wargaming.verification import Verification

load_dotenv()
GUILD_ID = int(os.environ.get("GUILD_ID"))
SERVICE_PORT = int(os.environ.get("SERVICE_PORT"))
DOMAIN = os.environ.get("DOMAIN")

client_id = os.environ.get("DISCORD_CLIENT_ID")
client_secret = os.environ.get("DISCORD_CLIENT_SECRET")
GAS_KEY = os.environ.get("GAS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
loop = asyncio.get_event_loop()


def construct_blueprint(bot, loop):
    app_wg_auth = Blueprint("wg_auth", __name__, url_prefix="")

    @app_wg_auth.route("/wg_link", methods=["GET"])
    def wg_link():
        userinfo_json = callback(request.url)
        discord_id = userinfo_json["id"]
        session["discord_id"] = discord_id
        return_to = f"{DOMAIN}/wg_auth"
        auth = Authentication(return_to=return_to)
        url = asyncio.run_coroutine_threadsafe(auth.authenticate(f"https://wargaming.net/id/openid/"),
                                               loop).result()  # noqa
        return redirect(f"https://wargaming.net{url}")

    @app_wg_auth.route("/wg_auth", methods=["GET"])
    def wg_auth():
        """ASIAサーバーユーザーの認証"""
        openid_mode = request.args.get("openid.mode")
        discord_id_str = session.get("discord_id")
        if openid_mode is None:
            raise FlaskCustomError("エラー", ["エラーが発生しました。",
                                              "お手数ですが再度Discordからお試しください。"], "E10001")
        if openid_mode == "cancel":
            raise FlaskCustomError("認証エラー", ["認証がキャンセルされました。",
                                                  "お手数ですが再度Discordからお試しください。"], "E10002")
        if discord_id_str is None:
            raise FlaskCustomError("認証エラー", ["認証エラーが発生しました。",
                                                  "制限時間を超過したか、BOTの再起動等によりセッションが切断されました。",
                                                  "お手数ですが再度Discordからお試しください。"], "E10003")
        else:
            discord_id = int(discord_id_str)
            current_url = request.url
            regex = r"https://wargaming.net/id/([0-9]+)-(\w+)/"
            verify = Verification(current_url)
            identities = asyncio.run_coroutine_threadsafe(verify.verify(), loop).result()  # noqa
            if not identities:
                raise FlaskCustomError("アカウント認証エラー", ["エラーが発生しました。",
                                                                "お手数ですが再度Discordからお試しください。"], "E10004")
            match = re.search(regex, identities["identity"])
            account_id = match.group(1)
            nickname = match.group(2)
            return comp_auth(discord_id=discord_id, account_id=account_id, nickname=nickname)

    def comp_auth(discord_id: int, account_id: str, nickname: str) -> str:
        """ユーザーの認証"""
        # 認証済みロールの付与
        session.pop("discord_id", None)
        region = asyncio.run_coroutine_threadsafe(api.wows_account_search(account_id, nickname),
                                                  loop).result()  # noqa
        if region == "ERROR":
            raise FlaskCustomError("アカウント認証エラー", ["指定されたアカウントにはPC版WoWSのプレイ歴がありません。",
                                                            "お手数ですが指定したアカウントでPC版WoWSを1戦以上プレイしてから再度お試しください。"],
                                   "E10005")
        else:
            from cogs.auth import add_role_authed
            asyncio.run_coroutine_threadsafe(add_role_authed(bot, discord_id), loop)  # noqa
            # DBへの情報の登録
            asyncio.run_coroutine_threadsafe(db.add_user(discord_id, account_id, region), loop)  # noqa
            return (f"<h1 align=\"center\">以下のアカウントで認証が完了しました。</h1>"
                    f"<h2 align=\"center\">サーバー：{region} / IGN：{nickname}"
                    f"<br>上記のアカウントがメインアカウントではない場合や情報が異なる場合はお問い合わせください。"
                    f"<br>一致している場合はこの画面を閉じてください。</h2>")

    def callback(url):
        callback_url = DOMAIN + request.path
        authorization_code = request.args.get("code")

        request_postdata = {"client_id": client_id, "client_secret": client_secret, "grant_type": "authorization_code",
                            "code": authorization_code, "redirect_uri": callback_url}
        accesstoken_request = requests.post("https://discord.com/api/oauth2/token", data=request_postdata)
        response_json = accesstoken_request.json()
        access_token = response_json.get("access_token")
        if access_token is None:
            raise FlaskCustomError("エラー", ["エラーが発生しました。", "お手数ですが再度Discordからお試しください。"],
                                   "E20001")
        # token_type = response_json["token_type"]
        # expires_in = response_json["expires_in"]
        # refresh_token = response_json["refresh_token"]
        # scope = response_json["scope"]
        headers = {"Authorization": f"Bearer {access_token}"}
        if request.path == "/wg_link":
            userinfo_request = requests.get("https://discord.com/api/users/@me", headers=headers)
        elif request.path == "/clan_edit":
            userinfo_request = requests.get(f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member",
                                            headers=headers)
        userinfo_json = userinfo_request.json()  # noqa
        # discord_id = userinfo_json["id"]
        # discord_username = userinfo_json["username"]
        return userinfo_json

    return app_wg_auth
