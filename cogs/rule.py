import os

import discord
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv

from api import wows_user_info
from db import search_user
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
        # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(view=RuleMessageView())
        # コマンドへのレスポンス
        response_embed = discord.Embed(description="ℹ️ 送信が完了しました", color=Color_OK)
        await interaction.response.send_message(embed=response_embed, ephemeral=True)  # noqa
        # ログの保存
        logger.info(f"{interaction.user.display_name}（UID：{interaction.user.id}）"
                    f"がコマンド「{interaction.command.name}」を使用しました。")

    async def create_message2(self, interaction: discord.Interaction):
        """ロール無しユーザー用メッセージを作成"""
        # # ビューを含むメッセージを送信
        channel = interaction.channel
        await channel.send(view=NoRoleMessageView())
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


class RuleMessageView(ui.LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    about_server = ui.TextDisplay("## 本サーバーについて\n"
                                  "本サーバーは初心者さんのコミュニケーションを第一としたサーバーです。\n"
                                  "教えてもらったり、慰めてもらったり、褒めてもらったり、そんな感じで仲間と一緒にゲームがプレイ出来たら楽しいですよね。\n"
                                  "このサーバーは初心者さんが楽しい仲間とともにwowsを楽しんでもらえたらと思って作ったサーバーです。\n"
                                  "人にはそれぞれの楽しみ方があります。\n"
                                  "相手を尊重し、楽しく一緒にプレイしましょう！\n"
                                  "特に、人格否定や暴言、求められていないアドバイスなどは厳しく対処いたします。 ")
    container_about_server = ui.Container(about_server)

    rule1_title = ui.TextDisplay("## サーバー心得")
    rule1_text01 = ui.TextDisplay("### 1.自分から\n"
                                  "自分がコメントした時、分隊募集した時、反応がないと寂しいですよね。是非「私が！」と声を上げてほしいです！")
    rule1_text02 = ui.TextDisplay("### 2.優しく\n"
                                  "優しい人と、厳しい人。どちらの人と一緒に居たいですか？優しいに上限はありません。いつもの2倍のやさしさで接してほしいです！")
    rule1_text03 = ui.TextDisplay("### 3.それぞれ\n"
                                  "上手くなりたい人もいるし、ただ楽しみたい人もいます。正解はありません。相手に合わせて教えたりプレイしたりしていこう！")
    rule1_text04 = ui.TextDisplay("### 4.尊重し\n"
                                  "自分も、味方も、対戦相手も、このゲームをプレイして楽しんでいる人に変わりはありません！楽しみ方に違いはあれど、それを否定する発言は控えよう！")
    rule1_text05 = ui.TextDisplay("### 5.ポジティブに\n"
                                  "自分が好きなゲーム・艦艇が否定されてたら悲しくなりませんか？ポジティブな意見を伝えよう！\n例）×この艦艇弱い　→　○この艦艇で戦果出せる人はうまい人だね！")
    rule1_text06 = ui.TextDisplay("### 6.初心者のパートナーであってほしい\n"
                                  "私たちは初心者と共に考え、学び、支え合いながら活動してほしいと望んでいます。")
    container_rule1 = ui.Container(rule1_title, rule1_text01, rule1_text02, rule1_text03,
                                   rule1_text04, rule1_text05, rule1_text06)

    rule2_title = ui.TextDisplay("## ルールおよびコミュニティスタンダード\n"
                                 "全てのメンバーは下に記載されているルールとコミュニティスタンダードを読んで同意する必要があります。ルールを知らなかったことでペナルティなどが免除されることはありません。")
    rule2_text01 = ui.TextDisplay("### まずDiscordのルールを尊重し、守ってください\n"
                                  "* [Discordのコミュニティガイドライン](https://discord.com/guidelines)\n"
                                  "* [Discordの利用規約](https://discord.com/terms)")
    rule2_text02 = ui.TextDisplay("### 敬意\n"
                                  "常に礼儀正しく、他人を思いやった行動を心がけてください。艦艇性能の話をする時も、その艦艇を愛する人がいることを忘れないでください。")
    rule2_text03 = ui.TextDisplay("### チームスコア投稿\n"
                                  "リザルトのチームスコア画面を投稿する時は、必ず他人のIGN（名前）が見えないように加工してください。（自分と分隊員のIGNは見えていて大丈夫です）")
    rule2_text04 = ui.TextDisplay("### テーマ、トピック\n"
                                  "ディスカッションとコメントはチャンネルに関連のあるものにしてください。政治や宗教のような対立が生じる可能性のあるテーマの議論は禁止されています。")
    rule2_text05 = ui.TextDisplay("### 宣伝しないで\n"
                                  "URLを投稿すると、モデレーションの対象となる可能性があります。（初心者に有益な情報は除く）")
    rule2_text06 = ui.TextDisplay("### 勧誘について\n"
                                  "クラン勧誘行為は、WNH公認クランリクルーターのみに許可されています。")
    rule2_text07 = ui.TextDisplay("### 荒らし、スパム\n"
                                  "荒らしやスパム行為を行わないでください。")
    rule2_text08 = ui.TextDisplay("### 不適切なコンテンツ\n"
                                  "「NSFW (Not Safe For Work、職場では不適切)」だと見なされたり、攻撃的や不快なコンテンツは許可されません。これには、性的なコンテンツや暴力、不適切なシンボル、画像、ユーザー名、罵りの言葉などが含まれますが、これらに限定されません。")
    rule2_text09 = ui.TextDisplay("### Modに関する質問\n"
                                  "次の質問を質問エリアで行う場合に限り許可されています。\n"
                                  "* Modの機能\n"
                                  "* Modパック（Aslain's ModPack、ModStation）の導入方法\n"
                                  "* 上記パックで導入したModに関する質問")
    rule2_text10 = ui.TextDisplay("### モデレーション\n"
                                  "モデレーターは規則に基づいてモデレーションを行います。モデレーションについてサーバー上で議論、批判しないでください。モデレーションに対する不服申し立ては、DMに送られるリンクからのみ可能です。")
    rule2_text11 = ui.TextDisplay("### WHNサーバー規則\n"
                                  "**本サーバーのご利用にあたっては[WHNサーバー規則](https://drive.google.com/file/d/14bH4MutYTQC5Qe-oY_fU4rdIqdKxjyly/view)への同意が必要です。**")
    container_rule2 = ui.Container(rule2_title, rule2_text01, rule2_text02, rule2_text03,
                                   rule2_text04, rule2_text05, rule2_text06, rule2_text07,
                                   rule2_text08, rule2_text09, rule2_text10, rule2_text11)

    action_row = ui.ActionRow()

    @action_row.button(label="上記の内容を確認し、同意します", emoji="✅", style=discord.ButtonStyle.green,  # noqa
                       custom_id="rule_button")  # noqa
    async def rule_agree(self, interaction: discord.Interaction, button: ui.Button):
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
            user_info_result = await search_user(interaction.user.id)
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
                wg_api_result = await wows_user_info(account_id, region)
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


class NoRoleMessageView(ui.LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    text = ui.TextDisplay("## サーバー利用手続きについて\n"
                          "このチャンネルが表示されている方は、何らかの理由により必要なロールが付与されていない状態です。\n"
                          "下のボタンを押すと、ロールが付与されますので、画面の指示に従って手続きを進めてください。")
    container = ui.Container(text)

    action_row = ui.ActionRow()

    @action_row.button(label="必要なロールを取得する", style=discord.ButtonStyle.green, custom_id="no_role_button")  # noqa
    async def no_role(self, interaction: discord.Interaction, button: ui.Button):
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
    bot.add_view(view=RuleMessageView())
    bot.add_view(view=NoRoleMessageView())
