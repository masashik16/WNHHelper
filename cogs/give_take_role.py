import datetime

from discord.ext import commands, tasks

from logs import logger

logger = logger.getChild("give_take_role")


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
            await cmd1.give_and_take_role("div")  # noqa
            await log_channel.send(f"月1ロール更新(分隊)が完了しました。")
            await cmd1.give_and_take_role("question")  # noqa
            await log_channel.send(f"月1ロール更新(質問)が完了しました。")
            await newbie.check_newbie_role()  # noqa
            await log_channel.send(f"初心者ロール資格確認が完了しました。")
            logger.info("月1ロール更新が完了しました。")
        else:
            pass


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(GiveTakeRole(bot))
