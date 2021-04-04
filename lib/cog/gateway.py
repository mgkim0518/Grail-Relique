from discord import Embed, Emoji, PartialEmoji
from discord.ext.commands import Cog, command
from datetime import datetime, timedelta
from random import choice
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
            if payload.emoji.name = '🧙'
                player_entry_message = 'I will participate in this game. I will follow the rules and never share spoilers to other player unless it is approved by GM.'
                await payload.member.send("Do you really want to be a player of this game? Then, Please type this message in here below correctly including puncuations.")
                await payload.member.send(player_entry_message)
                if message.content == player_entry_message and 
                    await payload.member.add_roles(self.bot.guild.get_role(db.record('SELECT RoleID FROM roles WHERE RoleName = Player'), reason = 'Access approved.')
            elif payload.emoji.name = '🏟️'
                await payload.member.add_roles(self.bot.guild.get_role(db.record('SELECT RoleID FROM roles WHERE RoleName = Spectator'), reason = 'Access approved.')
                await payload.member.send('Welcome, You are now spectator of this chat.')
            await self.reaction_message.remove_reaction(payload.emoji, payload.member)

def setup(bot):
    bot.add_cog(Gateway(bot))

#on_message - on_typing < 10sec