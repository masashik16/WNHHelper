import io
import os
import time

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import chat_exporter
import db
from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WNH_STAFF = int(os.environ.get("ROLE_ID_WNH_STAFF"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
GENERAL_INQRY_OPEN = int(os.environ.get("GENERAL_INQRY_OPEN"))
GENERAL_INQRY_CLOSE = int(os.environ.get("GENERAL_INQRY_CLOSE"))
GENERAL_INQRY_LOG = int(os.environ.get("GENERAL_INQRY_LOG"))
GENERAL_INQRY_SAVE = int(os.environ.get("GENERAL_INQRY_SAVE"))
REPORT_OPEN = int(os.environ.get("REPORT_OPEN"))
REPORT_CLOSE = int(os.environ.get("REPORT_CLOSE"))
REPORT_LOG = int(os.environ.get("REPORT_LOG"))
REPORT_SAVE = int(os.environ.get("REPORT_SAVE"))
CLAN_OPEN = int(os.environ.get("CLAN_OPEN"))
CLAN_CLOSE = int(os.environ.get("CLAN_CLOSE"))
CLAN_LOG = int(os.environ.get("CLAN_LOG"))
CLAN_SAVE = int(os.environ.get("CLAN_SAVE"))
CLAN_STAFF_ROLE = int(os.environ.get("CLAN_STAFF_ROLE"))
CLAN_MEET_ID = int(os.environ.get("CLAN_MEET_ID"))
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
        # ドロップダウンを含むビューを作成
        view = TicketDropdownView()
        # Embedの作成
        embed = discord.Embed(title="各種問い合わせについて",
                              description=f"最後の対応から24時間反応がないチケットはクローズします")
        embed.add_field(name="当サーバーに対するご意見/ご要望/その他お問い合わせ",
                        value="下のリストから「ご意見・ご要望・その他問い合わせ」を選択してチケットを作成してください。",
                        inline=False)
        embed.add_field(name="公認クランプログラムへのお申し込み",
                        value="<@&983915259838488587>ロールをご希望の方は「公認クランプログラムへのお申し込み」を選択してください。",
                        inline=False)
        embed.add_field(name="違反行為の報告",
                        value="* 不適切なメッセージを報告したい場合"
                              "\n報告したいメッセージを右クリックして「アプリ」→「メッセージの報告」をクリックし、報告内容を記載して送信してください"
                              "\n* 不適切なニックネームやアバター・VCでの違反行為等メッセージでの違反以外を報告したい場合"
                              "\nユーザーを右クリックして「アプリ」→「ユーザーの報告」をクリックし、報告内容を記載して送信してください"
                              "\n\n上記の手順でエラーが起こる場合は、下記リストから「違反行為の報告」を選択してチケットを作成してください。",
                        inline=False)
        embed.add_field(name="セクシャルハラスメント等の通報について",
                        value="セクシャルハラスメント等の通報で女性スタッフによる対応を希望する場合は<@767646985632481320>のDMへご連絡ください。",
                        inline=False)
        # # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(embed=embed, view=view)
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

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
        # 指定ロールを保有していない場合
        if isinstance(error, app_commands.CheckFailure):
            error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
            # ログの保存
            logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                         f"がコマンド「{interaction.command.name}」を使用しようとしましたが、権限不足により失敗しました。")


class TicketDropdownView(discord.ui.View):
    """ドロップダウンの作成"""

    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.select(
        cls=discord.ui.Select,
        custom_id="ticket_panel",
        placeholder="お問い合わせ内容を選択してください",
        options=[
            discord.SelectOption(label="ご意見・ご要望・その他お問い合わせ", value="GENERAL", emoji="📨"),
            discord.SelectOption(label="違反行為の報告", value="REPORT", emoji="🚨"),
            discord.SelectOption(label="公認クランプログラムへのお申し込み", value="CLAN", emoji="🈸"),
        ],
    )
    async def set_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            await interaction.response.defer()  # noqa
            select_value = select.values[0]
            # ドロップダウンの選択項目を初期化
            await interaction.message.edit(view=TicketDropdownView())
            # 選択されたカテゴリのカテゴリチャンネルの取得
            open_category = interaction.guild.get_channel(DICT_OPEN_CATEGORY[select_value])
            close_category = interaction.guild.get_channel(DICT_CLOSE_CATEGORY[select_value])
            # DBからチケット番号を取得
            channel_number_db = await db.get_inquiry_number(select_value)
            # channel_number_db = 1
            channel_number = f"{channel_number_db:04}"
            if select_value == "GENERAL":
                view = CloseButtonView()
                embed = discord.Embed(title="", description="お問い合わせありがとうございます。"
                                                            "\n問い合わせ内容をこのチャンネルに送信してお待ちください。担当者が順次対応いたします。"
                                                            "\nチケットを閉じたい場合は 🔒をクリックしてください。")
            elif select_value == "REPORT":
                view = CloseButtonView()
                embed = discord.Embed(title="", description="お問い合わせありがとうございます。"
                                                            "\n通報内容をこのチャンネルに送信してお待ちください。担当者が順次対応いたします。"
                                                            "\n可能な場合はスクリーンショット、メッセージリンクを添付して下さい。"
                                                            "\nメッセージリンクのコピー方法"
                                                            "\n・メッセージリンクをコピーしたいメッセージを右クリックし、「メッセージリンクをコピー」を選択します"
                                                            "\nチケットを閉じたい場合は 🔒を押してください。")

            else:
                view = ClanButtonView()
                embed = discord.Embed(title="", description="公認クランプログラムへお申し込み頂きありがとうございます。"
                                                            "\n本プログラムへのお申し込みに当たり、担当者との面談が必要となります。"
                                                            "\nお手数ですが下のボタンからフォームを開き、**本日から7日後以降**で希望日と希望枠を入力してください。"
                                                            "\nチケットを閉じたい場合は 🔒をクリックしてください。")
                embed.add_field(name="希望枠について", value="希望枠は以下の枠から平日、土日祝**それぞれ2枠**選択してください。"
                                                             "\n参加不可な枠には不可と入力してください。"
                                                             "\n**平日**"
                                                             "\n23:00～24:00"
                                                             "\n24:00～25:00"
                                                             "\n\n**土日祝**"
                                                             "\n10:00～11:00"
                                                             "\n11:00～12:00"
                                                             "\n12:00～13:00")
            # チケットの重複作成の防止
            open_channels = open_category.text_channels
            close_channels = close_category.text_channels
            channels = open_channels + close_channels
            users = []
            for channel in channels:
                async for message in channel.history(limit=1, oldest_first=True):
                    uid = message.content.replace("<@", "").replace(">", "")
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

                await ticket.send(content=f"{interaction.user.mention}", embed=embed, view=view)
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


class ClanButtonView(discord.ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="チケットを閉じる", emoji="🔒", style=discord.ButtonStyle.grey,
                       custom_id="ticket_close_clan")
    async def ticket_close_button_clan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await ticket_close(interaction)

    @discord.ui.button(label="面談希望日時を申請", emoji="🈸", style=discord.ButtonStyle.grey,
                       custom_id="ticket_clan_form_button")
    async def ticket_clan_form_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            error_embed = discord.Embed(description=f"⚠️ {int(retry_after) + 1}秒後に再度お試しください。",
                                        color=Color_ERROR)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        else:
            button.disabled = True
            await interaction.response.send_modal(ClanForm(view=self))  # noqa


class CloseButtonView(discord.ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="チケットを閉じる", emoji="🔒", style=discord.ButtonStyle.grey, custom_id="ticket_close")
    async def ticket_close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await ticket_close(interaction)


async def ticket_close(interaction: discord.Interaction):
    bucket = COOLDOWN.get_bucket(interaction.message)
    retry_after = bucket.update_rate_limit()
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
        view = ToolButtonView()
        tool_embed = discord.Embed(title="", description="🔓 チケットを再開"
                                                         "\n--以下スタッフ専用--"
                                                         "\n📑 チケットを保存"
                                                         "\n🗑️ チケットを削除")
        await interaction.channel.send(embed=tool_embed, view=view)  # noqa


class ToolButtonView(discord.ui.View):
    """ボタンの実装"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="チケットを再開", emoji="🔓", style=discord.ButtonStyle.grey, custom_id="ticket_open")
    async def ticket_open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
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

    @discord.ui.button(label="チケットを保存", emoji="📑", style=discord.ButtonStyle.grey, custom_id="ticket_save")
    async def ticket_save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
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
            first_user_message_list = [message.content async for message in
                                       interaction.channel.history(limit=1, oldest_first=True)]
            first_user_message = first_user_message_list[0]
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

    @discord.ui.button(label="チケットを削除", emoji="🗑️", style=discord.ButtonStyle.grey, custom_id="ticket_delete")
    async def ticket_delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = COOLDOWN.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
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


class ClanForm(discord.ui.Modal, title="面談希望日時　申請フォーム"):
    """フォームの実装"""

    def __init__(self, view):
        super().__init__()
        self.view = view

    # フォームの入力項目の定義（最大5個）

    clan_tag = discord.ui.TextInput(
        label="クランタグ",
        max_length=10,
    )

    dt1 = discord.ui.TextInput(
        label="第一希望（平日枠）",
        placeholder="希望日と希望枠を入力してください。",
        max_length=30,
    )

    dt2 = discord.ui.TextInput(
        label="第二希望（平日枠）",
        placeholder="選択可能日は本日から7日後以降です。",
        max_length=30,
    )

    dt3 = discord.ui.TextInput(
        label="第一希望（土日祝枠）",
        placeholder="参加できない枠は不可と入力してください。",
        max_length=30,
    )

    dt4 = discord.ui.TextInput(
        label="第二希望（土日祝枠）",
        placeholder="例：1/1 10:00～11:00",
        max_length=30,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """フォーム送信時の処理"""
        await interaction.response.defer()  # noqa
        # 担当者に送信
        embed = discord.Embed(title=f"クラン{self.clan_tag.value}　面談希望日時")
        embed.add_field(name="第一希望（平日枠）", value=self.dt1.value, inline=False)
        embed.add_field(name="第二希望（平日枠）", value=self.dt2.value, inline=False)
        embed.add_field(name="第一希望（土日祝枠）", value=self.dt3.value, inline=False)
        embed.add_field(name="第二希望（土日祝枠）", value=self.dt4.value, inline=False)
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
        error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"フォーム「公認クラン」でエラーが発生しました。\nエラー内容：{error}")


async def setup(bot):
    """起動時のコグへの追加"""
    await bot.add_cog(Contact(bot))
    bot.add_view(view=TicketDropdownView())
    bot.add_view(view=ClanButtonView())
    bot.add_view(view=CloseButtonView())
    bot.add_view(view=ToolButtonView())
