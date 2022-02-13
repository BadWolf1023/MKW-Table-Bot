import discord
import TableBot
import commands
import InteractionUtils
import UtilityFunctions
import asyncio
import TimerDebuggers

class ManualTeamsModal(discord.ui.Modal):
    def __init__(self, bot, prefix, is_lounge, view):
        super().__init__(title="Manual Teams Input")
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.view = view
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.singleline, label='Input', placeholder="Input teams here"))

    async def callback(self, interaction: discord.Interaction):
        message = InteractionUtils.create_proxy_msg(interaction)
        message.content = self.children[0].value
        await self.view.message.edit(view=None)
        await interaction.response.send_message('Manual teams created.')
        await commands.TablingCommands.manual_war_setup(message, self.bot, self.prefix, self.is_lounge, message.content)
        

class InputTeamsButton(discord.ui.Button['ManualTeamsView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Input Teams", row=1)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ManualTeamsModal(self.view.bot, self.view.prefix, self.view.is_lounge, self.view))

class ManualTeamsView(discord.ui.View):
    def __init__(self, bot, prefix, is_lounge):
        super().__init__()
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.message = None
        self.add_item(InputTeamsButton())
    
    async def delete(self, interaction: discord.Interaction):
        self.clear_items()
        self.stop()
        await interaction.response.edit_message(view=None)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        allowed = InteractionUtils.commandIsAllowed(self.is_lounge, interaction.user, self.bot, 'confirm_interaction')
        if not allowed: 
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        if not self.bot.manualWarSetUp:
            await self.delete(interaction)
            await interaction.followup.send("Manual teams have already been entered.", ephemeral=True)
            return False
        return allowed
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix)
    
    async def send(self, messageable, content=None, embed=None, file=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, embed=embed, file=file, view=self)

################################################################################################

class ConfirmButton(discord.ui.Button['ConfirmView']):
    def __init__(self, cat):
        self.cat = cat
        buttonType = discord.ButtonStyle.success if cat=='Yes' else discord.ButtonStyle.danger
        super().__init__(style=buttonType, label=cat, row=1)

    
    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        for ind, child in enumerate(self.view.children):
            child.disabled = True
            if child.cat != self.cat: 
                self.view.children.pop(ind)
        self.view.stop()

        await interaction.response.edit_message(view=self.view)

        message = InteractionUtils.create_proxy_msg(interaction, ['wp'])
        await commands.TablingCommands.after_start_war_command(message, self.view.bot, [self.cat], self.view.prefix, self.view.lounge)


class ConfirmView(discord.ui.View):
    def __init__(self, bot, prefix, lounge):
        super().__init__()
        self.bot = bot
        self.prefix = prefix
        self.lounge = lounge
        self.add_item(ConfirmButton('Yes'))
        self.add_item(ConfirmButton('No'))
    
    async def delete(self, interaction: discord.Interaction):
        self.clear_items()
        self.stop()
        await interaction.response.edit_message(view=None)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        allowed = InteractionUtils.commandIsAllowed(self.lounge, interaction.user, self.bot, 'confirm_interaction')
        if not allowed: 
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        if not self.bot.prev_command_sw:
            await self.delete(interaction)
            await interaction.followup.send("This has already been responded to.", ephemeral=True)
            return False
        return allowed
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix)
    
    async def send(self, messageable, content=None, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, file=file, embed=embed, view=self)


###########################################################################################

class PictureButton(discord.ui.Button['PictureView']):
    def __init__(self, bot):
        cooldown = bot.getWPCooldownSeconds()
        super().__init__(style=discord.ButtonStyle.gray if (cooldown > 0) else discord.ButtonStyle.primary, label='Update', row=0)
        self.bot = bot
        asyncio.create_task(self.activate())

    async def activate(self):
        await asyncio.sleep(self.bot.getWPCooldownSeconds())
        self.style = discord.ButtonStyle.primary
        try:
            if self.view.message.channel.id in TableBot.last_wp_message:
                await self.view.message.edit(view=self.view)
        except:
            pass

    @TimerDebuggers.timer_coroutine
    async def callback(self, interaction: discord.Interaction):
        msg = InteractionUtils.create_proxy_msg(interaction, ['wp'])

        await interaction.response.edit_message(view=None)
        await commands.TablingCommands.war_picture_command(msg,self.view.bot,['wp'],self.view.prefix,self.view.is_lounge,
                                                           requester=interaction.user.display_name)

