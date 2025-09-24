import os
import re
from datetime import datetime, timedelta

import discord
import pytz
from discord import app_commands
from discord import ui
from discord.ext import commands
from dotenv import load_dotenv

import db
from exception import discord_error
from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_SENIOR_MOD = int(os.environ.get("ROLE_ID_SENIOR_MOD"))
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
CHANNEL_ID_MOD_CASE = int(os.environ.get("CHANNEL_ID_MOD_CASE"))
CHANNEL_ID_RULE = int(os.environ.get("CHANNEL_ID_RULE"))
CHANNEL_ID_MOD_LOG = int(os.environ.get("CHANNEL_ID_MOD_LOG"))
CHANNEL_ID_REPORT_LOG = int(os.environ.get("CHANNEL_ID_REPORT_LOG"))
CHANNEL_ID_MOD_CONTACT_LOG = int(os.environ.get("CHANNEL_ID_MOD_CONTACT_LOG"))
ENV = os.environ.get("ENV")
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("mod")
JP = pytz.timezone("Asia/Tokyo")

# モデレーション種類の辞書の定義
MODERATION_TYPE = {1: "厳重注意", 2: "警告", 3: "発言禁止", 4: "BAN", 5: "処罰変更（内容変更）", 6: "処罰変更（取消）"}
CHANGE_TYPE = {1: "内容変更", 2: "取消"}


