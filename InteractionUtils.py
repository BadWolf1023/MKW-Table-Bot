import asyncio
import discord
import SmartTypes as ST
import common

def simulating_lounge_server(message_or_interaction):
    if common.is_beta and check_beta_server(message_or_interaction):
        return True
    return check_lounge_server(message_or_interaction)

def check_lounge_server(message_or_interaction):
    return message_or_interaction.guild.id == common.MKW_LOUNGE_SERVER_ID

def check_beta_server(message_or_interaction):
    return message_or_interaction.guild.id == common.TABLE_BOT_DISCORD_SERVER_ID

def bot_admin_check(ctx: discord.ApplicationContext):
    can = common.is_bot_admin(ctx.author)
    return can 

def commandIsAllowed(*args, **kwargs):
    return common.main.commandIsAllowed(*args, **kwargs)

def convert_key_to_command(key):
    map = {
        'blank_player': 'dc',
        'missing_player': 'dc',
        'gp_missing': 'changeroomsize',
        'gp_missing_1': 'earlydc',
        'tie': 'changeposition',
        'large_time': 'changeposition'
    }
    return map[key]

async def safe_defer(ctx: discord.ApplicationContext):
    try:
        await asyncio.sleep(1.5)
        if not ctx.responded:
            await ctx.defer()
    except:
        pass

class ChannelWrapper():
    def __init__(self, channel, ctx: discord.ApplicationContext):
        self.channel = channel
        self.ctx = ctx
        if self.ctx:
            self.ctx.responded = False
            asyncio.create_task(safe_defer(ctx))

    async def send(self,*args,**kwargs):
        if self.ctx and not self.ctx.responded:
            self.ctx.responded = True
            try:
                msg = await self.ctx.respond(*args,**kwargs)
            except:
                return await self.channel.send(*args,**kwargs)
            if isinstance(msg, discord.WebhookMessage):
                return msg
            return await msg.original_message()
        else:
            return await self.channel.send(*args,**kwargs)

    def __getattr__(self,attr):
        return self.channel.__getattribute__(attr)

def create_proxy_msg(interaction: discord.Interaction, args=None, ctx=None):
    proxyMsg = discord.Object(id=interaction.id)
    #print(interaction)
    #for attr in dir(interaction):
    #    try:
    #        print(f"{attr}: {getattr(interaction, attr)}")
    #    except:
    #        print(f"Can't get value for: {attr}")
    proxyMsg.channel = ChannelWrapper(interaction.channel, ctx)
    proxyMsg.guild = interaction.guild
    proxyMsg.content = build_msg_content(interaction.data, args)
    proxyMsg.author = interaction.user
    proxyMsg.proxy = True
    proxyMsg.mentions = build_mentions(interaction.data)
    return proxyMsg

def build_msg_content(data, args=None):
    if args: 
        return '/' + ' '.join(args)

    args = [data.get('name', '')]
    raw_args = data.get('options', [])
    for arg in raw_args: 
        args.append(str(arg.get('value', '')))
    return '/' + ' '.join(args)

def build_mentions(data):
    result = []
    found_discord_ids = []
    for option in data.get('options', []):
        smart_type_value = ST.SmartLookupTypes(option.get('value', ''))
        if smart_type_value.is_discord_mention():
            found_discord_ids.append(smart_type_value.modified_original)

    resolved_data = data.get('resolved', {})
    if not resolved_data:
        return result

    users = resolved_data.get('users', {})
    members = resolved_data.get('members', {})
    for discord_id in found_discord_ids:
        user_json = users.get(discord_id, None)
        member_json = members.get(discord_id, None)
        if user_json is None:
            continue
        user = discord.User(state=None, data=user_json)
        if member_json is not None:
            nickname = member_json.get('nick', None)
            if nickname is not None:
                user.name = nickname
        result.append(user)
    return result

async def on_component_error(error: Exception, interaction: discord.Interaction, prefix: str, channel_bot):
    message = None

    if interaction.message:
        message = interaction.message
    if not message:
        try:
            message = await interaction.original_message()
        except Exception:
            pass
    
    if message:
        await handle_component_exception(error, message, prefix, channel_bot)
    else:
        common.log_error("Exception raised on Component interaction could not be caught because there was no message from the interaction. THIS IS A BUG.")
        common.log_traceback("NO MESSAGE FROM INTERACTION ERROR. InteractionUtils.py -> on_component_error()")
        await common.safe_send(message,
                                f"Internal bot error. This exception occurred and could not be handled: no message from interaction on_error(). Try `/reset`. Please report this error at the MKW Table Bot server: https://discord.gg/K937DqM")

async def handle_component_exception(error, message, server_prefix, channel_bot):
    await common.client.handle_exception(error,message,server_prefix, channel_bot)
