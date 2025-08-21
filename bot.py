import asyncio
import os
import sys
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

import db
from logs import logger
from server import run_server

sys.path.insert(1, os.path.join(sys.path[0], ".."))

load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))
# 接続に必要なオブジェクトを生成
MY_GUILD = discord.Object(id=GUILD_ID)

# 読み込むCogの名前を格納
INITIAL_EXTENSIONS = [
    "cogs.auth",
    # "cogs.contact",
    "cogs.cmd1",
    # "cogs.cmd2",
    # "cogs.event",
    # "cogs.discord_event",
    # "cogs.division",
    # "cogs.give_take_role",
    # "cogs.mod",
    # "cogs.newbie_role",
    # "cogs.rule",
    "cogs.test"
]


def check_developer(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 398429758041620481


class MyBot(commands.Bot):
    # MyBotのコンストラクタ。
    def __init__(self):
        # スーパークラスのコンストラクタに値を渡して実行。
        super().__init__(
            command_prefix="/",
            intents=discord.Intents.all(),
            max_messages=1000)

    async def setup_hook(self):
        for cog in INITIAL_EXTENSIONS:
            await self.load_extension(cog)
        bot.tree.copy_global_to(guild=MY_GUILD)
        await bot.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        await bot.change_presence(activity=discord.Game(name="問い合わせは #お問い合わせはこちら から"))
        logger.info("接続しました")
        print("接続しました")

    async def on_thread_create(self, thread):
        if thread.parent_id == 1054002378984149003:
            action_datetime = time.time()
            await db.save_question_log(thread.owner_id, action_datetime)


# botのインスタンス化、および、起動処理
if __name__ == "__main__":
    bot = MyBot()
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(TOKEN))
    run_server(bot, loop)
    loop.run_forever()
    loop.close()
