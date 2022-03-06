import discord
from discord.commands import slash_command, Option, CommandPermission, SlashCommandGroup
from discord.ext import commands as ext_commands
import commands
import common
import InteractionUtils

REQUIRED_PERMISSIONS = [CommandPermission(role, 1, True, (common.TABLE_BOT_DISCORD_SERVER_ID if common.is_beta else common.MKW_LOUNGE_SERVER_ID)) for role in list(common.reporter_plus_roles)]
GUILDS = [common.MKW_LOUNGE_SERVER_ID]
if common.is_beta:
    GUILDS = [common.TABLE_BOT_DISCORD_SERVER_ID]
elif common.is_dev:
    GUILDS = common.SLASH_GUILDS
EMPTY_CHAR = "\u200b"

class TableTextModal(discord.ui.Modal):
    update_commands = {
        'rt': commands.LoungeCommands.rt_mogi_update,
        'ct': commands.LoungeCommands.ct_mogi_update
    }
    def __init__(self, bot, chan_bot, prefix, is_lounge, view):
        super().__init__(title="Table Text Input")
        self.bot = bot
        self.chan_bot = chan_bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.view = view
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.multiline, label='Table text', placeholder="Input table text here"))

    async def on_error(self): #not yet implemented in pycord - will be soon
        pass

    async def callback(self, interaction: discord.Interaction):
        message = self.view.proxy_msg
        message.content += '\n' + self.children[0].value
        # self.view.args.append(self.children[0].value)
        # print(message.content, self.view.args)
        response = await interaction.response.send_message("Table text submitted.")
        try:
            await self.update_commands[self.view.type](self.bot, self.chan_bot, message, self.view.args, self.bot.lounge_submissions)
        except Exception as error:
            await response.edit_original_message(content="An error occurred while submitting table text.")
            await InteractionUtils.on_component_error(error, interaction, self.prefix)
        await self.view.message.edit(view=None)


class TableTextButton(discord.ui.Button['TableTextView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Input Table Text", row=1)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TableTextModal(self.view.bot, self.view.chan_bot, self.view.prefix, self.view.is_lounge, self.view))

class TableTextView(discord.ui.View):
    def __init__(self, bot, chan_bot, prefix, is_lounge, ctx, proxy_msg, args, type):
        super().__init__()
        self.bot = bot
        self.chan_bot = chan_bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.author = ctx.author
        self.args = args
        self.ctx = ctx
        self.proxy_msg = proxy_msg
        self.type = type
        self.message = None
        self.add_item(TableTextButton())
        self.chan_bot.add_component(self)
    
    # async def delete(self, interaction: discord.Interaction):
    #     self.clear_items()
    #     self.stop()
    #     await interaction.response.edit_message(view=None)
    
    async def on_timeout(self):
        self.clear_items()
        self.stop()
        await self.message.edit(view=None)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        allowed = InteractionUtils.commandIsAllowed(self.is_lounge, interaction.user, self.chan_bot, 'restricted_interaction', is_interaction=True)
        if not allowed: 
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        if interaction.user != self.author:
            await interaction.response.send_message(f"You can't use this button: in use by {self.author.mention}.", ephemeral=True)
            return False
        return allowed
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.chan_bot)
    
    async def send(self, messageable, content=None, embed=None, file=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, embed=embed, file=file, view=self)


        
class LoungeSlash(ext_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    update = SlashCommandGroup("update", "Submit tables to updaters", guild_ids=GUILDS) 

    @update.command(name='rt',
    description="Submit an RT table to updaters")
    async def _rt_update(
        self, 
        ctx: discord.ApplicationContext,
        tier: Option(str, "Tier of event", choices=['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'squadqueue']),
        races_played: Option(int, "Number of races played in event"),
        table_text: Option(bool, "Whether you're including table text for a manual submission", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx, args=['rtupdate', tier, str(races_played)])
        args = ['rtupdate', tier, str(races_played)]
        # await message.channel.send(f"**IMPORTANT**: Unfortunately, Table Bot does not support submitting table text by slash commands at the present. Use `@{self.bot.user.name} rtupdate [tier] [races_played] [...table_text]` instead. This is an issue with Discord, so as soon as this is fixed, you will be able to use table texts with this slash command.")

        if not table_text:
            return await commands.LoungeCommands.rt_mogi_update(self.bot, message, this_bot, args, self.bot.lounge_submissions)
        
        view = TableTextView(self.bot, this_bot, server_prefix, is_lounge, ctx, message, args, 'rt')
        await view.send(message, content="Copy your table text from `/tt` before clicking this button.")
        
    @update.command(name='ct',
    description="Submit a CT table to updaters")
    async def _ct_update(
        self,
        ctx: discord.ApplicationContext,
        tier: Option(str, "Tier of event", choices=['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'squadqueue']),
        races_played: Option(int, "Number of races played in event"),
        table_text: Option(bool, "Whether you're including table text for a manual submission", required=False, default=None)
    ):
        command, message, this_bot, server_prefix, is_lounge = await self.bot.slash_interaction_pre_invoke(ctx, args=['ctupdate', tier, str(races_played)])
        args = ['ctupdate', tier, str(races_played)]
        # await message.channel.send(f"**IMPORTANT**: Unfortunately, Table Bot does not support submitting table text by slash commands at the present. Use `@{self.bot.user.name} ctupdate [tier] [races_played] [...table_text]` instead. This is an issue with Discord, so as soon as this is fixed, you will be able to use table texts with this slash command.")

        if not table_text:
            return await commands.LoungeCommands.ct_mogi_update(self.bot, message, this_bot, args, self.bot.lounge_submissions)

        view = TableTextView(self.bot, this_bot, server_prefix, is_lounge, ctx, message, args, 'ct')
        await view.send(message, content="Copy your table text from `/tt` before clicking this button.")
    
    @slash_command(name="approve",
    description="Approve a lounge submission",
    guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)
    async def _approve_submission(
        self,
        ctx: discord.ApplicationContext,
        id: Option(int, "Submission ID")
    ):
        command, message, this_bot, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(id)]
        
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
        command, message, this_bot, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        args = [command, str(id)]
        if reason: args.append(reason)
        
        await commands.LoungeCommands.deny_submission_command(self.bot, message, args, self.bot.lounge_submissions)
    
    @slash_command(name="pending",
    description="Show lounge submissions awaiting updater approval",
    guild_ids=GUILDS, permissions=REQUIRED_PERMISSIONS)
    async def _pending_submissions(
        self,
        ctx: discord.ApplicationContext
    ):
        command, message, _, _, _ = await self.bot.slash_interaction_pre_invoke(ctx)
        
        await commands.LoungeCommands.pending_submissions_command(message, self.bot.lounge_submissions)
    


def setup(bot):
    bot.add_cog(LoungeSlash(bot))