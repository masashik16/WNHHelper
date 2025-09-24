import discord
from discord import app_commands, InteractionType
Color_WARN = 0xffa500
Color_ERROR = 0xff0000

class FlaskCustomError(Exception):
    def __init__(self, error_title: str, error_list: list, error_code: str, response_code:int):
        self.error_title = error_title
        self.error_list = error_list
        self.error_code = error_code
        self.response_code = response_code

async def discord_error(name, interaction, error, logger):
    """コマンド実行時のエラー処理"""
    if interaction.type == InteractionType.modal_submit:
        type = "フォーム"
    elif interaction.type == InteractionType.application_command:
        type = "コマンド"
    elif interaction.type == InteractionType.component:
        type = "ボタン/ドロップダウン"
    else:
        type = "不明なタイプ"
    # 指定ロールを保有していない場合
    if isinstance(error, app_commands.CheckFailure):
        error_embed = discord.Embed(description="⚠️ 権限がありません", color=Color_ERROR)
        # ログの保存
        logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                     f"が{type}「{name}」を使用しようとしましたが、権限不足により失敗しました。",
                     exc_info=True)
    else:
        error_embed = discord.Embed(description="⚠️ エラーが発生しました", color=Color_ERROR)
        # ログの保存
        logger.error(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                     f"が{type}「{name}」を使用しようとしましたが、失敗しました。", exc_info=True)
    try:
        await interaction.response.send_message(embed=error_embed, ephemeral=True)  # noqa
    except discord.errors.InteractionResponded:
        await interaction.followup.send(embed=error_embed, ephemeral=True)