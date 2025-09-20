import io
import os
import time

import discord
from discord import app_commands
from discord import ui
from discord.ext import commands
from dotenv import load_dotenv

import chat_exporter
from bot import check_developer
from db import get_inquiry_number
from exception import discord_error
from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
ROLE_ID_CLAN_RECRUITER = int(os.environ.get("ROLE_ID_CLAN_RECRUITER"))
# ご意見・ご要望・その他問い合わせ
OPINION_LOG = int(os.environ.get("OPINION_LOG"))
GENERAL_INQRY_OPEN = int(os.environ.get("GENERAL_INQRY_OPEN"))
GENERAL_INQRY_CLOSE = int(os.environ.get("GENERAL_INQRY_CLOSE"))
GENERAL_INQRY_LOG = int(os.environ.get("GENERAL_INQRY_LOG"))
GENERAL_INQRY_SAVE = int(os.environ.get("GENERAL_INQRY_SAVE"))
# 通報
REPORT_OPEN = int(os.environ.get("REPORT_OPEN"))
REPORT_CLOSE = int(os.environ.get("REPORT_CLOSE"))
REPORT_LOG = int(os.environ.get("REPORT_LOG"))
REPORT_SAVE = int(os.environ.get("REPORT_SAVE"))
# 公認クラン
CLAN_OPEN = int(os.environ.get("CLAN_OPEN"))
CLAN_CLOSE = int(os.environ.get("CLAN_CLOSE"))
CLAN_LOG = int(os.environ.get("CLAN_LOG"))
CLAN_SAVE = int(os.environ.get("CLAN_SAVE"))
CLAN_STAFF_ROLE = int(os.environ.get("CLAN_STAFF_ROLE"))
CLAN_MEET_ID = int(os.environ.get("CLAN_MEET_ID"))

ENV = os.environ.get("ENV")
Color_OK = 0x00ff00
Color_WARN = 0xffa500
Color_ERROR = 0xff0000
logger = logger.getChild("contact")
COOLDOWN = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.member)
DICT_CATEGORY = {GENERAL_INQRY_OPEN: "GENERAL",
                 GENERAL_INQRY_CLOSE: "GENERAL", REPORT_OPEN: "REPORT",
                 REPORT_CLOSE: "REPORT", CLAN_OPEN: "CLAN", CLAN_CLOSE: "CLAN"}
DICT_NAME = {"GENERAL": "ご意見・ご要望・その他お問い合わせ", "REPORT": "違反行為の報告",
             "CLAN": "公認クランプログラムへのお申し込み"}
DICT_OPEN_CATEGORY = {"GENERAL": GENERAL_INQRY_OPEN, "REPORT": REPORT_OPEN,
                      "CLAN": CLAN_OPEN}
DICT_CLOSE_CATEGORY = {"GENERAL": GENERAL_INQRY_CLOSE, "REPORT": REPORT_CLOSE,
                       "CLAN": CLAN_CLOSE}
DICT_LOG_CATEGORY = {"GENERAL": GENERAL_INQRY_LOG, "REPORT": REPORT_LOG,
                     "CLAN": CLAN_LOG}
DICT_SAVE_CATEGORY = {"GENERAL": GENERAL_INQRY_SAVE, "REPORT": REPORT_SAVE,
                      "CLAN": CLAN_SAVE}


