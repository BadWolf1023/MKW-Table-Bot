import discord
import TableBot
import commands
import InteractionUtils
import UtilityFunctions
import asyncio
import TimerDebuggers
import common
import Stats
import time
from typing import Dict

class ManualTeamsModal(discord.ui.Modal):
    def __init__(self, bot, prefix, is_lounge, view):
        super().__init__(title="Manual Teams Input")
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.view = view
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.singleline, label='Input', placeholder="Input teams here"))

    async def on_error(self): #not yet implemented in pycord - will be soon
        pass

    async def callback(self, interaction: discord.Interaction):
        if not self.bot.manualWarSetUp: 
            return await interaction.response.send_message("This button has expired.", ephemeral=True, delete_after=3)
        message = InteractionUtils.create_proxy_msg(interaction)
        message.content = self.children[0].value
        response = await interaction.response.send_message('Manual teams processed.')
        args = message.content.split()
        try:
            await commands.TablingCommands.manual_war_setup(message, self.bot, args, self.prefix, self.is_lounge)
        except Exception as error:
            await response.edit_original_message(content='An error occurred while creating manual teams.')
            return await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)
        await self.view.message.edit(view=None)
        

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
        self.bot.add_component(self)
    
    async def delete(self, interaction: discord.Interaction):
        self.clear_items()
        self.stop()
        await interaction.response.edit_message(view=None)
    
    async def on_timeout(self):
        self.clear_items()
        self.stop()
        await self.message.edit(view=None)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        allowed = InteractionUtils.commandIsAllowed(self.is_lounge, interaction.user, self.bot, 'restricted_interaction', is_interaction=True)
        if not allowed: 
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)
            return False
        if not self.bot.manualWarSetUp:
            await self.delete(interaction)
            await interaction.followup.send("Manual teams have already been entered.", ephemeral=True)
            return False
        return allowed
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)
    
    async def send(self, messageable, content=None, embed=None, file=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, embed=embed, file=file, view=self)
        return self.message

################################################################################################

class ConfirmButton(discord.ui.Button['ConfirmView']):
    def __init__(self, cat):
        self.cat = cat
        buttonType = discord.ButtonStyle.success if cat=='Yes' else discord.ButtonStyle.danger
        super().__init__(style=buttonType, label=cat, row=1)

    
    async def callback(self, interaction: discord.Interaction):
        if self.view.responded:
            return

        self.view.responded = True
        self.disabled = True
        for ind, child in enumerate(self.view.children):
            child.disabled = True
            if child.cat != self.cat: 
                self.view.children.pop(ind)

        self.view.stop()
        # await common.safe_edit(interaction.message, view=self.view)
        await interaction.response.edit_message(view=self.view)

        message = InteractionUtils.create_proxy_msg(interaction, [self.cat])
        await commands.TablingCommands.after_start_war_command(message, self.view.bot, [self.cat], self.view.prefix, self.view.is_lounge)


