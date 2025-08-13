import datetime
import os

from discord.ext import commands, tasks
from dotenv import load_dotenv

from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
ROLE_ID_MATTARI = int(os.environ.get("ROLE_ID_MATTARI"))
ROLE_ID_GATSU = int(os.environ.get("ROLE_ID_GATSU"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("give_take_role")

tz = datetime.timezone(datetime.timedelta(hours=9))
time = datetime.time(hour=7, minute=0, tzinfo=tz)


class GiveTakeRole(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.role_task.start()

    def cog_unload(self):
        self.role_task.cancel()

    @tasks.loop(hours=24)
    async def role_task(self):
        """報奨ロールの更新"""
        if datetime.date.today().day == 1:
            log_channel = self.bot.get_channel(1359754126782890085)
            cmd1 = self.bot.get_cog("Commands1")
            newbie = self.bot.get_cog("Newbie")
            await cmd1.give_and_take_role("div")
            await log_channel.send(f"月1ロール更新(分隊)が完了しました。")
            await cmd1.give_and_take_role("question")
            await log_channel.send(f"月1ロール更新(質問)が完了しました。")
            await newbie.check_newbie_role()
            await log_channel.send(f"初心者ロール資格確認が完了しました。")
            logger.info("月1ロール更新が完了しました。")
        else:
            pass


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(GiveTakeRole(bot))
