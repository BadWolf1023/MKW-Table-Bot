from typing import TYPE_CHECKING
import discord
from discord.ext import commands as ext_commands
from discord.commands import slash_command, SlashCommandGroup, Option
from discord import Permissions

import TableBot
import commands
import common
import help_documentation
import Race

if TYPE_CHECKING:
    from BadWolfBot import BadWolfBot

EMPTY_CHAR = "\u200b"
GUILDS = common.SLASH_GUILDS
# SETTING_PERMISSIONS = [CommandPermission("owner", 2, True)]

PLAYER_ARG_DESCRIPTION = "Lounge name, FC, Discord user (mention), or Discord ID"
class MiscSlash(ext_commands.Cog):
    def __init__(self, bot: 'BadWolfBot'):
        self.bot = bot
    
    @slash_command(
        name='raw',
        description="Catch-all command to input a raw command (for experienced Table Bot users)",
        guild_ids=GUILDS
    )
    async def _catch_all_command(
        self,
        ctx: discord.ApplicationContext,
        input: Option(str, "Raw command input. You do not need to include your Table Bot server prefix in the command")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = input.split() #split the raw string
        message.content = input
        
        await self.bot.process_message_commands(message, args, this_bot, server_prefix, is_lounge)
    
    @slash_command(name="vr",
    description="Show details of a room",
    guild_ids=common.SLASH_GUILDS)
    async def _vr(
        self,
        ctx: discord.ApplicationContext,
        players: Option(str, "Player in the room (FC/Lounge Name/Discord Mention)", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if players: args.append(players)
        
        await commands.OtherCommands.vr_command(message, this_bot, args)
    
    @slash_command(name='wws',
    description="Show all active RT Worldwide rooms",
    guild_ids=common.SLASH_GUILDS)
    async def _wws(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        await commands.OtherCommands.wws_command(message, this_bot)  

    @slash_command(name='ctwws',
    description="Show all active CT Worldwide rooms",
    guild_ids=common.SLASH_GUILDS)
    async def _ctwws(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)

        await commands.OtherCommands.wws_command(message, this_bot, ww_type=Race.CTGP_CTWW_REGION)
    
    @slash_command(name="btwws",
        description="Show all active Battle Worldwide rooms",
        guild_ids=common.SLASH_GUILDS
    )
    async def _btwws(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        await commands.OtherCommands.wws_command(message, this_bot, ww_type=Race.BATTLE_REGION)
    
    @slash_command(name='help',
    description="Show help for Table Bot",
    guild_ids=common.SLASH_GUILDS)
    async def _help(
        self, 
        ctx: discord.ApplicationContext,
        # category: Option(str, "The category you need help with", required=False, default=None, choices=help_documentation.HELP_CATEGORIES + list(help_documentation.TABLING_HELP_FILES.keys())) #autocomplete=discord.utils.basic_autocomplete(get_help_categories)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        # if category: args.append(category)
        
        await help_documentation.send_help(message, is_lounge, args, server_prefix)
        
    @slash_command(name="settings",
    description="Show your Table Bot server settings",
    guild_ids=GUILDS)
    async def _show_settings(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.ServerDefaultCommands.show_settings_command(message)
    
    setting = SlashCommandGroup("setting", "Change your Table Bot server settings", guild_ids=GUILDS, default_member_permissions=Permissions(manage_guild=True))
    
    @setting.command(name="prefix",
    description="Change your server's Table Bot prefix",
    )
    async def _set_prefix(
        self,
        ctx: discord.ApplicationContext,
        prefix: Option(str, "New prefix")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, prefix]
        
        await commands.ServerDefaultCommands.change_server_prefix_command(message, args)
    
    @setting.command(name="ignore_large_times",
    description="Change what formats Table Bot should ignore large times for")
    async def _set_large_time_setting(
        self,
        ctx: discord.ApplicationContext,
        setting: Option(str, "Ignore large times when", choices=commands.LARGE_TIME_OPTIONS.values())
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, setting]
        
        await commands.ServerDefaultCommands.large_time_setting_command(message, this_bot, args, server_prefix)

    @setting.command(name="mii",
    description="Change whether table's show miis on picture footers")
    async def _set_mii(
        self,
        ctx: discord.ApplicationContext,
        setting: Option(str, "Default mii setting", choices=['on', 'off'])
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        setting = "1" if setting == "on" else "2"
        args = [command, setting]
        
        await commands.ServerDefaultCommands.mii_setting_command(message, this_bot, args, server_prefix)
    
    @setting.command(name="graph",
    description="Change your server's default graph")
    async def _set_graph(
        self,
        ctx: discord.ApplicationContext,
        setting: Option(str, "Default graph setting", choices=[x[0] for x in TableBot.graphs.values()])
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str([x[0] for x in TableBot.graphs.values()].index(setting)+1)]

        print(args, setting)
        
        await commands.ServerDefaultCommands.graph_setting_command(message, this_bot, args, server_prefix)

    @setting.command(name="theme",
    description="Change your server's default theme")
    async def _set_theme(
        self,
        ctx: discord.ApplicationContext,
        theme: Option(str, "Default theme", choices=[x[0] for x in TableBot.styles.values()])
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str([x[0] for x in TableBot.styles.values()].index(theme)+1)]
        
        await commands.ServerDefaultCommands.theme_setting_command(message, this_bot, args, server_prefix)

    flags = SlashCommandGroup("flag", "Configure your flag that is shown on tables", guild_ids=GUILDS)
    
    @flags.command(name="set",
    description="Set your table flag")
    async def _set_flag(
        self,
        ctx: discord.ApplicationContext,
        flag: Option(str, "Flag code")
    ):  
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, flag]
        
        await commands.OtherCommands.set_flag_command(message, args)
    
    @flags.command(name="remove",
    description="Remove your table flag")
    async def _remove_flag(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        await commands.OtherCommands.set_flag_command(message, args)
    
    @flags.command(name="show",
    description="Display your currently set flag for Table Bot")
    async def _get_flag(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):  
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        await commands.OtherCommands.get_flag_command(message, args, server_prefix)
    
    @slash_command(
        name="flags",
        description="Show available flag codes",
        guild_ids=GUILDS
    )
    async def _show_flags(
        self,
        ctx: discord.ApplicationContext
    ):
        await ctx.respond("**List of available flag codes:** https://gb.hlorenzi.com/help/flags")
    
    @slash_command(name="fc",
    description="Get a Lounge player's FC",
    guild_ids=GUILDS)
    async def _get_fc(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)

        await commands.OtherCommands.fc_command(message, args)

    @slash_command(name="page",
    description="Get player page link(s) for yourself or someone else",
    guild_ids=GUILDS)
    async def _get_page(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        await commands.OtherCommands.player_page_command(message, args)
    
    @slash_command(name='mii',
    description="Get a player's last used Mii",
    guild_ids=GUILDS)
    async def _get_mii(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        
        await commands.OtherCommands.mii_command(message, args)

    @slash_command(name='pastmii',
    description="Get a random previous mii of a Lounge player",
    guild_ids=GUILDS)
    async def _past_mii(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        
        await commands.OtherCommands.previous_mii_command(message, args)
    
    @slash_command(name="loungename",
    description="Get a player's Lounge name",
    guild_ids=GUILDS)
    async def _get_lounge(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, PLAYER_ARG_DESCRIPTION, required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        await commands.OtherCommands.lounge_name_command(message, args)
    
    @slash_command(name="stats",
    description="See some cool Table Bot stats",
    guild_ids=GUILDS)
    async def _stats(
        self,
        ctx: discord.ApplicationContext
    ):
        _, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)

        await commands.OtherCommands.stats_command(message, self.bot)


def setup(bot):
    bot.add_cog(MiscSlash(bot))