class Moderation(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.report_message_menu = app_commands.ContextMenu(
            name="メッセージを報告",
            callback=self.report_message,
        )
        self.bot.tree.add_command(self.report_message_menu)
        self.report_message_menu.error(self.cog_app_command_error)

        self.report_user_menu = app_commands.ContextMenu(
            name="ユーザーを報告",
            callback=self.report_user,
        )
        self.bot.tree.add_command(self.report_user_menu)
        self.report_user_menu.error(self.cog_app_command_error)

        self.delete_message_menu = app_commands.ContextMenu(
            name="メッセージを削除（管理者用）",
            callback=self.delete_message,
        )
        self.bot.tree.add_command(self.delete_message_menu)
        self.delete_message_menu.error(self.cog_app_command_error)

        self.warn_user_menu = app_commands.ContextMenu(
            name="ユーザーを警告（管理者用）",
            callback=self.warn_user,
        )
        self.bot.tree.add_command(self.warn_user_menu)
        self.warn_user_menu.error(self.cog_app_command_error)

        self.warn_profile_menu = app_commands.ContextMenu(
            name="不適切なプロフィールの変更指示（管理者用）",
            callback=self.warn_profile,
        )
        self.bot.tree.add_command(self.warn_profile_menu)
        self.warn_profile_menu.error(self.cog_app_command_error)

    @app_commands.command(description="MODログ（単一）の取得")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @discord.app_commands.rename(case_id="ケース番号")
    async def get_modlog_single(self, interaction: discord.Interaction, case_id: int):
        """モデレーションログ（単一）の取得"""
        # DBからケース情報を取得
        mod_case = await db.get_modlog_single(case_id)
        # ケースが存在しない場合
        if not mod_case:
            embed = discord.Embed(description="⚠️ データがありません", color=Color_ERROR)
            await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
        else:
            # 変数に代入
            case_id, moderate_type, user_id, moderator_id, length, reason, datetime_, point, thread_id, change_type, changed_case_id, change_datetime = mod_case
            # モデレーション種類を数値から変換
            moderation_type = MODERATION_TYPE[moderate_type]
            # 違反ユーザー情報を取得
            user = await self.bot.fetch_user(int(user_id))
            username = user.name
            # ケース情報メッセージ（Embed）を作成
            embed = discord.Embed(title=f"ケース{case_id} | {moderation_type} | {username}")
            embed.add_field(name="ユーザー",
                            value=f"<@{user_id}>")
            if change_datetime is not None:
                if change_type == 1:
                    embed.add_field(name="変更種類",
                                    value=f"内容変更済",
                                    inline=False)
                    embed.add_field(name="変更後のケース番号",
                                    value=f"{changed_case_id}",
                                    inline=False)
                    embed.add_field(name="変更日時",
                                    value=f"{change_datetime}",
                                    inline=False)
                else:
                    embed.add_field(name="変更種類",
                                    value=f"取消済",
                                    inline=False)

                    embed.add_field(name="取消日時",
                                    value=f"{change_datetime}",
                                    inline=False)
            else:
                embed.add_field(name="モデレーター",
                                value=f"<@{moderator_id}>")
                if length is not None:
                    embed.add_field(name="期間",
                                    value=f"{length}日", inline=False)
                if not point == 0:
                    embed.add_field(name="付与ポイント",
                                    value=f"{point}", inline=False)
                embed.add_field(name="処罰理由",
                                value=f"{reason}", inline=False)
                embed.add_field(name="記録へのリンク",
                                value=f"<#{thread_id}>", inline=False)
                embed.set_footer(text=f"UID：{user_id}・{datetime_}")
            # ケース情報を送信
            await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用してケース{case_id}の情報を取得しました。")

    @app_commands.command(description="MODログ（ユーザー単位）の取得")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @discord.app_commands.rename(user="ログを取得したいユーザー")
    async def get_modlog_multi(self, interaction: discord.Interaction, user: discord.User):
        """モデレーションログ（ユーザー単位）の取得"""
        # DBからケース情報を取得
        mod_case = await db.get_modlog_multi(user_id=user.id)
        # DBからポイントを取得
        point = await db.get_point(user_id=user.id)
        if point is None:
            point = 0
        else:
            point = point[0]
        # 違反ユーザー情報を取得
        username = user.name
        embed = discord.Embed(title=f"{username}に対するモデレーション記録 | 累積ポイント：{point}")
        # ケースが存在しない場合
        if not mod_case:
            response_embed = discord.Embed(description="⚠️ データがありません", color=Color_ERROR)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ケース情報メッセージ（Embed）を作成
        else:
            await interaction.response.defer(ephemeral=True)  # noqa
            # 複数のケースを1メッセージへ
            for case in mod_case:
                # 変数に代入
                case_id, moderate_type, user_id, moderator_id, length, reason, datetime_, point, thread_id, change_type, changed_case_id, change_datetime = case
                # モデレーション種類を数値から変換
                moderation_type = MODERATION_TYPE[moderate_type]
                # モデレーター情報を取得
                moderator = await self.bot.fetch_user(int(moderator_id))
                moderator_name = moderator.name
                # メッセージに追加
                if change_datetime is not None:
                    if change_type == 1:
                        embed.add_field(name=f"ケース{case_id}",
                                        value=f"変更種類：内容変更済\n変更後のケース番号：{changed_case_id}\n変更日時：{change_datetime}",
                                        inline=False)
                    else:
                        embed.add_field(name=f"ケース{case_id}",
                                        value=f"変更種類：取消済\n取消日時：{change_datetime}",
                                        inline=False)
                elif length is None and point is None:
                    embed.add_field(name=f"ケース{case_id}",
                                    value=f"種類：{moderation_type}\nモデレーター：{moderator_name}"
                                          f"\n理由：{reason}\n処罰日時：{datetime_}",
                                    inline=False)
                elif length is None:
                    embed.add_field(name=f"ケース{case_id}",
                                    value=f"種類：{moderation_type}\nモデレーター：{moderator_name}\n付与ポイント：{point}"
                                          f"\n処罰理由：{reason}\n処罰日時：{datetime_}",
                                    inline=False)
                else:
                    embed.add_field(name=f"ケース{case_id}",
                                    value=f"種類：{moderation_type}\nモデレーター：{moderator_name}\n期間：{length}日"
                                          f"\n処罰理由：{reason}\n処罰日時：{datetime_}",
                                    inline=False)
            # コマンドへのレスポンス
            await interaction.followup.send(embed=embed, ephemeral=True)
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用してユーザー：{username}（UID：{user.id}）のモデレーション記録を取得しました。")

    @app_commands.command(description="厳重注意の発行")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="警告対象のユーザー", warn_type_1="違反内容", evidence1="証拠画像1",
                                 evidence2="証拠画像2", evidence3="証拠画像3", evidence4="証拠画像4")
    @app_commands.choices(
        warn_type_1=[
            discord.app_commands.Choice(name="無許可の宣伝行為", value="無許可の宣伝行為"),
            discord.app_commands.Choice(name="外部リンクの投稿", value="外部リンクの投稿"),
            discord.app_commands.Choice(name="外部戦績サイト等のコンテンツの投稿",
                                        value="外部戦績サイト等のコンテンツの投稿"),
            discord.app_commands.Choice(name="処罰に関する議論", value="処罰に関する議論"),
            discord.app_commands.Choice(name="他人に対する攻撃", value="他人に対する攻撃"),
            discord.app_commands.Choice(name="不適切な表現", value="不適切な表現"),
            discord.app_commands.Choice(name="スパム行為", value="スパム行為"),
            discord.app_commands.Choice(name="オフトピック投稿", value="オフトピック投稿"),
            discord.app_commands.Choice(name="Modに関する投稿", value="Modに関する投稿"),
            discord.app_commands.Choice(name="初心者が入りにくい話題の高頻度投稿",
                                        value="初心者が入りにくい話題の高頻度投稿"),
            discord.app_commands.Choice(name="メインアカウント以外での本人確認",
                                        value="メインアカウント以外での本人確認"),
            discord.app_commands.Choice(name="晒し行為", value="晒し行為"),
            discord.app_commands.Choice(name="晒し行為（IGNがマスク処理されていないSS）",
                                        value="晒し行為（IGNがマスク処理されていないSS）"),
            discord.app_commands.Choice(name="DMによる迷惑行為", value="DMによる迷惑行為"),
            discord.app_commands.Choice(name="政治・宗教に関する投稿", value="政治・宗教に関する投稿"),
            discord.app_commands.Choice(name="円滑な運営を妨げる行為", value="円滑な運営を妨げる行為"),
            discord.app_commands.Choice(name="チャンネル規則への違反", value="チャンネル規則への違反"),
            discord.app_commands.Choice(name="センシティブなコンテンツの投稿", value="センシティブなコンテンツの投稿"),
            discord.app_commands.Choice(name="不適切なアバター・ユーザー名・カスタムステータスの使用",
                                        value="不適切なアバター・ユーザー名・カスタムステータスの使用"),
            discord.app_commands.Choice(name="リーク等不明確な情報の投稿", value="リーク等不明確な情報の投稿"),
            discord.app_commands.Choice(name="違反投稿に対する返信（禁止行為に類する行為）",
                                        value="違反投稿に対する返信（禁止行為に類する行為）"),
            discord.app_commands.Choice(name="その他管理者が不適切と判断した行為",
                                        value="その他管理者が不適切と判断した行為")
        ])
    async def warn_without_point(self, interaction: discord.Interaction, user: discord.User, warn_type_1: str,
                                 evidence1: discord.Attachment, evidence2: discord.Attachment = None,
                                 evidence3: discord.Attachment = None, evidence4: discord.Attachment = None):
        """厳重注意の発行"""
        # ギルドとチャンネルの取得
        guild = self.bot.get_guild(GUILD_ID)
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        # 違反ユーザー情報を取得
        await interaction.response.defer(ephemeral=True)  # noqa
        # コマンド実行日時の取得
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # 証拠画像を添付できる形式へ変換
        attachment = [evidence1, evidence2, evidence3, evidence4]
        evidence = []
        evidence_dm = []
        for e in attachment:
            try:
                f = await e.to_file()
            except AttributeError:
                break
            evidence.append(f)
        # DBへケース情報を保存
        case_id = await db.save_modlog(moderate_type=1, user_id=user.id, moderator_id=interaction.user.id, length="",
                                       reason=warn_type_1, datetime=action_datetime, point=0)
        # 警告メッセージの作成
        dm_embed = discord.Embed(title="厳重注意",
                                 description="WNH運営チームです。あなたは下記の内容で厳重注意となりました。"
                                 )
        dm_embed.add_field(name="ケース番号",
                           value=f"{case_id}", inline=False)
        dm_embed.add_field(name="厳重注意の理由",
                           value=f"{warn_type_1}", inline=False)
        dm_embed.add_field(name="発行日時",
                           value=f"{action_datetime}", inline=False)
        dm_embed.add_field(name="内容のスクリーンショット",
                           value=f"スクリーンショットはこのメッセージの下に添付されます。", inline=False)
        if warn_type_1 == "不適切なアバター・ユーザー名・カスタムステータスの使用":
            dm_embed.add_field(name="内容に関する指示",
                               value=f"本警告から24時間以内に内容の解消が行われない場合、警告が発行されます。",
                               inline=False)
        elif warn_type_1 == "違反投稿に対する返信（禁止行為に類する行為）":
            dm_embed.add_field(name="違反投稿に対する返信は、更なる違反投稿を誘発するため、禁止されています。",
                               value=f"違反投稿を見つけた際は、返信することなく、WNH運営チームまでご連絡ください。\nなお、本厳重注意に伴うサーバーの利用制限等はありません。",
                               inline=False)
        dm_embed.add_field(name="この厳重注意に対する質問・申立",
                           value=f"この厳重注意に対する質問・申立は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c",
                           inline=False)
        # 記録CHへケース情報を送信
        log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                   content=f"ユーザー情報：{user.mention}\nモデレーター：<@{interaction.user.id}>"  # noqa
                                                           f"\n処罰種類：厳重注意\n違反内容：{warn_type_1}",  # noqa
                                                   files=evidence)  # noqa
        # ログCHへ送信するケース情報（Embed）を作成
        log_embed = discord.Embed(title=f"ケース{case_id} | 厳重注意 | {user.name}")
        log_embed.add_field(name="ユーザー",
                            value=user.mention)
        log_embed.add_field(name="モデレーター",
                            value=f"<@{interaction.user.id}>")
        log_embed.add_field(name="処罰理由",
                            value=f"{warn_type_1}", inline=False)
        log_embed.add_field(name="記録へのリンク",
                            value=f"<#{log.thread.id}>", inline=False)  # noqa
        log_embed.set_footer(text=f"UID：{user.id}・{action_datetime}")
        # ログCHへケース情報を送信
        await channel_mod_log.send(embed=log_embed)
        # DBへケースIDと記録スレッドIDを保存
        await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
        # 証拠画像を添付できる形式へ変換
        for e in log.message.attachments:  # noqa
            try:
                f = await e.to_file()
            except AttributeError:
                break
            evidence_dm.append(f)
        # 違反ユーザーのDMへ警告を送信
        member = guild.get_member(user.id)
        if member is not None:
            try:
                await user.send(embed=dm_embed)
                await user.send(files=evidence_dm)
            except discord.Forbidden:
                channel = await guild.fetch_channel(CHANNEL_ID_RULE)
                thread = await channel.create_thread(name=f"ケース{case_id} | 警告", reason=f"ケース{case_id} ",
                                                     invitable=False)
                await thread.edit(locked=True)
                await thread.send(user.mention)
                await thread.send(embed=dm_embed)
                await thread.send(files=evidence_dm)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 厳重注意を発行しました", color=Color_OK)
        await interaction.followup.send(embed=response_embed)
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用し、ユーザー：{user.display_name}（UID：{user.id}）に厳重注意を発行しました。")

    @app_commands.command(description="警告の発行")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="警告対象のユーザー", point="付与ポイント", warn_type_2="違反内容",
                                 evidence1="証拠画像1",
                                 evidence2="証拠画像2", evidence3="証拠画像3", evidence4="証拠画像4")
    @app_commands.choices(
        warn_type_2=[
            discord.app_commands.Choice(name="無許可の宣伝行為", value="無許可の宣伝行為"),
            discord.app_commands.Choice(name="外部リンクの投稿", value="外部リンクの投稿"),
            discord.app_commands.Choice(name="外部戦績サイト等のコンテンツの投稿",
                                        value="外部戦績サイト等のコンテンツの投稿"),
            discord.app_commands.Choice(name="処罰に関する議論", value="処罰に関する議論"),
            discord.app_commands.Choice(name="他人に対する攻撃", value="他人に対する攻撃"),
            discord.app_commands.Choice(name="不適切な表現", value="不適切な表現"),
            discord.app_commands.Choice(name="スパム行為", value="スパム行為"),
            discord.app_commands.Choice(name="オフトピック投稿", value="オフトピック投稿"),
            discord.app_commands.Choice(name="Modに関する投稿", value="Modに関する投稿"),
            discord.app_commands.Choice(name="初心者が入りにくい話題の高頻度投稿",
                                        value="初心者が入りにくい話題の高頻度投稿"),
            discord.app_commands.Choice(name="メインアカウント以外での本人確認",
                                        value="メインアカウント以外での本人確認"),
            discord.app_commands.Choice(name="晒し行為", value="晒し行為"),
            discord.app_commands.Choice(name="晒し行為（IGNがマスク処理されていないSS）",
                                        value="晒し行為（IGNがマスク処理されていないSS）"),
            discord.app_commands.Choice(name="DMによる迷惑行為", value="DMによる迷惑行為"),
            discord.app_commands.Choice(name="政治・宗教に関する投稿", value="政治・宗教に関する投稿"),
            discord.app_commands.Choice(name="違法行為並びに同行為に関する投稿",
                                        value="違法行為並びに同行為に関する投稿"),
            discord.app_commands.Choice(name="各種サービス規約違反行為及び同行為に関する投稿",
                                        value="各種サービス規約違反行為及び同行為に関する投稿"),
            discord.app_commands.Choice(name="サーバーの設定ミスを悪用する行為",
                                        value="サーバーの設定ミスを悪用する行為"),
            discord.app_commands.Choice(name="処罰を回避する行為", value="処罰を回避する行為"),
            discord.app_commands.Choice(name="円滑な運営を妨げる行為", value="円滑な運営を妨げる行為"),
            discord.app_commands.Choice(name="チャンネル規則への違反", value="チャンネル規則への違反"),
            discord.app_commands.Choice(name="センシティブなコンテンツの投稿", value="センシティブなコンテンツの投稿"),
            discord.app_commands.Choice(name="不適切なアバター・ユーザー名・カスタムステータスの使用",
                                        value="不適切なアバター・ユーザー名・カスタムステータスの使用"),
            discord.app_commands.Choice(name="リーク等不明確な情報の投稿", value="リーク等不明確な情報の投稿"),
            discord.app_commands.Choice(name="その他管理者が不適切と判断した行為",
                                        value="その他管理者が不適切と判断した行為")
        ])
    async def warn_with_point(self, interaction: discord.Interaction, user: discord.User, point: int, warn_type_2: str,
                              evidence1: discord.Attachment, evidence2: discord.Attachment = None,
                              evidence3: discord.Attachment = None, evidence4: discord.Attachment = None):
        """警告の発行"""
        # ギルドとチャンネルの取得
        guild = self.bot.get_guild(GUILD_ID)
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        # ポイントが0の場合は拒否
        if point == 0:
            response_embed = discord.Embed(description="⚠️ 0ポイントの場合はポイントなし用コマンドで発行してください",
                                           color=Color_ERROR)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer(ephemeral=True)  # noqa
            # ユーザーの保有ポイントを取得
            old_point = await db.get_point(user_id=user.id)
            if old_point is None:
                new_point = point
            else:
                new_point = old_point[0] + point
            # コマンド実行日時の取得
            dt = datetime.now(JP)
            action_datetime = dt.strftime("%Y/%m/%d %H:%M")
            # 証拠画像を添付できる形式へ変換
            attachment = [evidence1, evidence2, evidence3, evidence4]
            evidence = []
            evidence_dm = []
            for e in attachment:
                try:
                    f = await e.to_file()
                except AttributeError:
                    break
                evidence.append(f)
            # DBへケース情報を保存
            case_id = await db.save_modlog(moderate_type=2, user_id=user.id, moderator_id=interaction.user.id,
                                           length="",
                                           reason=warn_type_2, datetime=action_datetime, point=point)
            # DBのポイントを更新
            await db.save_point(user_id=user.id, point=new_point)
            # 警告メッセージの作成
            dm_embed = discord.Embed(title="警告",
                                     description="WNH運営チームです。あなたに対して下記の内容で警告が発行されました。"
                                     )

            dm_embed.add_field(name="ケース番号",
                               value=f"{case_id}", inline=False)
            dm_embed.add_field(name="違反内容",
                               value=f"{warn_type_2}", inline=False)
            dm_embed.add_field(name="発行日時",
                               value=f"{action_datetime}", inline=False)
            dm_embed.add_field(name="違反内容のスクリーンショット",
                               value=f"スクリーンショットはこのメッセージの下に添付されます。", inline=False)
            if warn_type_2 == "不適切なアバター・ユーザー名・カスタムステータスの使用":
                dm_embed.add_field(name="違反内容に関する指示",
                                   value=f"本警告から24時間以内に違反内容の解消が行われない場合、再度警告が発行されます。",
                                   inline=False)
            dm_embed.add_field(name="この処罰に対する質問・申立",
                               value=f"この処罰に対する質問・申立は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c"
                                     f"\n\n尚、質問・申立の期限はこの警告を受けた日から3日以内とします。", inline=False)
            # 記録CHへケース情報を送信
            log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                       content=f"ユーザー情報：{user.mention}\nモデレーター：<@{interaction.user.id}>"  # noqa
                                                               f"\n処罰種類：警告\n付与ポイント：{point}\n処罰理由：{warn_type_2}",
                                                       # noqa
                                                       files=evidence)  # noqa
            # ログCHへ送信するケース情報（Embed）を作成
            log_embed = discord.Embed(title=f"ケース{case_id} | 警告 | {user.name}")
            log_embed.add_field(name="ユーザー",
                                value=user.mention)
            log_embed.add_field(name="モデレーター",
                                value=f"<@{interaction.user.id}>")
            log_embed.add_field(name="付与ポイント",
                                value=f"{point}", inline=False)
            log_embed.add_field(name="処罰理由",
                                value=f"{warn_type_2}", inline=False)
            log_embed.add_field(name="記録へのリンク",
                                value=f"<#{log.thread.id}>", inline=False)  # noqa
            log_embed.set_footer(text=f"UID：{user.id}・{action_datetime}")
            # ログCHへケース情報を送信
            await channel_mod_log.send(embed=log_embed)
            # DBへケースIDと記録スレッドIDを保存
            await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
            # 証拠画像を添付できる形式へ変換
            for e in log.message.attachments:  # noqa
                try:
                    f = await e.to_file()
                except AttributeError:
                    break
                evidence_dm.append(f)
            # 違反ユーザーのDMへ警告を送信
            member = guild.get_member(user.id)
            if member is not None:
                try:
                    await user.send(embed=dm_embed)
                    await user.send(files=evidence_dm)
                except discord.Forbidden:
                    channel = await guild.fetch_channel(CHANNEL_ID_RULE)
                    thread = await channel.create_thread(name=f"ケース{case_id} | 警告", reason=f"ケース{case_id} ",
                                                         invitable=False)
                    await thread.edit(locked=True)
                    await thread.send(user.mention)
                    await thread.send(embed=dm_embed)
                    await thread.send(files=evidence_dm)
            # コマンドへのレスポンス
            if new_point == 1:
                response_embed = discord.Embed(description="ℹ️ 警告を発行しました", color=Color_OK)
                await interaction.followup.send(embed=response_embed)
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、ユーザー：{user.display_name}（UID：{user.id}）"
                            f"に警告（{point}ポイント）を発行しました。")
            # 5ポイント以上のためBAN
            elif new_point >= 5:
                await auto_ban(interaction=interaction, base_case_id=case_id, member=user,  # noqa
                               base_thread_id=log.thread.id)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、ユーザー：{user.display_name}（UID：{user.id}）"
                            f"に警告（{point}ポイント）を発行しました。")
            # 2～4ポイントのため一定期間発言禁止
            else:
                await auto_timeout(interaction=interaction, base_case_id=case_id, member=user, point=new_point,
                                   base_thread_id=log.thread.id)  # noqa
                # ログの保存
                logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                            f"がコマンド「{interaction.command.name}」を使用し、ユーザー：{user.display_name}（UID：{user.id}）"
                            f"に警告（{point}ポイント）を発行しました。")

    @app_commands.command(description="対応実施通知の送信")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="送信先のユーザー", msg_type="種別")
    @app_commands.choices(
        msg_type=[
            discord.app_commands.Choice(name="メッセージ削除", value="不適切な投稿"),
            discord.app_commands.Choice(name="ユーザー名等の変更", value="不適切なユーザー名やアバターの使用")
        ])
    async def send_mod_message(self, interaction: discord.Interaction, user: discord.User, msg_type: str):
        """申立に関する対応メッセージ"""
        guild = self.bot.get_guild(GUILD_ID)
        embed = discord.Embed(title="モデレーション実施通知",
                              description="こちらはWNH運営チームです。"
                                          f"\nWNHにおいて、あなたが{msg_type}を行っていることが確認できたため、対応を行いました。"
                                          "\n詳細については、後ほどご連絡いたします。")
        embed.add_field(name="処罰に対する申立について",
                        value="処罰に対する申立については、後ほど送信されるDMをご確認ください。")
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            channel = await guild.fetch_channel(CHANNEL_ID_RULE)
            thread = await channel.create_thread(name=f"モデレーション実施通知",
                                                 reason=f"モデレーション実施通知の送信",
                                                 invitable=False)
            await thread.edit(locked=True)
            await thread.send(user.mention)
            await thread.send(embed=embed)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用し、{user.display_name}(UID:{user.id})にモデレーション通知を送信しました。")

    @app_commands.command(description="処罰内容の変更")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(change_type="変更内容", old_case_id="変更するケース番号", point="変更後のポイント",
                                 total_point="変更後の累積ポイント")
    @app_commands.choices(
        change_type=[
            discord.app_commands.Choice(name="処罰内容変更", value=1),
            discord.app_commands.Choice(name="処罰取消", value=2)
        ])
    async def change_case(self, interaction: discord.Interaction, old_case_id: int, change_type: int,
                          point: int, total_point: int):
        """処罰内容の変更"""
        # ギルドとチャンネルの取得
        guild = self.bot.get_guild(GUILD_ID)
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        # DBからケース情報を取得
        mod_case = await db.get_modlog_single(old_case_id)
        # ケースが存在しない場合
        if not mod_case:
            embed = discord.Embed(description="⚠️ データがありません", color=Color_ERROR)
            await interaction.response.send_message(embed=embed, ephemeral=True)  # noqa
        else:
            # 変数に代入
            old_case_id, moderate_type_db, user_id, moderator_id, length, reason, datetime_, old_point, thread_id, change_type_db, changed_case_id_db, change_datetime_db = mod_case
            # 違反ユーザー情報を取得
            user = await self.bot.fetch_user(int(user_id))
            await interaction.response.defer(ephemeral=True)  # noqa
            # コマンド実行日時の取得
            dt = datetime.now(JP)
            action_datetime = dt.strftime("%Y/%m/%d %H:%M")
            # DBへケース情報を保存
            if change_type == 1:
                moderate_type = 5
            else:
                moderate_type = 6
            case_id = await db.save_modlog(moderate_type=moderate_type, user_id=user.id,
                                           moderator_id=interaction.user.id,
                                           length="",
                                           reason=f"{old_case_id}への申立による", datetime=action_datetime, point=point)
            await db.update_modlog(old_case_id=old_case_id, change_type=change_type, new_case_id=case_id,
                                   change_datetime=action_datetime)
            # DBのポイントを更新
            await db.save_point(user_id=user.id, point=total_point)
            # 警告メッセージの作成
            change_type_str = CHANGE_TYPE[change_type]
            # 記録CHへケース情報を送信
            thread = await guild.fetch_channel(thread_id)
            log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                       content=f"ユーザー情報：{user.mention}\nモデレーター：<@{interaction.user.id}>"  # noqa
                                                               f"\n処罰種類：処罰内容変更\n変更種類：{change_type_str}\n原ケース番号：{thread.jump_url}\n変更後の付与ポイント：{point}\n変更後の累積ポイント：{total_point}")

            messages = [message async for message in thread.history(oldest_first=True)]
            content = messages[0].content
            if change_type == 1:
                await messages[0].edit(
                    content=f"{content}\n\n処罰内容変更済\n変更処理ケース番号：{log.thread.jump_url}")  # noqa
            else:
                await messages[0].edit(content=f"{content}\n\n処罰取消済")
            # ログCHへ送信するケース情報（Embed）を作成
            log_embed = discord.Embed(title=f"ケース{case_id} | 処罰内容変更 | {user.name}")
            log_embed.add_field(name="ユーザー",
                                value=user.mention)
            log_embed.add_field(name="モデレーター",
                                value=f"<@{interaction.user.id}>")
            log_embed.add_field(name="原ケース番号",
                                value=f"ケース{old_case_id}", inline=False)
            log_embed.add_field(name="変更種類",
                                value=f"{change_type_str}", inline=False)
            log_embed.add_field(name="変更後の付与ポイント",
                                value=f"{point}", inline=False)
            log_embed.add_field(name="記録へのリンク",
                                value=f"<#{log.thread.id}>", inline=False)  # noqa
            log_embed.set_footer(text=f"UID：{user.id}・{action_datetime}")
            # ログCHへケース情報を送信
            await channel_mod_log.send(embed=log_embed)
            # DBへケースIDと記録スレッドIDを保存
            await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
            # コマンドへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 処罰内容を変更しました", color=Color_OK)
            await interaction.followup.send(embed=response_embed)
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がコマンド「{interaction.command.name}」を使用し、ケース{old_case_id}"
                        f"の内容を変更しました。")

    @app_commands.command(description="処罰に対する申立対応用メッセージの送信")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="送信先のユーザー", msg_type="種別", case_id="ケース番号",
                                 comment_url="コメント内容に設定するメッセージのリンク")
    @app_commands.describe(case_id="例：1 複数の場合：1、5")
    @app_commands.choices(
        msg_type=[
            discord.app_commands.Choice(name="受付", value="受付"),
            discord.app_commands.Choice(name="棄却", value="棄却"),
            discord.app_commands.Choice(name="承認（処罰内容変更）", value="承認（処罰内容変更）"),
            discord.app_commands.Choice(name="承認（処罰取消）", value="承認（処罰取消）")
        ])
    async def send_appeal_message(self, interaction: discord.Interaction, user: discord.User, msg_type: str,
                                  case_id: str, comment_url: str = None):
        """申立に関する対応メッセージ"""
        guild = self.bot.get_guild(GUILD_ID)
        if msg_type == "受付":
            embed = discord.Embed(title="処罰に対する質問・申立を受け付けました。",
                                  description="以下のケース番号の処罰について、質問・申立を受け付けました。"
                                              "\nこれより、運営チームにて審査を行います。"
                                              "\n審査結果については、後日ご連絡いたします。")
            embed.add_field(name="受付したケース番号", value=f"{case_id}")
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                channel = await guild.fetch_channel(CHANNEL_ID_RULE)
                thread = await channel.create_thread(name=f"ケース{case_id}に関する質問・申立について",
                                                     reason=f"ケース{case_id}に関する質問・申立対応 ",
                                                     invitable=False)
                await thread.edit(locked=True)
                await thread.send(user.mention)
                await thread.send(embed=embed)
            # コマンドへのレスポンス
            response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
            await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        elif msg_type != "受付" and comment_url is not None:
            # URLがWNH内のメッセージリンクかどうか検証
            pattern = rf"(?<=https://discord.com/channels/{GUILD_ID})/([0-9]*)/([0-9]*)"
            result = re.search(pattern, comment_url)
            # WNH内のメッセージリンクではない場合
            if result is None:
                error_embed = discord.Embed(description="⚠️ このサーバーのメッセージではありません。。",
                                            color=Color_ERROR)
                await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            else:
                channel_id = int(result.group(1))
                channel = await guild.fetch_channel(channel_id)
                message_id = int(result.group(2))
                message = await channel.fetch_message(message_id)
                embed = discord.Embed(title=f"ケース{case_id}に対する質問・申立審査結果",
                                      description="あなたから質問・申立があった以下のケース番号の処罰について、次の通り審査しましたので通知します。")
                embed.add_field(name="ケース番号", value=f"{case_id}", inline=False)
                embed.add_field(name="審査結果", value=f"{msg_type}", inline=False)
                embed.add_field(name="コメント", value=message.content, inline=False)
                if not msg_type == "棄却":
                    embed.add_field(name="処罰内容の変更の反映について",
                                    value="反映までに数日かかる場合がございます。\n予めご了承ください。")
                view = SendAppealView(user, case_id, embed)
                await interaction.response.send_message(content=f"下記内容で<@{user.id}>に送信します。よろしいですか？",
                                                        # noqa
                                                        embed=embed, view=view, ephemeral=True)
        else:
            error_embed = discord.Embed(description="⚠️ 受付以外の場合はコメントが必須です。", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa

        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    @app_commands.command(description="MODコマンド（デモ）")
    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    @discord.app_commands.rename(user="警告対象のユーザー", warn_type_0="違反内容", evidence1="証拠画像1",
                                 evidence2="証拠画像2")
    @app_commands.choices(
        warn_type_0=[
            discord.app_commands.Choice(name="その他管理者が不適切と判断した行為",
                                        value="その他管理者が不適切と判断した行為")
        ])
    async def warn_demo(self, interaction: discord.Interaction, user: discord.User, warn_type_0: str,
                        evidence1: discord.Attachment, evidence2: discord.Attachment = None):
        """厳重注意の発行"""
        # 違反ユーザー情報を取得
        await interaction.response.defer(ephemeral=True)  # noqa
        # コマンド実行日時の取得
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # 警告メッセージの作成
        dm_embed = discord.Embed(title="厳重注意",
                                 description="WNH運営チームです。あなたは下記の内容で厳重注意となりました。"
                                 )
        dm_embed.add_field(name="ケース番号",
                           value=f"デモ01", inline=False)
        dm_embed.add_field(name="厳重注意の理由",
                           value=f"{warn_type_0}", inline=False)
        dm_embed.add_field(name="発行日時",
                           value=f"{action_datetime}", inline=False)
        dm_embed.add_field(name="内容のスクリーンショット",
                           value=f"スクリーンショットはこのメッセージの下に添付されます。", inline=False)
        dm_embed.add_field(name="この厳重注意に対する質問・申立",
                           value=f"この厳重注意に対する質問・申立は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c",
                           inline=False)
        # コマンドへのレスポンス
        await interaction.followup.send(content="ℹ️ 厳重注意（デモ）を発行しました", embed=dm_embed)

    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def delete_message(self, interaction: discord.Interaction, message: discord.Message):
        """コンテキストメニューからのメッセージの報告"""
        # 報告用フォームを表示
        guild = message.guild
        channel = message.channel
        user = message.author
        options = []
        async for additional_message in channel.history(after=message):
            if additional_message.author != user:
                continue
            created_time = additional_message.created_at.astimezone(JP).strftime("%Y/%m/%d %H:%M")
            if additional_message.content == "":
                content = "本文無し"
            else:
                content = additional_message.content[:100]
            option = discord.SelectOption(label=f"{created_time}", description=f"{content}",
                                          value=f"{additional_message.id}")
            options.append(option)
            if len(options) == 25:
                break
        if len(options) == 0:
            await interaction.response.send_modal(DeleteMessageForm(message=message, options=None))  # noqa
        else:
            await interaction.response.send_modal(DeleteMessageForm(message=message, options=options))  # noqa

    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def warn_profile(self, interaction: discord.Interaction, member: discord.Member):
        """コンテキストメニューからのメッセージの報告"""
        # 報告用フォームを表示
        await interaction.response.send_modal(WarnUserProfileForm(member=member))  # noqa

    @app_commands.checks.has_role(ROLE_ID_SENIOR_MOD)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def warn_user(self, interaction: discord.Interaction, member: discord.Member):
        """コンテキストメニューからのメッセージの報告"""
        # 報告用フォームを表示
        await interaction.response.send_modal(WarnUserForm(member=member))  # noqa

    @app_commands.checks.has_role(ROLE_ID_AUTHED)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        """コンテキストメニューからのメッセージの報告"""
        # 報告用フォームを表示
        await interaction.response.send_modal(MessageReportForm(message=message))  # noqa

    @app_commands.checks.has_role(ROLE_ID_AUTHED)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def report_user(self, interaction: discord.Interaction, member: discord.Member):
        """コンテキストメニューからのユーザーの報告"""
        # 報告用フォームを表示
        await interaction.response.send_modal(UserReportForm(member=member))  # noqa

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        await discord_error(interaction.command.name, interaction, error, logger)


class SendAppealView(ui.View):
    """メッセージをBOTとして転送"""

    def __init__(self, user: discord.User, case_id: str, embed: discord.Embed, timeout=360):
        super().__init__(timeout=timeout)
        self.user = user
        self.case_id = case_id
        self.embed = embed

    @ui.button(label="OK", style=discord.ButtonStyle.success)  # noqa
    async def send_appeal_button(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        try:
            await self.user.send(embed=self.embed)
        except discord.Forbidden:
            channel = await guild.fetch_channel(CHANNEL_ID_RULE)
            thread = await channel.create_thread(name=f"ケース{self.case_id}に関する質問・申立について",
                                                 reason=f"ケース{self.case_id}に関する質問・申立対応 ",
                                                 invitable=False)
            await thread.edit(locked=True)
            await thread.send(self.user.mention)
            await thread.send(embed=self.embed)
        response_embed = discord.Embed(description="ℹ️ 送信しました", color=Color_OK)
        await interaction.response.edit_message(content=None, embed=response_embed, view=None)  # noqa


class DeleteMessageForm(ui.Modal, title="メッセージを削除"):
    """メッセージ報告フォームの実装"""

    def __init__(self, message, options):
        super().__init__()
        self.message = message
        if options is not None:
            message_select = discord.ui.Label(
                text="追加で削除するメッセージ",
                component=discord.ui.Select(
                    options=options,
                    min_values=0,
                    max_values=len(options),
                    required=False,
                ),
            )
            self.message_select = message_select
            self.add_item(message_select)
        else:
            self.message_select = None

    # フォームの入力項目の定義（最大5個）
    rule_select = discord.ui.Label(
        text="違反内容",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="無許可の宣伝行為"),
                discord.SelectOption(label="外部リンクの投稿"),
                discord.SelectOption(label="外部戦績サイト等のコンテンツの投稿"),
                discord.SelectOption(label="処罰に関する議論"),
                discord.SelectOption(label="他人に対する攻撃"),
                discord.SelectOption(label="不適切な表現"),
                discord.SelectOption(label="スパム行為"),
                discord.SelectOption(label="オフトピック投稿"),
                discord.SelectOption(label="Modに関する投稿"),
                discord.SelectOption(label="初心者が入りにくい話題の高頻度投稿"),
                discord.SelectOption(label="メインアカウント以外での本人確認"),
                discord.SelectOption(label="晒し行為（IGNがマスク処理されていないSSの投稿を含む）"),
                discord.SelectOption(label="DMによる迷惑行為"),
                discord.SelectOption(label="政治・宗教に関する投稿"),
                discord.SelectOption(label="違法行為並びに同行為に関する投稿"),
                discord.SelectOption(label="各種サービス規約違反行為及び同行為に関する投稿"),
                discord.SelectOption(label="サーバーの設定ミスを悪用する行為"),
                discord.SelectOption(label="処罰を回避する行為"),
                discord.SelectOption(label="円滑な運営を妨げる行為"),
                discord.SelectOption(label="チャンネル規則への違反"),
                discord.SelectOption(label="センシティブなコンテンツの投稿"),
                discord.SelectOption(label="リーク等不明確な情報の投稿"),
                discord.SelectOption(label="違反投稿に対する返信"),
                discord.SelectOption(label="その他管理者が不適切と判断した行為"),
            ],
            min_values=1,
            max_values=24,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとチャンネルの取得
        guild = interaction.guild
        channel = interaction.channel
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        user = self.message.author
        messages = [self.message]
        if self.message_select and self.message_select.component.values != "":  # noqa
            for message_id in self.message_select.component.values:  # noqa
                message = await channel.fetch_message(int(message_id))
                messages.append(message)
        # コマンド実行日時の取得
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # 警告メッセージの作成
        reason_str = ""
        for reason in self.rule_select.component.values:  # noqa
            if reason_str == "":
                reason_str = reason
            else:
                reason_str = reason_str + f"、{reason}"

        # DBへケース情報を保存
        if ENV == "prod":
            case_id = await db.save_modlog(moderate_type=11, user_id=user.id, moderator_id=interaction.user.id,
                                           length="",
                                           reason=reason_str, datetime=action_datetime, point=0)
        else:
            case_id = 9999
        dm_embed = discord.Embed(title="メッセージ削除のお知らせ",
                                 description="WNH運営チームです。\nあなたが投稿した次のメッセージは以下の理由により削除されました。"
                                 )
        dm_embed.add_field(name="ケース番号",
                           value=f"{case_id}", inline=False)
        dm_embed.add_field(name="削除理由",
                           value=f"{reason_str}", inline=False)
        dm_embed.add_field(name="メッセージが送信されていたチャンネル",
                           value=f"<#{interaction.channel.id}>", inline=False)
        dm_embed.add_field(name="削除されたメッセージ",
                           value=f"削除されたメッセージの内容はこのメッセージの下に添付されます。", inline=False)
        dm_embed.add_field(name="この対応に対する質問・ご意見",
                           value=f"この対応に対する質問・ご意見は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c",
                           inline=False)
        log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                   content=f"ユーザー情報：{user.mention}\nモデレーター：<@{interaction.user.id}\n>"  # noqa
                                                           f"アクション種類：メッセージの削除\n削除理由：{reason_str}\n"
                                                           f"チャンネル：<#{interaction.channel.id}>")  # noqa
        for message in messages:
            create_time = message.created_at.astimezone(JP)
            create_time_str = create_time.strftime("%Y/%m/%d %H:%M")
            await log.thread.send(f"------------------------------\nメッセージID：{message.id}\n"  # noqa
                                  f"削除されたメッセージの送信日時：{create_time_str}")
            await message.forward(log.thread)  # noqa
        # ログCHへ送信するケース情報（Embed）を作成
        log_embed = discord.Embed(title=f"ケース{case_id} | メッセージの削除 | {user.name}")
        log_embed.add_field(name="ユーザー",
                            value=user.mention)
        log_embed.add_field(name="モデレーター",
                            value=f"<@{interaction.user.id}>")
        log_embed.add_field(name="削除理由",
                            value=f"{reason_str}", inline=False)
        log_embed.add_field(name="記録へのリンク",
                            value=f"<#{log.thread.id}>", inline=False)  # noqa
        log_embed.set_footer(text=f"UID：{user.id}・{action_datetime}")
        # ログCHへケース情報を送信
        # await channel_mod_log.send(embed=log_embed)
        # DBへケースIDと記録スレッドIDを保存
        # await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)
        # 違反ユーザーのDMへ警告を送信
        member = guild.get_member(user.id)
        if member is not None:
            try:
                await user.send(embed=dm_embed, view=ModContactButton())
                for message in messages:
                    create_time = message.created_at.astimezone(JP)
                    create_time_str = create_time.strftime("%Y/%m/%d %H:%M")
                    await user.send(f"------------------------------\n送信日時：{create_time_str}")
                    await message.forward(user)
            except discord.Forbidden:
                channel = await guild.fetch_channel(CHANNEL_ID_RULE)
                thread = await channel.create_thread(name=f"ケース{case_id} | メッセージの削除",
                                                     reason=f"ケース{case_id} ",
                                                     invitable=False)
                await thread.edit(locked=True)
                await thread.send(user.mention)
                await thread.send(embed=dm_embed)
                for message in messages:
                    create_time = message.created_at.astimezone(JP)
                    create_time_str = create_time.strftime("%Y/%m/%d %H:%M")
                    await thread.send(f"------------------------------\n送信日時：{create_time_str}")
                    await message.forward(thread)
        for message in messages:
            await message.delete()
        # フォームへのレスポンス
        response_embed = discord.Embed(description="ℹ️ メッセージを削除しました", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(
            f"スタッフ：{interaction.user}（UID：{interaction.user.id}）がメッセージ：{self.message.jump_url}を削除しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


class WarnUserProfileForm(ui.Modal, title="不適切なプロフィールの変更指示"):
    """メッセージ報告フォームの実装"""

    def __init__(self, member):
        super().__init__()
        self.member = member

    # フォームの入力項目の定義（最大5個）

    type_select = discord.ui.Label(
        text="プロフィールの種類",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="アバター"),
                discord.SelectOption(label="ユーザー名"),
                discord.SelectOption(label="アクティビティ/カスタムステータス"),
            ],
            min_values=1,
            max_values=3,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとチャンネルの取得
        guild = interaction.guild
        channel = interaction.channel
        role_wait_agree_rule = interaction.guild.get_role(ROLE_ID_WAIT_AGREE_RULE)
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        # コマンド実行日時の取得
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # 警告メッセージの作成
        profiles = ""
        for profile_type in self.type_select.component.values:  # noqa
            if profiles == "":
                profiles = profile_type
            else:
                profiles = profiles + f"、{profile_type}"
        activities = "なし"
        for activity in self.member.activities:
            if activities == "なし":
                activities = activity.name
            activities = activities + f"、{activity.name}"
        avatar = await self.member.display_avatar.to_file(filename="avatar.png")
        # DBへケース情報を保存
        case_id = 9999
        # case_id = await db.save_modlog(moderate_type=11, user_id=user.id, moderator_id=interaction.user.id, length="",
        #                                reason=reason_str, datetime=action_datetime, point=0)
        dm_embed = discord.Embed(title="WNHでのユーザープロフィールについて",
                                 description="WNH運営チームです。\nあなたがWNHで使用している次のプロフィールは不適切と判断されました。\n"
                                             "WNHの利用を再開するには、プロフィールを修正した上で、再度ルール同意ボタンを押してください。\n"
                                             "プロフィールを修正せずにルール同意ボタンを押した場合、警告が発行される場合があります。"
                                 )
        dm_embed.add_field(name="ケース番号",
                           value=f"{case_id}", inline=False)
        dm_embed.add_field(name="不適切と判断されたプロフィールの種類",
                           value=f"{profiles}", inline=False)
        dm_embed.add_field(name="発行日時",
                           value=f"{action_datetime}", inline=False)
        dm_embed.add_field(name="この対応に対する質問・ご意見",
                           value=f"この対応に対する質問・ご意見は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c",
                           inline=False)
        log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                   content=f"ユーザー情報：{self.member.mention}\nモデレーター：<@{interaction.user.id}>"  # noqa
                                                           f"\nアクション種類：不適切なプロフィールの変更指示\nプロフィールの種類：{profiles}\n\n"
                                                           f"表示名：{self.member.display_name}\nアバター：添付\nアクティビティ：{activities}",
                                                   file=avatar)  # noqa
        # ログCHへ送信するケース情報（Embed）を作成
        log_embed = discord.Embed(title=f"ケース{case_id} | 不適切なプロフィールの変更指示 | {self.member.name}")
        log_embed.add_field(name="ユーザー",
                            value=self.member.mention)
        log_embed.add_field(name="モデレーター",
                            value=f"<@{interaction.user.id}>")
        log_embed.add_field(name="プロフィールの種類",
                            value=f"{profiles}", inline=False)
        log_embed.add_field(name="記録へのリンク",
                            value=f"<#{log.thread.id}>", inline=False)  # noqa
        log_embed.set_footer(text=f"UID：{self.member.id}・{action_datetime}")
        # ログCHへケース情報を送信
        # await channel_mod_log.send(embed=log_embed)
        # DBへケースIDと記録スレッドIDを保存
        # await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)
        # 違反ユーザーのDMへ通知を送信
        if self.member in guild.members:
            await self.member.edit(roles=[role_wait_agree_rule], reason=f"ケース{case_id}による")
        try:
            await self.member.send(embed=dm_embed)
        except discord.Forbidden:
            channel = await guild.fetch_channel(CHANNEL_ID_RULE)
            thread = await channel.create_thread(name=f"ケース{case_id} | 不適切なプロフィールの変更指示",
                                                 reason=f"ケース{case_id} ",
                                                 invitable=False)
            await thread.edit(locked=True)
            await thread.send(self.member.mention)
            await thread.send(embed=dm_embed)
        # フォームへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 変更指示を送信しました。", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # # ログの保存
        # logger.info(
        #     f"スタッフ：{interaction.user}（UID：{interaction.user.id}）がメッセージ：{self.message.jump_url}を削除しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


