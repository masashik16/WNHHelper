import asyncio
import datetime
import importlib
import io
import os
import re
import statistics

import discord
from dateutil.relativedelta import *
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import chat_exporter
import db
import server
from bot import check_developer
from logs import logger

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
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("cmd1")



class Commands1(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.transfer_message_menu = app_commands.ContextMenu(
            name="メッセージをBOTとして転送",
            callback=self.transfer_message,
        )
        self.bot.tree.add_command(self.transfer_message_menu)
        self.transfer_message_menu.error(self.cog_app_command_error)

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
            discord.app_commands.Choice(name="newbie_role", value="newbie_role"),
            discord.app_commands.Choice(name="rule", value="rule"),
            discord.app_commands.Choice(name="server", value="server"),
            # discord.app_commands.Choice(name="test", value="test"),
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
            importlib.reload(server)
            loop = asyncio.get_event_loop()
            loop.create_task(server.start_server_process(self.bot))
        else:
            cog = f"cogs.{cog_name}"
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

    @app_commands.command(description="固定メッセージの作成")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.choices(
        message=[
            discord.app_commands.Choice(name="auth", value="auth"),
            discord.app_commands.Choice(name="contact", value="contact"),
            discord.app_commands.Choice(name="event1", value="event1"),
            discord.app_commands.Choice(name="event2", value="event2"),
            discord.app_commands.Choice(name="division", value="division"),
            discord.app_commands.Choice(name="newbie_role", value="newbie_role"),
            discord.app_commands.Choice(name="rule", value="rule"),
            discord.app_commands.Choice(name="no_role", value="no_role")
        ])
    async def create_module_message(self, interaction: discord.Interaction, message: str):
        """モジュールメッセージの作成"""
        if message == "auth":
            auth = self.bot.get_cog("Auth")
            await auth.create_message(interaction)  # noqa
        elif message == "contact":
            auth = self.bot.get_cog("Contact")
            await auth.create_message(interaction)  # noqa
        elif message == "division":
            division = self.bot.get_cog("Division")
            await division.create_message(interaction)  # noqa
        elif message == "event1":
            event = self.bot.get_cog("Event")
            await event.create_message(interaction, "event1")  # noqa
        elif message == "event2":
            event = self.bot.get_cog("Event")
            await event.create_message(interaction, "event2")  # noqa
        elif message == "newbie_role":
            newbie_role = self.bot.get_cog("Newbie")
            await newbie_role.create_message(interaction)  # noqa
        elif message == "rule":
            rule = self.bot.get_cog("Rule")
            await rule.create_message(interaction)  # noqa
        elif message == "no_role":
            rule = self.bot.get_cog("Rule")
            await rule.create_message2(interaction)  # noqa
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}:{message}」を使用しました。")

    @app_commands.command(description="イベントボタンの作成")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.choices(
        button=[
            discord.app_commands.Choice(name="event1", value="event1"),
            discord.app_commands.Choice(name="event2", value="event2"),
        ])
    async def create_event_button(self, interaction: discord.Interaction, button: str):
        """イベントボタンの作成"""
        if button == "event1":
            event = self.bot.get_cog("Event")
            await event.create_message(interaction, "event1")  # noqa
        elif button == "event2":
            event = self.bot.get_cog("Event")
            await event.create_message(interaction, "event2")  # noqa
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}:{button}」を使用しました。")

    @app_commands.command(description="DM履歴の確認")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="照会するユーザー")
    async def get_dm_log(self, interaction: discord.Interaction, user: discord.User):
        """DM履歴の確認"""
        await interaction.response.defer(ephemeral=True)  # noqa
        dm = await user.create_dm()
        embed = discord.Embed(title="DM履歴")
        async for message in dm.history(limit=200):
            if message.embeds:
                msg_embed = message.embeds[0]
                if not msg_embed.fields or msg_embed.fields[0].name != "ケース番号":
                    embed.add_field(name=f"<t:{int(message.created_at.timestamp())}:F>",
                                    value=f"投稿者：{message.author.name}\nEmbedタイトル：{msg_embed.title}",
                                    inline=False)
                else:
                    embed.add_field(name=f"<t:{int(message.created_at.timestamp())}:F>",
                                    value=f"投稿者：{message.author.name}\nEmbedタイトル：{msg_embed.title}\nケース番号：{msg_embed.fields[0].value}",
                                    inline=False)
            elif message.content == "":
                embed.add_field(name=f"<t:{int(message.created_at.timestamp())}:F>",
                                value=f"投稿者：{message.author.name}\n内容：ファイルのみ",
                                inline=False)
            else:
                embed.add_field(name=f"<t:{int(message.created_at.timestamp())}:F>",
                                value=f"投稿者：{message.author.name}\n内容：{message.content}",
                                inline=False)
        # コマンドへのレスポンス
        await interaction.followup.send(embed=embed)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

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

    @app_commands.command(description="ルール未同意メッセージ")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def plz_agree(self, interaction: discord.Interaction):
        """ルール未同意ユーザー向けメッセージの作成"""
        channel = self.bot.get_channel(1020535929259176027)
        # Embedの作成
        embed = discord.Embed(title="ルールに同意いただいていない方へ",
                              description="このメンションを受け取った方は現在加入手続きが未完了なため、サーバーをご利用頂けない状態です。"
                                          "\nサーバーをご利用いただくために、次のお手続きをお願いします。")
        embed.add_field(name="STEP1",
                        value="まずは<#977773343824560130>をお読みいただき、同意する場合は最下部のルール同意ボタンを押します",
                        inline=False)
        embed.add_field(name="STEP2",
                        value="同意ボタンを押した際に表示されるメッセージから<#1022770176082591836>に飛び、Wargaming IDで認証を行います",
                        inline=False)
        embed.add_field(name="Q&A",
                        value="Q1：インタラクションに失敗しましたと表示される\nA1：3分ほど待ってから再度お試しください。2回目でも同じ症状が発生する場合はお問い合わせください。\n"
                              "\nQ2：手続きを終えたのにチャンネルが増えない"
                              "\nA2：<#1022770176082591836>がまだ表示されている場合、3分ほど待ってから再度アカウント認証を行ってください。"
                              "2回目でも同じ症状が発生する場合はお問い合わせください。\n"
                              "\n上記Q&Aで解決できない場合は\nhttps://dyno.gg/form/b5f6b630\nからお問い合わせください。"
                              "\nお問い合わせの際は運営チームからの返信を受け取れるよう、画像のチェックボックスをONにしてください。",
                        inline=False)
        embed.set_image(url="https://dl.dropboxusercontent.com/s/8r6w28v0ocebeic/allow_dm.png")
        # Embedの送信
        await channel.send(f"<@&{ROLE_ID_WAIT_AGREE_RULE}>", embed=embed)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="未認証メッセージ")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def plz_auth(self, interaction: discord.Interaction):
        """未認証ユーザー向けメッセージの作成"""
        channel = self.bot.get_channel(1020535735109029948)
        # Embedの作成
        embed = discord.Embed(title="認証を行っていただいていない方へ",
                              description="このメンションを受け取った方はWargaming ID認証が未完了なため、サーバーをご利用頂けない状態です。"
                                          "\nサーバーをご利用いただくために、<#1022770176082591836>から、Wargaming IDで認証をお願いします。")
        embed.add_field(name="Q&A",
                        value="Q1：インタラクションに失敗しましたと表示される"
                              "\nA1：3分ほど待ってから再度お試しください。2回目でも同じ症状が発生する場合はお問い合わせください。\n"
                              "\nQ2：手続きを終えたのにチャンネルが増えない"
                              "\nA2：<#1022770176082591836>がまだ表示されている場合、3分ほど待ってから再度アカウント認証を行ってください。"
                              "2回目でも同じ症状が発生する場合はお問い合わせください。\n"
                              "\n上記Q&Aで解決できない場合は\nhttps://dyno.gg/form/b5f6b630\nからお問い合わせください。"
                              "\nお問い合わせの際は運営チームからの返信を受け取れるよう、画像のチェックボックスをONにしてください。",
                        inline=False)
        embed.set_image(url="https://dl.dropboxusercontent.com/s/8r6w28v0ocebeic/allow_dm.png")
        # Embedの送信
        await channel.send(f"<@&{ROLE_ID_WAIT_AUTH}>", embed=embed)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

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

    @app_commands.command(description="メッセージ編集用")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.rename(url1="編集するメッセージリンクのurl")
    @app_commands.rename(url2="反映したい内容のメッセージリンクのurl")
    async def edit_message(self, interaction: discord.Interaction, url1: str, url2: str):
        """BOTが送信したメッセージの編集"""
        # URLがWNH内のメッセージリンクかどうか検証
        pattern = rf"(?<=https://discord.com/channels/{GUILD_ID})/([0-9]*)/([0-9]*)"
        result1 = re.search(pattern, url1)
        result2 = re.search(pattern, url2)
        # WNH内のメッセージリンクではない場合
        if result1 is None or result2 is None:
            await interaction.response.send_message("このサーバーのメッセージではありません", ephemeral=True)  # noqa
        # WNH内のメッセージリンクの場合
        else:
            # 値の代入とチャンネル・メッセージの取得
            guild = self.bot.get_guild(GUILD_ID)
            editing_channel_id = int(result1.group(1))
            editing_channel = await guild.fetch_channel(editing_channel_id)
            editing_message_id = int(result1.group(2))
            editing_message = await editing_channel.fetch_message(editing_message_id)
            # 値の代入とチャンネル・メッセージの取得
            content_channel_id = int(result2.group(1))
            content_channel = await guild.fetch_channel(content_channel_id)
            content_message_id = int(result2.group(2))
            content_message = await content_channel.fetch_message(content_message_id)
            content = content_message.content
            # メッセージを編集
            try:
                await editing_message.edit(content=content)
            # 送信者がこのBOTでない場合
            except discord.Forbidden:
                response_embed = discord.Embed(
                    description="⚠️ 権限がありません。<@1019156547449913414>が送信したメッセージではない可能性があります。",
                    color=Color_ERROR)
                await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
            else:
                # コマンドへのレスポンス
                response_embed = discord.Embed(description="ℹ️ 編集が完了しました", color=Color_OK)
                await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、メッセージ「{url1}」を編集しました。。")

    @app_commands.command(description="メッセージをHTMLとして保存")
    @app_commands.checks.has_any_role(ROLE_ID_WNH_STAFF, ROLE_ID_SENIOR_MOD, ROLE_ID_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.rename(url="メッセージリンク")
    @app_commands.rename(count="取得するメッセージ数")
    async def save_message(self, interaction: discord.Interaction, url: str, count: int):
        # URLがWNH内のメッセージリンクかどうか検証
        pattern = rf"(?<=https://discord.com/channels/{GUILD_ID})/([0-9]*)/([0-9]*)"
        result = re.search(pattern, url)
        # WNH内のメッセージリンクではない場合
        if result is None:
            await interaction.response.send_message("このサーバーのメッセージではありません", ephemeral=True)  # noqa
        # WNH内のメッセージリンクの場合
        else:
            # 値の代入とチャンネル・メッセージの取得
            guild = self.bot.get_guild(GUILD_ID)
            channel_id = int(result.group(1))
            channel = await guild.fetch_channel(channel_id)
            message_id = int(result.group(2))
            base_message = await channel.fetch_message(message_id)
            message_list = [message async for message in channel.history(limit=count, around=base_message)]
            dt = base_message.created_at.strftime("%Y-%m-%d %H:%M")
            # HTMLを作成
            transcript = await chat_exporter.raw_export(
                channel,
                messages=message_list,
                tz_info="Asia/Tokyo",
                military_time=True
            )

            if transcript is None:
                return

            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{channel.name}-{dt}_{count}.html",
            )
            #
            # Embedを作成
            await interaction.response.send_message(file=transcript_file, ephemeral=True)  # noqa

    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def transfer_message(self, interaction: discord.Interaction, message: discord.Message):
        """メッセージをBOTとして転送"""
        view = MsgTransferDropdownView(message)
        await interaction.response.send_message("転送先の種類を選択してください。", view=view, ephemeral=True)  # noqa

    @app_commands.command(description="Embedを作成")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def create_embed(self, interaction: discord.Interaction):
        """Embedを作成"""
        # フォームの呼び出し
        await interaction.response.send_modal(CreateEmbedForm())  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{interaction.command.name}」を使用しようとしましたが、権限不足により失敗しました。")