class ConfirmView(discord.ui.View):
    def __init__(self, message, bot, prefix, is_lounge):
        super().__init__(timeout=300)
        self.message = message
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge
        self.responded = False
        self.add_item(ConfirmButton('Yes'))
        self.add_item(ConfirmButton('No'))
        self.bot.add_component(self)
    
    async def on_timeout(self):
        if not self.responded:
            self.clear_items()
            self.stop()
            await common.safe_edit(self.message, view=None)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        allowed = InteractionUtils.commandIsAllowed(self.is_lounge, interaction.user, self.bot, 'restricted_interaction', is_interaction=True)
        if not allowed: 
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False

        if not self.bot.prev_command_sw:
            await interaction.response.send_message("This button has expired.", ephemeral=True)
            await self.on_timeout()
            return False

        if self.responded:
            return False

        return allowed
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)
    
    async def send(self, messageable, content=None, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message: discord.Message = await messageable.send(content=content, file=file, embed=embed, view=self)
        return self.message


###########################################################################################

class PictureButton(discord.ui.Button['PictureView']):
    def __init__(self, bot):
        cooldown = bot.getWPCooldownSeconds()
        super().__init__(style=discord.ButtonStyle.gray if (cooldown > 0) else discord.ButtonStyle.primary, label='Update', row=0)
        self.bot = bot
        self.responded = False
        asyncio.create_task(self.activate())

    async def activate(self):
        await asyncio.sleep(self.bot.getWPCooldownSeconds())
        self.style = discord.ButtonStyle.primary
        try:
            if self.view.message.channel.id in TableBot.last_wp_button:
                await common.safe_edit(self.view.message, view=self.view)
        except:
            pass

    @TimerDebuggers.timer_coroutine
    async def callback(self, interaction: discord.Interaction):
        if self.responded:
            return

        self.responded = True
        msg = InteractionUtils.create_proxy_msg(interaction, ['wp'])
        Stats.log_command('wp')

        await common.safe_edit(interaction.message, view=None)
        await commands.TablingCommands.war_picture_command(msg,self.view.bot,['wp'],self.view.prefix,self.view.is_lounge,
                                                           requester=interaction.user.display_name)

class SubmitButton(discord.ui.Button['PictureView']):
    def __init__(self,channel_bot: TableBot.ChannelBot, rt_ct:str, tier:str ,num_races:int):
        super().__init__(style=discord.ButtonStyle.danger, label=f"Submit to {rt_ct.upper()} "
                                                                 f"{'T' if tier != 'SQ' else ''}{tier}", row=0)
        self.tier = tier
        self.channel_bot = channel_bot
        self.rt_ct = rt_ct
        self.num_races = num_races
        self.responded = False

    @TimerDebuggers.timer_coroutine
    async def callback(self, interaction: discord.Interaction):
        if self.channel_bot.has_been_lounge_submitted:
            await self.view.on_timeout()
            return await interaction.response.send_message("Table has already been submitted.", ephemeral=True)
        
        if self.responded:
            return await interaction.response.send_message("This button has already been used.", ephemeral=True)

        self.channel_bot.has_been_lounge_submitted = True

        args = [f'{self.rt_ct}update', str(self.tier), str(self.num_races)]
        message = InteractionUtils.create_proxy_msg(interaction, args)
        Stats.log_command(args[0])

        self.responded = True
        self.view.children.remove(self)
        await common.safe_edit(self.view.message, view=self)

        async def submit_table():
            try:
                if self.rt_ct.lower() == 'ct':
                    await commands.LoungeCommands.ct_mogi_update(common.client, message, self.channel_bot, args, common.client.lounge_submissions)
                else:
                    await commands.LoungeCommands.rt_mogi_update(common.client, message, self.channel_bot, args, common.client.lounge_submissions)
                
                # await self.view.on_timeout() #remove picture button as well, since table has been submitted
            except Exception as e:
                await InteractionUtils.handle_component_exception(e, message, self.view.prefix, self.view.bot)

        asyncio.create_task(submit_table())

class PictureView(discord.ui.View):
    def __init__(self, bot, prefix, is_lounge_server):
        super().__init__(timeout=600)
        self.bot = bot
        self.prefix = prefix
        self.is_lounge = is_lounge_server
        self.message: discord.Message = None

        self.add_item(PictureButton(self.bot))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        allowed = InteractionUtils.commandIsAllowed(self.is_lounge,interaction.user,self.bot,'restricted_interaction', is_interaction=True)
        if not allowed:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return False
        
        if len(self.children) == 0:
            await self.on_timeout()
            return False

        if interaction.data['custom_id'] != self.children[0].custom_id: # Submit button is the second child
            if self.bot.has_been_lounge_submitted:
                await interaction.response.send_message("Table has already been submitted.", ephemeral=True)
                return False

            return True

        cooldown = self.bot.getWPCooldownSeconds()
        cooldown_active = cooldown > 0
        if cooldown_active:
            await interaction.response.send_message(f"This button is on cooldown. Please wait {cooldown} more seconds.", 
                                                        ephemeral=True, delete_after=3.0)
            return False

        return True
    
    async def on_timeout(self) -> None:
        if self.is_finished():
            return
        self.clear_items()
        self.stop()
        if self.message:
            await common.safe_edit(self.message, view=None)
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)

    async def send(self, messageable, content=None, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.message = await messageable.send(content=content, file=file, embed=embed, view=self)
        return self.message


###########################################################################################

class UpdateVRButton(discord.ui.Button['VRView']):
    def __init__(self, bot: TableBot.ChannelBot):
        self.bot = bot
        super().__init__(style=discord.ButtonStyle.gray if self.bot.getRLCooldownSeconds() > 0 else discord.ButtonStyle.primary, label="Refresh")
        self.responded = False

        asyncio.create_task(self.update())

    async def update(self):
        await asyncio.sleep(self.bot.getRLCooldownSeconds())
        self.style = discord.ButtonStyle.primary
        try:
            await common.safe_edit(self.view.message, view=self.view)
        except:
            pass
    
    async def callback(self, interaction: discord.Interaction):
        if self.responded:
            return

        self.responded = True
        await interaction.response.edit_message(content='Refreshing room...')
        # await interaction.response.defer()
        msg = InteractionUtils.create_proxy_msg(interaction, [self.view.trigger_command])
        # Stats.log_command('vr')

        data = await commands.OtherCommands.vr_command(msg, self.bot, msg.content.split(), self_refresh=True)
            
        await self.view.refresh_vr(interaction, data)

class VRView(discord.ui.View):
    def __init__(self, trigger_command, bot: TableBot.ChannelBot):
        super().__init__(timeout=300)
        self.bot = bot
        self.trigger_command = trigger_command
        self.message: discord.Message = None
        self.last_vr_content = None

        self.add_item(UpdateVRButton(self.bot))
    
    async def refresh_vr(self, interaction: discord.Interaction, data: Dict[str, str]):
        super().__init__(timeout=300)
        self.add_item(UpdateVRButton(self.bot))

        content = data['content']

        if 'error' in data:
            content += '\n' + self.last_vr_content
        else:
            self.last_vr_content = content
        
        # await interaction.followup.edit_message(self.message.id, content=content, view=self)
        await common.safe_edit(self.message, content=content, view=self)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        cooldown_active = self.bot.getRLCooldownSeconds() > 0
        if cooldown_active:
            await interaction.response.send_message(f"The VR command is on cooldown. Please wait {self.bot.getRLCooldownSeconds()} more seconds.", 
                                                        ephemeral=True, delete_after=3.0)
            return False

        return True
    
    async def on_timeout(self) -> None:
        self.clear_items()
        self.stop()
        if self.message:
            await common.safe_edit(self.message, view=None)
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)

    async def send(self, messageable, content=None, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel

        self.last_vr_content = content
        self.message = await messageable.send(content=content, file=file, embed=embed, view=self)
        return self.message

#######################################################################################################


class RejectButton(discord.ui.Button['SuggestionView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Discard")
    
    async def callback(self, interaction: discord.Interaction):
        if self.view.current_error['id'] in self.view.responded:
            return

        self.view.responded.add(self.view.current_error['id'])
        self.view.bot.resolved_errors.add(self.view.current_error['id'])
        try:
            self.view.errors.pop()
        except IndexError:
            pass

        await self.view.next_suggestion(interaction=interaction)

class SuggestionButton(discord.ui.Button['SuggestionView']):
    def __init__(self, error, label, value=None, confirm=False):
        self.error = error #dict of error information
        self.confirm = confirm
        self.value = value
        if not confirm: 
            label = f"R{self.error['race']}: "+label
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=confirm)
    
    async def callback(self, interaction: discord.Interaction):
        if self.error['id'] in self.view.responded: # don't process callback if the error has been responded to
            return

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
        }
        
        command_mes = await command_mapping[self.error['type']](message, self.view.bot, args, server_prefix, self.view.is_lounge, dont_send=True)
        author_str = interaction.user.display_name

        self.view.responded.add(self.view.current_error['id'])

        await self.view.message.channel.send(f"{author_str} - "+command_mes)
        self.view.bot.semi_resolved_errors.add(self.view.current_error['id'])

        try:
            self.view.errors.pop()
        except IndexError:
            pass #rare case where it hits here (people click the button at almost the exact same time), error should be ignored
        
        await self.view.next_suggestion(interaction=interaction)

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
        self.is_lounge = lounge
        self.selected_values = None
        self.message = None
        self.responded = set()

        self.bot.getRoom().watch_suggestions(self, errors, self.bot.channel_id)
        self.errors = self.bot.getRoom().suggestion_errors
        self.current_error = self.errors[-1]
        self.create_suggestion()

    async def on_timeout(self) -> None:
        try:
            await self.message.delete()
        except:
            pass
        self.stop()
        self.clear_items()
        try:
            self.bot.getRoom().stop_watching_suggestions()
        except AttributeError: # room has already been destroyed/cleaned up
            pass

    async def refresh_suggestions(self):
        """Race removal happened, so buttons must be updated."""
        self.errors = self.bot.getRoom().suggestion_errors
        # print(self.errors)
        await self.next_suggestion()
    
    async def next_suggestion(self, interaction: discord.Interaction = None):
        if len(self.errors) > 0:
            self.current_error = self.errors[-1]
            content = f"**Suggested Fix ({ERROR_TYPE_DESCRIPTIONS[self.current_error['type']]}):**"
            self.clear_items()
            self.create_suggestion()

            if interaction:
                await interaction.response.defer()  # needed to force webhook message edit route for files kwarg support
                await interaction.followup.edit_message(
                    message_id=self.message.id,
                    content=content,
                    view=self
                )
            else:
                await common.safe_edit(self.message, content=content, view=self)
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
        

        elif err_type in {'missing_player', 'blank_player'}:
            for insert in ['during', 'before']:
                label = label_builder.format(error['player_name'], insert)
                self.add_item(SuggestionButton(error, label, value=insert))
        
        elif err_type == 'large_time':
            for place in error['placements']:
                for insert in ["placed"]:
                    label = label_builder.format(error['player_name'], insert, UtilityFunctions.place_to_str(place))
                    self.add_item(SuggestionButton(error, label, value=place))
        
        elif err_type == 'tie':
            for insert in error['placements']:
                label = label_builder.format(error['player_name'], UtilityFunctions.place_to_str(insert))
                self.add_item(SuggestionButton(error, label, value=insert))
        
        self.add_item(RejectButton())
    
    def enable_confirm(self):
        for child in self.children:
            child.disabled=False
    
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await InteractionUtils.on_component_error(error, interaction, self.prefix, self.bot)
        
    async def send(self, messageable, file=None, embed=None):
        if hasattr(messageable, 'channel'):
            messageable = messageable.channel
        
        self.bot.add_sug_view(self)

        self.message: discord.Message = await messageable.send(content=f"**Suggested Fix ({ERROR_TYPE_DESCRIPTIONS[self.current_error['type']]}):**", file=file, embed=embed, view=self)
        return self.message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        can_interact = interaction.channel.permissions_for(interaction.user).send_messages
        if not can_interact:
            await interaction.response.send_message("You cannot interact with this.", ephemeral=True)
            return False

        allowed = InteractionUtils.commandIsAllowed(self.is_lounge, interaction.user, self.bot, 'restricted_interaction', is_interaction=True) # InteractionUtils.convert_key_to_command(self.current_error['type'])
        if not allowed: 
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True, delete_after=3.0)
            return False
        
        if self.current_error['id'] in self.responded:
            await interaction.response.send_message("This button has already been used.", ephemeral=True)
            return False

        return allowed


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
    
    elif err_type in {'missing_player', 'blank_player'}:
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
