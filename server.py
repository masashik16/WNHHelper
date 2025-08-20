import asyncio
import ipaddress
import logging
import os
import re
import signal
import sys
from collections.abc import Awaitable, Callable, Coroutine
from datetime import datetime, timedelta

import pytz
import requests
from dotenv import load_dotenv
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig
from quart import abort, Quart, redirect, render_template, request, session

import api
import db
from logs import logger, handler
from openid_wargaming.authentication import Authentication
from openid_wargaming.verification import Verification

load_dotenv()
GUILD_ID = int(os.environ.get("GUILD_ID"))
SERVICE_PORT = int(os.environ.get("SERVICE_PORT"))
DOMAIN = os.environ.get("DOMAIN")
logger = logger.getChild("server")

client_id = os.environ.get("DISCORD_CLIENT_ID")
client_secret = os.environ.get("DISCORD_CLIENT_SECRET")
GAS_KEY = os.environ.get("GAS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

DISALLOW_NETWORKS = ["91.238.180.0/23", "147.45.0.0/16", "206.168.32.0/22", "194.165.16.0/23", "88.214.24.0/22",
                     "88.214.24.0/22"]

hypercorn_access_logger = logging.getLogger("server.access")
hypercorn_access_logger.addHandler(handler)
hypercorn_access_logger.setLevel(logging.INFO)
hypercorn_error_logger = logging.getLogger("server.error")
hypercorn_error_logger.addHandler(handler)
hypercorn_error_logger.setLevel(logging.ERROR)
shutdown_event = asyncio.Event()


class App(Quart):
    def run_task(
            self,
            host: str = "127.0.0.1",
            port: int = 5000,
            debug: bool | None = None,
            ca_certs: str | None = None,
            certfile: str | None = None,
            keyfile: str | None = None,
            shutdown_trigger: Callable[..., Awaitable[None]] | None = None,
    ) -> Coroutine[None, None, None]:
        config = HyperConfig()
        config.access_log_format = "%({X-Forwarded-For}i)s %(r)s %(s)s %(b)s %(D)s"
        config.accesslog = hypercorn_access_logger  # I modified this
        config.bind = [f"{host}:{port}"]
        config.ca_certs = ca_certs
        config.certfile = certfile
        if debug is not None:
            self.debug = debug
        config.errorlog = hypercorn_error_logger  # I modified this
        config.keyfile = keyfile
        config.use_reloader = True
        return serve(self, config, shutdown_trigger=shutdown_trigger)


app = None
bot_obj = None
public_url = None
_app = App(__name__)


def convert_timestamp(timestamp: int) -> str:
    """タイムゾーンを日本に変更"""

    timezone = pytz.timezone("Asia/Tokyo")
    dt_object = datetime.fromtimestamp(timestamp)
    jst_time = dt_object.astimezone(timezone)
    return jst_time.strftime("%Y/%m/%d %H:%M JST")


def create_app(port: int) -> Quart:
    global public_url

    _app.config.from_mapping(
        BASE_URL=f"{DOMAIN}/",
        PREFERRED_URL_SCHEME="https",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=5),
        SECRET_KEY=SECRET_KEY,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="None",
    )
    public_url = f"{DOMAIN}/"
    return _app


class CustomError(Exception):
    def __init__(self, error_title:str, error_list:list, error_code:str ):
        self.error_title = error_title
        self.error_list = error_list
        self.error_code = error_code


async def shutdown_server():
    shutdown_event.set()
    return


def signal_handler(_, __):
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(shutdown_server(), loop)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if sys.platform == "win32":
    signal.signal(signal.SIGBREAK, signal_handler)
else:
    signal.signal(signal.SIGTRAP, signal_handler)


@_app.before_request
async def before_request():
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
        remote_addr = ipaddress.ip_address(remote_addr)
    else:
        remote_addr = request.remote_addr
        remote_addr = ipaddress.ip_address(remote_addr)
    for disallow_network in DISALLOW_NETWORKS:
        ip_network = ipaddress.ip_network(disallow_network)
        if remote_addr in ip_network:
            return abort(403, "許可されていないIPアドレスです。")
    return


@_app.route("/wg_link", methods=["GET"])
async def wg_link():
    userinfo_json = await callback(request.url)
    discord_id = userinfo_json["id"]
    session["discord_id"] = discord_id
    return_to = f"{DOMAIN}/wg_auth"
    auth = Authentication(return_to=return_to)
    url = await auth.authenticate(f"https://wargaming.net/id/openid/")
    return redirect(f"https://wargaming.net{url}")


