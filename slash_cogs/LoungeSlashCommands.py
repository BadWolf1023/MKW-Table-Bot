import discord
from discord.commands import slash_command, Option, CommandPermission, SlashCommandGroup
from discord.ext import commands as ext_commands
import commands
import common

REQUIRED_PERMISSIONS = [CommandPermission(role, 2, True) for role in list(common.reporter_plus_roles)] # + [Permission(common.CW_ID, 2, True)]
# GUILDS = [common.MKW_LOUNGE_SERVER_ID]+common.SLASH_GUILDS
GUILDS = common.SLASH_GUILDS
EMPTY_CHAR = "\u200b"

class LoungeSlash(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    update = SlashCommandGroup("update", "Submit tables to updaters", guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)

    @update.command(name='rt',
    description="Submit an RT table to updaters. NO TABLE TEXT SUBMISSIONS")
    async def _rt_update(
        self, 
        ctx: discord.ApplicationContext,
        tier: Option(str, "Tier of event", choices=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'squadqueue']),
        races_played: Option(int, "Number of races played in event"),
        # table_text: Option(str, "Table text for manual submissions", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, tier, str(races_played)]
        # if table_text: args.append(table_text)

        # await ctx.respond(EMPTY_CHAR)
        await ctx.respond(f"**IMPORTANT**: Unfortunately, Table Bot does not support submitting tables at the present. \
            Use `{self.bot.user.name} rtupdate [tier] [races_played] [...table_text]` instead. This is an issue with Discord, so as soon as this is fixed, you will be able to use this slash command.")

        await commands.LoungeCommands.rt_mogi_update(self.bot, this_bot, message, args, self.bot.lounge_submissions)
        
    @update.command(name='ct',
    description="Submit a CT table to updaters. NO TABLE TEXT SUBMISSIONS")
    async def _ct_update(
        self,
        ctx: discord.ApplicationContext,
        tier: Option(str, "Tier of event", choices=['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4', 'Tier 5', 'Tier 6', 'Tier 7', 'squadqueue']),
        races_played: Option(int, "Number of races played in event"),
        # table_text: Option(str, "Table text for manual submissions", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, tier, str(races_played)]
        # if table_text: args.append(table_text)

        # await ctx.respond(EMPTY_CHAR)
        await ctx.respond(f"**IMPORTANT**: Unfortunately, Table Bot does not support submitting tables at the present. \
            Use `{self.bot.user.name} ctupdate [tier] [races_played] [...table_text]` instead. This is an issue with Discord, so as soon as this is fixed, you will be able to use this slash command.")

        await commands.LoungeCommands.ct_mogi_update(self.bot, this_bot, message, args, self.bot.lounge_submissions)
    
    @slash_command(name="approve",
    description="Approve a lounge submission",
    guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)
    async def _approve_submission(
        self,
        ctx: discord.ApplicationContext,
        id: Option(int, "Submission ID")
    ):
        command, message, this_bot, _, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, str(id)]

        await ctx.respond(EMPTY_CHAR)
        await commands.LoungeCommands.approve_submission_command(self.bot, message, args, self.bot.lounge_submissions)
    
    @slash_command(name="deny",
    description="Deny a lounge submission",
    guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)
    async def _deny_submission(
        self,
        ctx: discord.ApplicationContext,
        id: Option(int, "Submission ID"),
        reason: Option(str, "Reason for denial", required=False, default=None)
    ):
        command, message, this_bot, _, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)
        args = [command, str(id)]
        if reason: args.append(reason)

        await ctx.respond(EMPTY_CHAR)
        await commands.LoungeCommands.deny_submission_command(self.bot, message, args, self.bot.lounge_submissions)
    
    @slash_command(name="pending",
    description="Show a list of lounge submissions awaiting updater approval",
    guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)
    async def _pending_submissions(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx.interaction)

        await ctx.respond(EMPTY_CHAR)
        await commands.LoungeCommands.pending_submissions_command(message, self.bot.lounge_submissions)
    


def setup(bot):
    bot.add_cog(LoungeSlash(bot))