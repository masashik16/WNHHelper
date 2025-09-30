import asyncio
import re

from authlib.integrations.requests_client import OAuth2Session
from flask import Blueprint, request, redirect, session

import api
import db
from constant import FLASK_DOMAIN, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET
from exception import FlaskCustomError
from openid_wargaming.authentication import Authentication
from openid_wargaming.verification import Verification

loop = asyncio.get_event_loop()


def construct_blueprint(bot, loop):
    app_wg_auth = Blueprint("wg_auth", __name__, url_prefix="")

    @app_wg_auth.route("/wg_link", methods=["GET"])
    def wg_link():
        redirect_uri = FLASK_DOMAIN + request.path
        state = request.args.get("state")
        discord_std = OAuth2Session(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, state=state, redirect_uri=redirect_uri)
        token = discord_std.fetch_token("https://discord.com/api/oauth2/token", authorization_response=request.url)
        access_token = token.get("access_token")
        if access_token is None:
            raise FlaskCustomError("エラー", ["エラーが発生しました。", "お手数ですが再度Discordからお試しください。"],
                                   "E20001", 500)
        userinfo_request = discord_std.get(f"https://discord.com/api/users/@me")
        userinfo_json = userinfo_request.json()
        discord_id = userinfo_json["id"]
        session["discord_id"] = discord_id
        return_to = f"{FLASK_DOMAIN}/wg_auth"
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
                                              "お手数ですが再度Discordからお試しください。"], "E10001", 400)
        if openid_mode == "cancel":
            raise FlaskCustomError("認証エラー", ["認証がキャンセルされました。",
                                                  "お手数ですが再度Discordからお試しください。"], "E10002", 200)
        if discord_id_str is None:
            raise FlaskCustomError("認証エラー", ["認証エラーが発生しました。",
                                                  "制限時間を超過したか、BOTの再起動等によりセッションが切断されました。",
                                                  "お手数ですが再度Discordからお試しください。"], "E10003", 500)
        else:
            discord_id = int(discord_id_str)
            current_url = request.url
            regex = r"https://wargaming.net/id/([0-9]+)-(\w+)/"
            verify = Verification(current_url)
            identities = asyncio.run_coroutine_threadsafe(verify.verify(), loop).result()  # noqa
            if not identities:
                raise FlaskCustomError("アカウント認証エラー", ["エラーが発生しました。",
                                                                "お手数ですが再度Discordからお試しください。"], "E10004",
                                       500)
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
                                   "E10005", 200)
        else:
            from cogs.auth import add_role_authed
            asyncio.run_coroutine_threadsafe(add_role_authed(bot, discord_id), loop)  # noqa
            # DBへの情報の登録
            asyncio.run_coroutine_threadsafe(db.add_user(discord_id, account_id, region), loop)  # noqa
            return (f"<h1 align=\"center\">以下のアカウントで認証が完了しました。</h1>"
                    f"<h2 align=\"center\">サーバー：{region} / IGN：{nickname}"
                    f"<br>上記のアカウントがメインアカウントではない場合や情報が異なる場合はお問い合わせください。"
                    f"<br>一致している場合はこの画面を閉じてください。</h2>")

    return app_wg_auth
