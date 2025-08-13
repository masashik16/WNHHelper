import os
import re

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from bot import check_developer
import chat_exporter
import io

from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
CHANNEL_ID_RULE = int(os.environ.get("CHANNEL_ID_RULE"))
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("cmd2")


class Commands2(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @app_commands.command(description="メッセージ編集用")
    # @app_commands.check(check_developer)
    # @app_commands.guilds(GUILD_ID)
    # @app_commands.guild_only()
    # @app_commands.rename(url="メッセージリンクのurl")
    # async def remove_view(self, interaction: discord.Interaction, url: str):
    #     """BOTが送信したメッセージの編集"""
    #     # URLがWNH内のメッセージリンクかどうか検証
    #     pattern = rf"(?<=https://discord.com/channels/{GUILD_ID})/([0-9]*)/([0-9]*)"
    #     result = re.search(pattern, url)
    #     # WNH内のメッセージリンクではない場合
    #     if result is None:
    #         await interaction.response.send_message("このサーバーのメッセージではありません", ephemeral=True)  # noqa
    #     # WNH内のメッセージリンクの場合
    #     else:
    #         # 値の代入とチャンネル・メッセージの取得
    #         guild = self.bot.get_guild(GUILD_ID)
    #         channel_id = int(result.group(1))
    #         channel = await guild.fetch_channel(channel_id)
    #         message_id = int(result.group(2))
    #         message = await channel.fetch_message(message_id)
    #         # メッセージを編集
    #         try:
    #             await message.edit(content=message.content, embed=message.embeds[0], view=None)
    #         # 送信者がこのBOTでない場合
    #         except discord.Forbidden:
    #             response_embed = discord.Embed(
    #                 description="⚠️ 権限がありません。<@1019156547449913414>が送信したメッセージではない可能性があります。",
    #                 color=Color_ERROR)
    #             await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
    #         else:
    #             # コマンドへのレスポンス
    #             response_embed = discord.Embed(description="ℹ️ 編集が完了しました", color=Color_OK)
    #             await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
    #             # ログの保存
    #             logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
    #                         f"がコマンド「{interaction.command.name}」を使用し、メッセージ「{url}」を編集しました。。")

    @app_commands.command(description="メッセージ送信用")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def send_message(self, interaction: discord.Interaction):
        """メッセージの送信"""
        channel = interaction.channel
        # Embedの作成
        embed = discord.Embed(title="招待リンクについて",
                              description=f"招待の際はこちらをご利用ください"
                                          f"\nhttps://discord.gg/jy4JcxQ3TK ")
        # Embedの送信
        await channel.send(content="### 招待リンクについて\n"
                                   "\n招待の際はこちらをご利用ください"
                                   "\nhttps://discord.gg/jy4JcxQ3TK")
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="メッセージ送信用")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def send_message2(self, interaction: discord.Interaction):
        """メッセージの送信"""
        channel = interaction.channel
        # Embedの作成
        embed = discord.Embed(title="サーバー規則改定のお知らせ",
                              description=f"この度、サーバー規則を改定することとなりましたので、お知らせいたします。")
        embed.add_field(name="改定日",
                        value="<t:1747062000:D>",
                        inline=False)
        embed.add_field(name="改定内容",
                        value="WNHをご利用頂くには、Wargaming IDを用いた認証が必須となっておりますが、認証に用いるメインアカウントについて、PC版WoWSを1戦以上プレイしていることが必須となりました。"
                              "\nまた、処罰の種類に認証手続の取消を追加しました。",
                        inline=False)
        embed.add_field(name="改定に伴う影響",
                        value="本改定によって再認証が必要となる場合、既にロールを変更させて頂いております。現在認証済みロールが付いている方は追加のご対応は必要ございません。",
                        inline=False)
        # Embedの送信
        await channel.send(content="", embed=embed)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="メッセージ編集用")
    @app_commands.check(check_developer)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @app_commands.rename(url="メッセージリンクのurl")
    async def edit_message2(self, interaction: discord.Interaction, url: str):
        """BOTが送信したメッセージの編集"""
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
            message = await channel.fetch_message(message_id)
            # 編集後の内容の定義
            embed = discord.Embed(title="各種問い合わせについて",
                                  description=f"最後の対応から24時間反応がないチケットはクローズします")
            embed.add_field(name="当サーバーに対するご意見/ご要望/その他お問い合わせ",
                            value="下記リストから「ご意見・ご要望・その他問い合わせ」」を選択してチケットを作成してください。",
                            inline=False)
            embed.add_field(name="公認クランプログラムへのお申し込み",
                            value="<@&983915259838488587>ロールをご希望の方は「」を選択してください。",
                            inline=False)
            embed.add_field(name="違反行為の報告",
                            value="*　不適切なメッセージを報告したい場合"
                                  "\n報告したいメッセージを右クリックして「アプリ」→「メッセージの報告」をクリックし、報告内容を記載して送信してください"
                                  "\n\n* 不適切なニックネームやアバター・VCでの違反行為等メッセージでの違反以外を報告したい場合"
                                  "\nユーザーを右クリックして「アプリ」→「ユーザーの報告」をクリックし、報告内容を記載して送信してください"
                                  "\n\n上記の手順でエラーが起こる場合は、下記リストから「違反行為の報告」を選択してチケットを作成してください。",
                            inline=False)
            embed.add_field(name="セクシャルハラスメント等の通報について",
                            value="セクシャルハラスメント等の通報で女性スタッフによる対応を希望する場合は<@767646985632481320>>のDMへご連絡ください。",
                            inline=False)
            # メッセージを編集
            try:
                await message.edit(embed=embed)
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
                            f"がコマンド「{interaction.command.name}」を使用し、メッセージ「{url}」を編集しました。。")

    @app_commands.command(description="HelperのDM削除")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def delete_dm(self, interaction: discord.Interaction):
        """DM削除"""
        user = interaction.user
        dm = await user.create_dm()
        async for message in dm.history(limit=200):
            if message.author == self.bot.user:
                await message.delete()
                # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 完了しました", color=Color_OK)
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


async def send_dm_gas_5thcup(bot, discord_id, types):
    """サーバーによる認証後のロール付与"""
    user = await bot.fetch_user(discord_id)
    if types == "entry":
        response_embed = discord.Embed(title="WNH CUP the 5thへの選手申込が完了しました。",
                                       description="")
    else:
        response_embed = discord.Embed(title="WNH CUP the 5thへの選手申込をキャンセルしました。",
                                       description="")
    await user.send(embed=response_embed)


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Commands2(bot))
