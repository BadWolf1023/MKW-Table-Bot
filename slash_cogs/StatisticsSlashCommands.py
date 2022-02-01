import discord
from discord import permissions
from discord.ext import commands as ext_commands
from discord.commands import slash_command, SlashCommandGroup, CommandPermission, Option
import commands
import common
import Race
# from data_tracking import DataTracker

EMPTY_CHAR = "\u200b"
GUILDS = common.SLASH_GUILDS

ALL_TRACK_LOOKUPS = ['LC']
# for track_name, value in Race.track_name_abbreviation_mappings.items():
#     try:
#         if isinstance(value, tuple):
#             abbrevs = value[0]
#             if isinstance(abbrevs, str):
#                 abbrevs = [abbrevs]
#         else:
#             abbrevs = [value]
#         # abbrevs = [x.lower() for x in abbrevs]
#         ALL_TRACK_LOOKUPS.extend(abbrevs)
#         ALL_TRACK_LOOKUPS.append(track_name)
#     except:
#         pass

async def get_all_tracks(ctx: discord.AutocompleteContext):   
    return [lookup for lookup in ALL_TRACK_LOOKUPS if ctx.value.lower() in lookup.lower()]

class StatisticsSlash(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @slash_command(
        name='popular_tracks',
        description="Show a list of the most popular/most played tracks",
        guild_ids=GUILDS
    )
    async def _popular_tracks(
        self,
        ctx: discord.ApplicationContext,
        category: Option(str, "RT/CT", choices=['RT', 'CT']),
        timeframe: Option(int, "Timeframe of data to show in days.", required=False, default=None),
        tier: Option(str, "Specify a tier.", choices=['FFA', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, category.lower()]

        if timeframe is not None:
            args.append(timeframe)
        if tier is not None:
            args.append(tier)
        
        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.popular_tracks_command(self.bot, message, args, server_prefix, message.content)
    
    @slash_command(
        name='unpopular_tracks',
        description="Show a list of the least popular/lease played tracks",
        guild_ids=GUILDS
    )
    async def _unpopular_tracks(
        self,
        ctx: discord.ApplicationContext,
        category: Option(str, "RT/CT", choices=['RT', 'CT']),
        timeframe: Option(str, "Timeframe to show *in days* (ex. \"5d\" or \"5\")", required=False, default=None),
        tier: Option(str, "Specify a tier.", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, category.lower()]

        if timeframe is not None:
            args.append(timeframe)
        if tier is not None:
            args.append(tier)
        
        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.popular_tracks_command(self.bot, message, args, server_prefix, message.content, is_top_tracks=False)
    
    @slash_command(
        name='best_players',
        description="Show the best players of a particular track",
        guild_ids=GUILDS
    )
    async def _best_players(
        self,
        ctx: discord.ApplicationContext,
        track: Option(str, "Track"),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        timeframe: Option(int, "Timeframe of data in days.", required=False, default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included.", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, track]

        if tier is not None:
            args.append(tier.lower())
        if timeframe is not None:
            args.append(str(timeframe))
        if min_plays is not None:
            args.append("min="+str(min_plays))

        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.top_players_command(self.bot, message, args, server_prefix, message.content)
    
    @slash_command(
        name="best_tracks",
        description="Show a player's best tracks",
        guild_ids=GUILDS
    )
    async def _best_tracks(
        self,
        ctx: discord.ApplicationContext,
        category: Option(str, "RT/CT", choices=['RT/CT']),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        timeframe: Option(int, "Timeframe of data in days.", required=False, default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included.", required=False, default=None),
        player: Option(str, "See another player's best tracks.", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, category.lower()]

        if player is not None:
            args.append(player)
        if tier is not None:
            args.append(tier.lower())
        if timeframe is not None:
            args.append(str(timeframe))
        if min_plays is not None:
            args.append("min="+str(min_plays))
        
        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.player_tracks_command(self.bot, message, args, server_prefix, message.content)

    @slash_command(
        name="worst_tracks",
        description="Show a player's worst tracks",
        guild_ids=GUILDS
    )
    async def _worst_tracks(
        self,
        ctx: discord.ApplicationContext,
        category: Option(str, "RT/CT", choices=['RT/CT']),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        timeframe: Option(int, "Timeframe of data in days.", required=False, default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included.", required=False, default=None),
        player: Option(str, "See another player's worst tracks.", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, category.lower()]

        if player is not None:
            args.append(player)
        if tier is not None:
            args.append(tier.lower())
        if timeframe is not None:
            args.append(str(timeframe))
        if min_plays is not None:
            args.append("min="+str(min_plays))
        
        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.player_tracks_command(self.bot, message, args, server_prefix, message.content, sort_asc=True)
    
    @slash_command(
        name='record',
        description="Show your head-to-head record against another Lounge player",
        guild_ids=GUILDS
    )
    async def _record(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player to compare against (Lounge name)"),
        timeframe: Option(int, "Timeframe (in days) to include data for", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, player]

        if timeframe is not None:
            args.append(str(timeframe))

        await ctx.respond(EMPTY_CHAR)
        await commands.StatisticCommands.record_command(self, message, args, server_prefix, message.content)
    

def setup(bot):
    bot.add_cog(StatisticsSlash(bot))