from discord_components import *
from discord.ext import commands
from datetime import datetime
import discord

class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // CREATING EMBED OBJECTS
    player_embed=discord.Embed(title='Player Commands', color=65535, timestamp=datetime.utcnow())
    moderator_embed=discord.Embed(title='Moderator Commands', color=65535, timestamp=datetime.utcnow())
    administrator_embed=discord.Embed(title='Administrator Commands', color=65535, timestamp=datetime.utcnow())

    # // ADDING FIELDS TO PLAYERS EMBED
    player_embed.add_field(name='‏‏‎ ‎\nJoin', value='Join the current queue\n(Usage: =j)')
    player_embed.add_field(name=' ‎\nLeave', value='Leave the current queue\n(Usage: =l)')
    player_embed.add_field(name=' ‎\nPick', value='Pick an user to be on your team\n(Usage: =p @user)')
    player_embed.add_field(name=' ‎\nSelect Map', value='Pick a map to play\n(Usage: =map name)')
    player_embed.add_field(name=' ‎\nRename', value='Change your Ten Man username\n(Usage: =rename [name])')
    player_embed.add_field(name=' ‎\nRegister', value='Register yourself to play in the ten mans\n(Usage: =reg [name])')
    player_embed.add_field(name=' ‎\nShow Queue', value='Show the current queue\n(Usage: =q)')
    player_embed.add_field(name=' ‎\nShow Maps', value='Show the current map pool\n(Usage: =maps)')
    player_embed.add_field(name=' ‎\nShow Stats', value='Show your ten man stats\n(Usage: =stats or =stats @user)')
    player_embed.add_field(name=' ‎\nLeaderboard', value='Show the ten man leaderboard\n(Usage: =lb)')
    player_embed.add_field(name='‏‏‎ ‎\nShow Last Match', value='Shows the last match played\n(Usage: =lm)')
    player_embed.add_field(name=' ‎\nMatch Show', value='Shows a match\n(Usage: =match show [match id]')

    # // ADDING FIELDS TO MODERATOR EMBED
    moderator_embed.add_field(name=' ‎\nBan [Mod+]', value='Bans a player from the queue\n(Usage: =ban [@user] [length] [reason]')
    moderator_embed.add_field(name=' ‎\nUnBan [Mod+]', value='Unbans a player from the queue\n(Usage: =unban [@user]')
    moderator_embed.add_field(name=' ‎\nWin [Mod+]', value='Give a win to the mentioned users\n(Usage: =win [@users])')
    moderator_embed.add_field(name=' ‎\nLose [Mod+]', value='Give a loss to the mentioned users\n(Usage: =lose [@users])')
    moderator_embed.add_field(name=' ‎\nAdd Map [Mod+]', value='Adds a map to the map pool\n(Usage: =addmap [name])')
    moderator_embed.add_field(name=' ‎\nRemove Map [Mod+]', value='Removes a map from the map pool\n(Usage: =delmap [name])')
    moderator_embed.add_field(name=' ‎\nUnRegister [Mod+]', value='Unregister an user\n(Usage: =unreg [@user])')
    moderator_embed.add_field(name=' ‎\nClear Queue [Mod+]', value='Clears the current queue\n(Usage: =clear)')
    moderator_embed.add_field(name=' ‎\nForce Rename [Mod+]', value='Renames the user\n(Usage: =fr [@user] [new name])')
    moderator_embed.add_field(name=' ‎\nForce Join [Mod+]', value='Adds an user to the queue\n(Usage: =fj [@user])')
    moderator_embed.add_field(name=' ‎\nForce Leave [Mod+]', value='Removes an user from the queue\n(Usage: =fl [@user])')
    moderator_embed.add_field(name=' ‎\nForce Start [Mod+]', value='Force starts the queue\n(Usage: =fs)')
    moderator_embed.add_field(name=' ‎\nMatch Report [Mod+]', value='Reports a match\n(Usage: =match report [match id] [orange/blue])')
    moderator_embed.add_field(name=' ‎\nMatch Cancel [Mod+]', value='Cancels a match\n(Usage: =match cancel [match id])')
    moderator_embed.add_field(name=' ‎\nMatch Undo [Mod+]', value='Undos a match\n(Usage: =match undo [match id])')

    # // ADDING FIELDS TO ADMINISTRATOR EMBED
    administrator_embed.add_field(name=' ‎\nReplace [Admin+]', value='Sub players in a match\n(Usage: =sub [match id] [user 1] [user 2])')
    administrator_embed.add_field(name=' ‎\nReset Stats [Admin+]', value='Reset an users stats\n(Usage: =match cancel [match id])')
    administrator_embed.add_field(name=' ‎\nSet Elo [Admin+]', value='Sets an users elo\n(Usage: =setelo @user [amount])')
    administrator_embed.add_field(name=' ‎\nSet Wins [Admin+]', value='Sets an users wins\n(Usage: =setwins @user [amount])')
    administrator_embed.add_field(name=' ‎\nSet Losses [Admin+]', value='Sets an users losses\n(Usage: =setloss @user [amount])')
    administrator_embed.add_field(name=' ‎\nSettings Panel [Admin+]', value='Open Settings Panel\n(Usage: =settings)')


    # // CREATING THE SELECT MENU COMMAND
    # //////////////////////////////////////
    @commands.command()
    async def help(self, ctx):
        await ctx.author.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's Command Panel**", color=65535),
            components=[
                Select(
                    placeholder="View",
                    options=[
                        SelectOption(emoji='🔵', label="Player Commands", value="player"),
                        SelectOption(emoji='🔵', label="Moderator Commands", value="mod"),
                        SelectOption(emoji='🔵', label="Administrator Commands", value="admin")
                    ])])


    # // SELECT MENU LISTENER
    # //////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res):
        if res.values[0] == "player":
            await res.message.delete()
            return await res.author.send(embed=self.player_embed)
        
        if res.values[0] == "mod":
            await res.message.delete()
            return await res.author.send(embed=self.moderator_embed)
        
        if res.values[0] == "admin":
            await res.message.delete()
            return await res.author.send(embed=self.administrator_embed)




def setup(client):
    client.add_cog(Help(client))