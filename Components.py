import discord
import commands
import InteractionUtils

class ConfirmButton(discord.ui.Button['ConfirmView']):
    def __init__(self, cat):
        self.cat = cat
        buttonType = discord.ButtonStyle.success if cat=='yes' else discord.ButtonStyle.danger
        emoji = "✔" if cat == 'yes' else "✘"
        super().__init__(style=buttonType, label=emoji, row=1)
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        
        self.view.stop()

        this_bot = self.view.bot
        server_prefix = self.view.prefix

        if this_bot.prev_command_sw is False:
            return await interaction.response.edit_message(view=self.view)

        this_bot.prev_command_sw = False
        if self.cat == 'no':
            this_bot.manualWarSetUp = True
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(content=f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  *{server_prefix}A 2 3 / B 1 4 / Player 5 6*"
                                            )
            
        else:
            if this_bot.getRoom() is None or not this_bot.getRoom().is_initialized():
                await interaction.response.edit_message(view=self.view)
                await interaction.followup.send(content=f"Unexpected error. Somehow, there is no room loaded. War stopped. Recommend the command: {server_prefix}reset")
                this_bot.setWar(None)
                return
    
            numGPS = this_bot.getWar().numberOfGPs
            players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numGPS*4).items())
            this_bot.getWar().setTeams(this_bot.getWar().getConvertedTempTeams())

            view = PictureView(this_bot, server_prefix, self.view.lounge)
                    
            if len(players) != this_bot.getWar().get_num_players():
                await interaction.response.edit_message(view=self.view)
                
                return await interaction.followup.send(content=f'''**Warning:** *the number of players in the room doesn't match your war format and teams. **Table started, but teams might be incorrect.***'''
                                                + '\n' + this_bot.get_room_started_message(), view=view)

            try:
                await interaction.response.edit_message(view=self.view)
            except:
                pass 
            
            await interaction.followup.send(content=this_bot.get_room_started_message(), view=view)

class ConfirmView(discord.ui.View):
    def __init__(self, bot, prefix, lounge):
        super().__init__()
        self.bot = bot
        self.prefix = prefix
        self.lounge = lounge
        self.add_item(ConfirmButton('yes'))
        self.add_item(ConfirmButton('no'))


###########################################################################################


