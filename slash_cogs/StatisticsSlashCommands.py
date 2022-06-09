import discord
from discord.ext import commands as ext_commands
from discord.commands import slash_command, SlashCommandGroup, Option
import commands
import common
from typing import TYPE_CHECKING
# import Race
# from data_tracking import DataTracker


if TYPE_CHECKING:
    from BadWolfBot import BadWolfBot

EMPTY_CHAR = "\u200b"
GUILDS = common.SLASH_GUILDS

ALL_TRACK_LOOKUPS = []
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
    def __init__(self, bot: 'BadWolfBot'):
        self.bot = bot
    
    @slash_command(
        name='populartracks',
        description="Display the most popular/played tracks",
        guild_ids=GUILDS
    )
    async def _popular_tracks(
        self,
        ctx: discord.ApplicationContext,
        type: Option(str, "RT/CT", choices=['RT', 'CT']),
        days: Option(int,"Timeframe of data to show in days",min_value=1,default=None),
        tier: Option(str, "Specify a tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, type.lower()]

        if tier is not None:
            args.append(tier)
        if days is not None:
            args.append(str(days))
        
        await commands.StatisticCommands.popular_tracks_command(message, args, server_prefix, is_top_tracks=True)
    
    @slash_command(
        name='unpopulartracks',
        description="Display the least popular/played tracks",
        guild_ids=GUILDS
    )
    async def _unpopular_tracks(
        self,
        ctx: discord.ApplicationContext,
        type: Option(str, "RT/CT", choices=['RT', 'CT']),
        days: Option(int,"Timeframe of data to show in days",min_value=1,default=None),
        tier: Option(str, "Specify a tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, type.lower()]

        if tier is not None:
            args.append(tier)
        if days is not None:
            args.append(str(days))

        await commands.StatisticCommands.popular_tracks_command(message, args, server_prefix, is_top_tracks=False)
    
    @slash_command(
        name='topplayers',
        description="Display the top players of a particular track",
        guild_ids=GUILDS
    )
    async def _top_players(
        self,
        ctx: discord.ApplicationContext,
        track: Option(str, "Track name or abbreviation"),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        days: Option(int,"Timeframe of data in days",min_value=1,default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, track]

        if tier is not None:
            args.append(tier.lower())
        if days is not None:
            args.append(str(days)+"d")
        if min_plays is not None:
            args.append("min="+str(min_plays))

        message.content = ' '.join(args).lower()
        await commands.StatisticCommands.top_players_command(message, args, server_prefix)
    
    @slash_command(
        name="besttracks",
        description="Show a player's best tracks",
        guild_ids=GUILDS
    )
    async def _best_tracks(
        self,
        ctx: discord.ApplicationContext,
        type: Option(str, "RT/CT", choices=['RT','CT']),
        player: Option(str,"See another player's best tracks",required=False,default=None),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        days: Option(int,"Timeframe of data in days",min_value=1,default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, type.lower()]

        if player is not None:
            args.append(player)
        if tier is not None:
            args.append(tier.lower())
        if days is not None:
            args.append(str(days)+"d")
        if min_plays is not None:
            args.append("min="+str(min_plays))

        message.content = ' '.join(args).lower()
        await commands.StatisticCommands.player_tracks_command(message, args, server_prefix, sort_asc=False)

    @slash_command(
        name="worsttracks",
        description="Show a player's worst tracks",
        guild_ids=GUILDS
    )
    async def _worst_tracks(
        self,
        ctx: discord.ApplicationContext,
        type: Option(str, "RT/CT", choices=['RT','CT']),
        player: Option(str,"See another player's worst tracks",required=False,default=None),
        tier: Option(str, "Tier", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'], required=False, default=None),
        days: Option(int,"Timeframe of data in days",min_value=1,default=None),
        min_plays: Option(int, "Minimum number of plays for a player to be included", required=False, default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, type.lower()]

        if player is not None:
            args.append(player)
        if tier is not None:
            args.append(tier.lower())
        if days is not None:
            args.append(str(days)+"d")
        if min_plays is not None:
            args.append("min="+str(min_plays))

        message.content = ' '.join(args).lower()
        await commands.StatisticCommands.player_tracks_command(message, args, server_prefix, sort_asc=True)
    
    @slash_command(
        name='record',
        description="Show your head-to-head record against another Lounge player",
        guild_ids=GUILDS
    )
    async def _record(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player to compare against (Lounge name)"),
        days: Option(int,"Timeframe (in days) to include data for",min_value=1,default=None)
    ):
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player]

        if days is not None:
            args.append(str(days)+'d')

        await commands.StatisticCommands.record_command(message, args, server_prefix)
    

def setup(bot):
    bot.add_cog(StatisticsSlash(bot))