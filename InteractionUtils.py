import discord
import BadWolfBot
import common
import TableBotExceptions
import aiohttp
import traceback

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
    return can 

def commandIsAllowed(isLoungeServer:bool, message_author:discord.Member, this_bot, command:str):
    if not isLoungeServer:
        return True
    
    if common.author_is_table_bot_support_plus(message_author):
        return True
    
    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().canModifyTable(message_author.id) #Check ALL people who can modify table
    
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
    def __init__(self,channel, ctx: discord.ApplicationContext):
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

def create_proxy_msg(interaction: discord.Interaction, args=None, ctx=None):
    proxyMsg = discord.Object(id=interaction.id)

    proxyMsg.channel = ChannelWrapper(interaction.channel, ctx)
    proxyMsg.guild = interaction.guild
    proxyMsg.content = build_msg_content(interaction.data, args)
    proxyMsg.author = interaction.user
    proxyMsg.proxy = True
    proxyMsg.raw_mentions = []

    for i in proxyMsg.content.split(' '):
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

async def on_component_error(error: Exception, interaction: discord.Interaction, prefix):
    message = None
    if interaction.message:
        message = interaction.message
    elif await interaction.original_message():
        message = await interaction.original_message()
    
    if message:
        await handle_component_exception(error, message, prefix)
    else:
        common.log_error("Exception raised on Component interaction could not be caught because there was no message from the interaction. THIS IS A BUG AND NEEDS TO BE FIXED.")
        await common.safe_send(message,
                                f"Internal bot error. This exception occurred and could not be handled: {error}. Try `/reset`. Please report this error at the MKW Table Bot server: https://discord.gg/K937DqM")
            
async def handle_component_exception(error, message, server_prefix):
    try:
        raise error
    except (discord.errors.Forbidden):
        # self.lounge_submissions.clear_user_cooldown(message.author)
        await common.safe_send(message,
                                "MKW Table Bot is missing permissions and cannot do this command. Contact your admins. The bot needs the following permissions:\n- Send Messages\n- Read Message History\n- Manage Messages (Lounge only)\n- Add Reactions\n- Manage Reactions\n- Embed Links\n- Attach files\n\nIf the bot has all of these permissions, make sure you're not overriding them with a role's permissions. If you can't figure out your role permissions, granting the bot Administrator role should work. If none of these work, this is a bot permissions error with Discord.")
    except TableBotExceptions.BlacklistedUser:
        BadWolfBot.log_command_sent(message)
    except TableBotExceptions.WarnedUser:
        BadWolfBot.log_command_sent(message)
    except TableBotExceptions.TableNotLoaded as not_loaded:
        await common.safe_send(message,f"{not_loaded}")
    except TableBotExceptions.NotBadWolf as not_bad_wolf_exception:
        await common.safe_send(message,f"You are not Bad Wolf: {not_bad_wolf_exception}")
    except TableBotExceptions.NotLoungeStaff:
        await common.safe_send(message,f"Not a valid command. For more help, do the command: {server_prefix}help")
    except TableBotExceptions.NotBotAdmin as not_bot_admin_exception:
        await common.safe_send(message,f"You are not a bot admin: {not_bot_admin_exception}")
    except TableBotExceptions.NotServerAdministrator as not_admin_failure:
        await common.safe_send(message,f"You are not a server administrator: {not_admin_failure}")
    except TableBotExceptions.NotStaff as not_staff_exception:
        await common.safe_send(message,f"You are not staff in this server: {not_staff_exception}")
    except TableBotExceptions.WrongServer as wrong_server_exception:
        if common.running_beta:
            await common.safe_send(message,
                                    f"{wrong_server_exception}: **I am not <@735782213118853180>. Use <@735782213118853180> in <#389521626645004302> to submit your table.**")
        else:
            await message.channel.send(f"Not a valid command. For more help, do the command: `{server_prefix}help`")
    except TableBotExceptions.WrongUpdaterChannel as wrong_updater_channel_exception:
        await common.safe_send(message,
                                f"Use this command in the appropriate updater channel: {wrong_updater_channel_exception}")
    except TableBotExceptions.WarSetupStillRunning:
        await common.safe_send(message,
                                f"I'm still trying to set up your war. Please wait until I respond with a confirmation. If you think it has been too long since I've responded, you can try ?reset and start your war again.")
    except discord.errors.DiscordServerError:
        await common.safe_send(message,
                                "Discord's servers are either down or struggling, so I cannot send table pictures right now. Wait a few minutes for the issue to resolve.")
    except aiohttp.ClientOSError:
        await common.safe_send(message,
                                "Either Wiimmfi, Lounge, or Discord's servers had an error. This is usually temporary, so do your command again.")
        raise
    except TableBotExceptions.WiimmfiSiteFailure:
        logging_info = BadWolfBot.log_command_sent(message,extra_text="Error info: MKWX inaccessible, other error.")
        await common.safe_send(message,
                                "Cannot access Wiimmfi's mkwx. I'm either blocked by Cloudflare, or the website is down.")
        # await self.send_to_503_channel(logging_info)
    except TableBotExceptions.CommandDisabled:
        await common.safe_send(message,"This command has been disabled.")
    except (TableBotExceptions.CommandNotFound):
        await common.safe_send(message,f"Not a valid command. For more help, do the command: `{server_prefix}help`")
    except Exception as e:
        common.log_traceback(traceback)
        # self.lounge_submissions.clear_user_cooldown(message.author)
        await common.safe_send(message,
                                f"Internal bot error. An unknown problem occurred. Please wait 1 minute before sending another command. If this issue continues, try: `{server_prefix}reset`")
        raise e