class PictureButton(discord.ui.Button['PictureView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label='Picture')

    async def callback(self, interaction: discord.Interaction):
        msg = InteractionUtils.create_proxy_msg(interaction, ['wp'])
        await interaction.response.edit_message(view=self.view) # view=none? but maybe it's good to allow people to click them whenever (since there is a cooldown on ?wp)
        await commands.TablingCommands.war_picture_command(msg, self.view.bot, ['wp'], self.view.prefix, self.view.lounge)

class PictureView(discord.ui.View):
    def __init__(self, bot, prefix, is_lounge_server):
        super().__init__(timeout=600)
        self.bot = bot
        self.prefix = prefix
        self.lounge = is_lounge_server
        self.add_item(PictureButton())


###########################################################################################


class RejectButton(discord.ui.Button['SuggestionView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Discard Suggestion", row=3)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.bot.resolved_errors.add(self.view.index)

        await self.view.update_message("Suggestion discarded.")
        

class SuggestionButton(discord.ui.Button['SuggestionView']):
    def __init__(self, error, label, confirm=False):
        self.error = error #dict of error information
        self.confirm = confirm
        self.text = label
        super().__init__(style=discord.ButtonStyle.primary, label=label, row=2 if confirm else 1, disabled=confirm)
    
    async def callback(self, interaction: discord.Interaction):
        server_prefix = self.view.prefix

        args = get_command_args(self.error, self.text if not self.confirm else self.view.selected_values, self.view.bot)
        message = InteractionUtils.create_proxy_msg(interaction, args)

        command_mapping = {
            # "blank_player": commands.TablingCommands.change_room_size_command,
            "blank_player": commands.TablingCommands.disconnections_command,
            "gp_missing": commands.TablingCommands.change_room_size_command,
            ("gp_missing", 1): commands.TablingCommands.early_dc_command,
            "tie": commands.TablingCommands.quick_edit_command,
            "large_time": commands.TablingCommands.quick_edit_command,
            "missing_player": commands.TablingCommands.disconnections_command
        }
        if self.error['type'] == 'tie': 
            self.resolved
        command_mes = await command_mapping[self.error['type']](message, self.view.bot, args, server_prefix, self.view.lounge, dont_send=True)
        author_str = interaction.user.mention
        await self.view.update_message(f"{author_str}: "+command_mes)

class SuggestionSelectMenu(discord.ui.Select['SuggestionView']):
    def __init__(self, values, name):
        options = [discord.SelectOption(label=str(value)) for value in values]
        super().__init__(placeholder=name, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.update_selection_value(interaction.data['values'][0])
        self.placeholder = self.view.selected_values 

        self.view.enable_confirm()
        try:
            await interaction.response.edit_message(view=self.view)
        except: 
            pass

LABEL_BUILDERS = {
    'missing_player': '{} DCed *{}* race {}',
    # 'blank_player': 'Change Room Size',
    'blank_player': "{} DCed *{}* race {}",
    'tie': 'Confirm Placement',
    'large_time': 'Confirm Placement',
    'gp_missing': 'Change Room Size',
    ('gp_missing', 1): 'Missing player early DCed *{}* race {}'
}

class SuggestionView(discord.ui.View):
    def __init__(self, error, bot, prefix, lounge, id=None):
        super().__init__(timeout=120)
        self.bot = bot
        self.prefix = prefix
        self.error = error
        self.lounge = lounge
        self.index = id if id else self.error['id']
        self.selected_values = None

        self.create_row()
    
    def create_row(self):
        error = self.error
        err_type = error['type']
        label_builder = LABEL_BUILDERS[err_type]

        if err_type == 'gp_missing':
            if error['num_missing'] == 1:
                label_builder = LABEL_BUILDERS[(err_type, 1)]
                error['type'] = (err_type, 1)
                for insert in ['during', 'before']:
                    label = label_builder.format(insert, error['race'])
                    self.add_item(SuggestionButton(error, label))
            else:
                label = label_builder
                self.add_item(SuggestionSelectMenu(error['corrected_room_sizes'], name="Select correct room size"))
                self.add_item(SuggestionButton(error, label, confirm=True))
        

        elif err_type in { 'missing_player', 'blank_player' }:
            for insert in ['during', 'before']:
                label = label_builder.format(error['player_name'], insert, error['race'])
                self.add_item(SuggestionButton(error, label))
        
        elif err_type == 'large_time':
            label = label_builder
            self.add_item(SuggestionSelectMenu(error['placements'], name="Choose correct position"))
            self.add_item(SuggestionButton(error, label, confirm=True))
        
        elif err_type == 'tie':
            label = label_builder
            self.add_item(SuggestionSelectMenu(error['placements'], name="Choose correct position"))
            self.add_item(SuggestionButton(error, label, confirm=True))
        
        self.add_item(RejectButton())
    
    def enable_confirm(self):
        # if self.error['type'] in {'tie'} and (self.selected_values!=len(self.error['player_names']) or len(self.error['placements']) > len(set(self.selected_values))):
        #     return

        for child in self.children:
            child.disabled=False


def get_command_args(error, info, bot):
    err_type = error['type']

    if err_type == ('gp_missing', 1):
        GP = int((error['race']-1)/4) + 1
        time = "on" if "DCed *during*" in info else "before"
        args = ['earlydc', str(GP), time]
    
    elif err_type == 'gp_missing':
        race = error['race']
        room_size = str(info)
        args = ['changeroomsize', str(race), room_size]
    
    elif err_type in { 'missing_player', 'blank_player' }:
        playerNum = bot.player_to_dc_num(error['race'], error['player_fc'])

        time = "on" if "DCed *during*" in info else "before"
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
        print(placement)
        args = ['changeplace', str(playerNum), str(race), placement]
    
    return args
