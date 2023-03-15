from ._cache_ import Cache, Settings, SqlData, Lobby
from discord.ext import commands
import discord

class User:
    def __init__(self, guild_id: int, user_id: int):
        self.guid_id = guild_id
        self.user_id = user_id

    # // Get user info
    def info(self) -> dict:
        return Cache.fetch("users", self.guid_id)[self.user_id]

    # // Show the users stats in an embed
    async def stats(self, ctx:commands.Context, user:discord.Member):
        # // Get the user info
        user_info: dict = self.info()
        user_name: str = user_info["user_name"]
        user_elo: int = user_info["elo"]
        user_wins: int = user_info["wins"]
        user_loss: int = user_info["loss"]
        user_matches: int = user_wins + user_loss
        
        # // Make sure the match exists
        if user_info is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Create an embed
        embed = discord.Embed(
            description=f"**Elo:** {user_elo}\n**Wins:** {user_wins}\n**Losses:** {user_loss}\n**Matches:** {user_matches}", 
            color=33023
        )
        embed.set_author(name=user_name, icon_url=user.avatar_url)
    
        # // Return the embed
        return embed

    
    # // Check if user exists
    def exists(self) -> bool:
        return self.user_id in Cache.fetch("users", self.guid_id)
    
    # // Register a new user
    @staticmethod
    async def register(guild: discord.Guild, user: discord.Member, user_name: str) -> None:
        # // Update the cache and the database
        await Cache.update("users", guild=guild.id, data={
            user.id: {
                "user_name": user_name, 
                "elo": 0, 
                "wins": 0, 
                "loss": 0
            }
        }, sqlcmds=[
            f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({guild.id}, {user.id}, '{user_name}', 0, 0, 0)"
        ])

        # // Add the register role to the user
        register_role: int = Settings(guild.id).get("register_role")
        if register_role == 0:
            return
        
        # // Get the role
        role: discord.Role = guild.get_role(register_role)
        if role is None:
            return Settings(guild.id).update(reg_role=0)
        
        # // Add the role to the user
        try: await user.add_roles(guild.get_role(register_role))
        except Exception: return

    # // Add a role to the user
    @staticmethod
    async def add_role(user: discord.Member, role: discord.Role) -> None:
        # // Add the role to the user
        try: await user.add_roles(role)
        except Exception: return

    # // Remove a role from the user
    @staticmethod
    async def remove_role(user: discord.Member, role: discord.Role) -> None:
        # // Remove the role from the user
        try: await user.remove_roles(role)
        except Exception: return

    # // Change the users nickname
    @staticmethod
    async def change_nickname(user: discord.Member, nickname: str) -> None:
        # // Change the nickname
        try: await user.edit(nick=nickname)
        except Exception: return


    # // Add an elo role to the user
    @staticmethod
    async def add_elo_role(guild: discord.Guild, user: discord.Member, elo: int) -> None:
        roles: list = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level <= {elo} AND guild_id = {guild.id}")
        
        # // Check roles and add them
        if len(roles) <= 0:
            return
        
        # // Iterate over the roles
        for role_id in roles:
            role = guild.get_role(role_id[0])

            # // Add the role to the user
            if role not in user.roles:
                await User.add_role(user, role)
    

    # // Remove an elo role from the user
    @staticmethod
    async def remove_elo_role(guild: discord.Guild, user: discord.Member, elo: int) -> None:
        roles: list = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level > {elo} AND guild_id = {guild.id}")
        
        # // Check roles and add them
        if len(roles) <= 0:
            return
        
        # // Iterate over the roles
        for role_id in roles:
            role = guild.get_role(role_id[0])

            # // Add the role to the user
            if role in user.roles:
                await User.remove_role(user, role)


    # // Delete user
    async def delete(self) -> None:
        # // Fetch the current users
        users = Cache.fetch("users", self.guid_id)

        # // Delete the user
        del users[self.user_id]

        # // Update the cache and the database
        await Cache.set("users", guild=self.guid_id, data=users, sqlcmds=[
            f"DELETE FROM users WHERE guild_id = {self.guid_id} AND user_id = {self.user_id}"
        ])

    # // Reset an users stats
    async def reset(self):
        await self.update(elo=0, wins=0, loss=0)
        

    # // Check mod role or mod permissions
    @staticmethod
    async def is_mod(guild: discord.Guild, user: discord.Member) -> bool:
        # // If the user has admin role, return true
        if await User.is_admin(guild, user):
            return True
        
        # // Else, check for whether the user has mod role
        mod_role = Settings(guild.id).get("mod_role")
        return guild.get_role(mod_role) in user.roles
    
    
    # // Check admin role or admin permissions
    @staticmethod
    async def is_admin(guild: discord.Guild, user: discord.Member) -> bool:
        # // Get the admin role from settings
        admin_role = Settings(guild.id).get("admin_role")
        
        # // Check admin permissions
        if admin_role == 0 or user.guild_permissions.administrator:
            return user.guild_permissions.administrator
        return guild.get_role(admin_role) in user.roles
    

    # // Check if member is still in the server
    @staticmethod
    async def verify(guild: discord.Guild, user_id: int) -> discord.Member:
        member = guild.get_member(user_id)
        
        # // If the member is not valid (meaning they left the server, etc.)
        if member is not None:
            return member
        
        # // If the user is not in the database, return None
        if not User(guild.id, user_id).exists():
            return None
        
        # // Delete the user from the database
        await User(guild.id, user_id).delete()

        # // Return None
        return None
    

    # // Give an user a win
    @staticmethod
    async def win(guild: discord.Guild, lobby: int, user: discord.Member) -> discord.Embed:
        # // Get the user data
        user_data = User(guild.id, user.id).info()

        # // Get the lobby settings
        win_elo: int = Lobby(guild.id, lobby).get("win_elo")
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_data is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Update the user
        await User(guild.id, user.id).update(
            elo = user_data["elo"] + win_elo, 
            wins = user_data["wins"] + 1
        )

        # // Edit the users elo roles
        await User.add_elo_role(guild, user, user_data["elo"])
        
        # // Edit the users nickname
        await User.change_nickname(user, f"[{user_data['elo'] + win_elo}] {user.name}")

        # // Return the success embed
        return discord.Embed(
            description = f"{user.mention} has won and gained **{win_elo}** elo", 
            color = 3066993
        )
    

    # // Give an user a loss
    @staticmethod
    async def lose(guild: discord.Guild, lobby: int, user: discord.Member) -> discord.Embed:
        # // Get the user data
        user_data = User(guild.id, user.id).info()

        # // Get the lobby settings
        loss_elo: int = Lobby(guild.id, lobby).get("loss_elo")
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_data is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Update the user
        await User(guild.id, user.id).update(
            elo = user_data["elo"] - loss_elo, 
            loss = user_data["loss"] + 1
        )

        # // Edit the users elo roles
        await User.remove_elo_role(guild, user, user_data["elo"])
        
        # // Edit the users nickname
        await User.change_nickname(user, f"[{user_data['elo'] - loss_elo}] {user.name}")

        # // Return the success embed
        return discord.Embed(
            description = f"{user.mention} has lost and removed **{loss_elo}** elo", 
            color = 15158332
        )


    # // Update user data
    async def update(self, user_name = None, elo = None, wins = None, loss = None) -> None:
        # // Update user name
        if user_name is not None:
            await Cache.update("users", guild=self.guid_id, data={"user_name": user_name}, sqlcmds=[
                f"UPDATE users SET user_name = '{user_name}' WHERE guild_id = {self.guid_id} AND user_id = {self.user_id}"
            ])

        # // Update user elo
        if elo is not None:
            await Cache.update("users", guild=self.guid_id, data={"elo": elo}, sqlcmds=[
                f"UPDATE users SET elo = {elo} WHERE guild_id = {self.guid_id} AND user_id = {self.user_id}"
            ])

        # // Update user wins
        if wins is not None:
            await Cache.update("users", guild=self.guid_id, data={"wins": wins}, sqlcmds=[
                f"UPDATE users SET wins = {wins} WHERE guild_id = {self.guid_id} AND user_id = {self.user_id}"
            ])

        # // Update user losses
        if loss is not None:
            await Cache.update("users", guild=self.guid_id, data={"loss": loss}, sqlcmds=[
                f"UPDATE users SET loss = {loss} WHERE guild_id = {self.guid_id} AND user_id = {self.user_id}"
            ])
