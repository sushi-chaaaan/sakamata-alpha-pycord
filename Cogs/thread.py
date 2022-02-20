import os
from datetime import timedelta, timezone

from discord import ApplicationContext

import discord
from discord import Option
from discord.commands import permissions, slash_command
from discord.ext import commands
from discord.ext.ui import (
    InteractionProvider,
    Message,
    PageView,
    PaginationView,
    View,
    ViewTracker,
)

thread_log_channel = int(os.environ["THREAD_LOG_CHANNEL"])
jst = timezone(timedelta(hours=9), "Asia/Tokyo")
mod_role = int(os.environ["MOD_ROLE"])
admin_role = int(os.environ["ADMIN_ROLE"])
guild_id = int(os.environ["GUILD_ID"])


class Thread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name="on_thread_join")
    async def detect_thread(self, thread):
        thread_member_list = await thread.fetch_members()
        if self.bot.user.id in [x.id for x in thread_member_list]:
            return
        else:
            channel = self.bot.get_channel(thread_log_channel)
            embed = await self.compose_thread_create_log(thread)
            await channel.send(embed=embed)
            return

    @commands.Cog.listener(name="on_thread_update")
    async def detect_archive(self, before, after):
        if after.locked and not before.locked:
            return
        elif after.archived and not before.archived:
            await after.edit(archived=False)
            return
        else:
            return

    """
    Thread Board Parts
    normal
    ┣

    bottom
    ┗
    """

    @slash_command(guild_ids=[guild_id], name="board")
    @permissions.has_role(admin_role)
    async def _board_slash(
        self,
        ctx: ApplicationContext,
        category: Option(discord.CategoryChannel, "対象のカテゴリを選択してください。"),
    ):
        board = self._make_board(ctx.interaction, category.id)
        # print(board)
        # await ctx.respond('Done', ephemeral=True)
        # view = EscapeButton(board)
        # tracker = ViewTracker(view, timeout=None)
        # await tracker.track(InteractionProvider(ctx.interaction))
        await PagePage(text=board)._send(ctx.interaction)
        return

    @commands.command(name="thread_board")
    @commands.has_role(admin_role)
    async def _thread(self, ctx):
        text = self._make_board(ctx, ctx.message.channel.category.id)
        await ctx.send(text)
        return

    def _make_board(self, ctx, category_id: int) -> str:
        channels = [
            channel
            for channel in ctx.guild.channels
            if channel.category and channel.category.id == category_id
        ]
        sort_channels = sorted(channels, key=lambda channel: channel.position)
        # print(channels)
        thread_dic = {}
        threads = [
            thread
            for thread in ctx.guild.threads
            if not thread.is_private()
            and not thread.locked
            and thread.parent.category.id == category_id
        ]
        # print(threads)
        for thread in threads:
            thread_dic[thread] = thread.parent.position
        """
        thread_dic:
        {thread,
        thread:pos,
        ...}
        """
        final_board = []
        for channel in sort_channels:
            thread_board = [f"<#{channel.id}>"]
            child_thread = sorted(
                [
                    thread
                    for thread, parent in thread_dic.items()
                    if parent == channel.position
                ],
                key=lambda thread: len(thread.name),
            )
            # print(child_thread)
            mark_child_thread = [f"<#{thread.id}>" for thread in child_thread]
            if mark_child_thread:
                board = thread_board + mark_child_thread
                board_text_draft = "\n┣".join(board[:-1])
                board_text = f"{board_text_draft}\n┗{board[-1]}"
                final_board.append(board_text)
            else:
                final_board.append(f"<#{channel.id}>")
        final_text = "\n\n".join(final_board)
        return final_text

    async def compose_thread_create_log(self, thread):
        embed = discord.Embed(
            title="スレッドが作成されました。",
            url="",
            color=3447003,
            description="",
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=thread.owner.display_name,
            icon_url=thread.owner.display_avatar.url,
        )
        embed.add_field(name="作成元チャンネル", value=f"{thread.parent.mention}")
        embed.add_field(name="作成スレッド", value=f"{thread.mention}")
        embed.add_field(name="作成者", value=f"{thread.owner.mention}")
        embed.add_field(
            name="作成日時",
            value=f"{discord.utils.utcnow().astimezone(jst):%Y/%m/%d %H:%M:%S}",
        )
        return embed


class Page(PageView):
    def __init__(self, text: str):
        super(Page, self).__init__()
        self.text = text

    async def body(self, _paginator: PaginationView) -> Message | View:
        return Message(content=self.text)

    async def on_appear(self, paginator: PaginationView) -> None:
        # print(f"appeared page: {paginator.page}")
        pass


class PagePage:
    def __init__(self, text: str) -> None:
        self._text = text
        pass

    def _view(self) -> PaginationView:
        view = PaginationView(
            [
                Page(self._text),
                Page(f"```{self._text}```"),
            ],
            show_indicator=False,
        )
        return view

    async def _send(self, interaction: discord.Interaction):
        view = self._view()
        tracker = ViewTracker(view, timeout=None)
        await tracker.track(InteractionProvider(interaction, ephemeral=True))


def setup(bot):
    return bot.add_cog(Thread(bot))
