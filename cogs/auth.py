import os

import discord
from discord import app_commands
from discord import ui
from discord.ext import commands
from dotenv import load_dotenv

import api
import db
from logs import logger
from server import wg_auth_link
from exception import discord_error

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("auth")


class Auth(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_message(self, interaction: discord.Interaction):
        """認証用メッセージを作成"""
        # # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(view=AuthMessageView())
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="ユーザー認証情報の登録・更新")
    @app_commands.checks.has_role(ROLE_ID_ADMIN)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.describe(member="登録するユーザー", wg_id="WoWSのプレイヤーID",
                           region="アカウントの存在するサーバー")
    @app_commands.choices(
        region=[
            discord.app_commands.Choice(name="ASIA", value="ASIA"),
            discord.app_commands.Choice(name="EU", value="EU"),
            discord.app_commands.Choice(name="NA", value="NA")
        ])
    async def manual_auth(self, interaction: discord.Interaction, member: discord.Member, wg_id: str, region: str):
        """手動でのサーバー認証処理"""
        # ギルドとロールの取得
        role_wait_agree_rule = interaction.guild.get_role(ROLE_ID_WAIT_AGREE_RULE)
        role_wait_auth = interaction.guild.get_role(ROLE_ID_WAIT_AUTH)
        role_authed = interaction.guild.get_role(ROLE_ID_AUTHED)
        role_list = member.roles
        # DBへの反映
        result = await db.add_user(member.id, wg_id, region)
        # データがなかった場合の処理
        if result == "ADDED":
            # ルール未同意・未認証ロールの削除
            if role_wait_agree_rule in role_list:
                role_list.remove(role_wait_agree_rule)
            if role_wait_auth in role_list:
                role_list.remove(role_wait_auth)
            # 認証済みロールが付与されていない場合は付与
            if role_authed not in role_list:
                role_list.append(role_authed)
            # 反映
            await member.edit(roles=role_list, reason="手動認証による")
            # コマンドへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 登録しました", color=Color_OK)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用し、{member.display_name}を手動で認証しました。")
        # すでに登録されていた場合の処理
        elif result == "UPDATED":
            # ルール未同意・未認証ロールの削除
            if role_wait_agree_rule in role_list:
                role_list.remove(role_wait_agree_rule)
            if role_wait_auth in role_list:
                role_list.remove(role_wait_auth)
            # 認証済みロールが付与されていない場合は追加
            if role_authed not in role_list:
                role_list.append(role_authed)
            # 反映
            await member.edit(roles=role_list, reason="手動認証による")
            # コマンドへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 更新しました", color=Color_OK)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用し、{member.display_name}を手動で認証しました。")
        # エラー処理
        else:
            error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa

    @app_commands.command(description="戦闘数確認")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="照会するユーザー")
    async def get_user_info(self, interaction: discord.Interaction, user: discord.User):
        # DBからWargaming UIDを取得し代入
        user_info_result = await db.search_user(user.id)
        # 取得に失敗した場合
        if user_info_result == "ERROR":
            response_embed = discord.Embed(description="⚠ そのユーザーは存在しません。")
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # 取得に成功した場合
        else:
            discord_id, account_id, region = user_info_result
            # WoWSのプロフィールURLの生成
            wows_url = await get_wows_url(account_id, region)
            # 戦闘数の照会と代入
            wg_api_result = await api.wows_user_info(account_id, region)
            nickname, battles = wg_api_result
            # 対象ユーザーのアバターと表示名の取得
            avatar = user.display_avatar.url
            server_name = user.display_name
            # Embedの作成
            if nickname == "ERROR":
                embed = discord.Embed(color=Color_ERROR)
                embed.add_field(name="Discordアカウント", value=f"<@{discord_id}>", inline=False)
                embed.add_field(name="アカウントID", value=f"{account_id}", inline=True)
                embed.add_field(name="IGN", value=f"取得不可", inline=True)
                embed.add_field(name="サーバー", value=f"{region}", inline=True)
                embed.add_field(name="エラー詳細",
                                value=f"PC版WoWSを一切プレイしていないため、IGN等を取得できませんでした。", inline=False)
                embed.set_author(name=f"{server_name}さんのWoWSアカウント情報", url=f"{wows_url}",
                                 icon_url=f"{avatar}")
                # Embedの送信
                await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、{server_name}の情報を照会しました。")
            # 戦績非公開の場合
            elif battles == "private":
                # Embedの作成
                embed = discord.Embed(color=Color_ERROR)
                embed.add_field(name="Discordアカウント", value=f"<@{discord_id}>", inline=True)
                embed.add_field(name="IGN", value=f"{nickname}", inline=True)
                embed.add_field(name="戦闘数", value="非公開", inline=True)
                embed.add_field(name="サーバー", value=f"{region}", inline=True)
                embed.set_author(name=f"{server_name}さんのWoWSアカウント情報", url=f"{wows_url}",
                                 icon_url=f"{avatar}")
                # Embedの送信
                await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、{server_name}の情報を照会しました。")
            # 戦闘数が3000戦以下の場合
            elif battles <= 3000:
                # Embedの作成
                embed = discord.Embed(color=Color_OK)
                embed.add_field(name="Discordアカウント", value=f"<@{discord_id}>", inline=True)
                embed.add_field(name="IGN", value=f"{nickname}", inline=True)
                embed.add_field(name="戦闘数", value=f"{battles}戦", inline=True)
                embed.add_field(name="サーバー", value=f"{region}", inline=True)
                embed.set_author(name=f"{server_name}さんのWoWSアカウント情報", url=f"{wows_url}",
                                 icon_url=f"{avatar}")
                # Embedの送信
                await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、{server_name}の情報を照会しました。")
            # 戦闘数が3000戦以上の場合
            else:
                # Embedの作成
                embed = discord.Embed()
                embed.add_field(name="Discordアカウント", value=f"<@{discord_id}>", inline=True)
                embed.add_field(name="IGN", value=f"{nickname}", inline=True)
                embed.add_field(name="戦闘数", value=f"{battles}戦", inline=True)
                embed.add_field(name="サーバー", value=f"{region}", inline=True)
                embed.set_author(name=f"{server_name}さんのWoWSアカウント情報", url=f"{wows_url}",
                                 icon_url=f"{avatar}")
                # Embedの送信
                await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、{server_name}の情報を照会しました。")

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        await discord_error(interaction.command.name, interaction, error, logger)


