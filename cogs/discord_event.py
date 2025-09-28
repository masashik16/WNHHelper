from datetime import datetime
import os

import discord
import pytz
from discord.ext import commands
from dotenv import load_dotenv

from logs import logger

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=True)
GUILD_ID = int(os.environ.get("GUILD_ID"))
ROLE_ID_ADMIN = int(os.environ.get("ROLE_ID_ADMIN"))
ROLE_ID_WAIT_AGREE_RULE = int(os.environ.get("ROLE_ID_WAIT_AGREE_RULE"))
ROLE_ID_WAIT_AUTH = int(os.environ.get("ROLE_ID_WAIT_AUTH"))
ROLE_ID_AUTHED = int(os.environ.get("ROLE_ID_AUTHED"))
CHANNEL_ID_MESSAGE_LOG = int(os.environ.get("CHANNEL_ID_MESSAGE_LOG"))
CHANNEL_ID_USER_LOG = int(os.environ.get("CHANNEL_ID_USER_LOG"))
COLOR_OK = 0x00ff00
COLOR_WARN = 0xffa500
COLOR_ERROR = 0xff0000
logger = logger.getChild("discord_event")
JP = pytz.timezone("Asia/Tokyo")

"""コマンドの実装"""


class DiscordEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def dm_reply(self, message: discord.Message, /) -> None:
        """BOTのDMへメッセージが送信された場合にBOTからの送信専用である旨通知"""
        if type(message.channel) == discord.DMChannel and message.author != self.bot.user:
            user_dm = await message.author.create_dm()
            embed = discord.Embed(title="⚠️ このDMはWNH Helperからの送信専用です。",
                                  description="WNHへのお問い合わせは下記よりお願いします。", color=COLOR_OK)
            embed.add_field(name="認証前のお問い合わせ", value="https://dyno.gg/form/b5f6b630", inline=True)
            embed.add_field(name="処罰への申立", value="処罰通知に記載のURL", inline=True)
            embed.add_field(name="その他のお問い合わせ",
                            value="https://discord.com/channels/977773343396728872/977773343824560131", inline=True)
            await user_dm.send(embed=embed)

    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, old_member: discord.Member, new_member: discord.Member):
        """ユーザーがプロフィールを更新した場合に記録"""
        # 必要情報の取得
        guild = self.bot.get_guild(GUILD_ID)
        user_log_channel = await guild.fetch_channel(CHANNEL_ID_USER_LOG)
        dt = datetime.now(JP)
        ts = int(datetime.timestamp(dt))
        # ニックネームを更新した場合
        if old_member.nick != new_member.nick:
            embed = discord.Embed(title="", description=f"<@{old_member.id}>のニックネームが更新されました")
            embed.add_field(name="更新後", value=f"{new_member.nick}", inline=False)
            embed.add_field(name="更新前", value=f"{old_member.nick}", inline=False)
            embed.add_field(name="更新日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {old_member.id}```", inline=False)
            embed.set_author(name=old_member, icon_url=old_member.display_avatar.url)
            await user_log_channel.send(embed=embed)
        # アバターを更新した場合
        if old_member.display_avatar.url != new_member.display_avatar.url:
            embed = discord.Embed(title="", description=f"<@{new_member.id}>のアバターが更新されました")
            embed.add_field(name="更新日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {new_member.id}```", inline=False)
            embed.set_author(name=new_member, icon_url=new_member.display_avatar.url)
            msg = await user_log_channel.send(embed=embed)
            thread = await msg.create_thread(name="アバター")
            # f = await old_member.display_avatar.to_file(filename="old_avatar.png")
            # avatar_embed = discord.Embed(title="更新前")
            # avatar_embed.set_image(url=f"attachment://{f.filename}")
            # await thread.send(embed=avatar_embed, file=f)
            f = await old_member.display_avatar.to_file(filename="new_avatar.png")
            avatar_embed = discord.Embed(title="更新後")
            avatar_embed.set_image(url=f"attachment://{f.filename}")
            await thread.send(embed=avatar_embed, file=f)

    @commands.Cog.listener("on_user_update")
    async def on_user_update(self, old_user: discord.User, new_user: discord.User):
        """ユーザーがプロフィールを更新した場合の処理"""
        # 必要情報の取得
        guild = self.bot.get_guild(GUILD_ID)
        user_log_channel = await guild.fetch_channel(CHANNEL_ID_USER_LOG)
        dt = datetime.now(JP)
        ts = int(datetime.timestamp(dt))
        # アカウント名を更新した場合
        if old_user.name != new_user.name:
            embed = discord.Embed(title="", description=f"<@{old_user.id}>のユーザー名が更新されました")
            embed.add_field(name="更新後", value=f"{new_user.name}", inline=False)
            embed.add_field(name="更新前", value=f"{old_user.name}", inline=False)
            embed.add_field(name="更新日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {old_user.id}```", inline=False)
            embed.set_author(name=old_user, icon_url=old_user.display_avatar.url)
            await user_log_channel.send(embed=embed)
        # アバターを更新した場合
        if old_user.display_avatar.url != new_user.display_avatar.url:
            embed = discord.Embed(title="", description=f"<@{old_user.id}>のアバターが更新されました")
            embed.add_field(name="更新日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {old_user.id}```", inline=False)
            embed.set_author(name=old_user, icon_url=old_user.display_avatar.url)
            msg = await user_log_channel.send(embed=embed)
            thread = await msg.create_thread(name="アバター")
            # f = await old_user.display_avatar.to_file(filename="old_avatar.png")
            # avatar_embed = discord.Embed(title="更新前")
            # avatar_embed.set_image(url=f"attachment://{f.filename}")
            # await thread.send(embed=avatar_embed, file=f)
            f = await new_user.display_avatar.to_file(filename="new_avatar.png")
            avatar_embed = discord.Embed(title="更新後")
            avatar_embed.set_image(url=f"attachment://{f.filename}")
            await thread.send(embed=avatar_embed, file=f)

    @commands.Cog.listener("on_message_delete")
    async def message_delete_log(self, message: discord.Message):
        """メッセージ削除時に内容を記録"""
        # 送信者が自分（このBOT）以外かつ指定ギルドと一致する場合のみ処理
        if not message.author.bot and message.guild.id == GUILD_ID:
            # ギルド、チャンネルを取得し、チャンネルリンクを作成
            guild = self.bot.get_guild(GUILD_ID)
            message_log_channel = await guild.fetch_channel(CHANNEL_ID_MESSAGE_LOG)
            channel = message.channel
            url = f"https://discord.com/channels/{GUILD_ID}/{channel.id}"
            # 現在日時を取得
            dt = datetime.now(JP)
            ts = int(datetime.timestamp(dt))
            # メッセージの送信者情報を取得
            user = message.author
            avatar = user.display_avatar.url
            # 記録用メッセージの作成
            embed = discord.Embed(title="", description=f"{url}でメッセージが削除されました")
            embed.set_author(name=user, icon_url=avatar)
            embed.add_field(name="投稿日時", value=f"<t:{int(message.created_at.timestamp())}:F>", inline=False)
            embed.add_field(name="リンク", value=f"[リンクはこちら]({message.jump_url})", inline=False)
            embed.add_field(name="内容", value=f"{message.content}", inline=False)
            embed.add_field(name="削除日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {user.id}\nMessage = {message.id}```", inline=False)
            # 記録を送信
            msg = await message_log_channel.send(embed=embed)
            # 添付ファイルがある場合は追加送信
            if message.attachments:
                thread = await msg.create_thread(name="添付画像")
                for e in message.attachments:
                    try:
                        f = await e.to_file()
                        attachments_embed = discord.Embed()
                        attachments_embed.set_image(url=f"attachment://{f.filename}")
                        await thread.send(embed=attachments_embed, file=f)
                    except AttributeError:
                        break

    @commands.Cog.listener("on_message_edit")
    async def message_edit_log(self, old_message: discord.Message, new_message: discord.Message):
        """メッセージ編集時に内容を記録"""
        thread = None
        content_embed = True
        # 送信者が自分（このBOT）以外かつ指定ギルドと一致する場合のみ処理
        if not old_message.author.bot and old_message.guild.id == GUILD_ID:
            # ギルド、チャンネルを取得し、チャンネルリンクを作成
            guild = self.bot.get_guild(GUILD_ID)
            message_log_channel = await guild.fetch_channel(CHANNEL_ID_MESSAGE_LOG)
            channel = old_message.channel
            url = f"https://discord.com/channels/{GUILD_ID}/{channel.id}"
            # 現在日時を取得
            dt = datetime.now(JP)
            ts = int(datetime.timestamp(dt))
            # メッセージの送信者情報を取得
            user = old_message.author
            avatar = user.display_avatar.url
            # 記録用メッセージの作成
            embed = discord.Embed(title="", description=f"{url}でメッセージが更新されました")
            embed.set_author(name=user, icon_url=avatar)
            embed.add_field(name="リンク", value=f"[リンクはこちら]({new_message.jump_url})", inline=False)
            if len(new_message.content) + len(old_message.content) > 5000:
                embed.add_field(name="更新前", value="スレッドに記載", inline=False)
                embed.add_field(name="更新後", value="スレッドに記載", inline=False)
            else:
                embed.add_field(name="更新前", value=f"{old_message.content}", inline=False)
                embed.add_field(name="更新後", value=f"{new_message.content}", inline=False)
                content_embed = False
            embed.add_field(name="更新日時", value=f"<t:{ts}:F>", inline=False)
            embed.add_field(name="ID", value=f"```ini\nUser = {user.id}\nMessage = {old_message.id}```", inline=False)
            msg = await message_log_channel.send(embed=embed)
            # メッセージに添付ファイルが存在するか、更新前と更新後の総文字数が5000を超える場合
            if new_message.attachments or old_message.attachments or content_embed:
                thread = await msg.create_thread(name="添付画像・その他")
            # 更新前と更新後の総文字数が5000を超える場合に分割して送信
            if len(new_message.content) + len(old_message.content) > 5000:
                content_embed = discord.Embed(title="内容（旧メッセージ）", description=f"{old_message.content}")
                await thread.send(embed=content_embed)
                content_embed = discord.Embed(title="内容（新メッセージ）", description=f"{new_message.content}")
                await thread.send(embed=content_embed)
            # 編集前のメッセージの添付ファイルを送信
            if old_message.attachments:
                embed = discord.Embed(title="添付ファイル（旧メッセージ）")
                await thread.send(embed=embed)
                for e in old_message.attachments:
                    try:
                        f = await e.to_file()
                        attachments_embed = discord.Embed()
                        attachments_embed.set_image(url=f"attachment://{f.filename}")
                        await thread.send(embed=attachments_embed, file=f)
                    except AttributeError:
                        break
            # 編集後のメッセージの添付ファイルを送信
            if new_message.attachments:
                embed = discord.Embed(title="添付ファイル（新メッセージ）")
                await thread.send(embed=embed)
                for e in new_message.attachments:
                    try:
                        f = await e.to_file()
                        attachments_embed = discord.Embed()
                        attachments_embed.set_image(url=f"attachment://{f.filename}")
                        await thread.send(embed=attachments_embed, file=f)
                    except AttributeError:
                        break

    @commands.Cog.listener("on_thread_create")
    async def thread_join(self, thread: discord.Thread, /) -> None:
        """スレッドのメッセージ削除・編集を記録するため、スレッドが作成された場合にこのBOTを追加"""
        await thread.add_user(self.bot.user)


async def setup(bot):
    await bot.add_cog(DiscordEvent(bot))
