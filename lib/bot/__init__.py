from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from asyncio import sleep
from datetime import datetime
from discord import DMChannel, Embed, File, Intents, Permissions, Role, utils
from discord.errors import HTTPException, Forbidden
from discord.ext.commands import Bot as Botbase
from discord.ext.commands import (BadArgument, command, Cog, CommandNotFound, CommandOnCooldown,
                                 Context, has_permissions, MissingRequiredArgument, when_mentioned_or
                                 )
from glob import glob
from ..db import db
from pandas import DataFrame, read_excel

OWNER_IDS = set()
COGS = [path.split('\\')[-1][:-3] for path in glob('./lib/cogs/*.py')]

def get_prefix(bot, message):
    prefix = db.field("SELECT Prefix FROM war_guild WHERE GuildID = ?", message.guild.id)
    return when_mentioned_or(prefix)(bot, message)

async def bot_start(self):
    if not self.ready:
        self.guild = self.get_guild(db.record('SELECT GuildID FROM war_guild'))
        self.stdout = self.get_channel(db.record('SELECT ChannelID FROM channels WHERE ChannelUsage = "staff-room"'))
        self.owner_ids = OWNER_IDS
        self.scheduler.add_job(self.rules_reminder, CronTrigger(hour='3,9,15,21', minute=0, second=0))
        self.scheduler.start()
        self.update_db()

        while not self.cogs_ready.all_ready():
            await sleep(0.5)
        await self.stdout.send('Now online!')
        embed = Embed(title='Now online!', description='Grail has been set! Players should have their servant to take part in this.',
                      colour=0xDD9767, timestamp=datetime.utcnow())            
            # embed.set_image(url='https://cdnb.artstation.com/p/assets/images/images/014/599/369/large/daniel-kuchar-traindummy.jpg?1544641253')
        await self.stdout.send(embed=embed)
        self.ready = True
        print('bot ready')
        # meta = self.get_cog('Meta')
        # await meta.set()

    else:
        print('ready and willing!')


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f' {cog} cog ready')

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Bot(Botbase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=get_prefix,
            owner_ids=OWNER_IDS,
            intents=Intents.all()
        )

    def setup(self):
        for cog in COGS:
            self.load_extension(f'lib.cogs.{cog}')
            print(f' {cog} cog loaded')

    def update_db(self):
        db.multiexec('INSERT OR IGNORE INTO war_guild (GuildID) VALUES (?)',
                     ((guild.id,) for guild in self.war_guild))
        db.multiexec('INSERT OR IGNORE INTO members (UserID) VALUES (?)',
                     ((member.id,) for member in self.guild.members if not member.bot))
        to_remove = []
        stored_members = db.column('SELECT UserID FROM members')
        for id_ in stored_members:
            if not self.guild.get_member(id_):
                to_remove.append(id_)
        db.multiexec('DELETE FROM members WHERE UserID = ?',((id_,) for id_ in to_remove))
        db.commit()

    def run(self,version):
        self.VERSION = version
        print('running setup...')
        self.setup()
        with open('./lib/bot/token.0', 'r', encoding='utf-8') as tf:
            self.TOKEN = tf.read()
        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)
        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else: 
                await ctx.send("I'm not ready to receive commands. Please wait few seconds.")
            
    async def rules_reminder(self):
        await self.stdout.send('Ze Lady wants you to behave!')

    async def on_connect(self):
        print("bot connected")

    async def on_disconnect(self):
        print("bot disconnected")

    # async def on_error(self, err, *args, **kwargs):
    #     if err == 'on_command_error':
    #         await args[0].send('Something went wrong.')
    #     else:
    #         admin_channel = self.get_channel(789392718798389282)
    #         await admin_channel.send('An error occured.')
    #     raise

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, CommandNotFound):
            await ctx.send('Wrong Command.')
            pass
        elif isinstance(exc, BadArgument):
            await ctx.send('That option is unavailable.')
            pass
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send('One or more arguments are missing.')
        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(f'That command is on {str(exc.cooldown.type).split(".")[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs')
        elif hasattr(exc, 'original'):
            if isinstance(exc.original, HTTPException):
                await ctx.send('Unable to send message.')
            elif isinstance(exc.original, Forbidden):
                await ctx.send('I do not have permission to do that.')
            else:
                raise exc.original
        else:
            raise exc


    async def on_guild_join(self, guild):
        print('detected new server')
        OWNER_IDS.add(guild.owner.id)
        db.execute('INSERT OR REPLACE INTO war_guild (GuildID) VALUES (?)', guild.id)
        db.multiexec('INSERT OR IGNORE INTO channels (ChannelName, ChannelID, ChannelType) VALUES (?, ?, ?)', 
                     ((channel.name, channel.id, 'text') for channel in guild.text_channels))
        db.multiexec('INSERT OR IGNORE INTO channels (ChannelName, ChannelID, ChannelType) VALUES (?, ?, ?)', 
                     ((channel.name, channel.id, 'voice') for channel in guild.voice_channels))
        db.commit()
        print(' updating guild and channel info to a database...')
        text_channel_name = ['gateway', 'chatroom', 'gameplay-map', 'spectator-chat', 'log', 'staff-room']
        voice_channel_name = ['player-voicechat','spectator-voicechat']
        text_channel_usage = ['gateway', 'chatroom', 'gameplay-map', 'spectator-chat', 'log', 'staff-room']
        voice_channel_usage = ['player-voicechat','spectator-voicechat']
        existing_text_channel = db.column('SELECT ChannelName FROM channels WHERE ChannelType = "text"')
        existing_voice_channel = db.column('SELECT ChannelName FROM channels WHERE ChannelType = "voice"')
        if set(existing_text_channel).issubset(set(text_channel_name)) and set(existing_voice_channel).issubset(set(voice_channel_name)):
            staff_room = utils.find(lambda c: c.name =='staff-room', guild.text_channels)
            await staff_room.send("I think I have been here before.")
            db.multiexec('UPDATE channels SET ChannelUsage=? WHERE ChannelName=?',
                         (chan for chan in text_channel_name), 
                         (chann for chann in text_channel_usage))
            db.multiexec('UPDATE channels SET ChannelUsage=? WHERE ChannelName=?',
                         (chan for chan in voice_channel_name), 
                         (chann for chann in voice_channel_usage))

        else:
            print(' initiating setup sequence...')
            channels = []
            roles = []
            num = 0
            for chan in text_channel_name:
                channels.append(await guild.create_text_channel(chan))
                db.execute('INSERT OR REPLACE INTO channels VALUES (?,?,"text",?)', chan, channels[-1].id, text_channel_usage[num])
                num+=1
            num = 0
            for chan in voice_channel_name:
                channels.append(await guild.create_voice_channel(chan))
                db.execute('INSERT OR REPLACE INTO channels VALUES (?,?,"voice",?)', chan, channels[-1].id, voice_channel_usage[num])
                num+=1
            role_name = ['GM', 'Mediator', 'Player', 'Ghost', 'Spectator']
            for rol in role_name:
                roles.append(await guild.create_role(name=rol))
                db.execute('INSERT OR IGNORE INTO roles VALUES (?,?)', rol, roles[-1].id)
                db.commit()
            print(' adding permissions to roles and channels...')
            gm_role = utils.find(lambda n: n.name =='GM', guild.roles) 
            await gm_role.edit(permissions=Permissions(administrator=True))
            mediator_role = utils.find(lambda n: n.name =='Mediator', guild.roles)
            gateway = utils.find(lambda c: c.name == 'gateway', guild.text_channels)
            await mediator_role.edit(permissions=Permissions(permissions=1875899287))
            await gateway.set_permissions(guild.default_role, read_messages = True, send_messages = False, add_reactions = True)
            await guild.me.add_roles(gm_role)
            player_voice = utils.find(lambda c: c.name == 'player-voicechat', guild.voice_channels)
            spect_voice = utils.find(lambda c: c.name == 'spectator-voicechat', guild.voice_channels)
            for r in ['Mediator', 'Player']:
                game_role = utils.find(lambda n: n.name == r, guild.roles)
                await player_voice.set_permissions(game_role, view_channel = True, connect = True, speak = True)
                await spect_voice.set_permissions(game_role, view_channel = False, connect = False, speak = False)
            for r in ['Ghost', 'Spectator']:
                game_role = utils.find(lambda n: n.name == r, guild.roles)
                await player_voice.set_permissions(game_role, view_channel = False, connect = False, speak = False)
                await spect_voice.set_permissions(game_role, view_channel = True, connect = True, speak = True)
            perm_data = read_excel('./lib/bot/TextPermission.xlsx', header=[0,1], index_col=[0], engine='openpyxl')
            perm_index = perm_data.index.tolist()
            perm_columns = perm_data.columns.to_flat_index().tolist()
            for i in perm_index:
                that_chan = utils.find(lambda c: c.name == i, guild.text_channels)
                for j in perm_columns:
                    p_perm_dict = {}
                    w_perm_dict = {}
                    if j[1] == 'Player':
                        p_overwrite = PermissionOverite()
                        for ro in ['Mediator', 'Player']:
                            p_perm_dict[ro] = p_overwrite
                            ro_role = utils.find(lambda n: n.name == ro, guild.roles)
                            await that_chan.set_permissions(ro_role, overwrite=p_perm_dict)
                    else:
                        w_overwrite = PermissionOverite()
                        for ro in ['Ghost', 'Spectator']:
                            w_perm_dict[ro] = w_overwrite
                            ro_role = utils.find(lambda n: n.name == ro, guild.roles)
                            await that_chan.set_permissions(ro_role, overwrite=w_perm_dict)
        print('initial setup has been done.')
        await bot_start(self)

    async def on_ready(self):
        if db.record('SELECT GuildID FROM war_guild'):
            await bot_start(self)
        else:
            print('Invite me to any server you want me in to continue')

    # async def on_guild_remove(self, guild):
    #     db.multiexec('DROP TABLE')

    # async def on_message(self,message):
    #     if not message.author.bot:
    #         if isinstance(message.channel, DMChannel):
    #             if len(message.content) < 50:
    #                 await message.channel.send('Your message should be 50 characters at least.')
    #             else:
    #                 member = self.guild.get_member(message.author.id)
    #                 embed = Embed(title='Modmail',
    #                               colour=member.colour,
    #                               timestamp=datetime.utcnow())
    #                 embed.set_thumbnail(url=member.avatar_url)
    #                 fields = [('Member', f'{member.display_name}', False),
    #                           ('Message', message.content, False)]
    #                 for name, value, inline in fields:
    #                     embed.add_field(name=name, value=value, inline=inline)
    #                 mod = self.get_cog('Mod')
    #                 await mod.log_channel.send(embed=embed)
    #                 await message.channel.send('Message relayed to moderator.')
    #         else:
    #             await self.process_commands(message)

bot=Bot()