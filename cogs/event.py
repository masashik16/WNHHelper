import os
import time

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
THREAD_ID_EVENT1 = int(os.environ.get("THREAD_ID_EVENT1"))
THREAD_ID_EVENT2 = int(os.environ.get("THREAD_ID_EVENT2"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("event")

"""Event1の設定"""
# EVENT1_INPUT1 = discord.ui.TextInput(label="1.IGN", max_length=50, )
EVENT1_INPUT2 = ui.TextInput(label="1.申し込み種別", placeholder="受講者 or 見学者", max_length=30, )
EVENT1_INPUT3 = ui.TextInput(label="2.参加可能時間", placeholder="20:00～22:00", max_length=30, )
EVENT1_INPUT4 = ui.TextInput(label="3.事前質問", placeholder="", style=discord.TextStyle.long, max_length=400, )  # noqa
EVENT1_INPUT5 = ui.TextInput(label="4.その他記載事項", placeholder="", style=discord.TextStyle.long,  # noqa
                             required=False, max_length=400, )
# EVENT1_INPUT5 = discord.ui.TextInput(label="5.TEXT", placeholder="TEXT", max_length=30, )
EVENT1_INPUTS = [EVENT1_INPUT2, EVENT1_INPUT3, EVENT1_INPUT4, EVENT1_INPUT5]
"""Event2の設定"""

EVENT2_INPUT1 = ui.TextInput(label="1.IGN", max_length=50, )
EVENT2_INPUT2 = ui.TextInput(label="2.VCの可否", placeholder="可 or 聞き専", max_length=30, )
EVENT2_INPUT3 = ui.TextInput(label="3.一番得意または一番乗っている艦種", max_length=30, )
EVENT2_INPUT4 = ui.TextInput(label="4.11月25日、26日の練習試合に参加出来ますか？",
                             placeholder="両日可 or 25のみ or 26のみ or 両日不可", max_length=30, )
EVENT2_INPUT5 = ui.TextInput(label="5.募集要項の条件を満たしていますか？",
                             placeholder="いいえの場合お申し込みができません。", max_length=30, )
EVENT2_INPUTS = [EVENT2_INPUT1, EVENT2_INPUT2, EVENT2_INPUT3, EVENT2_INPUT4, EVENT2_INPUT5]


class Event(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @app_commands.command(description="イベント申し込み先スレッドの設定")
    # @app_commands.checks.has_role(ROLE_ID_ADMIN)
    # @app_commands.guilds(GUILD_ID)
    # @app_commands.guild_only()
    # @app_commands.choices(
    #     event=[
    #         discord.app_commands.Choice(name="event1", value="event1"),
    #         discord.app_commands.Choice(name="event2", value="event2"),
    #     ])
    # async def set_thread(self, interaction: discord.Interaction, event: str):
    #     if not interaction.channel.type == discord.ChannelType.public_thread:
    #         # コマンドへのレスポンス
    #         error_embed = discord.Embed(description="⚠️ スレッド内で実行してください。", color=Color_ERROR)
    #         await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
    #         return
    #     dotenv_file = dotenv.find_dotenv()
    #     if event == "event1":
    #         dotenv.set_key(dotenv_file, "THREAD_ID_EVENT1", str(interaction.channel.id))
    #     else:
    #         dotenv.set_key(dotenv_file, "THREAD_ID_EVENT2", str(interaction.channel.id))
    #     # コマンドへのレスポンス
    #     response_embed = discord.Embed(description=f"ℹ️ {event}の送信先をこのスレッドに設定しました。", color=Color_OK)
    #     await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
    #     # ログの保存
    #     logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
    #                 f"がコマンド「{interaction.command.name}」を使用しました。")

    async def create_message(self, interaction: discord.Interaction, event: str):
        """イベント応募フォームの作成"""
        if event == "event1":
            # ボタンを含むビューを作成
            view = Event1Button()
            # ビューを含むメッセージを送信
            channel = interaction.channel
            await channel.send(view=view)
        elif event == "event2":
            # ボタンを含むビューを作成
            view = Event2Button()
            # ビューを含むメッセージを送信
            channel = interaction.channel
            await channel.send(view=view)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
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


class Event1Button(ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)
        self.event1_entry_button.disabled = True
        self.event1_cancel_button.disabled = True

    @ui.button(label="申込はこちら", style=discord.ButtonStyle.blurple, custom_id="Event1_submit")  # noqa
    async def event1_entry_button(self, interaction: discord.Interaction, button: ui.Button):
        """申込ボタン押下時の処理"""
        # ボタンへのレスポンス
        await interaction.response.send_modal(Event1Form())  # noqa

    @ui.button(label="変更・キャンセルはこちら", style=discord.ButtonStyle.red, custom_id="Event1_cancel")  # noqa
    async def event1_cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        """キャンセルボタン押下時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとスレッドの取得
        thread_event1 = interaction.guild.get_thread(THREAD_ID_EVENT1)
        # ボタンを押したユーザー情報を取得
        user = interaction.user
        user_id = user.id
        # 申込情報の取得
        entry_log = await discord.utils.get(thread_event1.history(), content=f"<@{user_id}>")
        # 申込情報が見つからない場合
        if entry_log is None:
            # ボタンへのレスポンス
            embed1 = discord.Embed(description="⚠️ 申込情報が見つかりませんでした", color=Color_ERROR)
            await interaction.followup.send(embed=embed1, ephemeral=True)
        # 申込情報の編集
        elif entry_log.embeds[0].to_dict()["title"] == "申込受付":
            # キャンセル情報（Embed）の作成
            color = discord.Color.from_str("0xff0000").value
            embed_dict = entry_log.embeds[0].to_dict()
            embed_dict["color"] = color
            embed_dict["title"] = "申込キャンセル"
            embed = discord.Embed.from_dict(embed_dict)
            t = int(time.time())
            embed.add_field(name="7.キャンセル送信日", value=f"<t:{t}:F>", inline=False)
            # 申込情報をキャンセルに変更
            await entry_log.edit(embed=embed)
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="ℹ️ キャンセルを受け付けました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
        # 申込が既にキャンセル済みの場合
        else:
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="⚠️ 既にキャンセルされています", color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)

    @ui.button(label="運営用", style=discord.ButtonStyle.gray, custom_id="Event1_Admin")  # noqa
    async def event1_admin_button(self, interaction: discord.Interaction, button: ui.Button):
        wnh_staff_role = interaction.guild.get_role(ROLE_ID_WNH_STAFF)
        if wnh_staff_role not in interaction.user.roles:
            raise discord.app_commands.CheckFailure
        if self.event1_entry_button.disabled is True:
            self.event1_entry_button.disabled = False
            self.event1_cancel_button.disabled = False
        else:
            self.event1_entry_button.disabled = True
            self.event1_cancel_button.disabled = True
        await interaction.response.edit_message(view=self)  # noqa

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{item}」を使用しようとしましたが、権限不足により失敗しました。")


class Event1Form(ui.Modal, title="イベント申込フォーム"):
    """フォームの実装"""

    def __init__(self):
        super().__init__()
        for item in EVENT1_INPUTS:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとスレッドの取得
        thread_event1 = interaction.guild.get_thread(THREAD_ID_EVENT1)
        # フォームを送信したユーザーの情報を取得
        user = interaction.user
        user_id = user.id
        server_name = user.display_name
        avatar = user.display_avatar.url
        # イベント応募メッセージ（Embed）の作成
        entry_log_embed = discord.Embed(title=f"申込受付", color=0x0000ff)
        for i in EVENT1_INPUTS:
            if not i.value == "":
                entry_log_embed.add_field(name=i.label, value=i.value, inline=False)
            else:
                entry_log_embed.add_field(name=i.label, value="入力なし", inline=False)
        entry_log_embed.add_field(name="Discord ユーザー", value=f"<@{user_id}>", inline=False)
        entry_log_embed.set_author(name=f"{server_name}", icon_url=f"{avatar}")
        # 既に申込済みかどうか確認
        entry_log = await discord.utils.get(thread_event1.history(), content=f"<@{user_id}>")
        # 未申込の場合
        if entry_log is None:
            # 申込情報の送信
            await thread_event1.send(content=f"<@{user_id}>", embed=entry_log_embed)
            # フォームへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 申込みを受け付けました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
            # 既に申込済みの場合（既存申込の修正）
        else:
            # 申込情報編集
            await entry_log.edit(content=f"<@{user_id}>", embed=entry_log_embed)
            # フォームへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 申込みを修正しました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がフォーム「イベント1」を使用しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「イベント1」でエラーが発生しました。\nエラー内容：{error}")


class Event2Button(ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)
        self.event2_entry_button.disabled = True
        self.event2_cancel_button.disabled = True

    @ui.button(label="申込はこちら", style=discord.ButtonStyle.blurple, custom_id="Event2_Submit")  # noqa
    async def event2_entry_button(self, interaction: discord.Interaction, button: ui.Button):
        """申込ボタン押下時の処理"""
        # ボタンへのレスポンス
        await interaction.response.send_modal(Event2Form())  # noqa

    @ui.button(label="変更・キャンセルはこちら", style=discord.ButtonStyle.red, custom_id="Event2_Cancel")  # noqa
    async def event2_cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        """キャンセルボタン押下時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとスレッドの取得
        thread_event2 = interaction.guild.get_thread(THREAD_ID_EVENT2)
        # ボタンを押したユーザー情報を取得
        user = interaction.user
        user_id = user.id
        # 申込情報の取得
        entry_log = await discord.utils.get(thread_event2.history(), content=f"<@{user_id}>")
        # 申込情報が見つからない場合
        if entry_log is None:
            # ボタンへのレスポンス
            embed1 = discord.Embed(description="⚠️ 申込情報が見つかりませんでした", color=Color_ERROR)
            await interaction.followup.send(embed=embed1, ephemeral=True)
        # 申込情報の編集
        elif entry_log.embeds[0].to_dict()["title"] == "申込受付":
            # キャンセル情報（Embed）の作成
            color = discord.Color.from_str("0xff0000").value
            embed_dict = entry_log.embeds[0].to_dict()
            embed_dict["color"] = color
            embed_dict["title"] = "申込キャンセル"
            embed = discord.Embed.from_dict(embed_dict)
            t = int(time.time())
            embed.add_field(name="7.キャンセル送信日", value=f"<t:{t}:F>", inline=False)
            # 申込情報をキャンセルに変更
            await entry_log.edit(embed=embed)
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="ℹ️ キャンセルを受け付けました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
        # 申込が既にキャンセル済みの場合
        else:
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="⚠️ 既にキャンセルされています", color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)

    @ui.button(label="運営用", style=discord.ButtonStyle.gray, custom_id="Event2_Admin")  # noqa
    async def event2_admin_button(self, interaction: discord.Interaction, button: ui.Button):
        wnh_staff_role = interaction.guild.get_role(ROLE_ID_WNH_STAFF)
        if wnh_staff_role not in interaction.user.roles:
            raise discord.app_commands.CheckFailure
        if self.event2_entry_button.disabled is True:
            self.event2_entry_button.disabled = False
            self.event2_cancel_button.disabled = False
        else:
            self.event2_entry_button.disabled = True
            self.event2_cancel_button.disabled = True
        await interaction.response.edit_message(view=self)  # noqa

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{item}」を使用しようとしましたが、権限不足により失敗しました。")


class Event2Form(ui.Modal, title="イベント申込フォーム"):
    """フォームの実装"""

    def __init__(self):
        super().__init__()
        for item in EVENT2_INPUTS:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとスレッドの取得
        thread_event2 = interaction.guild.get_thread(THREAD_ID_EVENT2)
        # フォームを送信したユーザーの情報を取得
        user = interaction.user
        user_id = user.id
        server_name = user.display_name
        avatar = user.display_avatar.url
        # イベント応募メッセージ（Embed）の作成
        entry_log_embed = discord.Embed(title=f"申込受付", color=0x0000ff)
        for i in EVENT2_INPUTS:
            if not i.value == "":
                entry_log_embed.add_field(name=i.label, value=i.value, inline=False)
            else:
                entry_log_embed.add_field(name=i.label, value="入力なし", inline=False)
        entry_log_embed.add_field(name="Discord ユーザー", value=f"<@{user_id}>", inline=False)
        entry_log_embed.set_author(name=f"{server_name}", icon_url=f"{avatar}")
        # 既に申込済みかどうか確認
        entry_log = await discord.utils.get(thread_event2.history(), content=f"<@{user_id}>")
        # 未申込の場合
        if entry_log is None:
            # 申込情報の送信
            await thread_event2.send(content=f"<@{user_id}>", embed=entry_log_embed)
            # フォームへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 申込みを受け付けました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
            # 既に申込済みの場合（既存申込の修正）
        else:
            # 申込情報編集
            await entry_log.edit(content=f"<@{user_id}>", embed=entry_log_embed)
            # フォームへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 申込みを修正しました", color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がフォーム「イベント1」を使用しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「イベント2」でエラーが発生しました。\nエラー内容：{error}")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Event(bot))
    bot.add_view(view=Event1Button())
    bot.add_view(view=Event2Button())
