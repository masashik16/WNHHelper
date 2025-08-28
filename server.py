import asyncio
import ipaddress
import logging
import os
import signal
import sys
from collections.abc import Awaitable, Callable, Coroutine
from datetime import timedelta

from cachelib.file import FileSystemCache
from dotenv import load_dotenv
from flask import abort, Flask, render_template, request
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig

from exception import FlaskCustomError
from flask_session import Session
from logs import logger, handler
from views.wg_auth import construct_blueprint as app_wg_auth

load_dotenv()
GUILD_ID = int(os.environ.get("GUILD_ID"))
SERVICE_PORT = int(os.environ.get("SERVICE_PORT"))
DOMAIN = os.environ.get("DOMAIN")
ENV = os.environ.get("ENV")
logger = logger.getChild("server")

client_id = os.environ.get("DISCORD_CLIENT_ID")
client_secret = os.environ.get("DISCORD_CLIENT_SECRET")
GAS_KEY = os.environ.get("GAS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
# Python 3.14以降でos.reload_environ()とともに変更
# DISALLOW_NETWORKS = os.environ.get("DISALLOW_NETWORKS").replace(" ", "").split(",")
DISALLOW_NETWORKS = ["91.238.180.0/23", "147.45.0.0/16", "206.168.32.0/22", "194.165.16.0/23", "88.214.24.0/22",
                     "88.214.24.0/22", "185.93.89.0/24", "195.178.110.0/24", "185.177.72.0/24"]

hypercorn_access_logger = logging.getLogger("server.access")
hypercorn_access_logger.addHandler(handler)
hypercorn_access_logger.setLevel(logging.INFO)
hypercorn_error_logger = logging.getLogger("server.error")
hypercorn_error_logger.addHandler(handler)
hypercorn_error_logger.setLevel(logging.ERROR)
shutdown_event = asyncio.Event()



class App(Flask):
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
        return serve(self, config, shutdown_trigger=shutdown_event.wait)


app = None
bot_obj = None
public_url = None
server_task = None
_app = App(__name__, static_url_path="/")
sess = Session()


def create_app(bot, loop) -> Flask:
    global public_url

    _app.config.from_mapping(
        BASE_URL=f"{DOMAIN}/",
        PREFERRED_URL_SCHEME="https",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=5),
        SECRET_KEY=SECRET_KEY,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_PERMANENT=False,
        SESSION_TYPE="cachelib",
        SESSION_CACHELIB=FileSystemCache(threshold=250, cache_dir="flask_session"),
    )
    public_url = f"{DOMAIN}/"
    _app.register_blueprint(app_wg_auth(bot, loop))
    sess.init_app(_app)
    return _app


def shutdown_server():
    print("サーバーをシャットダウンしています")
    shutdown_event.set()
    return


def signal_handler(_, __):
    shutdown_server()
    return


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if sys.platform == "win32":
    signal.signal(signal.SIGBREAK, signal_handler)
else:
    signal.signal(signal.SIGTRAP, signal_handler)


@_app.before_request
def before_request():
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
        remote_addr = ipaddress.ip_address(remote_addr)
    elif ENV == "prod":
        sparked_ip = ipaddress.ip_address("23.230.3.203")
        ip_address = ipaddress.ip_address(request.remote_addr)
        if not ip_address == sparked_ip:
            ip_network = ipaddress.ip_network(ip_address)
            hypercorn_access_logger.info(f"直IPでのアクセスを検知しました。アクセス元：{str(ip_network)}")
        raise FlaskCustomError("不正なアクセスを検知しました", ["直IPでのアクセスは許可されていません。",
                                                                "もしURLでのアクセスなのにこのエラーが表示されている場合、運営チームまでお問い合わせください。"],
                               "E40301", 403)
    else:
        remote_addr = request.remote_addr
        remote_addr = ipaddress.ip_address(remote_addr)
    for disallow_network in DISALLOW_NETWORKS:
        ip_network = ipaddress.ip_network(disallow_network)
        if remote_addr in ip_network:
            return abort(403, "許可されていないIPアドレスです。")
    return


@_app.route("/", methods=["GET"])
def default():
    return abort(403, "不正なアクセスです。")


@_app.errorhandler(500)
def error_500(error):
    """500エラーが発生した場合の処理"""
    return render_template('custom_error.html', error_title="エラー",
                           error_list=["エラーが発生しました", "お手数ですが再度お試しください"],
                           error_code="E500")


@_app.errorhandler(FlaskCustomError)
def handle_custom_error(e):
    return render_template('custom_error.html', error_title=e.error_title, error_list=e.error_list,
                           error_code=e.error_code), e.response_code


# 認証用リンクの生成
def wg_auth_link():
    """ASIAサーバー用認証リンクの生成"""
    callback_url = DOMAIN + f"/wg_link"
    login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify&redirect_uri=" + callback_url + "&prompt=consent"
    return login_url


def clan_auth_link():
    """ASIAサーバー用認証リンクの生成"""
    callback_url = DOMAIN + f"/clan_edit"
    login_url = "https://discord.com/api/oauth2/authorize?response_type=code&client_id=" + client_id + "&scope=identify+guilds.members.read&redirect_uri=" + callback_url + "&prompt=consent"
    return login_url


def run_server(bot, loop):
    """サーバーの起動"""
    global app
    global bot_obj
    global server_task
    bot_obj = bot

    app = create_app(bot, loop)
    ctx = app.app_context()
    ctx.push()
    print("サーバー起動中")
    server_task = loop.create_task(
        app.run_task(host="0.0.0.0", port=SERVICE_PORT, debug=False, shutdown_trigger=shutdown_event.wait))  # noqa
    return
