import datetime
import importlib
import os
import statistics
import sys
import time

import discord
from dateutil.relativedelta import *
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import db
import server
from api import wows_user_clan
from bot import check_developer
from logs import logger
from views import wg_auth

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_SENIOR_MOD = int(os.environ.get("ROLE_ID_SENIOR_MOD"))
ROLE_ID_MOD = int(os.environ.get("ROLE_ID_MOD"))
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
ROLE_ID_CLAN_RECRUITER = int(os.environ.get("ROLE_ID_CLAN_RECRUITER"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("cmd1")


class Commands1(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="cogをリロード")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.choices(
        cog_name=[
            discord.app_commands.Choice(name="auth", value="auth"),
            discord.app_commands.Choice(name="contact", value="contact"),
            discord.app_commands.Choice(name="cmd1", value="cmd1"),
            discord.app_commands.Choice(name="cmd2", value="cmd2"),
            discord.app_commands.Choice(name="discord_event", value="discord_event"),
            discord.app_commands.Choice(name="division", value="division"),
            discord.app_commands.Choice(name="event", value="event"),
            discord.app_commands.Choice(name="give_take_role", value="give_take_role"),
            discord.app_commands.Choice(name="mod", value="mod"),
            discord.app_commands.Choice(name="msg", value="msg"),
            discord.app_commands.Choice(name="newbie_role", value="newbie_role"),
            discord.app_commands.Choice(name="rule", value="rule"),
            discord.app_commands.Choice(name="server", value="server"),
            discord.app_commands.Choice(name="test", value="test"),
        ])
    @app_commands.choices(
        sync_command=[
            discord.app_commands.Choice(name="true", value=1),
            discord.app_commands.Choice(name="false", value=0)
        ])
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str, sync_command: int):
        """cogの再読み込み"""
        await interaction.response.defer(ephemeral=True)  # noqa
        if cog_name == "server":
            server.shutdown_server()
            reload_list = [wg_auth, server]
            for module in reload_list:
                importlib.reload(module)
            server.run_server(self.bot, self.bot.loop)
        else:
            cog = f"cogs.{cog_name}"
            sys.modules[cog] = importlib.reload(sys.modules[cog])
            guild = self.bot.get_guild(GUILD_ID)
            await self.bot.reload_extension(cog)
            if sync_command == 1:
                await self.bot.tree.sync(guild=guild)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description=f"ℹ️ cog「{cog_name}」をリロードしました。", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="プログラムを終了")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def shutdown(self, interaction: discord.Interaction):
        from server import shutdown_server, server_task
        response_embed = discord.Embed(description=f"ℹ️ シャットダウンを開始しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        shutdown_server()
        while True:
            server_active = server_task.done()  # noqa
            if server_active is False:
                break
            time.sleep(3)
        await self.bot.close()
        sys.exit()

    @app_commands.command(description="動的タイムスタンプ生成")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(year_date="年月日", input_time="時刻")
    @app_commands.describe(year_date="例：2000/01/01", input_time="例：00:00")
    @app_commands.choices(
        formats=[
            discord.app_commands.Choice(name="〇〇時間後（〇〇日後）", value="R"),
            discord.app_commands.Choice(name="〇〇年〇〇月〇〇日", value="D"),
            discord.app_commands.Choice(name="〇〇：〇〇", value="t"),
            discord.app_commands.Choice(name="〇〇年〇〇月〇〇日　〇〇曜日　〇〇：〇〇", value="F")
        ])
    async def timestamp(self, interaction: discord.Interaction, year_date: str, input_time: str, formats: str):
        """Discordでの動的タイムスタンプの作成"""
        # 入力値の整形
        date_str = year_date + " " + input_time + " " + "+0900"
        # 入力値をdatatimeで変換
        try:
            date_dt = datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M %z")
        # 入力形式が誤っている場合
        except ValueError:
            embed = discord.Embed(description="⚠️ 入力が誤っています。次の内容を確認してください。\n", color=Color_ERROR)
            embed.add_field(name="よくあるミス",
                            value="**年月日**\n西暦4桁、月2桁、日2桁で入力する必要があります。"
                                  "\n2000年1月1日の場合は2000/01/01と入力してください。"
                                  "\n\n**時刻**"
                                  "\n24時間表記で時分各2桁で入力する必要があります。"
                                  "\n午後8時の場合は20:00と入力してください。")
            await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
        # 入力値をタイムスタンプに変換して送信
        else:
            timestamp = int(date_dt.timestamp())
            await interaction.response.send_message(  # noqa
                f"下記の内容で生成しました。\n<t:{timestamp}:{formats}>\n```<t:{timestamp}:{formats}>```",
                ephemeral=True)
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="クランURLの生成")
    @app_commands.checks.has_any_role(ROLE_ID_WNH_STAFF, ROLE_ID_CLAN_RECRUITER)
    @app_commands.guild_only()
    async def clan_url(self, interaction: discord.Interaction):
        # DBからWargaming UIDを取得し代入
        await interaction.response.defer(ephemeral=True)  # noqa
        user_info_result = await db.search_user(interaction.user.id)
        try:
            discord_id, account_id, region = user_info_result
        except ValueError:
            logger.error(f"{interaction.user.id}でエラー")
            response_embed = discord.Embed(
                description="ℹ️ 認証情報が登録されていません。運営チームにお問い合わせください。", color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
        clan_id = await wows_user_clan(account_id)  # noqa
        if clan_id == "ERROR_ACCOUNT_NOT_FOUND":
            response_embed = discord.Embed(
                description="ℹ️ この機能はASIAサーバー所属ユーザーのみ利用できます。", color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
        elif clan_id == "ERROR_NOT_JOINED_CLAN":
            response_embed = discord.Embed(
                description="ℹ️ この機能はクランに所属しているユーザーのみ利用できます。", color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
        else:
            clan_url = f"https://clans.worldofwarships.asia/clan-profile/{clan_id}"
            response_embed = discord.Embed(
                description=f"ℹ️ あなたの所属しているクランのURLはこちらです。\n{clan_url}", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa

    @app_commands.command(description="報奨ロールの更新")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.rename(mode="更新するロールの種類")
    @app_commands.choices(
        mode=[
            discord.app_commands.Choice(name="分隊", value="div"),
            discord.app_commands.Choice(name="質問", value="question")
        ])
    async def manual_give_and_take_role(self, interaction: discord.Interaction, mode: str):
        await interaction.response.defer(ephemeral=True)  # noqa
        await self.give_and_take_role(mode)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 更新しました", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name} - {mode}」を使用しました。")

    async def give_and_take_role(self, mode: str):
        """報奨ロールの更新"""
        # DBへ受付状況の登録
        guild = self.bot.get_guild(GUILD_ID)
        # 1ヶ月前のタイムスタンプの取得
        d = datetime.date.today() - relativedelta(months=1)
        t = datetime.time()
        one_month_ago = datetime.datetime.combine(d, t)
        one_month_ago_ts = one_month_ago.timestamp()
        # DBから取得
        if mode == "div":
            log = await db.get_division_log()
            role = guild.get_role(1211291951761072218)
            for member in role.members:
                await member.remove_roles(role, reason="定期更新による")
        else:
            log = await db.get_question_log()
            role = guild.get_role(1211291816805273610)
            for member in role.members:
                await member.remove_roles(role, reason="定期更新による")
        # 1か月前以降の分を取得
        log_list = []
        for i in log:
            if float(i[2]) > one_month_ago_ts:
                log_list.append(i[1])
        add_role_list = []
        # ユーザー抽出
        rank_1st = statistics.multimode(log_list)
        if type(rank_1st) is str:
            log_list = [user_id for user_id in log_list if user_id != rank_1st]
            add_role_list.append(int(rank_1st))  # noqa
        else:
            for user_id_multi in rank_1st:
                log_list = [user_id for user_id in log_list if user_id != user_id_multi]
                add_role_list.append(int(user_id_multi))
        rank_2nd = statistics.multimode(log_list)
        if type(rank_2nd) is str:
            log_list = [user_id for user_id in log_list if user_id != rank_2nd]
            add_role_list.append(int(rank_2nd))  # noqa
        else:
            for user_id_multi in rank_2nd:
                log_list = [user_id for user_id in log_list if user_id != user_id_multi]
                add_role_list.append(int(user_id_multi))
        log_list = [user_id for user_id in log_list if user_id != rank_2nd]
        rank_3rd = statistics.multimode(log_list)
        if type(rank_3rd) is str:
            add_role_list.append(int(rank_3rd))  # noqa
        else:
            for user_id_multi in rank_3rd:
                add_role_list.append(int(user_id_multi))
        for user_id in add_role_list:
            member = guild.get_member(user_id)
            if member is not None:
                await member.add_roles(role, reason="定期更新による")

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{interaction.command.name}」を使用しようとしましたが、権限不足により失敗しました。")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Commands1(bot))
