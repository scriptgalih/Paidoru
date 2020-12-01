from discord.ext import commands
import discord
import pymongo
import json
import asyncio

with open('cogs/dbCred.json') as json_file:
    db_cred = json.load(json_file)

myClient = pymongo.MongoClient(db_cred['client'])
myDB = myClient[db_cred['db_name']]
col_botinfo = myDB['botinfo']
col_serverinfo = myDB['serverinfo']
col_greeting_msg = myDB['greeting_msg']


class GreetingMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emj = [
            '\N{WHITE HEAVY CHECK MARK}',
            '\N{NEGATIVE SQUARED CROSS MARK}'
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print('cog:greeting ready')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print('new member join')
        if col_serverinfo.find_one()['greeting'] is False:
            return
        # print('new member join 2')
        greet_str = col_serverinfo.find_one({'guild': member.guild.id})['greeting_message']
        # print(member.guild.id)
        if greet_str is None:
            return
        await member.send(greet_str)

    @commands.command()
    @commands.is_owner()
    async def run(self, ctx):
        if not ctx.message.guild:
            return
        if col_serverinfo.find_one({'guild': ctx.guild.id})['greeting'] is True:
            await ctx.send('the command has started', delete_after=3)
            return

        confirm_message = await ctx.send('are you sure you want to run the greeting message privately')
        await confirm_message.add_reaction(self.emj[0])
        await confirm_message.add_reaction(self.emj[1])

        def check(reaction, user):
            return str(reaction.emoji) in self.emj and ctx.author == user

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=10, check=check)
            # print(str(reaction))
            if str(reaction) == '\N{WHITE HEAVY CHECK MARK}':
                col_serverinfo.update_one({'guild': ctx.guild.id}, {'$set': {'greeting': True}})
                await confirm_message.edit(content='the greeting message has started')
            else:
                await confirm_message.edit(content='Canceled')

        except asyncio.TimeoutError:
            await confirm_message.edit(content="You ran out of time!")

    @commands.command(name="stop")
    @commands.is_owner()
    async def cmd_stop_greeting_message(self, ctx):
        if not ctx.message.guild:
            return
        if col_serverinfo.find_one({'guild': ctx.guild.id})['greeting'] is False:
            await ctx.send('the command has stopped', delete_after=5)
            return

        col_serverinfo.update_one({'guild': ctx.guild.id}, {'$set': {'greeting': False}})
        await ctx.send('the greeting message has stopped', delete_after=5)

    @commands.group(name='change')
    @commands.is_owner()
    async def group_change(self, ctx):
        if not ctx.message.guild:
            return
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed...')

    @commands.group(name='show')
    @commands.is_owner()
    async def group_show(self, ctx):
        if not ctx.message.guild:
            return
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid git command passed...')

    @group_change.command(name='message')
    @commands.is_owner()
    async def change_message(self, ctx):
        if not ctx.message.guild:
            return
        confirm_message = await ctx.send('are you sure you want to change the greeting message',
                                         delete_after=15)
        await confirm_message.add_reaction(self.emj[0])
        await confirm_message.add_reaction(self.emj[1])
        cmd = 'm. change message'
        col_serverinfo.update_one({'guild': ctx.guild.id},
                                  {'$set': {'greeting_message': ctx.message.content.replace(cmd, '')}})

        def check(reaction, user):
            return str(reaction.emoji) in self.emj and ctx.author == user

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=10, check=check)
            # print(str(reaction))
            if str(reaction) == '\N{WHITE HEAVY CHECK MARK}':
                await confirm_message.edit(content='the greeting message has been changed')
            else:
                await confirm_message.edit(content='Canceled')

        except asyncio.TimeoutError:
            await confirm_message.edit(content="You ran out of time!")

    @group_show.command(name='message')
    @commands.is_owner()
    async def show_message(self, ctx):
        if ctx.author == self.client.user:
            return
        if not ctx.message.guild:
            return
        message_str = col_serverinfo.find_one()['greeting_message']
        await ctx.send(message_str)


def setup(client):
    client.add_cog(GreetingMessage(client))
