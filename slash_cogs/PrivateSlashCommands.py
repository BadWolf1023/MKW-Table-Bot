import discord
import commands
from discord.ext import commands as ext_commands
from discord.commands import SlashCommandGroup, slash_command, Option, CommandPermission
import common

REQUIRED_PERMISSIONS = [CommandPermission(id,2,True) for id in common.OWNERS]

EMPTY_CHAR = '\u200b'

class PrivateSlash(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    admin = SlashCommandGroup("admin", "Configure Table Bot admins", guild_ids=common.SLASH_GUILDS, permissions=REQUIRED_PERMISSIONS)

    @admin.command(name="add",
    description="Add a bot admin")
    async def _add_admin(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User Discord ID")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user]

        
        await commands.BadWolfCommands.add_bot_admin_command(message, args)
    
    @admin.command(name="remove",
    description="Remove a bot admin")
    async def _remove_admin(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User Discord ID")
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user]
        
        await commands.BadWolfCommands.remove_bot_admin_command(message, args)
    
    @slash_command(name="logs",
    description="Show Table Bot's logs",
    guild_ids=common.SLASH_GUILDS, 
    permissions=REQUIRED_PERMISSIONS)
    async def _get_logs(
        self, 
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BadWolfCommands.get_logs_command(message)
    
    @slash_command(name="garbage_collect",
    description="Table Bot garbage collection",
    guild_ids=common.SLASH_GUILDS, 
    permissions=REQUIRED_PERMISSIONS)
    async def _garbage_collect(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BadWolfCommands.garbage_collect_command(message)
    
    @slash_command(name="server_usage",
    description="See statistics about Table Bot's server usage",
    guild_ids=common.SLASH_GUILDS, 
    permissions=REQUIRED_PERMISSIONS)
    async def _server_usage(
        self,
        ctx: discord.ApplicationContext
    ):
        _, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BadWolfCommands.server_process_memory_command(message)
    
    @slash_command(name='close_bot',
    description="Gracefully close Table Bot and save its data",
    guild_ids=common.SLASH_GUILDS,
    permissions=REQUIRED_PERMISSIONS)
    async def _close_bot(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            self.bot.save_data()
            await ctx.respond("Data has been saved and all table bots have been cleaned up; bot gracefully closed.")
        except Exception as e:
            await ctx.respond("An error occurred while saving data; data not successfully saved.")
            raise e

        self.bot.destroy_all_tablebots()
        await self.bot.close()

def setup(bot):
    bot.add_cog(PrivateSlash(bot))