class MsgTransferDropdownView(discord.ui.View):
    """メッセージをBOTとして転送"""

    def __init__(self, message: discord.Message, timeout=360):
        super().__init__(timeout=timeout)
        self.message = message
        self.send_list = None
        self.type = None
        self.remove_item(self.set_channel)  # noqa
        self.remove_item(self.set_user)
        self.remove_item(self.set_role)
        self.remove_item(self.transfer_message_button)  # noqa

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="転送先の種類を選択",
        options=[
            discord.SelectOption(label="チャンネル", value="channel"),
            discord.SelectOption(label="特定のユーザーのDM", value="user"),
            discord.SelectOption(label="特定のロールを持つユーザーのDM", value="role"),
        ],
    )
    async def set_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "channel":
            self.add_item(self.set_channel)  # noqa
            self.type = "channel"
        elif select.values[0] == "user":
            self.add_item(self.set_user)
            self.type = "user"
        else:
            self.add_item(self.set_role)
            self.type = "role"
        self.remove_item(self.set_type)
        await interaction.response.edit_message(content="転送先を選択してください。", view=self)  # noqa

    # noinspection PyTypeChecker
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="転送先のチャンネルを選択",
        channel_types=[discord.ChannelType.text, discord.ChannelType.news],
    )
    async def set_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.send_list = select.values[0]
        transfer_to = self.send_list.name
        embed = discord.Embed()
        embed.add_field(name="送信内容", value=self.message.content, inline=False)
        embed.add_field(name="転送先のチャンネル", value=transfer_to, inline=False)
        self.remove_item(self.set_channel)  # noqa
        self.add_item(self.transfer_message_button)  # noqa
        await interaction.response.edit_message(  # noqa
            content="下記内容で転送します。よろしいですか？", embed=embed, view=self)

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="転送先のユーザーを選択",
        max_values=25
    )
    async def set_user(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.send_list = select.values
        transfer_to = None
        for user in self.send_list:
            if transfer_to is None:
                transfer_to = user.name
            else:
                transfer_to = transfer_to + f"\n{user.name}"
        embed = discord.Embed()
        embed.add_field(name="送信内容", value=self.message.content, inline=False)
        embed.add_field(name="転送先のユーザー", value=transfer_to, inline=False)
        self.remove_item(self.set_user)
        self.add_item(self.transfer_message_button)  # noqa
        await interaction.response.edit_message(  # noqa
            content="下記内容で転送します。よろしいですか？", embed=embed, view=self)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="転送先のロールを選択",
    )
    async def set_role(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.send_list = select.values[0]
        transfer_to = self.send_list.name
        embed = discord.Embed()
        embed.add_field(name="送信内容", value=self.message.content, inline=False)
        embed.add_field(name="転送先のロール", value=transfer_to, inline=False)
        self.remove_item(self.set_role)
        self.add_item(self.transfer_message_button)  # noqa
        await interaction.response.edit_message(  # noqa
            content="下記内容で転送します。よろしいですか？", embed=embed, view=self)

    @discord.ui.button(label="OK", style=discord.ButtonStyle.success)  # noqa
    async def transfer_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.type == "channel":
            channel = await self.send_list.fetch()
            if not self.message.embeds:
                await channel.send(content=self.message.content)
            else:
                await channel.send(content=self.message.content, embed=self.message.embeds[0])
            logger.info(
                f"ユーザー：{interaction.user}（UID：{interaction.user.id}）がメッセージID：{self.message.jump_url}を{channel.name}に転送しました。")
        elif self.type == "user":
            for user in self.send_list:
                if not self.message.embeds:
                    await user.send(content=self.message.content)
                else:
                    await user.send(content=self.message.content, embed=self.message.embeds[0])
                logger.info(
                    f"ユーザー：{interaction.user}（UID：{interaction.user.id}）がメッセージID：{self.message.jump_url}を{user.display_name}に転送しました。")
        else:
            for user in self.send_list.members:
                if not self.message.embeds:
                    await user.send(content=self.message.content)
                else:
                    await user.send(content=self.message.content, embed=self.message.embeds[0])
                logger.info(
                    f"ユーザー：{interaction.user}（UID：{interaction.user.id}）がメッセージID：{self.message.jump_url}を{user.display_name}に転送しました。")
        response_embed = discord.Embed(description="ℹ️ 転送しました", color=Color_OK)
        await interaction.response.edit_message(content=None, embed=response_embed, view=None)  # noqa


class CreateEmbedButton(discord.ui.View):
    """ボタンの実装"""

    def __init__(self, message: discord.Message, embed: discord.Embed):
        super().__init__(timeout=None)
        self.message = message
        self.embed = embed

    @discord.ui.button(label="フィールドを追加", style=discord.ButtonStyle.blurple)  # noqa
    async def add_field_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ボタン押下時の処理"""
        # フォームの呼び出し
        await interaction.response.send_modal(AddEmbedFieldForm(message=self.message, embed=self.embed))  # noqa


class CreateEmbedForm(discord.ui.Modal, title="Embedを作成"):
    """フォームの実装"""

    def __init__(self):
        """ギルド、ロール、チャンネルの事前定義"""
        super().__init__(timeout=600)

    # フォームの入力項目の定義（最大5個）
    message_content = discord.ui.TextInput(
        label="メッセージ_本文",
        style=discord.TextStyle.long,  # noqa
        max_length=4000,
        required=False
    )

    embed_title = discord.ui.TextInput(
        label="Embed_タイトル",
        max_length=256,
        required=False
    )

    embed_description = discord.ui.TextInput(
        label="Embed_本文",
        style=discord.TextStyle.long,  # noqa
        max_length=4000,
        required=False
    )

    field1_name = discord.ui.TextInput(
        label="フィールド1_名前",
        max_length=256,
        required=False
    )

    field1_value = discord.ui.TextInput(
        label="フィールド1_本文",
        style=discord.TextStyle.long,  # noqa
        max_length=4000,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # noqa
        if self.embed_title.value == "" and self.embed_description.value == "" and self.field1_name.value == "" and self.field1_value.value == "":
            error_embed = discord.Embed(title="⚠️ エラーが発生しました", description="最低1項目は入力が必要です。",
                                        color=Color_ERROR)
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        else:
            # Embedの作成
            embed = discord.Embed(title=self.embed_title.value, description=self.embed_description.value)
            embed.add_field(name=self.field1_name.value, value=self.field1_value.value, inline=False)
            # フォームへのレスポンス
            channel = interaction.channel
            message = await channel.send(content="読み込み中")
            view = CreateEmbedButton(message=message, embed=embed)
            await message.edit(content=self.message_content.value, embed=embed, view=view)
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がフォーム「Embedフォーム_新規作成」を使用しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「Embedフォーム_新規作成」でエラーが発生しました。\nエラー内容：{error}")


class AddEmbedFieldForm(discord.ui.Modal, title="フィールドを追加"):
    """フォームの実装"""

    def __init__(self, message: discord.Message, embed: discord.Embed):
        """ギルド、ロール、チャンネルの事前定義"""
        super().__init__(timeout=600)
        self.message = message
        self.embed = embed

    # フォームの入力項目の定義（最大5個）
    field1_name = discord.ui.TextInput(
        label="フィールド1_名前",
        max_length=256,
        required=False
    )

    field1_value = discord.ui.TextInput(
        label="フィールド1_本文",
        style=discord.TextStyle.long,  # noqa
        max_length=4000,
        required=False
    )

    field2_name = discord.ui.TextInput(
        label="フィールド1_名前",
        max_length=256,
        required=False
    )

    field2_value = discord.ui.TextInput(
        label="フィールド1_本文",
        style=discord.TextStyle.long,  # noqa
        max_length=4000,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # Embedの作成
        self.embed.add_field(name=self.field1_name.value, value=self.field1_value.value, inline=False)
        self.embed.add_field(name=self.field2_name.value, value=self.field2_value.value, inline=False)
        # フォームへのレスポンス
        view = CreateEmbedButton(message=self.message, embed=self.embed)
        await self.message.edit(embed=self.embed, view=view)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がフォーム「Embedフォーム_フィールド追加」を使用しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「Embedフォーム_フィールド追加」でエラーが発生しました。\nエラー内容：{error}")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Commands1(bot))
