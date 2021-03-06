from discord.commands import slash_command, SlashCommandGroup, Option
from discord.ext import commands as ext_commands
from discord import Permissions
import discord
import commands
import common
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BadWolfBot import BadWolfBot

EMPTY_CHAR = '\u200b'

allowed = common.botAdmins | common.OWNERS

# REQUIRED_PERMISSIONS = [CommandPermission(int(id),2,True) for id in allowed]
GUILDS = [] if common.is_prod else common.SLASH_GUILDS

class AdminSlash(ext_commands.Cog):
    def __init__(self, bot: 'BadWolfBot'):
        self.bot = bot

    sha = SlashCommandGroup("sha", "Configure Table Bot's SHA-track mappings", guild_ids=GUILDS)

    @sha.command(name="add",
    description="Add a SHA-track mapping",
    )
    async def _add_sha(
        self,
        ctx: discord.ApplicationContext,
        sha: Option(str, "SHA to add"),
        track: Option(str, "Track name (paste the track name exactly as it appears)")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, sha, track]
        
        await commands.BotAdminCommands.add_sha_track(message, args)

    @sha.command(name="remove",
    description="Remove a SHA-track mapping",
    )
    async def _remove_sha(
        self,
        ctx: discord.ApplicationContext,
        sha: Option(str, "SHA to remove")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, sha]
        
        await commands.BotAdminCommands.remove_sha_track(message, args)
    
    blacklist = SlashCommandGroup("blacklist", "Configure Table Bot's blacklists", guild_ids=GUILDS)
    blacklist_user = blacklist.create_subgroup("user", "Configure Table Bot's blacklisted users", guild_ids=GUILDS)
    blacklist_word = blacklist.create_subgroup("word", "Configure Table Bot's blacklisted words", guild_ids=GUILDS)

    @blacklist_user.command(name="add",
    description="Blacklist a user from using Table Bot",
    )
    async def _add_user_blacklist(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User's Discord ID"),
        reason: Option(str, "Reason for blacklist")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user, reason]

        await commands.BotAdminCommands.blacklist_user_command(message, args)
    
    @blacklist_user.command(name="remove",
    description="Remove a user from Table Bot's blacklisted users",
    )
    async def _remove_user_blacklist(
        self,
        ctx: discord.ApplicationContext,
        user: Option(int, "User's Discord ID")
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, user]
        
        await commands.BotAdminCommands.blacklist_user_command(message, args)

    @blacklist_word.command(name="add",
    description="Blacklist a word from being used with Table Bot",
    )
    async def _add_word_blacklist(
        self, 
        ctx: discord.ApplicationContext,
        word: Option(str, "Word to blacklist")
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, word]
        
        await commands.BotAdminCommands.add_blacklisted_word_command(message, args)
    
    @blacklist_word.command(name="remove",
    description="Remove a blacklisted word",
    )
    async def _remove_word_blacklist(
        self, 
        ctx: discord.ApplicationContext,
        word: Option(str, "Word to remove from blacklist")
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, word]
        
        await commands.BotAdminCommands.remove_blacklisted_word_command(message, args)
    
    @slash_command(name='global_vr',
    description="Turn the /vr command on or off",
    guild_ids=GUILDS,
    )
    async def _global_vr(
        self,
        ctx: discord.ApplicationContext,
        status: Option(str, "on/off", choices=["on", "off"])
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        status = True if status == 'on' else False
        
        await commands.BotAdminCommands.global_vr_command(message, on=status)
    

def setup(bot):
    bot.add_cog(AdminSlash(bot))