import math

import discord

from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    img_attachment,
    msg_attachment,
    audio_attachment,
    video_attachment,
    component_media_gallery_image,
    component_media_gallery_video,
    component_thumbnail,
    PARSE_MODE_NONE,
)


class Attachment:
    def __init__(self, attachments, guild):
        self.attachments = attachments
        self.guild = guild

    async def flow(self):
        await self.build_attachment()
        return self.attachments

    async def build_attachment(self):
        if isinstance(self.attachments, discord.Attachment):
            if self.attachments.content_type is not None:
                if "image" in self.attachments.content_type:
                    return await self.image()
                elif "video" in self.attachments.content_type:
                    return await self.video()
                elif "audio" in self.attachments.content_type:
                    return await self.audio()
            await self.file()
        elif isinstance(self.attachments, discord.ThumbnailComponent):
            return await self.ui_thumbnail()
        elif isinstance(self.attachments, discord.UnfurledMediaItem):
            if "image" in self.attachments.content_type:
                return await self.ui_image()
            elif "video" in self.attachments.content_type:
                return await self.ui_video()
        else:
            await self.ui_file()

    async def image(self):
        self.attachments = await fill_out(self.guild, img_attachment, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def video(self):
        self.attachments = await fill_out(self.guild, video_attachment, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def audio(self):
        file_icon = DiscordUtils.file_attachment_audio
        file_size = self.get_file_size(self.attachments.size)
        filename = self.attachments.url.split("://")[1]

        self.attachments = await fill_out(self.guild, audio_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_AUDIO", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_FILE", str(filename), PARSE_MODE_NONE)
        ])

    async def file(self):
        file_icon = await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE)
        ])

    async def ui_image(self):
        self.attachments = await fill_out(self.guild, component_media_gallery_image, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def ui_video(self):
        self.attachments = await fill_out(self.guild, component_media_gallery_video, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])



    async def ui_file(self):
        file_icon = await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.media.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.name), PARSE_MODE_NONE)
        ])

    async def ui_thumbnail(self):
        self.attachments = await fill_out(self.guild, component_thumbnail, [
            ("ATTACH_URL", self.attachments.media.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", self.attachments.media.proxy_url, PARSE_MODE_NONE)
        ])

    @staticmethod
    def get_file_size(file_size):
        if file_size == 0:
            return "0 bytes"
        size_name = ("bytes", "KB", "MB")
        i = int(math.floor(math.log(file_size, 1024)))
        p = math.pow(1024, i)
        s = round(file_size / p, 2)
        return "%s %s" % (s, size_name[i])

    async def get_file_icon(self) -> str:
        acrobat_types = "pdf"
        webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
        code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
        document_types = (
            "txt", "doc", "docx", "rtf", "xls", "xlsx", "ppt", "pptx", "odt", "odp", "ods", "odg", "odf", "swx",
            "sxi", "sxc", "sxd", "stw"
        )
        archive_types = (
            "br", "rpm", "dcm", "epub", "zip", "tar", "rar", "gz", "bz2", "7x", "deb", "ar", "Z", "lzo", "lz", "lz4",
            "arj", "pkg", "z"
        )

        if isinstance(self.attachments, discord.Attachment):
            l = [self.attachments.proxy_url, self.attachments.filename]
        else:
            l = [self.attachments.media.proxy_url, self.attachments.name]

        for tmp in l:
            if not tmp:
                continue
            extension = tmp.rsplit('.', 1)[-1]
            if extension in acrobat_types:
                return DiscordUtils.file_attachment_acrobat
            elif extension in webcode_types:
                return DiscordUtils.file_attachment_webcode
            elif extension in code_types:
                return DiscordUtils.file_attachment_code
            elif extension in document_types:
                return DiscordUtils.file_attachment_document
            elif extension in archive_types:
                return DiscordUtils.file_attachment_archive

        return DiscordUtils.file_attachment_unknown
