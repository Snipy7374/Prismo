from __future__ import annotations

from disnake import Event
from disnake.ext import commands

from bot import PrismoBot

class GitHub(commands.Cog):
    def __init__(self, bot: PrismoBot) -> None:
        self.bot = bot
    
    @commands.command()
    async def repo(self, ctx: commands.Context[PrismoBot], owner: str, name: str):
        await ctx.send(repr(await ctx.bot.github_client.fetch_repository(owner, name)))

    @commands.Cog.listener(Event.message)
    async def handle_issues_or_prs_mentions(self, ctx: commands.Context[PrismoBot]):
        pass


def setup(bot: PrismoBot):
    bot.add_cog(GitHub(bot))