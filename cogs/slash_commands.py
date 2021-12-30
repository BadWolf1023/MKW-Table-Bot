#External
import discord
from discord.embeds import EmptyEmbed
from discord.ext import commands as ext_commands
from discord.commands import slash_command
from discord.commands import Option
from discord.utils import get

#Internal Imports
import InteractionUtils
import TableBot
import UtilityFunctions
import Race 
import help_documentation
import commands
import ServerFunctions
import Lounge
import TableBotExceptions
import common
import MogiUpdate
import URLShortener
import AbuseTracking
import WiimmfiSiteFunctions
import TagAIShell
from data_tracking import DataTracker
import BadWolfBot as BWB

guilds = [775253594848886785]
EMPTY_CHAR = '\u200b'

def get_help_categories(ctx: discord.AutocompleteContext):
    return [category for category in help_documentation.HELP_CATEGORIES if category.startswith(ctx.value.lower())]

class Slash(ext_commands.Cog):
    '''
    Cog that holds all slash commands; only exists for organizational purposes.
    '''
    def __init__(self, bot):
        self.bot = bot

    # @ext_commands.Cog.listener()
    # async def on_application_command_error(ctx, error):
    #     pas
    #TODO: implement

    @slash_command(name='sw',
    description= 'Load a room and start tabling a war',
    guild_ids=guilds)
    async def _start_war(
        self,
        ctx: discord.ApplicationContext,
        war_format: Option(str, "Format", choices=['FFA', '2v2', '3v3', '4v4', '5v5', '6v6']),
        num_teams: Option(int, 'Number of teams (defaults to correct teams for 12 players)', required=False, default=None),
        room_arg: Option(str, 'LoungeName/LoungeMention/rxx/FC', required=False, default=None),
        gps: Option(int, 'Number of GPs', required=False, default=None),
        psb: Option(bool, 'Suppress large finish time warnings', required=False, default=None),
        miis: Option(bool, 'Show miis on table', required=False, default=None)
    ):
        await on_interaction_check(ctx.interaction)

        if num_teams is None:
            num_teams = UtilityFunctions.get_max_teams(war_format)

        args = [ctx.interaction.data['name'], war_format, str(num_teams)]
        
        bool_map = {True: 'yes', False: 'no'}
        if room_arg:
            args.append(room_arg)
        if gps:
            gps = 'gps='+str(gps)
            args.append(gps)
        if psb is not None:
            psb = 'psb='+bool_map[psb]
            args.append(psb)
        if miis is not None:
            miis = 'miis='+bool_map[miis]
            args.append(miis)

        message = InteractionUtils.create_proxy_msg(ctx.interaction)
        
        is_lounge_server = message.guild.id == common.MKW_LOUNGE_SERVER_ID
        # server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
        server_prefix = '/'
        this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)
        command = message.content

        await ctx.respond(EMPTY_CHAR)
        # await ctx.defer()
        await commands.TablingCommands.start_war_command(message, this_bot, args, server_prefix, is_lounge_server, command, common.author_is_table_bot_support_plus)
        
    
    @slash_command(name='wp',
    description='Display a table picture of the room',
    guild_ids=guilds)
    async def _war_picture(
        self,
        ctx: discord.ApplicationContext,
        max_race: Option(str, "Maximum race to display in picture", required=False, default=None),
        byrace: Option(bool, 'Show each race in picture', required=False, default=False),
        gsc: Option(bool, 'Show GSC table', required=False, default=False),
        use_lounge_names: Option(bool, "Show lounge names on table", required=False, default=None),
        use_mii_names: Option(bool, "Show mii names on table", required=False, default=None)
    ):
        await on_interaction_check(ctx.interaction)
        args = [ctx.interaction.data['name']]

        bool_map = {True: 'yes', False: 'no'}

        if gsc:
            args.append('gsc')
        if byrace:
            args.append('byrace')
        if max_race:
            args.append('maxrace='+max_race)
        if use_lounge_names is not None:
            args.append('uselounge='+bool_map[use_lounge_names])
        if use_mii_names is not None:
            args.append('usemii='+bool_map[use_mii_names])

        message = InteractionUtils.create_proxy_msg(ctx.interaction)

        is_lounge_server = message.guild.id == common.MKW_LOUNGE_SERVER_ID
        # server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
        server_prefix = '/'
        this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)

        await ctx.respond(EMPTY_CHAR) 
        # await ctx.defer()
        await commands.TablingCommands.war_picture_command(message, this_bot, args, server_prefix, is_lounge_server)
    
    @slash_command(name='dc', 
    description="Confirm a player's DC status for a race",
    guilds_ids=guilds)
    async def _dc_config(
        self,
        ctx: discord.ApplicationContext,
        dc_number: Option(int, 'DC number of player who DCed (check /dcs)'),
        status: Option(str, 'DC status', choices=['during', 'before']) #TODO: add lounge_name and race parameters so don't have to lookup /dcs
    ):
        await on_interaction_check(ctx.interaction)

        args = [ctx.interaction.data['name'], str(dc_number), status]

        message = InteractionUtils.create_proxy_msg(ctx.interaction)

        is_lounge_server = check_lounge_server(message)
        server_prefix = "/"
        this_bot = BWB.check_create_channel_bot(message)

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.disconnections_command(message, this_bot, args, server_prefix, is_lounge_server)

    @slash_command(name='edit',
    description="Edit a player's GP score",
    guild_ids=guilds)
    async def _edit_score(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, 'Player (playerNumber or LoungeName)'),
        gp: Option(str, "GP to edit"),
        score: Option(int, "New score")
    ):
        await on_interaction_check(ctx.interaction)
        args = [ctx.interaction.data['name'], player, gp, score]

        message = InteractionUtils.create_proxy_msg(ctx.interaction)
        
        this_bot = BWB.check_create_channel_bot(message)
        server_prefix = '/'

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.change_player_score_command(message, this_bot, args, server_prefix, check_lounge_server(message))
    
    @slash_command(name='change_position',
    description="Change a race's positions",
    guild_ids=guilds)
    async def _change_position(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to change positions for"),
        player: Option(str, "Player to change positions for (playerNumber or LoungeName)"),
        position: Option(int, "New position for player")
    ):
        await on_interaction_check(ctx.interaction)
        args = [ctx.interaction.data['name'], str(race), player, str(position)]

        message = InteractionUtils.create_proxy_msg(ctx.interaction)
        this_bot = BWB.check_create_channel_bot(message)
        server_prefix = '/'

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.quick_edit_command(message, this_bot, args, server_prefix, check_lounge_server(message))


    @slash_command(name='pen',
    description="Give a penalty or a reward to a player",
    guild_ids=guilds)
    async def _penalty(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, 'Player to give a penalty/reward to'),
        amount: Option(int, "Penalty: positive number; Reward: negative number")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, player, str(amount)]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.player_penalty_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name='change_room_size',
    description="Change the number of players in a race",
    guild_ids=guilds)
    async def _change_room_size(
        self, 
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to change room size"),
        room_size: Option(int, "Corrected room size")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, str(race), str(room_size)]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.change_room_size_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name="merge_room",
    description="Add another room to the table",
    guild_ids=guilds)
    async def _merge_room(
        self,
        ctx: discord.ApplicationContext,
        room_arg: Option(str, "rxx of room or LoungeName in room")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, room_arg]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.merge_room_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name="remove_race",
    description="Remove a race from the table",
    guild_ids=guilds)
    async def _remove_race(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to remove from table")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, str(race)]
        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.remove_race_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name="change_name", 
    description="Change a player's name",
    guild_ids=guilds)
    async def _change_name(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "playerNumber or LoungeName"),
        name: Option(str, "New name (put a # at the beginning to remove the player from table)")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, player, name]
        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.change_player_name_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name="change_tag",
    description="Change a player's tag",
    guild_ids=guilds)
    async def _change_tag(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "playerNumber or LoungeName"),
        tag: Option(str, "Corrected tag")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, player, tag]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.change_player_tag_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name="early_dc",
    description="Fix player incorrectly missing from race 1 of GP",
    guild_ids=guilds)
    async def _early_dc(
        self,
        ctx: discord.ApplicationContext,
        gp: Option(int, "GP where early DC occurred"),
        status: Option(str, "DC status", choices=['during', 'before'], required=False, default="during")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, str(gp), status]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.early_dc_command(message, this_bot, args, server_prefix, is_lounge)
    
    @slash_command(name='sub',
    description="Sub a player in for another",
    guild_ids=guilds)
    async def _substitute(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race when sub occurred"),
        sub_in: Option(str, "Player subbing in (playerNumber or LoungeName)"),
        sub_out: Option(str, "Player subbing out (playerNumber or LoungeName)")
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command, str(race), sub_in, sub_out]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.substitue_player_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name='rxx',
    description="Get the rxx and Wiimmfi link of room",
    guild_ids=guilds)
    async def _rxx(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.rxx_command(message, this_bot, server_prefix, is_lounge)

    @slash_command(name='ap',
    description="Show a list of all players who have been in the room",
    guild_ids=guilds)
    async def _all_players(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.all_players_command(message, this_bot, server_prefix, is_lounge)

    @slash_command(name='dcs',
    description="Show a list of all DCs that have occurred",
    guild_ids=guilds)
    async def _get_dcs(
        self, 
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command]

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.disconnections_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name='races',
    description="Display a list of all races that have been played",
    guild_ids=guilds)
    async def _get_races(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.display_races_played_command(message, this_bot, server_prefix, is_lounge)

    @slash_command(name="rr",
    description="Display a race's results",
    guild_ids = guilds)
    async def _race_results(
        self,
        ctx: discord.ApplicationContext,
        race: Option(int, "Race to display results of", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command]
        if race: args.append(str(race))

        await ctx.respond(EMPTY_CHAR)
        await commands.TablingCommands.race_results_command(message, this_bot, args, server_prefix, is_lounge)

    @slash_command(name='reset',
    description='Reset the table in this channel',
    guild_ids=guilds)
    async def _reset_table(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)

        await ctx.respond(EMPTY_CHAR)
        # await ctx.defer()
        await commands.TablingCommands.reset_command(message, BWB.table_bots)
    
    @slash_command(name="vr",
    description="Show details of a room",
    guild_ids=guilds)
    async def _vr(
        self,
        ctx: discord.ApplicationContext,
        players: Option(str, "Player(s) in the room", default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        args = [command]
        if players: args.append(players)

        await ctx.respond(EMPTY_CHAR)
        await commands.OtherCommands.vr_command(this_bot, message, args, message, BWB.createEmptyTableBot())
    
    @slash_command(name='ww',
    description="Show all active RT worldwide rooms",
    guild_ids=guilds)
    async def _ww(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        
        await ctx.respond(EMPTY_CHAR)
        await commands.OtherCommands.wws_command(None, this_bot, message) #can refactor wws_command to get rid of `client` argument (no longer needed)
    
    @slash_command(name='ctww',
    description="Show all active CT worldwide rooms",
    guild_ids=guilds)
    async def _ctww(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)

        await ctx.respond(EMPTY_CHAR)
        await commands.OtherCommands.wws_command(None, this_bot, message, ww_type=Race.CTGP_CTWW_REGION) #can refactor wws_command to get rid of `client` argument (no longer needed)
    
    @slash_command(name='help',
    description="Need help with Table Bot?",
    guild_ids=guilds)
    async def _help(
        self, 
        ctx: discord.ApplicationContext,
        category: Option(str, "The category you need help with", required=False, default=None, autocomplete=discord.utils.basic_autocomplete(get_help_categories))
    ):
        command, message, this_bot, server_prefix, is_lounge = await on_interaction_check(ctx.interaction)
        # server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
        args = [command]
        if category: args.append(category)

        await ctx.respond(EMPTY_CHAR)
        await help_documentation.send_help(message, is_lounge, args, server_prefix)



def check_lounge_server(message):
    return message.guild.id == common.MKW_LOUNGE_SERVER_ID

async def on_interaction_check(interaction):
    if interaction.type != discord.InteractionType.application_command:
        return

    message = InteractionUtils.create_proxy_msg(interaction)

    is_lounge_server = check_lounge_server(message)

    await AbuseTracking.blacklisted_user_check(message)
    await AbuseTracking.abuse_track_check(message)
                
    BWB.log_command_sent(message)
    
    this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)
    this_bot.updatedLastUsed()
    if is_lounge_server and this_bot.isFinishedLounge():
        this_bot.freeLock()
    
    if not BWB.commandIsAllowed(is_lounge_server, message.author, this_bot, interaction.data.get('name')):
        await BWB.send_lounge_locked_message(message, this_bot)

    return interaction.data['name'], message, this_bot, '/', is_lounge_server 

def setup(bot):
    bot.add_cog(Slash(bot))
