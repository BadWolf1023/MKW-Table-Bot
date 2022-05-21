import discord
import commands
from discord.ext import commands as ext_commands
from discord.commands import SlashCommandGroup, slash_command, Option
from discord import Permissions
from discord import permissions
import common

# REQUIRED_PERMISSIONS = [CommandPermission(id,2,True) for id in common.OWNERS]

EMPTY_CHAR = '\u200b'

GUILDS = [common.MKW_TABLE_BOT_CENTRAL_SERVER_ID] if common.is_prod else common.SLASH_GUILDS

class PrivateSlash(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    admin = SlashCommandGroup("admin", "Configure Table Bot admins", guild_ids=GUILDS)

    @admin.command(name="add",
    description="Add a bot admin")
    # @discord.default_permissions(administrator=True)
    async def _add_admin(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User Discord ID")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user]

        await commands.BotOwnerCommands.add_bot_admin_command(message, args)
    
    @admin.command(name="remove",
    description="Remove a bot admin")
    async def _remove_admin(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User Discord ID")
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user]
        
        await commands.BotOwnerCommands.remove_bot_admin_command(message, args)
    
    @slash_command(name="logs",
    description="Show Table Bot's logs",
    guild_ids=GUILDS,
    )
    async def _get_logs(
        self, 
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BotOwnerCommands.get_logs_command(message)
    
    @slash_command(name="garbagecollect",
    description="Table Bot garbage collection",
    guild_ids=GUILDS,
    )
    async def _garbage_collect(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BotOwnerCommands.garbage_collect_command(message)
    
    @slash_command(name="serverusage",
    description="See statistics about Table Bot's server usage",
    guild_ids=GUILDS,
    )
    async def _server_usage(
        self,
        ctx: discord.ApplicationContext
    ):
        _, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.BotOwnerCommands.server_process_memory_command(message)
    
    @slash_command(name='closebot',
    description="Gracefully close Table Bot and save its data",
    guild_ids=GUILDS,
    )
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