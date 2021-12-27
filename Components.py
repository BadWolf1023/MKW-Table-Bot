import discord
import commands

class ConfirmButton(discord.ui.Button['ConfirmView']):
    def __init__(self, cat):
        self.cat = cat
        buttonType = discord.ButtonStyle.success if cat=='yes' else discord.ButtonStyle.danger
        emoji = "Yes" if cat == 'yes' else "No"
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
                    
            if len(players) != this_bot.getWar().get_num_players():
                await interaction.response.edit_message(view=self.view)
                await interaction.followup.send(content=f'''Respond "{server_prefix}no" when asked ***Is this correct?*** - the number of players in the room doesn't match your war format and teams. Trying to still start war, but teams will be incorrect.''')
                
            this_bot.getWar().setTeams(this_bot.getWar().getConvertedTempTeams())
            view = PictureView(this_bot, server_prefix, self.view.lounge)
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(content=this_bot.get_room_started_message(), view=view)

class ConfirmView(discord.ui.View):
    def __init__(self, bot, prefix, lounge):
        super().__init__()
        self.bot = bot
        self.prefix = prefix
        self.lounge = lounge
        self.add_item(ConfirmButton('yes'))
        self.add_item(ConfirmButton('no'))


#######################################################


class PictureButton(discord.ui.Button['PictureView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label='Picture')

    async def callback(self, interaction: discord.Interaction):
        # for child in self.view.children:
        #     child.disabled=True
        
        # self.view.stop()

        msg = create_proxy_msg(interaction, ['wp'])
        await interaction.response.edit_message(view=self.view) # view=none? but maybe it's good to allow people to click them whenever (since there is a cooldown on ?wp)
        await commands.TablingCommands.war_picture_command(msg, self.view.bot, ['wp'], self.view.prefix, self.view.lounge)

class PictureView(discord.ui.View):
    def __init__(self, bot, prefix, is_lounge_server):
        super().__init__(timeout=600)
        self.bot = bot
        self.prefix = prefix
        self.lounge = is_lounge_server
        self.add_item(PictureButton())


#############################################################

class RejectButton(discord.ui.Button['SuggestionView']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Discard Suggestion", row=3)
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        
        self.view.stop()
        self.view.bot.resolved_errors.append(self.view.index)

        await interaction.response.edit_message(content='Suggestion discarded.', view=None)

class SuggestionButton(discord.ui.Button['SuggestionView']):
    def __init__(self, error, label, confirm=False):
        self.error = error #dict of error information
        self.confirm = confirm
        self.text = label
        super().__init__(style=discord.ButtonStyle.primary, label=label, row=2 if confirm else 1, disabled=confirm)
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        
        self.view.stop()

        this_bot = self.view.bot
        server_prefix = self.view.prefix

        args = get_command_args(self.error, self.text if not self.confirm else self.view.selected_values, self.view.bot)
        message = create_proxy_msg(interaction, args)

        command_mapping = {
            "blank_player": commands.TablingCommands.change_room_size_command,
            "gp_missing": commands.TablingCommands.change_room_size_command,
            ("gp_missing", 1): commands.TablingCommands.early_dc_command,
            "tie": commands.TablingCommands.quick_edit_command,
            "large_time": commands.TablingCommands.quick_edit_command,
            "missing_player": commands.TablingCommands.disconnections_command
        }

        command_mes = await command_mapping[self.error['type']](message, self.view.bot, args, server_prefix, self.view.lounge, dont_send=True)
        if self.error['type'] == 'tie':
            try:
                await interaction.response.send_message(content=command_mes, view=None)
            except: #if the interaction has already been responded to, will throw error and need to followup instead
                await interaction.followup.send(command_mes)
        else:
            await interaction.response.edit_message(content=command_mes, view=None)

class SuggestionSelectMenu(discord.ui.Select['SuggestionView']):
    def __init__(self, values, name=None):
        options = [discord.SelectOption(label=str(value)) for value in values] if not name else\
                    [discord.SelectOption(label=str(place)+" "+name,value=place) for place in values] #for 'tie' only
        super().__init__(placeholder=name if name else "Select room size", options=options)
    
    async def callback(interaction: discord.Interaction):
        self.view.selected_values = interaction.data['values'][0]
        self.view.enable_confirm()
        await interaction.response.edit_message(view=self.view)

LABEL_BUILDERS = {
    'missing_player': '{} DCed *{}* race {}',
    'blank_player': 'Change Room Size',
    'tie': 'Confirm Placements',
    'large_time': 'Confirm Placements',
    'gp_missing': 'Change Room Size',
    ('gp_missing', 1): 'Missing player early DCed *{}* race {}'
}

class SuggestionView(discord.ui.View):
    def __init__(self, error, bot, prefix, lounge, index):
        super().__init__(timeout=300)
        self.bot = bot
        self.prefix = prefix
        self.error = error
        self.lounge = lounge
        self.index = index
        self.selected_values = []

        self.create_row()
    
    def create_row(self):
        error = self.error
        err_type = error['type']
        label_builder = LABEL_BUILDERS[err_type]

        if err_type == 'gp_missing':
            if error['num_missing'] == 1:
                label_builder = LABEL_BUILDERS[(err_type, 1)]
                error['type'] = (err_type, 1)
                for insert in ['on', 'before']:
                    label = label_builder.format(insert, error['race'])
                    self.add_item(SuggestionButton(error, label))
            else:
                label = label_builder
                self.add_item(SuggestionSelectMenu(error['corrected_room_sizes']))
                self.add_item(SuggestionButton(error, label, confirm=True))
        
        elif err_type == 'blank_player':
            label = label_builder
            self.add_item(SuggestionSelectMenu(error['corrected_room_sizes']))
            self.add_item(SuggestionButton(error, label, confirm=True))

        elif err_type == 'missing_player':
            for insert in ['on', 'before']:
                label = label_builder.format(error['player_name'], insert, error['race'])
                self.add_item(SuggestionButton(error, label))
        
        elif err_type == 'large_time':
            label = label_builder
            self.add_item(SuggestionSelectMenu(error['placements']))
            self.add_item(SuggestionButton(error, label, comfirm=True))
        
        elif err_type == 'tie':
            label = label_builder
            players = error['player_names']
            for p in players:
                self.add_item(SuggestionSelectMenu(error['placements'], p))
            self.add_item(SuggestionButton(error, label, confirm=True))
        
        self.add_item(RejectButton())
    
    def enable_confirm(self):
        if self.error['type'] in {'tie'} and (self.selected_values!=len(self.error['player_names']) or len(self.error['placements']) > len(set(self.selected_values))):
            return

        for child in self.children:
            child.disabled=False


def get_command_args(error, info, bot):
    err_type = error['type']

    if err_type == ('gp_missing', 1):
        GP = int((error['race']-1)/4) + 1
        time = "on" if "DCed *on*" in info else "before"
        args = ['earlydc', str(GP), time]
    
    elif err_type == 'gp_missing':
        race = error['race']
        room_size = str(info)
        args = ['changeroomsize', race, room_size]
    
    elif err_type == 'blank_player':
        race = error['race']
        room_size = str(info)
        args = ['changeroomsize', str(race), room_size]
    
    elif err_type == 'missing_player':
        playerNum = bot.player_to_dc_num(error['player_fc'])

        time = "on" if "DCed *on*" in info else "before"
        args = ['dc', str(playerNum), time]
    
    elif err_type == 'large_time':
        playerNum = bot.player_to_num(error['player_fc'])
        placement = str(info)
        args = ['changeplace', str(playerNum), placement]
    
    elif err_type == 'tie':
        playerNum = bot.player_to_num(error['player_fc'])
        placement = str(info)
        args = ['changeplace', str(playerNum), placement]
    
    return args

def create_proxy_msg(interaction, args=None):
    proxyMsg = discord.Object(id=interaction.id)
    proxyMsg.channel = interaction.channel
    proxyMsg.guild = interaction.guild
    proxyMsg.content = build_msg_content(interaction.data, args)
    proxyMsg.author = interaction.user
    proxyMsg.raw_mentions = []
    for i in proxyMsg.content:
        if i.startswith('<@') and i.endswith('>'):
            proxyMsg.raw_mentions.append(i)
    
    return proxyMsg

def build_msg_content(data, args = None):
    if args: return '/' + ' '.join(args)

    args = [data.get('name', '')]
    raw_args = data.get('options', [])
    for arg in raw_args: 
        args.append(str(arg.get('value', '')))
    return '/' + ' '.join(args)