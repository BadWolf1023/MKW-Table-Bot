import discord
import common
import InteractionExceptions

def check_lounge_server(message):
    return message.guild.id == common.MKW_LOUNGE_SERVER_ID

def check_beta_server(message):
    return message.guild.id == common.MKW_LOUNGE_SERVER_ID

def check_lounge_server_id(id):
    return id == common.MKW_LOUNGE_SERVER_ID

def check_beta_server_id(id):
    return check_lounge_server_id(id)

def bot_admin_check(ctx: discord.ApplicationContext):
    can = common.is_bot_admin(ctx.author)
    if not can:
        raise InteractionExceptions.NoPermission() 

def commandIsAllowed(isLoungeServer:bool, message_author:discord.Member, this_bot, command:str):
    if not isLoungeServer:
        return True
    
    if common.author_is_table_bot_support_plus(message_author):
        return True
    
    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().canModifyTable(message_author.id) #Fixed! Check ALL people who can modify table, not just the person who started it!
    
    if command not in common.needPermissionCommands:
        return True
    
    if this_bot is None or not this_bot.is_table_loaded() or not this_bot.getRoom().is_freed:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    return this_bot.getRoom().canModifyTable(message_author.id)

def convert_key_to_command(key):
    map = {
        'blank_player': 'dc',
        'missing_player': 'dc',
        'gp_missing': 'changeroomsize',
        'gp_missing_1': 'dc',
        'tie': 'changeposition',
        'large_time': 'changeposition'
    }
    return map[key]


class MessageWrapper():
    def __init__(self,msg, ctx):
        self.msg = msg
        self.ctx = ctx

    async def delete(self):
        await self.msg.edit("\u200b")
        if self.ctx:
            self.ctx.responded = False

    def __getattr__(self,attr):
        return self.msg.__getattribute__(attr)

class ChannelWrapper():
    def __init__(self,channel, ctx):
        self.channel = channel
        self.ctx = ctx
        if self.ctx:
            self.ctx.responded = False
        self.message = None

    async def send(self,*args,**args2):
        if self.ctx and not self.ctx.responded:
            if self.message:
                await self.message.edit(*args, **args2)
                return self.message

            self.ctx.responded = True
            msg = await (await self.ctx.respond(*args,**args2)).original_message()
            msg = MessageWrapper(msg, self.ctx)

            self.message = msg
            return msg
        else:
            return await self.channel.send(*args,**args2)

    def __getattr__(self,attr):
        return self.channel.__getattribute__(attr)

def create_proxy_msg(interaction, args=None, ctx=None):
    proxyMsg = discord.Object(id=interaction.id)

    proxyMsg.channel = ChannelWrapper(interaction.channel, ctx)
    proxyMsg.guild = interaction.guild
    proxyMsg.content = build_msg_content(interaction.data, args)
    proxyMsg.author = interaction.user
    proxyMsg.proxy = True
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