@_app.route("/wg_auth", methods=["GET"])
async def wg_auth():
    """ASIAサーバーユーザーの認証"""
    openid_mode = request.args.get("openid.mode")
    discord_id_str = session.get("discord_id")
    if openid_mode is None:
        raise CustomError("エラー", ["エラーが発生しました。",
                          "お手数ですが再度Discordからお試しください。"], "E10001")
    if openid_mode == "cancel":
        raise CustomError("認証エラー", ["認証がキャンセルされました。",
                          "お手数ですが再度Discordからお試しください。"], "E10002")
    if discord_id_str is None:
        raise CustomError("認証エラー", ["認証エラーが発生しました。",
                          "制限時間を超過したか、BOTの再起動等によりセッションが切断されました。",
                          "お手数ですが再度Discordからお試しください。"], "E10003")
    else:
        discord_id = int(discord_id_str)
        current_url = request.url
        regex = r"https://wargaming.net/id/([0-9]+)-(\w+)/"
        verify = Verification(current_url)
        identities = await verify.verify()
        if not identities:
            raise CustomError("アカウント認証エラー", ["エラーが発生しました。",
                              "お手数ですが再度Discordからお試しください。"], "E10004")
        match = re.search(regex, identities["identity"])
        account_id = match.group(1)
        nickname = match.group(2)
        return await comp_auth(discord_id=discord_id, account_id=account_id, nickname=nickname)


async def comp_auth(discord_id: int, account_id: str, nickname: str) -> str:
    """ユーザーの認証"""
    # 認証済みロールの付与
    session.pop("discord_id", None)
    region = await api.wows_account_search(account_id, nickname)
    if region == "ERROR":
        raise CustomError("アカウント認証エラー", ["指定されたアカウントにはPC版WoWSのプレイ歴がありません。",
                          "お手数ですが指定したアカウントでPC版WoWSを1戦以上プレイしてから再度お試しください。"], "E10005")
    else:
        from cogs.auth import add_role_authed
        asyncio.run_coroutine_threadsafe(add_role_authed(bot_obj, discord_id), bot_obj.loop)
        # DBへの情報の登録
        await db.add_user(discord_id, account_id, region)
        return (f"<h1 align=\"center\">以下のアカウントで認証が完了しました。</h1>"
                f"<h2 align=\"center\">サーバー：{region} / IGN：{nickname}"
                f"<br>上記のアカウントがメインアカウントではない場合や情報が異なる場合はお問い合わせください。"
                f"<br>一致している場合はこの画面を閉じてください。</h2>")


@_app.route("/", methods=["GET"])
async def default():
    return f"<h1 align=\"center\">不正なアクセスです。</h1>"


# async def form_link_entry():
#     """ASIAサーバー用認証リンクの生成"""
#     callback_url = DOMAIN + "/5thcup_entry/"
#     login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify&redirect_uri=" + callback_url + "&prompt=consent"
#
#     return login_url
#
#
# async def form_link_cancel():
#     """ASIAサーバー用認証リンクの生成"""
#     callback_url = DOMAIN + "/5thcup_cancel/"
#     login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify&redirect_uri=" + callback_url + "&prompt=consent"
#     return login_url


