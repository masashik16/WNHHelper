import os

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import api
import db
from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_MATTARI = int(os.environ.get("ROLE_ID_MATTARI"))
ROLE_ID_GATSU = int(os.environ.get("ROLE_ID_GATSU"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("newbie_role")


class Newbie(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    """初心者ロール用ボタンの作成"""

    async def create_message(self, interaction: discord.Interaction):
        """初心者用ロール選択用メッセージの送信"""
        # ドロップダウンを含むビューを作成
        view = NewbieButton()
        # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(view=view)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="初心者ロールの要件確認")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def manual_check_newbie_role(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # noqa
        await self.check_newbie_role()
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 処理が完了しました", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    async def check_newbie_role(self):
        """初心者用ロールの条件を満たしているか再確認"""
        # ギルドとロールの取得
        guild = self.bot.get_guild(GUILD_ID)
        role_mattari = guild.get_role(ROLE_ID_MATTARI)
        role_gatsu = guild.get_role(ROLE_ID_GATSU)
        # まったりロールの確認
        for mattari_member in role_mattari.members:
            # DBからWargaming UIDを取得し代入
            user_info_result = await db.search_user(mattari_member.id)
            try:
                discord_id, account_id, region = user_info_result
            except ValueError:
                logger.error(f"{mattari_member.id}でエラー")
            else:
                # 戦闘数の照会と代入
                wg_api_result = await api.wows_user_info(account_id, region)
                nickname, battles = wg_api_result
                # 戦闘数が3001以上の場合ロールを解除
                if battles == "private" or battles > 3000:
                    await mattari_member.remove_roles(role_mattari, reason="定期資格審査による")
        # がつがつロールの確認
        for gatsu_member in role_gatsu.members:
            user_info_result = await db.search_user(gatsu_member.id)
            try:
                discord_id, account_id, region = user_info_result
            except ValueError:
                logger.error(f"{gatsu_member.id}でエラー")
            else:
                # 戦闘数の照会と代入
                wg_api_result = await api.wows_user_info(account_id, region)
                nickname, battles = wg_api_result
                # 戦闘数が3001以上の場合ロールを解除
                if battles == "private" or battles > 3000:
                    await gatsu_member.remove_roles(role_gatsu, reason="定期資格審査による")

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{interaction.command.name}」を使用しようとしましたが、権限不足により失敗しました。")


class NewbieButton(ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="まったり", emoji="🔵", style=discord.ButtonStyle.blurple, custom_id="mattari")  # noqa
    async def button_mattari(self, interaction: discord.Interaction, button: ui.Button):
        """まったりロール用ボタン押下時の処理"""
        # ギルドとロールの取得

        role_mattari = interaction.guild.get_role(ROLE_ID_MATTARI)
        role_gatsu = interaction.guild.get_role(ROLE_ID_GATSU)
        # ボタンを押したユーザーの取得
        member = interaction.guild.get_member(interaction.user.id)
        # ロール保有状況の取得
        role = member.get_role(ROLE_ID_MATTARI)
        # まったりロールを保有している場合は削除
        if role is not None:
            response_embed = discord.Embed(description=f"ℹ️ <@&{ROLE_ID_MATTARI}>を削除しました。", color=Color_OK)
            await member.remove_roles(role_mattari, reason="初心者用ボタンによる")
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer(ephemeral=True)  # noqa
            # DBからWargaming UIDを取得し代入
            user_info_result = await db.search_user(interaction.user.id)
            discord_id, account_id, region = user_info_result
            # 戦闘数の照会と代入
            wg_api_result = await api.wows_user_info(account_id, region)
            nickname, battles = wg_api_result
            # 戦績非公開の場合
            if battles == "private":
                # ボタンへのレスポンス
                response_embed = discord.Embed(description="⚠️ 戦績を公開にしてから再度お試しください。",
                                               color=Color_WARN)
                await interaction.followup.send(embed=response_embed, ephemeral=True)
            else:
                # 戦闘数が3000戦以上の場合
                if role is None and battles > 3000:
                    # Embedの作成と送信
                    response_embed = discord.Embed(description="⚠️ あなたは初心者ではありません。", color=Color_WARN)
                    await interaction.followup.send(embed=response_embed, ephemeral=True)
                # 戦闘数が3000戦以下の場合
                elif role is None and battles <= 3000:
                    # がつがつロールを保有している場合は削除
                    await member.remove_roles(role_gatsu, reason="初心者用ボタンによる")
                    # まったりロールを付与
                    await member.add_roles(role_mattari, reason="初心者用ボタンによる")
                    # ボタンへのレスポンス
                    response_embed = discord.Embed(description=f"ℹ️ <@&{ROLE_ID_MATTARI}>を付与しました。",
                                                   color=Color_OK)
                    await interaction.followup.send(embed=response_embed, ephemeral=True)

    @ui.button(label="がつがつ", emoji="🟠", style=discord.ButtonStyle.blurple, custom_id="gatugatu")  # noqa
    async def button_gatsu(self, interaction: discord.Interaction, button: ui.Button):
        """がつがつロール用ボタン押下時の処理"""
        # ギルドとロールの取得

        role_mattari = interaction.guild.get_role(ROLE_ID_MATTARI)
        role_gatsu = interaction.guild.get_role(ROLE_ID_GATSU)
        # ボタンを押したユーザーの取得
        member = interaction.guild.get_member(interaction.user.id)
        # ロール保有状況の取得
        role = member.get_role(ROLE_ID_GATSU)
        # がつがつロールを保有している場合は削除
        if role is not None:
            response_embed = discord.Embed(description=f"ℹ️ <@&{ROLE_ID_GATSU}>を削除しました。", color=Color_OK)
            await member.remove_roles(role_gatsu, reason="初心者用ボタンによる")
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer(ephemeral=True)  # noqa
            # DBからWargaming UIDを取得し代入
            user_info_result = await db.search_user(interaction.user.id)
            discord_id, account_id, region = user_info_result
            # 戦闘数の照会と代入
            wg_api_result = await api.wows_user_info(account_id, region)
            nickname, battles = wg_api_result
            # 戦績非公開の場合
            if battles == "private":
                # ボタンへのレスポンス
                response_embed = discord.Embed(description="⚠️ 戦績を公開にしてから再度お試しください。",
                                               color=Color_WARN)
                await interaction.followup.send(embed=response_embed, ephemeral=True)
            else:
                # 戦闘数が3000戦以上の場合
                if role is None and battles >= 3000:
                    response_embed = discord.Embed(description="⚠️ あなたは初心者ではありません。", color=Color_WARN)
                    await interaction.followup.send(embed=response_embed, ephemeral=True)
                # 戦闘数が3000戦以下の場合
                elif role is None and battles < 3000:
                    # まったりロールを保有している場合は削除
                    await member.remove_roles(role_mattari, reason="初心者用ボタンによる")
                    # がつがつロールを付与
                    await member.add_roles(role_gatsu, reason="初心者用ボタンによる")
                    # ボタンへのレスポンス
                    response_embed = discord.Embed(description=f"ℹ️ <@&{ROLE_ID_GATSU}>を付与しました。", color=Color_OK)
                    await interaction.followup.send(embed=response_embed, ephemeral=True)


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Newbie(bot))
    bot.add_view(view=NewbieButton())
