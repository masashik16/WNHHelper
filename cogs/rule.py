import os

import discord
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
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("newbie_role")

"""コマンドの実装"""


class Rule(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    """ルール同意ボタンの作成"""

    async def create_message(self, interaction: discord.Interaction):
        """ルール同意用メッセージの作成"""
        # ドロップダウンを含むビューを作成
        view = RuleButton()
        # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(view=view)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    async def create_message2(self, interaction: discord.Interaction):
        """認証用メッセージを作成"""
        # ドロップダウンを含むビューを作成
        view = NoRoleButton()
        # Embedの作成
        embed = discord.Embed(title="サーバー利用手続きについて",
                              description="このチャンネルが表示されている方は、何らかの理由により必要なロールが付与されていない状態です。"
                                          "\n下のボタンを押すと、ロールが付与されますので、画面の指示に従って手続きを進めてください。")
        # # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(embed=embed, view=view)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @commands.Cog.listener("on_member_join")
    async def member_join(self, member: discord.Member):
        role = member.guild.get_role(ROLE_ID_WAIT_AGREE_RULE)
        await member.add_roles(role, reason="参加時ロール付与")

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{interaction.command.name}」を使用しようとしましたが、権限不足により失敗しました。")


class RuleButton(discord.ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ルールに同意する", emoji="✅", style=discord.ButtonStyle.green, custom_id="Rule_Agree")  # noqa
    async def rule_agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ルール同意ボタン押下時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとロールの取得
        role_wait_agree_rule = interaction.guild.get_role(ROLE_ID_WAIT_AGREE_RULE)
        role_wait_auth = interaction.guild.get_role(ROLE_ID_WAIT_AUTH)
        role_authed = interaction.guild.get_role(ROLE_ID_AUTHED)
        # ボタンを押したユーザーを取得
        member = interaction.guild.get_member(interaction.user.id)
        # ユーザーがルール同意済かどうか確認
        role = member.get_role(ROLE_ID_WAIT_AGREE_RULE)
        # 未同意の場合
        if role is not None:
            user_info_result = await db.search_user(interaction.user.id)
            if user_info_result == "ERROR":
                role_list = member.roles
                if role_wait_agree_rule in role_list:
                    role_list.remove(role_wait_agree_rule)
                if role_wait_auth not in role_list:
                    role_list.append(role_wait_auth)
                # 反映
                await member.edit(roles=role_list, reason="ルール同意による（認証履歴なし）")
                # ボタンへのレスポンス
                response_embed = discord.Embed(title="ルールに同意いただきありがとうございます。",
                                               description="続いて<#1022770176082591836>から認証を行ってください。",
                                               color=Color_OK)
                await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
            else:
                discord_id, account_id, region = user_info_result
                role_list = member.roles
                if role_wait_agree_rule in role_list:
                    role_list.remove(role_wait_agree_rule)
                if role_authed not in role_list:
                    role_list.append(role_authed)
                # 戦闘数の照会と代入
                wg_api_result = await api.wows_info(account_id, region)
                nickname, battles = wg_api_result
                await member.edit(roles=role_list, reason="ルール同意による（認証履歴あり）")
                response_embed = discord.Embed(title="ルールに同意いただきありがとうございます。",
                                               description="過去に認証履歴があるため認証は不要です。"
                                                           "\nあなたのメインアカウントが下記の情報と異なる場合、お手数ですがhttps://discord.com/channels/977773343396728872/977773343824560131からご連絡ください。",
                                               color=Color_OK)
                response_embed.add_field(name="登録されているWoWSアカウント情報",
                                         value=f"サーバー：{region}\nIGN：{nickname}")
                await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa
        # 既に同意済みの場合
        else:
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="ℹ️ あなたは既にルールに同意しています。", color=Color_WARN)
            await interaction.followup.send(embed=response_embed, ephemeral=True)  # noqa


class NoRoleButton(discord.ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="必要なロールを取得する", style=discord.ButtonStyle.green,  # noqa
                       custom_id="role_none")
    async def none_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ルール同意ボタン押下時の処理"""
        # ギルドとロールの取得
        role_wait_agree_rule = interaction.guild.get_role(ROLE_ID_WAIT_AGREE_RULE)
        # ボタンを押したユーザーを取得
        member = interaction.guild.get_member(interaction.user.id)
        # ユーザーがルール同意済かどうか確認
        role = member.get_role(ROLE_ID_WAIT_AGREE_RULE)
        # 未同意の場合
        if role is None:
            await member.add_roles(role_wait_agree_rule, reason="ルール未同意ロール未付与のため付与")
            # ボタンへのレスポンス
            response_embed = discord.Embed(title="必要なロールが付与されました。",
                                           description="続いて<#977773343396728880>から手続きの流れをご確認ください。",
                                           color=Color_OK)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # 既に同意済みの場合
        else:
            # ボタンへのレスポンス
            response_embed = discord.Embed(description="ℹ️ すでに必要なロールが付与されています。", color=Color_WARN)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Rule(bot))
    bot.add_view(view=RuleButton())
    bot.add_view(view=NoRoleButton())
