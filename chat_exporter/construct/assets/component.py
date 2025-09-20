from chat_exporter.construct.assets import Attachment
from chat_exporter.ext.discord_import import discord

from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    component_button,
    component_menu,
    component_menu_options,
    component_menu_options_emoji,
    component_text_display,
    component_container,
    component_section,
    component_separator,
    PARSE_MODE_NONE,
    PARSE_MODE_EMOJI,
    PARSE_MODE_MARKDOWN,
)


class Component:
    styles = {
        "primary": "#5865F2",
        "secondary": "#4F545C",
        "success": "#2D7D46",
        "danger": "#D83C3E",
        "blurple": "#5865F2",
        "grey": "#4F545C",
        "gray": "#4F545C",
        "green": "#2D7D46",
        "red": "#D83C3E",
        "link": "#4F545C",
    }

    components: str = ""
    menus: str = ""
    buttons: str = ""
    menu_div_id: int = 0

    action_row_components:str = ""
    container:str = ""
    container_components:str = ""
    files:str = ""
    gallery_medias:str = ""
    media_galleries:str = ""
    section_components:str = ""
    separators:str = ""
    text_displays: str = ""
    thumbnails:str = ""

    def __init__(self, component, guild):
        self.component = component
        self.guild = guild

    async def build_component(self, c):
        if isinstance(c, discord.Button):
            await self.build_button(c)
        elif isinstance(c, discord.SelectMenu):
            await self.build_menu(c)
            Component.menu_div_id += 1
        elif isinstance(c, discord.ActionRow):
            await self.build_action_row(c)
        elif isinstance(c, discord.FileComponent):
            await self.build_files(c)
        elif isinstance(c, discord.MediaGalleryComponent):
            await self.build_media_gallery(c)
        elif isinstance(c, discord.SectionComponent):
            await self.build_section(c)
        elif isinstance(c, discord.SeparatorComponent):
            await self.build_separator(c)
        elif isinstance(c, discord.TextDisplay):
            await self.build_text_display(c)
        elif isinstance(c, discord.ThumbnailComponent):
            await self.build_thumbnail(c)

    async def build_button(self, c):
        if c.url:
            url = str(c.url)
            target = " target='_blank'"
            icon = str(DiscordUtils.button_external_link)
        else:
            url = "javascript:;"
            target = ""
            icon = ""
            
        label = str(c.label) if c.label else ""
        style = self.styles[str(c.style).split(".")[1]]
        emoji = str(c.emoji) if c.emoji else ""

        self.buttons += await fill_out(self.guild, component_button, [
            ("DISABLED", "chatlog__component-disabled" if c.disabled else "", PARSE_MODE_NONE),
            ("URL", url, PARSE_MODE_NONE),
            ("LABEL", label, PARSE_MODE_MARKDOWN),
            ("EMOJI", emoji, PARSE_MODE_EMOJI),
            ("ICON", icon, PARSE_MODE_NONE),
            ("TARGET", target, PARSE_MODE_NONE),
            ("STYLE", style, PARSE_MODE_NONE)
        ])

    async def build_menu(self, c):
        placeholder = c.placeholder if c.placeholder else ""
        options = c.options
        content = ""

        if not c.disabled:
            content = await self.build_menu_options(options)

        self.menus += await fill_out(self.guild, component_menu, [
            ("DISABLED", "chatlog__component-disabled" if c.disabled else "", PARSE_MODE_NONE),
            ("ID", str(self.menu_div_id), PARSE_MODE_NONE),
            ("PLACEHOLDER", str(placeholder), PARSE_MODE_MARKDOWN),
            ("CONTENT", str(content), PARSE_MODE_NONE),
            ("ICON", DiscordUtils.interaction_dropdown_icon, PARSE_MODE_NONE),
        ])

    async def build_menu_options(self, options):
        content = []
        for option in options:
            if option.emoji:
                content.append(await fill_out(self.guild, component_menu_options_emoji, [
                    ("EMOJI", str(option.emoji), PARSE_MODE_EMOJI),
                    ("TITLE", str(option.label), PARSE_MODE_MARKDOWN),
                    ("DESCRIPTION", str(option.description) if option.description else "", PARSE_MODE_MARKDOWN)
                ]))
            else:
                content.append(await fill_out(self.guild, component_menu_options, [
                    ("TITLE", str(option.label), PARSE_MODE_MARKDOWN),
                    ("DESCRIPTION", str(option.description) if option.description else "", PARSE_MODE_MARKDOWN)
                ]))

        if content:
            content = f'<div id="dropdownMenu{self.menu_div_id}" class="dropdownContent">{"".join(content)}</div>'

        return content

    async def build_text_display(self, c):
        content = str(c.content) if c.content else ""
        self.text_displays += await fill_out(self.guild, component_text_display, [
            ("CONTENT", content, PARSE_MODE_MARKDOWN)
        ])

    async def build_container(self,c):
        if c.accent_color:
            r = str(c.accent_color.r)
            g = str(c.accent_color.g)
            b = str(c.accent_color.b)
        else:
            r = ""
            g = ""
            b = ""
        self.components += await fill_out(self.guild, component_container, [
            ("COMPONENT", self.container_components, PARSE_MODE_NONE),
            ("EMBED_R", r, PARSE_MODE_NONE),
            ("EMBED_R", g, PARSE_MODE_NONE),
            ("EMBED_R", b, PARSE_MODE_NONE),
        ])

    async def build_action_row(self, c):
        for cc in c.children:
            await self.build_component(cc)
        if self.menus:
            self.action_row_components += f'<div class="chatlog__components">{self.menus}</div>'
            self.menus = ""
        if self.buttons:
            self.action_row_components += f'<div class="chatlog__components">{self.buttons}</div>'
            self.buttons = ""


    async def build_files(self, c):
        self.files += await Attachment(c, self.guild).flow()

    async def build_thumbnail(self, c):
        self.thumbnails += await Attachment(c, self.guild).flow()

    async def build_media_gallery(self, c):
        print("A")
        for i in c.items:
            self.gallery_medias += await Attachment(i.media, self.guild).flow()
        self.media_galleries = f'<div class="chatlog__components">{self.gallery_medias}</div>'
        self.gallery_medias = ""


    async def build_section(self, c):
        for cc in c.children:
            await self.build_component(cc)
        await self.build_component(c.accessory)
        if self.text_displays:
            self.section_components += self.text_displays
            self.text_displays = ""
        if self.buttons:
            self.section_components += f'<div class="chatlog__components">{self.buttons}</div>'
            self.buttons = ""
        if self.thumbnails:
            self.section_components += f'<div class="chatlog__components">{self.thumbnails}</div>'
            self.thumbnails = ""
        self.section_components = await fill_out(self.guild, component_section, [
            ("COMPONENT", self.section_components, PARSE_MODE_NONE)])


    async def build_separator(self, c):
        if c.spacing == discord.SeparatorSpacing.small:
            spacing = ""
        else:
            spacing = "large"
        if c.visible:
            visible = ""
        else:
            visible = "invisible"

        self.separators += await fill_out(self.guild, component_separator, [
            ("SPACING", spacing, PARSE_MODE_NONE),
            ("VISIBLE", visible, PARSE_MODE_NONE)
        ])

    async def flow(self):
        if isinstance(self.component, discord.Container):
            for c in self.component.children:
                await self.build_component(c)
                if self.text_displays:
                    self.container_components += self.text_displays
                    self.text_displays = ""

                if self.action_row_components:
                    self.container_components += self.action_row_components
                    self.action_row_components = ""

                if self.files:
                    self.container_components += self.files
                    self.files = ""

                if self.media_galleries:
                    self.container_components += self.media_galleries
                    self.media_galleries = ""

                if self.section_components:
                    self.container_components += self.section_components
                    self.section_components = ""

                if self.separators:
                    self.container_components += self.separators
                    self.separators = ""

            await self.build_container(self.component)
            self.container_components = ""

        elif isinstance(self.component, discord.ActionRow):
            await self.build_action_row(self.component)
            self.components += self.action_row_components
            self.action_row_components = ""

        else:
            await self.build_component(self.component)

            if self.menus:
                self.components += f'<div class="chatlog__components">{self.menus}</div>'
                self.menus = ""

            if self.buttons:
                self.components += f'<div class="chatlog__components">{self.buttons}</div>'
                self.buttons = ""

            if self.text_displays:
                self.components += self.text_displays
                self.text_displays = ""

            if self.action_row_components:
                self.components += self.action_row_components
                self.action_row_components = ""

            if self.files:
                self.components += self.files
                self.files = ""

            if self.media_galleries:
                self.components += self.media_galleries
                self.media_galleries = ""

            if self.section_components:
                self.components += self.section_components
                self.section_components = ""

            if self.separators:
                self.components += self.separators
                self.separators = ""

        return self.components
