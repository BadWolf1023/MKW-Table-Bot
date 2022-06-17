#External
import discord
from discord.ext import commands as ext_commands
from discord.commands import slash_command, Option
# from discord import option
from typing import TYPE_CHECKING

#Internal Imports
import UtilityFunctions
import commands
import common
import TimerDebuggers

if TYPE_CHECKING:
    from BadWolfBot import BadWolfBot

EMPTY_CHAR = '\u200b'

class Table_Slash(ext_commands.Cog):
    '''
    Cog that holds all slash commands; only exists for organizational purposes.
    '''
    def __init__(self, bot: 'BadWolfBot'):
        self.bot = bot

    @slash_command(name='sw',
    description= 'Start a table',
    guild_ids=common.SLASH_GUILDS)
    @TimerDebuggers.timer_coroutine
    async def _start_war(
        self,
        ctx: discord.ApplicationContext,
        format: Option(str, "Format", choices=['FFA', '2v2', '3v3', '4v4', '5v5', '6v6']),
        num_teams: Option(int, 'Number of teams'),
        room_arg: Option(str, 'Lounge Name/Mention/rxx/FC', required=False, default=None),
        gps: Option(int, "Number of GPs", min_value=1, max_value=15, default=None),
        psb: Option(str, 'Suppress large finish time warnings', required=False, default=None, choices=['yes', 'no']),
        miis: Option(str, 'Show miis on table', required=False, default=None, choices=['on', 'off'])
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        # if num_teams is None:
        #     num_teams = UtilityFunctions.get_max_teams(war_format)

        args = [command, format, str(num_teams)]

        if room_arg:
            args.append(room_arg)
        if gps:
            gps = 'gps='+str(gps)
            args.append(gps)
        if psb is not None:
            psb = 'psb='+psb
            args.append(psb)
        if miis is not None:
            miis = 'miis='+miis
            args.append(miis)
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
        
    
    @slash_command(name='wp',
    description='Display a table picture of the room',
    guild_ids=common.SLASH_GUILDS)
    async def _war_picture(
        self,
        ctx: discord.ApplicationContext,
        max_race: Option(str, "Maximum race to display in picture", required=False, default=None),
        byrace: Option(bool, 'Show each race in picture', required=False, default=False),
        gsc: Option(bool, 'Show GSC table', required=False, default=False),
        show_lounge_names: Option(bool,"Show lounge names on table",required=False,default=None),
        show_mii_names: Option(bool,"Show mii names on table",required=False,default=None)
    ):
        args = []

        bool_map = {True: 'yes', False: 'no'}

        if gsc:
            args.append('gsc')
        if byrace:
            args.append('byrace')
        if max_race:
            args.append('maxrace='+max_race)
        if show_lounge_names is not None:
            args.append('uselounge=' + bool_map[show_lounge_names])
        if show_mii_names is not None:
            args.append('usemii=' + bool_map[show_mii_names])
        
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx, args=args)
        args.insert(0, command)

        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name='dc',
    description="Confirm a player's DC status for a race",
    guilds_ids=common.SLASH_GUILDS)
    async def _dc_config(
        self,
        ctx: discord.ApplicationContext,
        dc_number: Option(int, 'Number of player who DCed (check /dcs)'),
        status: Option(str, 'Was the player on results?', choices=['on', 'before']) #TODO: add lounge_name and race parameters so don't have to lookup /dcs
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        args = [command, str(dc_number), status]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='edit',
    description="Edit a player's GP score",
    guild_ids=common.SLASH_GUILDS)
    async def _edit_score(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, 'Player number (run /ap) or Lounge name'),
        gp: Option(int, "GP to edit"),
        score: Option(int, "New GP score")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player, str(gp), str(score)]

        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='gpedit',
    description="Edit all players' scores for a GP",
    guild_ids=common.SLASH_GUILDS)
    async def _edit_all_scores(
        self,
        ctx: discord.ApplicationContext,
        gp: Option(int, "GP to edit"),
        scores: Option(str, "New scores for players, in the order listed by running /ap")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(gp)] + scores.split(" ")

        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name='cp',
    description="Change a player's finish position in a race",
    guild_ids=common.SLASH_GUILDS)
    async def _change_position(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player number (run /ap) or Lounge name"),
        race: Option(int, "Race number (run /races) to change positions for"),
        position: Option(int, "New position for player")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player, str(race), str(position)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)


    @slash_command(name='pen',
    description="Give a penalty or a reward to a player",
    guild_ids=common.SLASH_GUILDS)
    async def _penalty(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, 'Player number (run /ap) or Lounge name'),
        amount: Option(int, "Penalty amount (use a negative number to award)")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player, str(amount)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(
        name="teampen",
        description="Apply a penalty or reward to a team",
        guild_ids=common.SLASH_GUILDS
    )
    async def _team_penalty(
        self,
        ctx: discord.ApplicationContext,
        team: Option(str, 'Team tag'),
        amount: Option(int, 'Penalty amount (negative number to reward)')
    ):
        command, message, this_bot, prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, team, str(amount)]

        await self.bot.process_message_commands(message, args, this_bot, prefix, is_lounge, from_slash=True)

    @slash_command(name='changeroomsize',
    description="Change the number of players in a race",
    guild_ids=common.SLASH_GUILDS)
    async def _change_room_size(
        self, 
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to change room size"),
        room_size: Option(int, "Corrected room size", min_value=1, max_value=12)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(race), str(room_size)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="mergeroom",
    description="Merge another room into the table",
    guild_ids=common.SLASH_GUILDS)
    async def _merge_room(
        self,
        ctx: discord.ApplicationContext,
        room_arg: Option(str, "Lounge name or rxx number", name="with")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, room_arg]

        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="removerace",
    description="Remove a race from the table",
    guild_ids=common.SLASH_GUILDS)
    async def _remove_race(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race number (run /races) to remove from table")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(race)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="changename",
    description="Change a player's name",
    guild_ids=common.SLASH_GUILDS)
    async def _change_name(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player number (run /ap) or Lounge name"),
        name: Option(str, "New name (put a \"#\" at the beginning to remove the player from table)")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player, name]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="changetag",
    description="Change a player's tag",
    guild_ids=common.SLASH_GUILDS)
    async def _change_tag(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player number (run /ap) or Lounge name"),
        tag: Option(str, "Corrected tag")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, player, tag]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="earlydc",
    description="Fix player incorrectly missing from race 1 of GP",
    guild_ids=common.SLASH_GUILDS)
    async def _early_dc(
        self,
        ctx: discord.ApplicationContext,
        gp: Option(int, "GP when the early DC occurred"),
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(gp)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name='sub',
    description="Sub a player in for another",
    guild_ids=common.SLASH_GUILDS)
    async def _substitute(
        self,
        ctx: discord.ApplicationContext,
        sub_in: Option(str, "Player subbing in (number or Lounge name)"),
        sub_out: Option(str, "Player subbing out (number or Lounge name)"),
        race: Option(int, "Race when sub occurred"),
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, sub_in, sub_out, str(race)]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="undo",
    description="Undo a table modification you made",
    guild_ids=common.SLASH_GUILDS)
    async def _undo(
        self,
        ctx: discord.ApplicationContext,
        undo_all: Option(bool, 'Undo every command at once', required=False, default=False)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if undo_all: args.append("all")
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="redo",
    description="Redo a table modification you undid",
    guild_ids=common.SLASH_GUILDS)
    async def _redo(
        self,
        ctx: discord.ApplicationContext,
        redo_all: Option(bool, "Redo every command at once", required=False, default=False)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if redo_all: args.append("all")
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="undos",
    description="Show which commands you can undo and in which order",
    guild_ids=common.SLASH_GUILDS)
    async def _show_undos(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="redos",
    description="Show which commands you can redo and in which order",
    guild_ids=common.SLASH_GUILDS)
    async def _show_redos(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="subs",
    description="Show the table's subs",
    guild_ids=common.SLASH_GUILDS)
    async def _show_subs(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='tt',
    description="Get the Lorenzi table text",
    guild_ids=common.SLASH_GUILDS)
    async def _table_text(
        self, 
        ctx: discord.ApplicationContext,
        max_race: Option(int, "Maximum race to display on table text", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if max_race: args.append(str(max_race))
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='rxx',
    description="Get the rxx and Wiimmfi link of room",
    guild_ids=common.SLASH_GUILDS)
    async def _rxx(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="tableid",
    description="Get the Table ID",
    guild_ids=common.SLASH_GUILDS)
    async def _table_id(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='ap',
    description="List all players who have been in the room",
    guild_ids=common.SLASH_GUILDS)
    async def _all_players(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='dcs',
    description="List all DCs that have occurred",
    guild_ids=common.SLASH_GUILDS)
    async def _get_dcs(
        self, 
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='races',
    description="List all races that have been played",
    guild_ids=common.SLASH_GUILDS)
    async def _get_races(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name="rr",
    description="Show a race's results",
    guild_ids=common.SLASH_GUILDS)
    async def _race_results(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to display results of", required=False, default=None),
        show_team_points: Option(bool, "Whether to display team points for this race as well", default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if race: args.append(str(race))
        if show_team_points: 
            args.append("teampoints=true")
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(name='reset',
    description='Reset the table in this channel',
    guild_ids=common.SLASH_GUILDS)
    async def _reset_table(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)

    @slash_command(
        name="predict",
        description="Preview MMR changes of the event",
        guild_ids=common.SLASH_GUILDS
    )
    async def _predict(
        self,
        ctx: discord.ApplicationContext,
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        await self.bot.process_message_commands(message, [command], this_bot, server_prefix, is_lounge, from_slash=True)
    
    @slash_command(name="copyfrom",
    description="Make this table a copy of another table",
    guild_ids=common.SLASH_GUILDS)
    async def _copy_from(
        self,
        ctx: discord.ApplicationContext,
        channel: Option(str, "Channel that the other table is in (the channel mention or the ID)"),
        # guild: Option(str, "Guild that the other table is in (only need this if other table is in different guild)", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, channel]
        # if guild: args.append(guild)
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge, from_slash=True)

def setup(bot):
    bot.add_cog(Table_Slash(bot))