class AuthMessageView(ui.LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    text1 = ui.TextDisplay("## 認証について\n"
                           "本サーバーでは、DiscordアカウントおよびWargaming IDによる認証が必須となっています。\n"
                           "認証ボタンを押した後、WoWSのメインアカウントでログインしてください。\n"
                           "**（メインアカウントはご自身が保有するWoWSアカウントの中で一番戦闘数が多いものとします）**")
    text2 = ui.TextDisplay("### 取得する情報について\n"
                           "本サーバーでは運営のため以下の情報を収集します。\n"
                           "* Wargamingアカウントに関連する情報\n"
                           "  * SPA ID（数字からなる各プレイヤー固有のID）\n"
                           "  * IGN\n"
                           "  * WoWSのプレイ状況に関するデータ\n"
                           "* Discordアカウントに関連する情報\n"
                           "  * Discord ID（数字からなる各ユーザー固有のID）\n"
                           "  * Discord ユーザー名")
    container = ui.Container(text1, text2)

    action_row = ui.ActionRow()

    @action_row.button(label="認証はこちら", style=discord.ButtonStyle.green, custom_id="Auth_button")  # noqa
    async def auth_button(self, interaction: discord.Interaction, button: ui.Button):
        """認証ボタン押下時の処理"""
        # ボタンへのレスポンス
        link = wg_auth_link()
        # Embedを作成
        response_embed = discord.Embed(description="下記のURLからメインアカウントで認証を行ってください。")
        response_embed.add_field(name="リンクはこちら",
                                 value=f"{link}", inline=False)
        # Embedを送信
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa


# class AuthDropdownView(discord.ui.View):
#     def __init__(self, timeout=None):
#         super().__init__(timeout=timeout)
#
#     """ドロップダウンの作成"""
#
#     @discord.ui.select(
#         cls=discord.ui.Select,
#         custom_id="Auth",
#         placeholder="メインアカウントのサーバーを選択",
#         options=[
#             discord.SelectOption(label="アジア", value="ASIA", emoji="🇸🇬"),
#             discord.SelectOption(label="ヨーロッパ", value="EU", emoji="🇪🇺"),
#             discord.SelectOption(label="北アメリカ", value="NA", emoji="🇺🇸"),
#         ],
#     )
#     async def set_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
#         discord_id = interaction.user.id
#         region = select.values[0]
#         # ASIAサーバーが選択された場合
#         if region == "ASIA":
#             # ドロップダウンの選択項目を初期化
#             await interaction.message.edit(view=AuthDropdownView())
#             # 認証用リンクの生成
#
#             link = await discord_link()
#             # Embedを作成
#             response_embed = discord.Embed(description="下記のURLからメインアカウントで認証を行ってください。")
#             response_embed.add_field(name="リンクはこちら",
#                                      value=f"{link}", inline=False)
#             # Embedを送信
#             await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
#         # EUサーバーが選択された場合
#         elif region == "EU":
#             # ドロップダウンの選択項目を初期化
#             await interaction.message.edit(view=AuthDropdownView())
#             # 認証用リンクの生成
#             link = await discord_link()
#             # Embedを作成
#             response_embed = discord.Embed(description="下記のURLからメインアカウントで認証を行ってください。")
#             response_embed.add_field(name="リンクはこちら",
#                                      value=f"{link}", inline=False)
#             # Embedを送信
#             await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
#         # NAサーバーが選択された場合
#         elif region == "NA":
#             # ドロップダウンの選択項目を初期化
#             await interaction.message.edit(view=AuthDropdownView())
#             # 認証用リンクの生成
#             link = await discord_link()
#             # Embedを作成
#             response_embed = discord.Embed(description="下記のURLからメインアカウントで認証を行ってください。")
#             response_embed.add_field(name="リンクはこちら",
#                                      value=f"{link}", inline=False)
#             # Embedを送信
#             await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa


async def get_wows_url(account_id, region):
    """WoWSのプロフィールリンクの生成"""
    if region == "ASIA":
        return f"https://profile.worldofwarships.asia/statistics/{account_id}/"
    elif region == "EU":
        return f"https://profile.worldofwarships.eu/statistics/{account_id}/"
    elif region == "NA":
        return f"https://profile.worldofwarships.com/statistics/{account_id}/"


async def add_role_authed(bot, discord_id):
    """サーバーによる認証後のロール付与"""
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(discord_id)
    role_wait_auth = guild.get_role(ROLE_ID_WAIT_AUTH)
    role_authed = guild.get_role(ROLE_ID_AUTHED)
    role_list = member.roles
    # ルール未同意・未認証ロールの削除
    if role_wait_auth in role_list:
        role_list.remove(role_wait_auth)
    # 認証済みロールが付与されていない場合は追加
    if role_authed not in role_list:
        role_list.append(role_authed)
    # 反映
    await member.edit(roles=role_list, reason="WG ID認証完了による")


async def check_authed(bot, discord_id):
    """サーバーによる認証後のロール付与"""
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(int(discord_id))
    try:
        role_authed = member.get_role(ROLE_ID_AUTHED)
    except:
        return False
    if role_authed is None:
        return False
    else:
        return True


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Auth(bot))
    # bot.add_view(view=AuthDropdownView())
    bot.add_view(view=AuthMessageView())
