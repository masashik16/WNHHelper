import os

from dotenv import load_dotenv

"""コピー用
from constant import GUILD_ID, ROLE_ID_ADMIN, ROLE_ID_WNH_STAFF, ROLE_ID_SENIOR_MOD, ROLE_ID_MOD, \
    ROLE_ID_CLAN_RECRUITER, ROLE_ID_WAIT_AGREE_RULE, ROLE_ID_WAIT_AUTH, ROLE_ID_AUTHED, ROLE_ID_MATTARI, ROLE_ID_GATSU, ROLE_ID_DIVISION, CHANNEL_ID_RULE, \
    CHANNEL_ID_DIVISION, CHANNEL_ID_MOD_CASE, CHANNEL_ID_MOD_LOG, CHANNEL_ID_MOD_CONTACT_LOG, CHANNEL_ID_REPORT_LOG, CHANNEL_ID_MESSAGE_LOG, CHANNEL_ID_USER_LOG, THREAD_ID_EVENT1, \
    THREAD_ID_EVENT2, CHANNEL_ID_OPINION_LOG, GENERAL_INQUIRY_OPEN, GENERAL_INQUIRY_CLOSE, GENERAL_INQUIRY_LOG, GENERAL_INQUIRY_SAVE, REPORT_OPEN, REPORT_CLOSE, REPORT_LOG, REPORT_SAVE, \
    CLAN_OPEN, CLAN_CLOSE, CLAN_LOG, CLAN_SAVE, CLAN_STAFF_ROLE, CLAN_MEET_ID, DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME, FLASK_SERVICE_PORT, FLASK_DOMAIN, WARGAMING_APPLICATION_ID, \
    DISCORD_TOKEN, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, ENV, COLOR_OK, COLOR_ERROR, COLOR_WARN
"""

load_dotenv()
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)


# サーバーID
GUILD_ID = int(os.environ.get("GUILD_ID"))
# 管理者ロール
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
# スタッフロール
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
# 上級モデレーターロール
ROLE_ID_SENIOR_MOD = int(os.environ.get("ROLE_ID_SENIOR_MOD"))
# モデレーターロール
ROLE_ID_MOD = int(os.environ.get("ROLE_ID_MOD"))
# 公認クランリクルーターロール
ROLE_ID_CLAN_RECRUITER = int(os.environ.get("ROLE_ID_CLAN_RECRUITER"))
# ルール同意前ロール
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
# ルール同意後ロール
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
# 認証済みロール
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
# まったりロール
ROLE_ID_MATTARI = int(os.environ.get("ROLE_ID_MATTARI"))
# がつがつロール
ROLE_ID_GATSU = int(os.environ.get("ROLE_ID_GATSU"))
# 分隊ロール
ROLE_ID_DIVISION = int(os.environ.get("ROLE_ID_DIVISION"))


# ルールCH
CHANNEL_ID_RULE = int(os.environ.get("CHANNEL_ID_RULE"))
# 分隊募集CH
CHANNEL_ID_DIVISION = int(os.environ.get("CHANNEL_ID_DIVISION"))
# モデレーション記録CH
CHANNEL_ID_MOD_CASE = int(os.environ.get("CHANNEL_ID_MOD_CASE"))
# モデレーションログCH
CHANNEL_ID_MOD_LOG = int(os.environ.get("CHANNEL_ID_MOD_LOG"))
# 処罰に対する意見等CH
CHANNEL_ID_MOD_CONTACT_LOG = int(os.environ.get("CHANNEL_ID_MOD_CONTACT_LOG"))
# 報告受付CH
CHANNEL_ID_REPORT_LOG = int(os.environ.get("CHANNEL_ID_REPORT_LOG"))
# メッセージログCH
CHANNEL_ID_MESSAGE_LOG = int(os.environ.get("CHANNEL_ID_MESSAGE_LOG"))
# ユーザーログCH
CHANNEL_ID_USER_LOG = int(os.environ.get("CHANNEL_ID_USER_LOG"))
# イベント1_スレッドID
THREAD_ID_EVENT1 = int(os.environ.get("THREAD_ID_EVENT1"))
# イベント2_スレッドID
THREAD_ID_EVENT2 = int(os.environ.get("THREAD_ID_EVENT2"))
# ご意見・ご要望CH
CHANNEL_ID_OPINION_LOG = int(os.environ.get("CHANNEL_ID_OPINION_LOG"))
# お問い合わせ_チャンネル・カテゴリID
GENERAL_INQUIRY_OPEN = int(os.environ.get("GENERAL_INQUIRY_OPEN"))
GENERAL_INQUIRY_CLOSE = int(os.environ.get("GENERAL_INQUIRY_CLOSE"))
GENERAL_INQUIRY_LOG = int(os.environ.get("GENERAL_INQUIRY_LOG"))
GENERAL_INQUIRY_SAVE = int(os.environ.get("GENERAL_INQUIRY_SAVE"))
# 通報_チャンネル・カテゴリID
REPORT_OPEN = int(os.environ.get("REPORT_OPEN"))
REPORT_CLOSE = int(os.environ.get("REPORT_CLOSE"))
REPORT_LOG = int(os.environ.get("REPORT_LOG"))
REPORT_SAVE = int(os.environ.get("REPORT_SAVE"))
# 公認クラン_チャンネル・カテゴリID
CLAN_OPEN = int(os.environ.get("CLAN_OPEN"))
CLAN_CLOSE = int(os.environ.get("CLAN_CLOSE"))
CLAN_LOG = int(os.environ.get("CLAN_LOG"))
CLAN_SAVE = int(os.environ.get("CLAN_SAVE"))
# 公認クラン面談申請送信先
CLAN_STAFF_ROLE = int(os.environ.get("CLAN_STAFF_ROLE"))
CLAN_MEET_ID = int(os.environ.get("CLAN_MEET_ID"))


# DB接続情報
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT"))
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")


# Flask Port
FLASK_SERVICE_PORT=int(os.environ.get("SERVICE_PORT"))
# Flask Domain
FLASK_DOMAIN=os.environ.get("FLASK_DOMAIN")
# Flask Secret Key
FLASK_SECRET_KEY=os.environ.get("FLASK_SECRET_KEY")
# Wargaming ApplicationID
WARGAMING_APPLICATION_ID=os.environ.get("WARGAMING_APPLICATION_ID")
# Discord Token
DISCORD_TOKEN=os.environ.get("DISCORD_TOKEN")
# Discord Client ID
DISCORD_CLIENT_ID=int(os.environ.get("DISCORD_CLIENT_ID"))
# Discord Client Secret
DISCORD_CLIENT_SECRET=os.environ.get("DISCORD_CLIENT_SECRET")
# 環境
ENV = os.environ.get("ENV")


COLOR_OK = 0x00ff00
COLOR_WARN = 0xffa500
COLOR_ERROR = 0xff0000