class Contact(commands.Cog):
    """コマンド実装用のクラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_message(self, interaction: discord.Interaction):
        """認証用メッセージを作成"""
        channel = interaction.channel
        await channel.send(view=CreateTicketView())
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
    async def edit_message99(self, interaction: discord.Interaction, url: str):
        """BOTが送信したメッセージの編集"""
        import re
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
            # メッセージを編集
            try:
                await message.edit(view=ToolButtonView())
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

    @app_commands.command(description="チケットクローズ案内_通常")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def ticket_close_normal(self, interaction: discord.Interaction):
        await interaction.channel.send("追加する情報がなければ、チケットを閉じて下さい。"
                                       "\nよろしくお願いいたします。"
                                       "\n\nWNH 運営チーム")
        response_embed = discord.Embed(description="ℹ️ 完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa

    @app_commands.command(description="チケットクローズ案内_24h無反応")
    @app_commands.checks.has_role(ROLE_ID_WNH_STAFF)
    @app_commands.guilds(GUILD_ID)
    @app_commands.guild_only()
    async def ticket_close_24h(self, interaction: discord.Interaction):
        await interaction.channel.send("運営チームの最後の対応から24時間反応がなかったためチケットをクローズします。"
                                       "\n\nWNH 運営チーム")
        response_embed = discord.Embed(description="ℹ️ 完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa

    async def cog_app_command_error(self, interaction, error):
        """コマンド実行時のエラー処理"""
        await discord_error(interaction.command.name, interaction, error, logger)


class CreateTicketView(ui.LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    text1 = ui.TextDisplay("## 各種問い合わせについて\n"
                           "最後の対応から24時間反応がないチケットはクローズします")
    text2 = ui.TextDisplay("### 当サーバーに対するご意見/ご要望/その他お問い合わせ\n"
                           "下のリストから「ご意見・ご要望・その他問い合わせ」を選択してチケットを作成してください。")
    text3 = ui.TextDisplay("### 公認クランプログラムへのお申し込み\n"
                           f"<@&{ROLE_ID_CLAN_RECRUITER}>ロールをご希望の方は「公認クランプログラムへのお申し込み」を選択してください。")
    text4 = ui.TextDisplay("### 違反行為の報告\n"
                           "* 不適切なメッセージを報告したい場合\n"
                           "報告したいメッセージを右クリックして「アプリ」→「メッセージの報告」をクリックし、報告内容を記載して送信してください\n\n"
                           "* 不適切なニックネームやアバター・VCでの違反行為等メッセージでの違反以外を報告したい場合\n"
                           "ユーザーを右クリックして「アプリ」→「ユーザーの報告」をクリックし、報告内容を記載して送信してください\n\n"
                           "上記の手順でエラーが起こる場合は、下記リストから「違反行為の報告」を選択してチケットを作成してください。")
    text5 = ui.TextDisplay("### セクシャルハラスメント等の通報について\n"
                           "セクシャルハラスメント等の通報で女性スタッフによる対応を希望する場合は<@767646985632481320>のDMへご連絡ください。")
    container_container = ui.Container(text1, text2, text3, text4, text5)

    action_row = ui.ActionRow()

    @action_row.select(
        cls=ui.Select,
        custom_id="ticket_panel",
        placeholder="お問い合わせ内容を選択してください",
        options=[
            discord.SelectOption(label="ご意見・ご要望", value="OPINION", emoji="💬"),
            discord.SelectOption(label="その他問い合わせ", value="GENERAL", emoji="📨"),
            discord.SelectOption(label="違反行為の報告", value="REPORT", emoji="🚨"),
            discord.SelectOption(label="公認クランプログラムへのお申し込み", value="CLAN", emoji="🈸"),
        ],
    )
    async def set_channel(self, interaction: discord.Interaction, select: ui.Select):
        bucket = COOLDOWN.get_bucket(interaction.message)
        select_value = select.values[0]
        if ENV == "prod":
            retry_after = bucket.update_rate_limit()
        else:
            retry_after = None
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        elif select_value == "OPINION":
            await interaction.response.send_modal(InquiryForm())  # noqa
        else:
            await interaction.response.defer()  # noqa
            # ドロップダウンの選択項目を初期化
            await interaction.message.edit(view=CreateTicketView())
            # 選択されたカテゴリのカテゴリチャンネルの取得
            open_category = interaction.guild.get_channel(DICT_OPEN_CATEGORY[select_value])
            close_category = interaction.guild.get_channel(DICT_CLOSE_CATEGORY[select_value])
            # DBからチケット番号を取得
            if ENV == "prod":
                channel_number_db = await get_inquiry_number(select_value)
            else:
                channel_number_db = 1
            channel_number = f"{channel_number_db:04}"
            user = interaction.user
            if select_value == "GENERAL":
                view = GeneralTicketView(user)
            elif select_value == "REPORT":
                view = ReportTicketView(user)
            else:
                view = ClanTicketView(user)
            # チケットの重複作成の防止
            open_channels = open_category.text_channels
            close_channels = close_category.text_channels
            channels = open_channels + close_channels
            users = []
            for channel in channels:
                async for message in channel.history(limit=1, oldest_first=True):
                    uid = message.components[0].content.replace("<@", "").replace(">", "")
                    users.append(int(uid))
            if interaction.user.id in users:
                error_embed = discord.Embed(
                    description="⚠️ 作成しようとしたカテゴリのチケットが既にあります。\nチケットは1カテゴリにつき同時に1つまでしか作成できません。",
                    color=Color_ERROR)
                await interaction.followup.send(embed=error_embed, ephemeral=True)  # noqa
            else:
                # チャンネルの作成
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True),
                    interaction.guild.get_role(ROLE_ID_WNH_STAFF): discord.PermissionOverwrite(read_messages=True)
                }
                channel_name_dict = {"GENERAL": "一般", "REPORT": "通報", "CLAN": "公認クラン"}
                channel_name = channel_name_dict[select_value]
                ticket = await open_category.create_text_channel(name=f"{channel_name}-{channel_number}",
                                                                 overwrites=overwrites)

                await ticket.send(view=view)
                # ログの送信
                category_name = DICT_NAME[select_value]
                embed = discord.Embed(colour=Color_OK)
                embed.add_field(name="情報", value=f"チケット：{ticket.name}"
                                                   f"\n内容：チケット作成")
                embed.add_field(name="カテゴリ", value=f"{category_name}")
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
                channel = interaction.guild.get_channel(DICT_LOG_CATEGORY[select_value])
                await channel.send(embed=embed)
                # Embedを送信
                await interaction.followup.send(f"チケット{ticket.jump_url}が作成されました。",
                                                ephemeral=True)  # noqa

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        await discord_error(item.label, interaction, error, logger)  # noqa


class OpinionView(ui.LayoutView):
    def __init__(self, user, content) -> None:
        super().__init__(timeout=None)

        opinion_text = ui.TextDisplay(content)
        opinion_info = ui.TextDisplay(f"## ご意見・ご要望\n"
                                      f"送信者：{user.mention}\n"
                                      f"以下内容")
        separator = ui.Separator()
        container = ui.Container(opinion_info, separator, opinion_text)
        self.add_item(container)


class InquiryForm(ui.Modal, title="ご意見・ご要望"):
    """フォームの実装"""

    def __init__(self):
        """ギルド、ロール、チャンネルの事前定義"""
        super().__init__()

    # フォームの入力項目の定義（最大5個）

    content = ui.Label(
        text="内容",
        description="WNH運営チームへのご意見・ご要望をご記入ください。",
        component=ui.TextInput(
            style=discord.TextStyle.long,  # noqa
            max_length=3900
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer(ephemeral=True)  # noqa
        # ギルドとチャンネルの取得
        channel_inqury = await interaction.guild.fetch_channel(1019170633625632768)
        # フォームを送信したユーザーの情報を取得
        user = interaction.user
        # 分隊募集メッセージ（Embed）の作成
        view = OpinionView(user, self.content.component.value)
        # メッセージを送信し、紐づくスレッドを作成
        message = await channel_inqury.send(view=view)
        thread = await message.create_thread(name=f"議論用")
        await thread.add_user(user)
        # フォームへのレスポンス
        response_embed = discord.Embed(description=f"ℹ️ ご意見・ご要望を受け付けました。",
                                       color=Color_OK)
        await interaction.followup.send(embed=response_embed, ephemeral=True)
        # DBに保存
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がフォーム「問い合わせ」を使用しました。")


class ClanButton(ui.ActionRow):
    def __init__(self) -> None:
        super().__init__()

    @ui.button(label="チケットを閉じる", emoji="🔒", style=discord.ButtonStyle.grey,  # noqa
               custom_id="ticket_close_clan")
    async def ticket_close_button_clan(self, interaction: discord.Interaction, button: ui.Button):
        await ticket_close(interaction)

    @ui.button(label="面談希望日時を申請", emoji="🈸", style=discord.ButtonStyle.grey,  # noqa
               custom_id="ticket_clan_form_button")
    async def ticket_clan_form_button(self, interaction: discord.Interaction, button: ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            button.disabled = True
            await interaction.response.send_modal(ClanForm(view=self))  # noqa


class ClanTicketView(ui.LayoutView):
    def __init__(self, user=None) -> None:
        super().__init__(timeout=None)
        if user is not None:
            mention = ui.TextDisplay(f"{user.mention}")
            self.text1 = ui.TextDisplay("公認クランプログラムへお申し込み頂きありがとうございます。\n"
                                        "本プログラムへのお申し込みに当たり、担当者との面談が必要となります。\n"
                                        "お手数ですが下のボタンからフォームを開き、**本日から7日後以降**で希望日と希望枠を入力してください。\n"
                                        "チケットを閉じたい場合は 🔒をクリックしてください。")
            self.text2 = ui.TextDisplay("### 希望枠について\n"
                                        "希望枠は以下の枠から平日、土日祝**それぞれ2枠**選択してください。\n"
                                        "参加不可な枠には不可と入力してください。\n"
                                        "* 平日\n"
                                        "  * 23:00～24:00\n"
                                        "  * 24:00～25:00\n"
                                        "* 土日祝\n"
                                        "  * 10:00～11:00\n"
                                        "  * 11:00～12:00\n"
                                        "  * 12:00～13:00")
            container = ui.Container(self.text1, self.text2)
            self.add_item(mention)
            self.add_item(container)

        button = ClanButton()
        self.add_item(button)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        await discord_error(item.label, interaction, error, logger)  # noqa


class CloseButton(ui.ActionRow):
    def __init__(self) -> None:
        super().__init__()

    @ui.button(label="チケットを閉じる", emoji="🔒", style=discord.ButtonStyle.grey, custom_id="ticket_close")  # noqa
    async def ticket_close_button(self, interaction: discord.Interaction, button: ui.Button):
        await ticket_close(interaction)


class GeneralTicketView(ui.LayoutView):
    def __init__(self, user=None) -> None:
        super().__init__(timeout=None)
        if user is not None:
            mention = ui.TextDisplay(f"{user.mention}")
            text = ui.TextDisplay("お問い合わせありがとうございます。\n"
                                  "問い合わせ内容をこのチャンネルに送信してお待ちください。担当者が順次対応いたします。\n"
                                  "チケットを閉じたい場合は 🔒をクリックしてください。")
            container = ui.Container(text)
            self.add_item(mention)
            self.add_item(container)

        button = CloseButton()
        self.add_item(button)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        await discord_error(item.label, interaction, error, logger)  # noqa


class ReportTicketView(ui.LayoutView):
    def __init__(self, user=None) -> None:
        super().__init__(timeout=None)
        if user is not None:
            mention = ui.TextDisplay(f"{user.mention}")
            text = ui.TextDisplay("お問い合わせありがとうございます。\n"
                                  "通報内容をこのチャンネルに送信してお待ちください。担当者が順次対応いたします。\n"
                                  "可能な場合はスクリーンショット、メッセージリンクを添付して下さい。\n"
                                  "### メッセージリンクのコピー方法\n"
                                  "メッセージリンクをコピーしたいメッセージを右クリックし、「メッセージリンクをコピー」を選択します"
                                  "チケットを閉じたい場合は 🔒をクリックしてください。")
            container = ui.Container(text)
            self.add_item(mention)
            self.add_item(container)

        button = CloseButton()
        self.add_item(button)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        await discord_error(item.label, interaction, error, logger)  # noqa


async def ticket_close(interaction: discord.Interaction):
    bucket = COOLDOWN.get_bucket(interaction.message)
    if ENV == "prod":
        retry_after = bucket.update_rate_limit()
    else:
        retry_after = None
    category = DICT_CATEGORY[interaction.channel.category_id]
    to_move = DICT_CLOSE_CATEGORY[category]
    if retry_after:
        error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                    color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
    elif interaction.channel.category_id == to_move:
        error_embed = discord.Embed(description=f"⚠️ チケットは既にクローズされています。",
                                    color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
    else:
        await interaction.response.defer()  # noqa
        # 権限の更新
        overwrite_dict = interaction.channel.overwrites
        overwrite_member = list(overwrite_dict)
        overwrite = discord.PermissionOverwrite()
        overwrite.read_messages = True  # noqa
        overwrite.send_messages = False  # noqa
        for member in overwrite_member:
            obj_type = type(member)
            if obj_type == discord.Member:
                await interaction.channel.set_permissions(member, overwrite=overwrite)

        category_ch = interaction.guild.get_channel(to_move)
        offset = int(interaction.channel.name[-4:])
        if offset == 1:
            await interaction.channel.move(beginning=True, category=category_ch)
        else:
            offset = offset - 1
            await interaction.channel.move(beginning=True, offset=offset, category=category_ch)
        # ログの送信
        category_name = DICT_NAME[category]
        embed = discord.Embed(colour=Color_WARN)
        embed.add_field(name="情報", value=f"チケット：{interaction.channel.name}"
                                           f"\n内容：チケット閉")
        embed.add_field(name="カテゴリ", value=f"{category_name}")
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        channel = interaction.guild.get_channel(DICT_LOG_CATEGORY[category])
        await channel.send(embed=embed)
        # 通知の送信
        embed = discord.Embed(title="", description=f"{interaction.user.mention}がチケットを閉じました。",
                              colour=Color_WARN)
        await interaction.channel.send(embed=embed)  # noqa
        # ツールの送信
        await interaction.channel.send(view=ToolButtonView())  # noqa


class ToolButtonView(ui.LayoutView):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    text = ui.TextDisplay("🔓 チケットを再開\n"
                          "--以下スタッフ専用--\n"
                          "📑 チケットを保存\n"
                          "🗑️ チケットを削除")
    container = ui.Container(text)
    action_row = ui.ActionRow()

    @action_row.button(label="チケットを再開", emoji="🔓", style=discord.ButtonStyle.grey,  # noqa
                       custom_id="ticket_open")  # noqa
    async def ticket_open_button(self, interaction: discord.Interaction, button: ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        if ENV == "prod":
            retry_after = bucket.update_rate_limit()
        else:
            retry_after = None
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer()  # noqa
            # 権限の更新
            overwrite_dict = interaction.channel.overwrites
            overwrite_member = list(overwrite_dict)
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = True  # noqa
            overwrite.send_messages = True  # noqa
            for member in overwrite_member:
                obj_type = type(member)
                if obj_type == discord.Member:
                    await interaction.channel.set_permissions(member, overwrite=overwrite)
            category = DICT_CATEGORY[interaction.channel.category_id]
            to_move = DICT_OPEN_CATEGORY[category]
            category_ch = interaction.guild.get_channel(to_move)
            offset = int(interaction.channel.name[-4:])
            if offset == 1:
                await interaction.channel.move(beginning=True, category=category_ch)
            else:
                offset = offset - 1
                await interaction.channel.move(beginning=True, offset=offset, category=category_ch)
            # ログの送信
            category_name = DICT_NAME[category]
            embed = discord.Embed(colour=Color_OK)
            embed.add_field(name="情報", value=f"チケット：{interaction.channel.name}"
                                               f"\n内容：チケット再開")
            embed.add_field(name="カテゴリ", value=f"{category_name}")
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
            channel = interaction.guild.get_channel(DICT_LOG_CATEGORY[category])
            await channel.send(embed=embed)
            # 通知の送信
            embed = discord.Embed(title="", description=f"{interaction.user.mention}がチケットを再開しました。",
                                  colour=Color_OK)
            await interaction.channel.send(embed=embed)  # noqa
            await interaction.message.delete()

    @action_row.button(label="チケットを保存", emoji="📑", style=discord.ButtonStyle.grey,  # noqa
                       custom_id="ticket_save")  # noqa
    async def ticket_save_button(self, interaction: discord.Interaction, button: ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        if ENV == "prod":
            retry_after = bucket.update_rate_limit()
        else:
            retry_after = None
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        elif interaction.user.get_role(ROLE_ID_WNH_STAFF) is None:
            error_embed = discord.Embed(description="⚠️ この機能はWNH STAFF専用です。", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer()  # noqa
            # HTMLを作成
            transcript = await chat_exporter.export(
                interaction.channel,
                tz_info="Asia/Tokyo",
                military_time=True
            )

            if transcript is None:
                return

            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{interaction.channel.name}.html",
            )
            # チケットを保存
            category = DICT_CATEGORY[interaction.channel.category_id]
            category_name = DICT_NAME[category]
            first_user_message_list = [message async for message in
                                       interaction.channel.history(limit=1, oldest_first=True)]
            first_user_message = first_user_message_list[0].components[0].content
            user = await interaction.client.fetch_user(int(first_user_message[2:-1]))
            embed = discord.Embed(colour=Color_OK)
            embed.add_field(name="チケット所有者", value=f"{user.mention}")
            embed.add_field(name="チケット", value=f"{interaction.channel.name}")
            embed.add_field(name="カテゴリ", value=f"{category_name}")
            embed.set_author(name=user.name, icon_url=user.avatar.url)
            channel = interaction.guild.get_channel(DICT_SAVE_CATEGORY[category])
            await channel.send(embed=embed, file=transcript_file)
            # 通知の送信
            embed = discord.Embed(title="", description=f"チケットを保存しました。",
                                  colour=Color_OK)
            await interaction.channel.send(embed=embed)  # noqa

    @action_row.button(label="チケットを削除", emoji="🗑️", style=discord.ButtonStyle.grey,  # noqa
                       custom_id="ticket_delete")  # noqa
    async def ticket_delete_button(self, interaction: discord.Interaction, button: ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        if ENV == "prod":
            retry_after = bucket.update_rate_limit()
        else:
            retry_after = None
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        elif interaction.user.get_role(ROLE_ID_WNH_STAFF) is None:
            error_embed = discord.Embed(description="⚠️ この機能はWNH STAFF専用です。", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            # ログの送信
            category = DICT_CATEGORY[interaction.channel.category_id]
            category_name = DICT_NAME[category]
            embed = discord.Embed(colour=Color_ERROR)
            embed.add_field(name="情報", value=f"チケット：{interaction.channel.name}"
                                               f"\n内容：チケット削除")
            embed.add_field(name="カテゴリ", value=f"{category_name}")
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
            channel = interaction.guild.get_channel(DICT_LOG_CATEGORY[category])
            await channel.send(embed=embed)
            # 通知の送信
            await interaction.response.defer()  # noqa
            embed = discord.Embed(title="", description=f"チケットはまもなく削除されます。",
                                  colour=Color_ERROR)
            await interaction.channel.send(embed=embed)  # noqa
            time.sleep(3)
            await interaction.channel.delete()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item, /) -> None:
        """エラー処理"""
        await discord_error(item.label, interaction, error, logger)  # noqa


class ClanForm(ui.Modal, title="面談希望日時　申請フォーム"):
    """フォームの実装"""

    def __init__(self, view):
        super().__init__()
        self.view = view

    # フォームの入力項目の定義（最大5個）

    clan_tag = ui.Label(
        text="クランタグ",
        component=discord.ui.TextInput(
            max_length=10,
        ),
    )

    dt1 = ui.Label(
        text="第一希望（平日枠）",
        description="本日から7日後以降で希望日と希望枠を入力してください。（参加できない枠は不可と入力してください。）",
        component=ui.TextInput(
            placeholder="例：1/1 10:00～11:00",
            max_length=30,
        ),
    )

    dt2 = ui.Label(
        text="第一希望（平日枠）",
        description="本日から7日後以降で希望日と希望枠を入力してください。（参加できない枠は不可と入力してください。）",
        component=ui.TextInput(
            placeholder="例：1/1 10:00～11:00",
            max_length=30,
        ),
    )

    dt3 = ui.Label(
        text="第一希望（平日枠）",
        description="本日から7日後以降で希望日と希望枠を入力してください。（参加できない枠は不可と入力してください。）",
        component=ui.TextInput(
            placeholder="例：1/1 10:00～11:00",
            max_length=30,
        ),
    )

    dt4 = ui.Label(
        text="第一希望（平日枠）",
        description="本日から7日後以降で希望日と希望枠を入力してください。（参加できない枠は不可と入力してください。）",
        component=ui.TextInput(
            placeholder="例：1/1 10:00～11:00",
            max_length=30,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer()  # noqa
        # 担当者に送信
        embed = discord.Embed(title=f"クラン{self.clan_tag.component.value}　面談希望日時")  # noqa
        embed.add_field(name="第一希望（平日枠）", value=self.dt1.component.value, inline=False)  # noqa
        embed.add_field(name="第二希望（平日枠）", value=self.dt2.component.value, inline=False)  # noqa
        embed.add_field(name="第一希望（土日祝枠）", value=self.dt3.component.value, inline=False)  # noqa
        embed.add_field(name="第二希望（土日祝枠）", value=self.dt4.component.value, inline=False)  # noqa
        channel = interaction.guild.get_channel(CLAN_MEET_ID)
        await channel.send(content=f"<@&{CLAN_STAFF_ROLE}>\n{interaction.channel.jump_url}", embed=embed)
        # フォームへのレスポンス
        await interaction.message.edit(view=self.view)
        response_embed = discord.Embed(
            description=f"面談希望日時を送信しました。\n担当者より折り返しご連絡しますのでチケットはこのままでお待ちください。",
            color=Color_OK)
        await interaction.channel.send(embed=response_embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """エラー発生時の処理"""
        await discord_error(self.title, interaction, error, logger)


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Contact(bot))
    bot.add_view(view=CreateTicketView())
    bot.add_view(view=ClanTicketView())
    bot.add_view(view=GeneralTicketView())
    bot.add_view(view=ReportTicketView())
    bot.add_view(view=ToolButtonView())