# @_app.route("/5thcup_entry/")
# async def form_entry():
#     userinfo_json = await callback(request.url)
#     discord_id = userinfo_json["id"]
#     discord_username = userinfo_json["username"]
#     user_info_result = await db.search_user(discord_id)
#     discord_id, account_id, region = user_info_result
#     # 戦闘数の照会と代入
#     wg_api_result = await api.wows_info(account_id, region)
#     nickname, battles = wg_api_result
#     from cogs.auth import check_authed
#     task = asyncio.run_coroutine_threadsafe(check_authed(bot_obj, discord_id), bot_obj.loop)
#     if task.result() is True:
#         logger.info(
#             f"{discord_username}（UID：{discord_id}）がコマンド「5thcup_entry」を表示しました。")
#         return render_template("5thcup_entry.html", discord_id=discord_id, discord_username=discord_username,
#                                ign=nickname)
#     else:
#         return f"<h1 align=\"center\">このページを表示するには、WNHの参加手続きを完了している必要があります。</h1>"
#
#
# @_app.route("/5thcup_cancel/")
# async def form_cancel():
#     userinfo_json = await callback(request.url)
#     discord_id = userinfo_json["id"]
#     discord_username = userinfo_json["username"]
#     user_info_result = await db.search_user(discord_id)
#     discord_id, account_id, region = user_info_result
#     # 戦闘数の照会と代入
#     wg_api_result = await api.wows_info(account_id, region)
#     nickname, battles = wg_api_result
#     from cogs.auth import check_authed
#     task = asyncio.run_coroutine_threadsafe(check_authed(bot_obj, discord_id), bot_obj.loop)
#     if task.result() is True:
#         return render_template("5thcup_cancel.html", discord_id=discord_id, discord_username=discord_username,
#                                ign=nickname)
#     else:
#         return f"<h1 align=\"center\">このページを表示するには、WNHの参加手続きを完了している必要があります。</h1>"
#
#
# @_app.route("/thanks/")
# async def get_form():
#     return f"<h1 align=\"center\">フォームを送信しました。\nDMに完了通知が届いていない場合、正常に送信できていないため、再度送信してください。</h1>"
#
#
# @_app.route("/5thcup_gas/")
# async def form_gas_5thcup():
#     key = request.args.get("key")
#     discord_id = request.args.get("discord_id", 1)
#     types = request.args.get("type")
#     discord_id = int(discord_id)
#     if key is None:
#         return f"<h1 align=\"center\">ERROR</h1>"
#     elif key != GAS_KEY:
#         return f"<h1 align=\"center\">ERROR</h1>"
#     else:
#         from cogs.cmd2 import send_dm_gas_5thcup
#         task = asyncio.run_coroutine_threadsafe(send_dm_gas_5thcup(bot_obj, discord_id, types), bot_obj.loop)
#         print(task.result())
#         return f"<h1 align=\"center\">OK</h1>"

# #
# @_app.route('/cause_custom_error')
# def cause_custom_error():
#     raise CustomError("認証エラー", "認証時にエラーが発生しました。",
#                       "お手数ですがエラーコードを添えて運営チームにご連絡ください。", "エラーコード：E30001")


@_app.errorhandler(500)
async def error_500(error):
    """500エラーが発生した場合の処理"""
    return await render_template('custom_error.html', error_title="エラー", error_list=["エラーが発生しました", "お手数ですが再度お試しください"],error_code="E500" )


@_app.errorhandler(CustomError)
async def handle_custom_error(e):
    return await render_template('custom_error.html', error_title=e.error_title, error_list=e.error_list, error_code=e.error_code), 500


# 認証用リンクの生成
async def wg_auth_link():
    """ASIAサーバー用認証リンクの生成"""
    callback_url = DOMAIN + f"/wg_link"
    login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify&redirect_uri=" + callback_url + "&prompt=consent"
    return login_url


async def clan_auth_link():
    """ASIAサーバー用認証リンクの生成"""
    callback_url = DOMAIN + f"/clan_edit"
    login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify+guilds.members.read&redirect_uri=" + callback_url + "&prompt=consent"
    return login_url


async def callback(url):
    callback_url = DOMAIN + request.path
    authorization_code = request.args.get("code")

    request_postdata = {"client_id": client_id, "client_secret": client_secret, "grant_type": "authorization_code",
                        "code": authorization_code, "redirect_uri": callback_url}
    accesstoken_request = requests.post("https://discord.com/api/oauth2/token", data=request_postdata)
    response_json = accesstoken_request.json()
    access_token = response_json.get("access_token")
    if access_token is None:
        raise CustomError("エラー", ["エラーが発生しました。", "お手数ですが再度Discordからお試しください。"], "E20001")
    # token_type = response_json["token_type"]
    # expires_in = response_json["expires_in"]
    # refresh_token = response_json["refresh_token"]
    # scope = response_json["scope"]
    headers = {"Authorization": f"Bearer {access_token}"}
    if request.path == "/wg_link":
        userinfo_request = requests.get("https://discord.com/api/users/@me", headers=headers)
    elif request.path == "/clan_edit":
        userinfo_request = requests.get(f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member", headers=headers)
    userinfo_json = userinfo_request.json()  # noqa
    # discord_id = userinfo_json["id"]
    # discord_username = userinfo_json["username"]
    return userinfo_json


async def run_server(bot, loop) -> None:
    """サーバーの起動"""
    global app
    global bot_obj
    bot_obj = bot

    app = create_app(SERVICE_PORT)
    ctx = app.app_context()
    loop.create_task(ctx.push())
    loop.create_task(
        app.run_task(host="0.0.0.0", port=SERVICE_PORT, debug=False, shutdown_trigger=shutdown_event.wait))  # noqa
    return
