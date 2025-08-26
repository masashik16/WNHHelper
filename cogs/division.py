import os
import time

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import db
from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
CHANNEL_ID_DIVISION = int(os.environ.get("CHANNEL_ID_DIVISION"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("division")


class Division(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_message(self, interaction: discord.Interaction):
        """分隊募集フォーム用ボタンを作成"""
        # ボタンを含むビューを作成
        view = DivisionButton()
        # Embedの作成
        embed = discord.Embed(description="分隊を募集するには下のボタンを押してください", color=0x0000ff)
        # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(embed=embed, view=view)
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


"""ボタンの実装"""


class DivisionButton(ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="分隊を募集する", style=discord.ButtonStyle.blurple, custom_id="div")  # noqa
    async def division_button(self, interaction: discord.Interaction, button: ui.Button):
        """ボタン押下時の処理"""
        if interaction.user.is_timed_out():
            error_embed = discord.Embed(description="⚠️ タイムアウト中は利用できません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            # フォームの呼び出し
            await interaction.response.send_modal(DivisionForm())  # noqa


class DivisionForm(ui.Modal, title="分隊募集フォーム"):
    """フォームの実装"""

    def __init__(self):
        """ギルド、ロール、チャンネルの事前定義"""
        super().__init__()

    # フォームの入力項目の定義（最大5個）
    dtime = ui.TextInput(
        label="1.日時",
        placeholder="例：今日19:00~21:00",
        max_length=30,
    )

    tier = ui.TextInput(
        label="2. Tier（オペレーションの場合は名称）",
        placeholder="例：8～10",
        max_length=30,
    )

    member_count = ui.TextInput(
        label="3.募集人数",
        placeholder="例：2人",
        max_length=30,
    )

    newbie = ui.TextInput(
        label="4.初心者ですか？（無回答でもOK）",
        placeholder="はい or いいえ",
        max_length=30,
        required=False,
    )

    other = ui.TextInput(
        label="5.その他注記事項（無回答でもOK）",
        style=discord.TextStyle.long,  # noqa
        placeholder="",
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとチャンネルの取得
        channel_division = await interaction.guild.fetch_channel(CHANNEL_ID_DIVISION)
        # フォームを送信したユーザーの情報を取得
        user = interaction.user
        server_name = user.display_name
        avatar = user.display_avatar.url
        # 分隊募集メッセージ（Embed）の作成
        embed = discord.Embed(title=f"分隊募集中！", color=0x0000ff)
        embed.add_field(name="1.日時", value=self.dtime.value, inline=False)
        embed.add_field(name="2. Tier（オペレーションの場合は名称）", value=self.tier.value, inline=False)
        embed.add_field(name="3. 募集人数", value=self.member_count.value, inline=False)
        if not self.newbie.value == "":
            embed.add_field(name="4. 初心者ですか？", value=self.newbie.value, inline=False)
        else:
            embed.add_field(name="4. 初心者ですか？", value="入力なし", inline=False)
        if not self.other.value == "":
            embed.add_field(name="5. その他注記事項", value=self.other.value, inline=False)
        else:
            embed.add_field(name="5. その他注記事項", value="入力なし", inline=False)
        embed.set_author(name=f"{server_name}", icon_url=f"{avatar}")
        # 分隊募集メッセージを送信し、紐づくスレッドを作成
        message = await channel_division.send("<@&990131642238652436>", embed=embed)
        thread = await message.create_thread(name=f"{server_name} - 分隊募集")
        await thread.add_user(user)
        # フォームへのレスポンス
        response_embed = discord.Embed(description=f"ℹ️ <#{CHANNEL_ID_DIVISION}>に分隊募集を作成しました",
                                       color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # DBに保存
        action_datetime = time.time()
        await db.save_division_log(user.id, action_datetime)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がフォーム「分隊募集」を使用しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「分隊募集」でエラーが発生しました。\nエラー内容：{error}")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Division(bot))
    bot.add_view(view=DivisionButton())
