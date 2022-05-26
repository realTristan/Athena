from discord_components import *
from discord.ext import commands
from datetime import datetime
import discord

class Help(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # // CREATING EMBED OBJECTS
    player_embed=discord.Embed(title='Player Commands', color=33023, timestamp=datetime.utcnow())
    moderator_embed=discord.Embed(title='Moderator Commands', color=33023, timestamp=datetime.utcnow())
    administrator_embed=discord.Embed(title='Administrator Commands', color=33023, timestamp=datetime.utcnow())

    # // ADDING FIELDS TO PLAYERS EMBED
    player_embed.add_field(name='‏‏‎ ‎\nJoin', value='Join the current queue\n(Usage: =j)')
    player_embed.add_field(name=' ‎\nLeave', value='Leave the current queue\n(Usage: =l)')
    player_embed.add_field(name=' ‎\nPick', value='Pick an user to be on your team\n(Usage: =p [@user])')
    player_embed.add_field(name=' ‎\nPick Map', value='Pick a map to play\n(Usage: =pickmap [name])')
    player_embed.add_field(name=' ‎\nRename', value='Change your Ten Man username\n(Usage: =rename [name])')
    player_embed.add_field(name=' ‎\nRegister', value='Register yourself to play in the ten mans\n(Usage: =reg [name])')
    player_embed.add_field(name=' ‎\nShow Queue', value='Show the current queue\n(Usage: =q)')
    player_embed.add_field(name=' ‎\nShow Maps', value='Show the current map pool\n(Usage: =maps)')
    player_embed.add_field(name=' ‎\nShow Stats', value='Show your ten man stats\n(Usage: =stats or =stats [@user])')
    player_embed.add_field(name=' ‎\nLeaderboard', value='Show the ten man leaderboard\n(Usage: =lb)')
    player_embed.add_field(name='‏‏‎ ‎\nShow Last Match', value='Shows the last match played\n(Usage: =lm)')
    player_embed.add_field(name=' ‎\nMatch Show', value='Shows a match\n(Usage: =match show [match id])')
    player_embed.add_field(name=' ‎\nRecent Matches', value='Shows recent matches\n(Usage: =recent [amount])')
    player_embed.add_field(name=' ‎\nCreate Party', value='Create a party\n(Usage: =party create)')
    player_embed.add_field(name=' ‎\nParty Invite', value='Invite a player to your party\n(Usage: =party invite [@user])')
    player_embed.add_field(name=' ‎\nLeave Party', value='Leave a party\n(Usage: =party leave)')
    player_embed.add_field(name=' ‎\nShow Party', value='Show a players party\n(Usage: =party show [@user])')
    player_embed.add_field(name=' ‎\nKick User in Party', value='Kick a player from your party\n(Usage: =party kick [@user])')
    player_embed.add_field(name=' ‎\nLobby Info', value='Get information about the current lobby\n(Usage: =lobby info)')

    # // ADDING FIELDS TO MODERATOR EMBED
    moderator_embed.add_field(name=' ‎\nBan [Mod+]', value='Bans a player from the queue\n(Usage: =ban [@user] [length] [reason])')
    moderator_embed.add_field(name=' ‎\nUnBan [Mod+]', value='Unbans a player from the queue\n(Usage: =unban [@user])')
    moderator_embed.add_field(name=' ‎\nWin [Mod+]', value='Give a win to the mentioned users\n(Usage: =win [@users])')
    moderator_embed.add_field(name=' ‎\nLose [Mod+]', value='Give a loss to the mentioned users\n(Usage: =lose [@users])')
    moderator_embed.add_field(name=' ‎\nAdd Map [Mod+]', value='Adds a map to the map pool\n(Usage: =addmap [name])')
    moderator_embed.add_field(name=' ‎\nRemove Map [Mod+]', value='Removes a map from the map pool\n(Usage: =delmap [name])')
    moderator_embed.add_field(name=' ‎\nRegister User [Mod+]', value='Register an user\n(Usage: =reg [@user] [name])')
    moderator_embed.add_field(name=' ‎\nUnRegister User [Mod+]', value='Unregister an user\n(Usage: =unreg [@user])')
    moderator_embed.add_field(name=' ‎\nClear Queue [Mod+]', value='Clears the current queue\n(Usage: =clear)')
    moderator_embed.add_field(name=' ‎\nForce Rename [Mod+]', value='Renames the user\n(Usage: =fr [@user] [new name])')
    moderator_embed.add_field(name=' ‎\nForce Join [Mod+]', value='Adds an user to the queue\n(Usage: =fj [@user])')
    moderator_embed.add_field(name=' ‎\nForce Leave [Mod+]', value='Removes an user from the queue\n(Usage: =fl [@user])')
    moderator_embed.add_field(name=' ‎\nMatch Report [Mod+]', value='Reports a match\n(Usage: =match report [match id] [orange/blue])')
    moderator_embed.add_field(name=' ‎\nMatch Cancel [Mod+]', value='Cancels a match\n(Usage: =match cancel [match id])')
    moderator_embed.add_field(name=' ‎\nMatch Undo [Mod+]', value='Undos a match\n(Usage: =match undo [match id])')
    moderator_embed.add_field(name=' ‎\nMatch Rollback [Mod+]', value='Rollbacks every match with the user in it\n(Usage: =rb [user id])')
    moderator_embed.add_field(name=' ‎\nReplace [Mod+]', value='Sub players in a match\n(Usage: =sub [user 1] [user 2] [match id])')
    
    # // ADDING FIELDS TO ADMINISTRATOR EMBED
    administrator_embed.add_field(name=' ‎\nLobby Create [Admin+]', value='Create a new lobby\n(Usage: =lobby add)')
    administrator_embed.add_field(name=' ‎\nLobby Remove [Admin+]', value='Remove an existing lobby\n(Usage: =lobby del)')
    administrator_embed.add_field(name=' ‎\nLobby Settings [Admin+]', value='Change lobby settings\n(Usage: =lobby settings)')
    administrator_embed.add_field(name=' ‎\nShow Lobbies [Admin+]', value='Show server lobby\'s\n(Usage: =lobby list)')
    administrator_embed.add_field(name=' ‎\nReset Stats [Admin+]', value='Reset an users stats\n(Usage: =reset [@user])')
    administrator_embed.add_field(name=' ‎\nReset All Stats [Admin+]', value='Reset all players stats\n(Usage: =reset all)')
    administrator_embed.add_field(name=' ‎\nSet Elo [Admin+]', value='Sets an users elo\n(Usage: =set elo [@user] [amount])')
    administrator_embed.add_field(name=' ‎\nSet Wins [Admin+]', value='Sets an users wins\n(Usage: =set wins [@user] [amount])')
    administrator_embed.add_field(name=' ‎\nSet Losses [Admin+]', value='Sets an users losses\n(Usage: =set loss [@user] [amount])')
    administrator_embed.add_field(name=' ‎\nSettings Menu [Admin+]', value='Open Settings Menu\n(Usage: =settings)')
    administrator_embed.add_field(name=' ‎\nAdd Elo Role [Admin+]', value='Add new elo role\n(Usage: =elorole add [@role] [elo])')
    administrator_embed.add_field(name=' ‎\nRemove Elo Role [Admin+]', value='Remove elo role\n(Usage: =elorole del [@role])')
    administrator_embed.add_field(name=' ‎\nShow Elo Roles [Admin+]', value='Show elo roles\n(Usage: =elorole list)')
    administrator_embed.add_field(name=' ‎\nSet Admin Role [Admin+]', value='Sets the current admin role\n(Usage: =adminrole set @role)')
    administrator_embed.add_field(name=' ‎\nRemove Admin Role [Admin+]', value='Removes the current admin role\n(Usage: =adminrole remove)')
    administrator_embed.add_field(name=' ‎\nShow Admin Role [Admin+]', value='Shows the current admin role\n(Usage: =adminrole show)')
    administrator_embed.add_field(name=' ‎\nSet Mod Role [Admin+]', value='Sets the current mod role\n(Usage: =modrole set @role)')
    administrator_embed.add_field(name=' ‎\nRemove Mod Role [Admin+]', value='Removes the current mod role\n(Usage: =modrole remove)')
    administrator_embed.add_field(name=' ‎\nShow Mod Role [Admin+]', value='Shows the current mod role\n(Usage: =modrole show)')


    # // CREATING THE SELECT MENU COMMAND
    # //////////////////////////////////////
    @commands.command(name="help", description='`=help`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def help(self, ctx:commands.Context):
        if not ctx.author.bot:
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's Command Menu**", color=33023),
                components=[
                    Select(
                        placeholder="View Commands",
                        options=[
                            SelectOption(emoji='🔵', label="Player Commands", value="player"),
                            SelectOption(emoji='🔵', label="Moderator Commands", value="mod"),
                            SelectOption(emoji='🔵', label="Administrator Commands", value="admin")
                        ])])


    # // SELECT MENU LISTENER
    # //////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res:Interaction):
        if not res.author.bot:
            if res.values[0] == "player":
                await res.send(embed=discord.Embed(description=f"{res.author.mention} the commands have been sent to your dm's", color=3066992))
                return await res.author.send(embed=self.player_embed)
            
            if res.values[0] == "mod":
                await res.send(embed=discord.Embed(description=f"{res.author.mention} the commands have been sent to your dm's", color=3066992))
                return await res.author.send(embed=self.moderator_embed)
            
            if res.values[0] == "admin":
                await res.send(embed=discord.Embed(description=f"{res.author.mention} the commands have been sent to your dm's", color=3066992))
                return await res.author.send(embed=self.administrator_embed)




def setup(client: commands.Bot):
    client.add_cog(Help(client))