class WarnUserForm(ui.Modal, title="ユーザーに警告"):
    """メッセージ報告フォームの実装"""

    def __init__(self, member):
        super().__init__()
        self.member = member

    # フォームの入力項目の定義（最大5個）

    type_select = discord.ui.Label(
        text="警告理由",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="複数回の違反"),
                discord.SelectOption(label="重大な違反"),
            ],
            min_values=1,
            max_values=2,
        ),
    )

    point_select = discord.ui.Label(
        text="ポイント",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="1"),
                discord.SelectOption(label="2"),
                discord.SelectOption(label="3"),
                discord.SelectOption(label="4"),
                discord.SelectOption(label="5"),
            ],
        ),
    )

    comment_input = ui.Label(
        text="コメント",
        component=ui.TextInput(
            style=discord.TextStyle.long,  # noqa
            max_length=3500,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        point = self.point_select.component.values[0]  # noqa
        reason = self.type_select.component.values[0]  # noqa
        comment = self.comment_input.component.value  # noqa
        guild = interaction.guild
        channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
        channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
        await interaction.response.defer(ephemeral=True)  # noqa
        # ユーザーの保有ポイントを取得
        if ENV == "prod":
            old_point = await db.get_point(user_id=self.member.id)
            if old_point is None:
                new_point = int(point)
            else:
                new_point = old_point[0] + int(point)
        else:
            new_point = int(point)
        # コマンド実行日時の取得
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # DBへケース情報を保存
        if ENV == "prod":
            case_id = await db.save_modlog(moderate_type=2, user_id=self.member.id, moderator_id=interaction.user.id,
                                           length="",
                                           reason=reason, datetime=action_datetime, point=point)
            # DBのポイントを更新
            await db.save_point(user_id=self.member.id, point=new_point)
        else:
            case_id = 9999
        # 警告メッセージの作成
        dm_embed = discord.Embed(title="警告",
                                 description="WNH運営チームです。あなたに対して下記の内容で警告が発行されました。"
                                 )

        dm_embed.add_field(name="ケース番号",
                           value=f"{case_id}", inline=False)
        dm_embed.add_field(name="警告理由",
                           value=f"{reason}", inline=False)
        dm_embed.add_field(name="コメント",
                           value=f"{comment}", inline=False)
        dm_embed.add_field(name="発行日時",
                           value=f"{action_datetime}", inline=False)
        dm_embed.add_field(name="この処罰に対する質問・申立",
                           value=f"この処罰に対する質問・申立は下記URLからのみ受け付けます。\nhttps://dyno.gg/form/6beb077c"
                                 f"\n\n尚、質問・申立の期限はこの警告を受けた日から3日以内とします。", inline=False)
        # 記録CHへケース情報を送信
        log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                   content=f"ユーザー情報：{self.member.mention}\nモデレーター：<@{interaction.user.id}>"  # noqa
                                                           f"\n処罰種類：警告\n付与ポイント：{point}\n警告理由：{reason}\nコメント：{comment}")  # noqa
        # ログCHへ送信するケース情報（Embed）を作成
        log_embed = discord.Embed(title=f"ケース{case_id} | 警告 | {self.member.name}")
        log_embed.add_field(name="ユーザー",
                            value=self.member.mention)
        log_embed.add_field(name="モデレーター",
                            value=f"<@{interaction.user.id}>")
        log_embed.add_field(name="付与ポイント",
                            value=f"{point}", inline=False)
        log_embed.add_field(name="警告理由",
                            value=f"{reason}", inline=False)
        log_embed.add_field(name="記録へのリンク",
                            value=f"<#{log.thread.id}>", inline=False)  # noqa
        log_embed.set_footer(text=f"UID：{self.member.id}・{action_datetime}")
        if ENV == "prod":
            # ログCHへケース情報を送信
            await channel_mod_log.send(embed=log_embed)
            # DBへケースIDと記録スレッドIDを保存
            await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
        if self.member in guild.members:
            try:
                await self.member.send(embed=dm_embed)
            except discord.Forbidden:
                channel = await guild.fetch_channel(CHANNEL_ID_RULE)
                thread = await channel.create_thread(name=f"ケース{case_id} | 警告", reason=f"ケース{case_id} ",
                                                     invitable=False)
                await thread.edit(locked=True)
                await thread.send(self.member.mention)
                await thread.send(embed=dm_embed)
        # コマンドへのレスポンス
        if new_point == 1:
            response_embed = discord.Embed(description="ℹ️ 警告を発行しました", color=Color_OK)
            await interaction.followup.send(embed=response_embed)
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がフォーム「ユーザーを警告」を使用し、ユーザー：{self.member.display_name}（UID：{self.member.id}）"
                        f"に警告（{point}ポイント）を発行しました。")
        # 5ポイント以上のためBAN
        elif new_point >= 5:
            await auto_ban(interaction=interaction, base_case_id=case_id, member=self.member,
                           base_thread_id=log.thread.id)  # noqa
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がフォーム「ユーザーを警告」を使用し、ユーザー：{self.member.display_name}（UID：{self.member.id}）"
                        f"に警告（{point}ポイント）を発行しました。")
        # 2～4ポイントのため一定期間発言禁止
        else:
            await auto_timeout(interaction=interaction, base_case_id=case_id, member=self.member, point=new_point,
                               base_thread_id=log.thread.id)  # noqa
            # ログの保存
            logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                        f"がフォーム「ユーザーを警告」を使用し、ユーザー：{self.member.display_name}（UID：{self.member.id}）"
                        f"に警告（{point}ポイント）を発行しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


class ModContactButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="意見・質問・申立を送信", style=discord.ButtonStyle.blurple, custom_id="mod_inquiry")  # noqa
    async def mod_contact_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(  # noqa
            ModContactForm(message=interaction.message, button=self.mod_contact_button, view=self))


class ModContactForm(ui.Modal, title="ユーザーに警告"):
    """メッセージ報告フォームの実装"""

    def __init__(self, message, button, view):
        super().__init__()
        self.message = message
        self.button = button
        self.view = view
        if message.embeds[0].title == "警告":
            options = [
                discord.SelectOption(label="ご意見"),
                discord.SelectOption(label="質問"),
                discord.SelectOption(label="申立"),
            ]
        else:
            options = [
                discord.SelectOption(label="ご意見"),
                discord.SelectOption(label="質問"),
            ]
        type_select = discord.ui.Label(
            text="種類",
            description="ご意見のみの場合は回答を行っておりません。",
            component=discord.ui.Select(
                options=options,
                min_values=1,
                max_values=2,
            ),
        )
        self.type_select = type_select
        self.add_item(type_select)

        comment_input = ui.Label(
            text="内容",
            component=ui.TextInput(
                style=discord.TextStyle.long,  # noqa
                max_length=3500,
            ),
        )
        self.comment_input = comment_input
        self.add_item(comment_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # noqa
        guild = interaction.client.get_guild(GUILD_ID)
        channel = guild.get_channel(CHANNEL_ID_MOD_CONTACT_LOG)
        member = guild.get_member(interaction.user.id)
        case_id = self.message.embeds[0].fields[0].value
        create_time = self.message.created_at.astimezone(JP)
        passed_time = datetime.now().astimezone(JP) - create_time
        self.button.disabled = True
        await self.message.edit(view=self.view)
        if passed_time.days >= 3:
            response_embed = discord.Embed(description=f"️⚠️ 処罰から3日以上経過しているため送信できません。",
                                           color=Color_ERROR)
            await interaction.followup.send(embed=response_embed, ephemeral=True)
        else:
            types = ""
            for send_type in self.type_select.component.values:  # noqa
                if types == "":
                    types = send_type
                else:
                    types = types + f"、{send_type}"
            embed = discord.Embed(title=f"処罰に対する意見・質問・申立", color=0x0000ff)
            embed.add_field(name="1. ケース番号", value=case_id, inline=False)  # noqa
            embed.add_field(name="2. 種別", value=types, inline=False)  # noqa
            embed.add_field(name="3. 内容", value=self.comment_input.component.value, inline=False)  # noqa
            embed.set_author(name=f"{member.display_name}", icon_url=f"{member.avatar.url}")
            await channel.send(embed=embed)
            response_embed = discord.Embed(description=f"ℹ️ 送信しました。",
                                           color=Color_OK)
            await interaction.followup.send(embed=response_embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


class MessageReportForm(ui.Modal, title="不適切なメッセージを報告"):
    """メッセージ報告フォームの実装"""

    def __init__(self, message):
        super().__init__()
        self.message = message

    # # フォームの入力項目の定義（最大5個）
    # warn = ui.TextDisplay("### 注意事項\n"
    #                       "このフォームはメッセージの報告用です。不適切なアバターやニックネーム、VCでの行為の報告は、ユーザーを右クリックして「アプリ>ユーザーの報告」からお願いします。")

    input_warn = ui.TextInput(
        label="注意事項（入力しないでください）",
        style=discord.TextStyle.long,  # noqa
        placeholder="このフォームはユーザーの報告用です。報告したい特定のメッセージがある場合は、メッセージを右クリックして「アプリ>メッセージの報告」からお願いします。",
        max_length=1,
        required=False,
    )

    input_text = ui.Label(
        text="報告内容の詳細",
        component=ui.TextInput(
            style=discord.TextStyle.long,  # noqa
            placeholder="例：〇〇に対する暴言を吐いている",
            max_length=300,
        )
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        # ギルドとチャンネルの取得
        await interaction.response.defer(ephemeral=True)  # noqa
        channel_report_log = await interaction.guild.fetch_channel(CHANNEL_ID_REPORT_LOG)
        # フォームを送信したユーザー情報を取得
        report_user = interaction.user
        uid = report_user.id
        author = interaction.guild.get_member(self.message.author.id)
        author_name = author.display_name
        avatar = author.display_avatar.url
        # 報告日時の記録
        dt = datetime.now(JP)
        report_datetime = dt.strftime("%Y/%m/%d %H:%M")
        ts = int(datetime.timestamp(dt))
        # メッセージリンクの生成
        url = self.message.jump_url
        # 報告メッセージの生成
        embed = discord.Embed(title="不適切なメッセージが報告されました", color=0x0000ff)
        embed.set_author(name=author, icon_url=avatar)
        embed.add_field(name="報告対象のメッセージ", value=f"{url}", inline=False)
        embed.add_field(name="報告対象のメッセージの投稿者", value=f"<@{self.message.author.id}>", inline=False)
        if self.message.content == "":
            embed.add_field(name="報告対象のメッセージの内容", value=f"本文がありません", inline=False)
        else:
            embed.add_field(name="報告対象のメッセージの内容", value=f"{self.message.content}", inline=False)
        embed.add_field(name="報告したユーザー", value=f"<@{uid}>", inline=False)
        embed.add_field(name="報告内容の詳細", value=self.input_text.component.value, inline=False)  # noqa
        embed.add_field(name="報告日時", value=f"<t:{ts}:F>", inline=False)
        embed.add_field(name="ID", value=f"```ini\nUser = {author.id}\nMessage = {self.message.id}```", inline=False)
        # 報告メッセージの送信
        msg = await channel_report_log.send(embed=embed)
        thread = await msg.create_thread(
            name=f"メッセージの報告 - {self.message.author.name} - {self.message.channel.name}")
        if self.message.attachments:
            for e in self.message.attachments:
                try:
                    f = await e.to_file()
                    image_embed = discord.Embed()
                    image_embed.set_image(url=f"attachment://{f.filename}")
                    await thread.send(embed=image_embed, file=f)
                except AttributeError:
                    break
        # フォームへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 報告を受け付けました", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(
            f"ユーザー：{interaction.user}（UID：{interaction.user.id}）がメッセージ：{self.message.jump_url}を報告しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


class UserReportForm(ui.Modal, title="不適切なユーザーを報告"):
    """ユーザー報告フォームの実装"""

    def __init__(self, member):
        super().__init__()
        self.member = member

    # フォームの入力項目の定義（最大5個）

    # warn = ui.TextDisplay("### 注意事項\n"
    #                       "このフォームはメッセージの報告用です。不適切なアバターやニックネーム、VCでの行為の報告は、ユーザーを右クリックして「アプリ>ユーザーの報告」からお願いします。")

    input_warn = ui.TextInput(
        label="注意事項（入力しないでください）",
        style=discord.TextStyle.long,  # noqa
        placeholder="このフォームはユーザーの報告用です。報告したい特定のメッセージがある場合は、メッセージを右クリックして「アプリ>メッセージの報告」からお願いします。",
        max_length=1,
        required=False,
    )

    input_text = ui.Label(
        text="報告内容の詳細",
        component=ui.TextInput(
            style=discord.TextStyle.long,  # noqa
            placeholder="例：不適切なユーザー名を設定している",
            max_length=300,
        )
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        # ギルドとチャンネルの取得
        await interaction.response.defer(ephemeral=True)  # noqa
        channel_report_log = await interaction.guild.fetch_channel(CHANNEL_ID_REPORT_LOG)
        # フォームを送信したユーザー情報を取得
        report_user = interaction.user
        uid = report_user.id
        # 報告対象のユーザー情報を取得
        server_name = self.member.display_name
        avatar = self.member.display_avatar
        # 報告日時の記録
        dt = datetime.now(JP)
        report_datetime = dt.strftime("%Y/%m/%d %H:%M")
        ts = int(datetime.timestamp(dt))
        # 報告メッセージの生成
        embed = discord.Embed(title="不適切なユーザーが報告されました", color=0x0000ff)
        embed.set_author(name=self.member, icon_url=avatar.url)
        embed.add_field(name="報告対象のユーザー", value=f"<@{self.member.id}>", inline=False)
        embed.add_field(name="報告時の対象ユーザーの表示名", value=f"{server_name}", inline=False)
        embed.add_field(name="報告したユーザー", value=f"<@{uid}>", inline=False)
        embed.add_field(name="報告内容の詳細", value=self.input_text.component.value, inline=False)  # noqa
        embed.add_field(name="報告日時", value=f"<t:{ts}:F>", inline=False)
        embed.add_field(name="ID", value=f"```ini\nUser = {self.member.id}```", inline=False)
        # 報告メッセージの送信
        msg = await channel_report_log.send(embed=embed)
        thread = await msg.create_thread(name=f"ユーザーの報告 - {server_name}")
        f = await avatar.to_file(filename="avatar.png")
        avatar_embed = discord.Embed(title="報告時のユーザーのアバター")
        avatar_embed.set_image(url=f"attachment://{f.filename}")
        await thread.send(embed=avatar_embed, file=f)
        # フォームへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 報告を受け付けました", color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # ログの保存
        logger.info(
            f"ユーザー：{interaction.user}（UID：{interaction.user.id}）がユーザー：{server_name}（UID：{self.member.id}）を報告しました。")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


async def auto_timeout(interaction: discord.Interaction, base_case_id: int, member: discord.Member, point: int,
                       base_thread_id: int):
    """一定ポイント到達時の自動発言禁止処理"""
    # ポイントに応じて期間を設定
    if point == 2:
        length = 7
    elif point == 3:
        length = 14
    else:
        length = 28
    # ギルドとチャンネルの取得
    guild = interaction.guild
    channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
    channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
    # 違反ユーザー情報を取得
    if member in guild.members:
        # 実行日時を記録
        dt = datetime.now(JP)
        action_datetime = dt.strftime("%Y/%m/%d %H:%M")
        # DBへケース情報を保存
        case_id = await db.save_modlog(moderate_type=3, user_id=member.id, moderator_id=interaction.client.user.id,
                                       length=length,
                                       reason=f"{base_case_id}に基づく自動処理", datetime=action_datetime, point=0)
        # 処分通達メッセージを作成
        dm_embed = discord.Embed(title="発言禁止処分の通知",
                                 description=f"WNH運営チームです。あなたは次の期間発言禁止となりました。"
                                 )
        dm_embed.add_field(name="ケース番号",
                           value=f"{case_id}", inline=False)
        dm_embed.add_field(name="期間",
                           value=f"{length}日", inline=False)
        dm_embed.add_field(name="この処分に対する質問・申立",
                           value=f"この処分はケース{base_case_id}に基づき自動で行われています。\n質問・申立はケース{base_case_id}に対して行ってください。",
                           inline=False)
        # 記録CHへケース情報を送信
        log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                                   content=f"ユーザー情報：{member.mention}\nモデレーター：<@{interaction.client.user.id}>"  # noqa
                                                           f"\n処罰種類：発言禁止\n期間：{length}日"  # noqa
                                                           f"\n処罰理由：ケース{base_case_id}に基づく自動処理"  # noqa
                                                           f"\n元ケース：<#{base_thread_id}>")  # noqa
        # ログCHへ送信するケース情報（Embed）を作成
        log_embed = discord.Embed(title=f"ケース{case_id} | 発言禁止 | {member.name}")
        log_embed.add_field(name="ユーザー",
                            value=member.mention)
        log_embed.add_field(name="モデレーター",
                            value=f"<@{interaction.client.user.id}>")
        log_embed.add_field(name="期間",
                            value=f"{length}日", inline=False)
        log_embed.add_field(name="処罰理由",
                            value=f"ケース{base_case_id}に基づく自動処理", inline=False)
        log_embed.add_field(name="記録へのリンク",
                            value=f"<#{log.thread.id}>", inline=False)  # noqa
        log_embed.set_footer(text=f"UID：{member.id}・{action_datetime}")
        # ログCHへケース情報を送信
        await channel_mod_log.send(embed=log_embed)
        # DBへケースIDと記録スレッドIDを保存
        await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
        # 違反ユーザーのDMへ通達を送信
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            channel = await guild.fetch_channel(CHANNEL_ID_RULE)
            thread = await channel.create_thread(name=f"ケース{case_id} | 発言禁止", reason=f"ケース{case_id} ",
                                                 invitable=False)
            await thread.edit(locked=True)
            await thread.send(member.mention)
            await thread.send(embed=dm_embed)
        # 発言禁止処理
        await member.timeout(timedelta(days=length), reason=f"ケース{case_id}")
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 警告を発行・発言禁止にしました", color=Color_OK)
        await interaction.followup.send(embed=response_embed)
        # ログの保存
        logger.info(
            f"ユーザー：{member.display_name}（UID：{member.id}）のポイントが{point}ポイントに達したため{length}日間の発言禁止処理が行われました。")
    # ユーザー情報を取得できなかった場合
    else:
        response_embed = discord.Embed(
            description="ℹ️ 警告を発行しました。\n⚠️ ユーザーがサーバーに存在しないため発言禁止処理はスキップされました。",
            color=Color_OK)
        await interaction.followup.send(embed=response_embed)
        pass


async def auto_ban(interaction: discord.Interaction, base_case_id: int, member: discord.Member,
                   base_thread_id: int):
    """5ポイント到達時の自動BAN処理"""
    # ギルドとチャンネルの取得
    guild = interaction.guild
    channel_mod_case = await guild.fetch_channel(CHANNEL_ID_MOD_CASE)
    channel_mod_log = await guild.fetch_channel(CHANNEL_ID_MOD_LOG)
    # 実行日時を記録
    dt = datetime.now(JP)
    action_datetime = dt.strftime("%Y/%m/%d %H:%M")
    # DBへケース情報を保存
    case_id = await db.save_modlog(moderate_type=4, user_id=member.id, moderator_id=interaction.client.user.id,
                                   length="",
                                   reason=f"{base_case_id}に基づく自動処理", datetime=action_datetime, point=0)
    # 処分通達メッセージを作成
    dm_embed = discord.Embed(title="BAN処分の通知",
                             description=f"WNH運営チームです。あなたはBANとなりました。"
                             )
    dm_embed.add_field(name="ケース番号",
                       value=f"{case_id}", inline=False)
    dm_embed.add_field(name="この処分に対する質問・申立",
                       value=f"この処分はケース{base_case_id}に基づき自動で行われています。\n質問・申立はケース{base_case_id}に対して行ってください。",
                       inline=False)
    # 記録CHへケース情報を送信
    log = await channel_mod_case.create_thread(name=f"ケース{case_id}",
                                               content=f"ユーザー情報：{member.mention}\nモデレーター：<@{interaction.client.user.id}>"  # noqa
                                                       f"\n処罰種類：BAN\n処罰理由：ケース{base_case_id}に基づく自動処理"  # noqa
                                                       f"\n元ケース：<#{base_thread_id}>")
    # ログCHへ送信するケース情報（Embed）を作成
    log_embed = discord.Embed(title=f"ケース{case_id} | BAN | {member.name}")
    log_embed.add_field(name="ユーザー",
                        value=member.mention)
    log_embed.add_field(name="モデレーター",
                        value=f"<@{interaction.client.user.id}>")
    log_embed.add_field(name="処罰理由",
                        value=f"ケース{base_case_id}に基づく自動処理", inline=False)
    log_embed.add_field(name="記録へのリンク",
                        value=f"<#{log.thread.id}>", inline=False)  # noqa
    log_embed.set_footer(text=f"UID：{member.id}・{action_datetime}")
    # ログCHへケース情報を送信
    await channel_mod_log.send(embed=log_embed)
    # DBへケースIDと記録スレッドIDを保存
    await db.update_modlog_id(thread_id=log.thread.id, case_id=case_id)  # noqa
    # 違反ユーザーのDMへ通達を送信
    if member in guild.members:
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
    # ユーザーをBAN
    await guild.ban(user=member, delete_message_days=0, reason=f"ケース{case_id}")
    # コマンドへのレスポンス
    response_embed = discord.Embed(description="ℹ️ 警告を発行・BANしました", color=Color_OK)
    await interaction.followup.send(embed=response_embed)
    # ログの保存
    logger.info(
        f"ユーザー：{member.display_name}（UID：{member.id}）のポイントが5ポイントに達したためBAN処理が行われました。")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Moderation(bot))
