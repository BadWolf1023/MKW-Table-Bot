import discord
from discord import permissions
from discord.ext import commands as ext_commands
from discord.commands import slash_command, SlashCommandGroup, CommandPermission, Option

import TableBot
import UserDataProcessing
import commands
import common

EMPTY_CHAR = "\u200b"
GUILDS = common.SLASH_GUILDS
SETTING_PERMISSIONS = [CommandPermission("administrator", 2, True)]

class MiscSlash(ext_commands.Cog):
    def __init__(self, bot):
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
        
        await self.bot.simulate_on_message(message, args, message.content, this_bot, server_prefix, is_lounge)
    
    setting = SlashCommandGroup("setting", "Change your Table Bot server settings", guild_ids=GUILDS)
    
    @slash_command(name="settings",
    description="Show your Table Bot server settings",
    guild_ids=GUILDS)
    async def _show_settings(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, this_bot, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.ServerDefaultCommands.show_settings_command(message, this_bot, server_prefix)
    
    @setting.command(name="prefix",
    description="Change your server's Table Bot prefix")
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
        setting: Option(str, "War formats to ignore large time warnings for", choices=commands.LARGE_TIME_OPTIONS.values())
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, setting]
        
        await commands.ServerDefaultCommands.large_time_setting_command(message, this_bot, args, server_prefix)

    @setting.command(name="mii",
    description="Change whether table's show miis on picture footers")
    async def _set_theme(
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
        
        await commands.OtherCommands.set_flag_command(message, args, self.bot.user_flag_exceptions)
    
    @flags.command(name="remove",
    description="Remove your table flag")
    async def _remove_flag(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        await commands.OtherCommands.set_flag_command(message, args, self.bot.user_flag_exceptions)
    
    @flags.command(name="show",
    description="Display your currently set flag for Table Bot")
    async def _get_flag(
        self,
        ctx: discord.ApplicationContext
    ):  
        command, message, _, server_prefix, _ = await self.bot.slash_interaction_pre_invoke(ctx)

        
        await commands.OtherCommands.get_flag_command(message, server_prefix)
    
    @slash_command(name="fc",
    description="Get a Lounge player's FC",
    guild_ids=GUILDS)
    async def _get_fc(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player", required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)

        await commands.OtherCommands.fc_command(message, args, message.content)
    
    @slash_command(name='mii',
    description="Get a Lounge player's last used Mii",
    guild_ids=GUILDS)
    async def _get_mii(
        self,
        ctx: discord.ApplicationContext,
        player: Option(str, "Player", required=False, default=None)
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command]
        if player: args.append(player)
        
        await commands.OtherCommands.mii_command(message, args, message.content)
    
    @slash_command(name="loungename",
    description="Get your Lounge name",
    guild_ids=GUILDS)
    async def _get_lounge(
        self,
        ctx: discord.ApplicationContext,
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)

        
        await commands.OtherCommands.lounge_name_command(message)


def setup(bot):
    bot.add_cog(MiscSlash(bot))