import discord
import BadWolfBot as BWB
import common
import AbuseTracking
import InteractionExceptions


def check_lounge_server(message):
    return message.guild.id == common.MKW_LOUNGE_SERVER_ID

def bot_admin_check(ctx: discord.ApplicationContext):
    can = common.is_bot_admin(ctx.author)
    if not can:
        raise InteractionExceptions.NoPermission()

async def on_interaction_check(interaction):
    if interaction.type != discord.InteractionType.application_command:
        return

    message = create_proxy_msg(interaction)

    is_lounge_server = check_lounge_server(message)

    await AbuseTracking.blacklisted_user_check(message)
    await AbuseTracking.abuse_track_check(message)
                
    BWB.log_command_sent(message)
    
    this_bot = BWB.check_create_channel_bot(message)
    this_bot.updatedLastUsed()
    if is_lounge_server and this_bot.isFinishedLounge():
        this_bot.freeLock()
    
    if not BWB.commandIsAllowed(is_lounge_server, message.author, this_bot, interaction.data.get('name')):
        await BWB.send_lounge_locked_message(message, this_bot)

    return interaction.data['name'], message, this_bot, '/', is_lounge_server 

def create_proxy_msg(interaction: discord.Interaction, args=None):
    proxyMsg = discord.Object(id=interaction.id)
    proxyMsg.channel = interaction.channel
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