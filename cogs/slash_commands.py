#External
import discord
from discord.ext import commands as ext_commands
from discord.commands import slash_command
from discord.commands import Option

#Internal Imports
import ServerFunctions
import Stats
import LoungeAPIFunctions
import UserDataProcessing
import TableBot
import UtilityFunctions
import Race 
import help_documentation
import commands
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

class Slash(ext_commands.Cog):
    '''
    Cog that holds all slash commands; only exists for organizational purposes.
    '''
    def __init__(self, bot):
        self.bot = bot

    # @ext_commands.Cog.listener()
    # async def on_application_command_error(ctx, error):
    #     pass
    #TODO: implement

    @slash_command(name='startwar',
    description= 'Load a room and start tabling a war.',
    guild_ids=guilds)
    async def _start_war(
        self,
        ctx,
        war_format: Option(str, "format", choices=['FFA', '2v2', '3v3', '4v4', '5v5', '6v6']),
        num_teams: Option(int, 'number of teams (defaults to correct teams for 12 players)', required=False, default=None),
        room_arg: Option(str, 'LoungeName/LoungeMention/rxx/FC', required=False, default=None),
        gps: Option(int, 'number of GPs', required=False, default=None),
        psb: Option(bool, 'suppress large finish time warnings', required=False, default=None),
        miis: Option(bool, 'show miis on table', required=False, default=None)
    ):
        await on_interaction_check(ctx.interaction)

        if num_teams is None:
            num_teams = UtilityFunctions.get_max_teams(war_format)

        args = ['/'+ctx.interaction.data['name'], war_format, str(num_teams)]
        
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

        message = create_proxy_msg(ctx.interaction)
        
        is_lounge_server = message.guild.id == common.MKW_LOUNGE_SERVER_ID
        server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
        this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)
        command = message.content

        await ctx.respond('\u200b')
        # await ctx.defer()
        await commands.TablingCommands.start_war_command(message, this_bot, args, server_prefix, is_lounge_server, command, common.author_is_table_bot_support_plus)
        
    
    @slash_command(name='warpicture',
    description='Display a table picture of the room.',
    guild_ids=guilds)
    async def _war_picture(
        self,
        ctx,
        max_race: Option(str, "Maximum race to display in picture", required=False, default=None),
        byrace: Option(bool, 'Show each race in picture', required=False, default=False),
        gsc: Option(bool, 'Show GSC table', required=False, default=False),
        use_lounge_names: Option(bool, "Show lounge names on table", required=False, default=None),
        use_mii_names: Option(bool, "Show mii names on table", required=False, default=None)
    ):
        await on_interaction_check(ctx.interaction)
        args = ['/'+ctx.interaction.data['name']]

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

        message = create_proxy_msg(ctx.interaction)

        is_lounge_server = message.guild.id == common.MKW_LOUNGE_SERVER_ID
        server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
        this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)

        await ctx.respond('\u200b') 
        # await ctx.defer()
        await commands.TablingCommands.war_picture_command(message, this_bot, args, server_prefix, is_lounge_server)

    @slash_command(name='reset',
    description='Reset the table in this channel.',
    guild_ids=guilds)
    async def _reset_table(
        self,
        ctx
    ):
        await on_interaction_check(ctx.interaction)

        message = create_proxy_msg(ctx.interaction)
        await ctx.respond('\u200b')
        # await ctx.defer()
        await commands.TablingCommands.reset_command(message, BWB.table_bots)
    

def build_msg_content(data, args = None):
    if args: return '/' + ' '.join(args)

    args = [data.get('name', '')]
    raw_args = data.get('options', [])
    for arg in raw_args: 
        args.append(str(arg.get('value', '')))
    return '/' + ' '.join(args)

def create_proxy_msg(interaction, args=None):
    proxyMsg = discord.Object(id=interaction.id)
    proxyMsg.channel = interaction.channel
    proxyMsg.guild = interaction.guild
    proxyMsg.content = build_msg_content(interaction.data, args)
    proxyMsg.author = interaction.user
    proxyMsg.raw_mentions = []
    for i in proxyMsg.content:
        if i.startswith('<@') and i.endswith('>'):
            proxyMsg.raw_mentions.append(i)
    
    return proxyMsg


async def on_interaction_check(interaction):
    if interaction.type != discord.InteractionType.application_command:
        return

    message = create_proxy_msg(interaction)

    is_lounge_server = message.guild.id == common.MKW_LOUNGE_SERVER_ID

    await AbuseTracking.blacklisted_user_check(message)
    await AbuseTracking.abuse_track_check(message)
                
    BWB.log_command_sent(message)
    
    this_bot:TableBot.ChannelBot = BWB.check_create_channel_bot(message)
    this_bot.updatedLastUsed()
    if is_lounge_server and this_bot.isFinishedLounge():
        this_bot.freeLock()
    
    if not BWB.commandIsAllowed(is_lounge_server, message.author, this_bot, interaction.data.get('name')):
        await BWB.send_lounge_locked_message(message, this_bot)


def setup(bot):
    bot.add_cog(Slash(bot))