class PictureView(discord.ui.View):
    def __init__(self, bot, prefix, is_lounge_server):
        super().__init__(timeout=60*10)
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge_server
        self.message: discord.Message = None

        self.add_item(PictureButton(self.bot))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        allowed = InteractionUtils.commandIsAllowed(self.is_lounge,interaction.user,self.bot,'wp')
        if not allowed: 
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)

        cooldown = self.bot.getWPCooldownSeconds()
        cooldown_active = cooldown > 0
        if cooldown_active:
            await interaction.response.send_message(f"This button is on cooldown. Please wait {cooldown} more seconds.", 
                                                        ephemeral=True, delete_after=3.0)
            return False

        return allowed
    
    async def on_timeout(self) -> None:
        self.clear_items()
        self.stop()
        if self.message:
            await self.message.edit(view=None)
        self = None
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix)

    async def send(self, messageable, content=None, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, file=file, embed=embed, view=self)


###########################################################################################


class RejectButton(discord.ui.Button['SuggestionView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Discard")
    
    async def callback(self, interaction: discord.Interaction):
        self.view.bot.resolved_errors.add(self.view.current_error['id'])

        # await self.view.on_timeout()
        await self.view.next_suggestion()

class SuggestionButton(discord.ui.Button['SuggestionView']):
    def __init__(self, error, label, value=None, confirm=False):
        self.error = error #dict of error information
        self.confirm = confirm
        self.value = value
        if not confirm: 
            label = f"R{self.error['race']}: "+label
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=confirm)
    
    async def callback(self, interaction: discord.Interaction):
        server_prefix = self.view.prefix

        args = get_command_args(self.error, self.value if not self.confirm else self.view.selected_values, self.view.bot)
        message = InteractionUtils.create_proxy_msg(interaction, args)

        command_mapping = {
            "blank_player": commands.TablingCommands.disconnections_command,
            "gp_missing": commands.TablingCommands.change_room_size_command,
            "gp_missing_1": commands.TablingCommands.early_dc_command,
            "tie": commands.TablingCommands.quick_edit_command,
            "large_time": commands.TablingCommands.quick_edit_command,
            "missing_player": commands.TablingCommands.disconnections_command

            # "gp_missing": commands.TablingCommands.change_room_size_command, CHECKED
            # "gp_missing_1": commands.TablingCommands.early_dc_command, CHECKED
            # "tie": commands.TablingCommands.quick_edit_command, BROKEN
            # "large_time": commands.TablingCommands.quick_edit_command, CHECKED
            # "missing_player": commands.TablingCommands.disconnections_command CHECKED
        }
        
        command_mes = await command_mapping[self.error['type']](message, self.view.bot, args, server_prefix, self.view.lounge, dont_send=True)
        author_str = interaction.user.display_name

        # self.view.stop()
        # self.view.clear_items()

        # await self.view.message.delete()
        await self.view.message.channel.send(f"{author_str} - "+command_mes)
        self.view.bot.resolved_errors.add(self.view.current_error['id'])
        await self.view.next_suggestion()

class SuggestionSelectMenu(discord.ui.Select['SuggestionView']):
    def __init__(self, values, name):
        options = [discord.SelectOption(label=str(value)) for value in values]
        super().__init__(placeholder=name, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.selected_values = interaction.data['values'][0]
        self.placeholder = self.view.selected_values 

        self.view.enable_confirm()
        try:
            await interaction.response.edit_message(view=self.view)
        except: 
            pass

LABEL_BUILDERS = {
    'missing_player': '{} DCed [{}] race',
    'blank_player': "{} DCed [{}] race",
    'tie': '{} placed [{}]',
    'large_time': '{} {} [{}]', #placed / did not place
    'gp_missing': 'Change Room Size',
    'gp_missing_1': 'Player early DCed [{}] race'
}

ERROR_TYPE_DESCRIPTIONS = {
    'missing_player': 'Missing Player',
#    'blank_player': "{} DCed [{}] race",
    'tie': 'Tie',
    'large_time': 'Large Finish Time',
    'gp_missing': 'Missing Players',
    'gp_missing_1': 'Early DC'
}

class SuggestionView(discord.ui.View):
    @TimerDebuggers.timer
    def __init__(self, errors, bot, prefix, lounge, id=None):
        super().__init__(timeout=120)
        self.bot = bot
        self.prefix = prefix
        self.errors = errors
        self.lounge = lounge
        self.selected_values = None
        self.message = None

        # self.bot.resolved_errors.add(self.sug_id) # don't show the same suggestion again
        self.current_error = self.errors.pop()
        self.create_suggestion()

    async def on_timeout(self) -> None:
        try:
            await self.message.delete()
        except:
            pass
        self.stop()
        self.clear_items()
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix)
        
    async def send(self, messageable, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel
        
        self.bot.add_sug_view(self)

        self.message: discord.Message = await messageable.send(content=f"**Suggested Fix ({ERROR_TYPE_DESCRIPTIONS[self.current_error['type']]}):**", file=file, embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        allowed = InteractionUtils.commandIsAllowed(self.lounge, interaction.user, self.bot, InteractionUtils.convert_key_to_command(self.current_error['type']))
        if not allowed: 
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True, delete_after=3.0)
        return allowed
    
    async def next_suggestion(self):
        if len(self.errors) > 0:
            self.current_error = self.errors.pop()
            self.clear_items()
            self.create_suggestion()
            await self.message.edit(content=f"**Suggested Fix ({ERROR_TYPE_DESCRIPTIONS[self.current_error['type']]}):**", view=self)
        else:
            await self.on_timeout()

    def create_suggestion(self):
        error = self.current_error
        err_type = error['type']
        label_builder = LABEL_BUILDERS[err_type]

        if 'gp_missing' in err_type:
            if '_1' in err_type:
                label_builder = LABEL_BUILDERS[err_type]
                for insert in ['during', 'before']:
                    label = label_builder.format(insert)
                    self.add_item(SuggestionButton(error, label, value=insert))
            else:
                label = label_builder
                self.add_item(SuggestionSelectMenu(error['corrected_room_sizes'], name=f"R{error['race']}: Select correct room size"))
                self.add_item(SuggestionButton(error, label, confirm=True))
        

        elif err_type in { 'missing_player', 'blank_player' }:
            for insert in ['during', 'before']:
                label = label_builder.format(error['player_name'], insert)
                self.add_item(SuggestionButton(error, label, value=insert))
        
        elif err_type == 'large_time':
            for insert in ["placed"]:
                label = label_builder.format(error['player_name'], insert, UtilityFunctions.place_to_str(error['placement']))
                self.add_item(SuggestionButton(error, label, value=error['placement']))
        
        elif err_type == 'tie':
            for insert in error['placements']:
                label = label_builder.format(error['player_name'], UtilityFunctions.place_to_str(insert))
                self.add_item(SuggestionButton(error, label, value=insert))
        
        self.add_item(RejectButton())
    
    def enable_confirm(self):
        for child in self.children:
            child.disabled=False


def get_command_args(error, info, bot):
    err_type = error['type']

    if err_type == 'gp_missing_1':
        GP = int((error['race']-1)/4) + 1
        time = "on" if info == 'during' else "before"
        args = ['earlydc', str(GP), time]
    
    elif err_type == 'gp_missing':
        race = error['race']
        room_size = str(info)
        args = ['changeroomsize', str(race), room_size]
    
    elif err_type in { 'missing_player', 'blank_player' }:
        playerNum = bot.player_to_dc_num(error['race'], error['player_fc'])

        time = "on" if info == 'during' else "before"
        args = ['dc', str(playerNum), time]
    
    elif err_type == 'large_time':
        playerNum = bot.player_to_num(error['player_fc'])
        placement = str(info)
        race = error['race']
        args = ['changeplace', str(playerNum), str(race), placement]
    
    elif err_type == 'tie':
        playerNum = bot.player_to_num(error['player_fc'])
        race = error['race']
        placement = str(info)
        args = ['changeplace', str(playerNum), str(race), placement]
    
    return args
