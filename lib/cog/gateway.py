from discord import Embed, Emoji, PartialEmoji
from discord.ext.commands import Cog, command
from datetime import datetime, timedelta
from ..db import db

class Gateway(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.gateway_message = (await self.get_channel(db.record('SELECT ChannelID FROM channels WHERE ChannelUsage = gateway'))
                                    .fetch_message(db.record('SELECT GatewayMessage FROM war_guild'))
            self.bot.cogs_ready.ready_up('gateway')

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.bot.ready and payload.message_id == self.gateway_message.id:
            if payload.emoji.name = '🧙':
                candidate = payload.member
                player_embed = Embed(title=candidate.display_name + 'wants to take part in the next game.',
                                     description='Do you agree on enrolling him?',
                                     colour=0xDD9767,
                                     timestamp=datetime.utcnow())
                player_embed.set_thumbnail(url=member.avatar_url)
                join_message = await self.get_channel(db.record('SELECT ChannelID FROM channels WHERE ChannelUsage = staff_room').send(embed=player_embed)
                join_message.add_reaction('✅')
                join_message.add_reaction('❌')
            elif payload.emoji.name = '🏟️':
                await payload.member.add_roles(self.bot.guild.get_role(db.record('SELECT RoleID FROM roles WHERE RoleName = Spectator'), reason = 'Access approved.')
                await payload.member.send('Welcome, You are now spectator of this chat.')
            await self.reaction_message.remove_reaction(payload.emoji, payload.member)

def setup(bot):
    bot.add_cog(Gateway(bot))

#on_message - on_typing < 10sec