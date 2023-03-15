from cache import Cache, Settings, SqlData, Lobby
import discord

class Users:
    # // Get user info
    @staticmethod
    def info(guild_id: int, user_id: int) -> any:
        return Cache.fetch("users", guild_id)[user_id]

    # // Show the users stats in an embed
    @staticmethod
    def stats(user: discord.Member) -> discord.Embed:
        # // Get the user info
        user_info: dict = Users.info(user.guild, user.id)
        user_name: str = user_info.get("user_name")
        user_elo: int = user_info.get("elo")
        user_wins: int = user_info.get("wins")
        user_losses: int = user_info.get("losses")
        user_matches: int = user_wins + user_losses
        
        # // Make sure the match exists
        if user_info is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Create an embed
        embed: discord.Embed = discord.Embed(
            description = f"**Elo:** {user_elo}\n**Wins:** {user_wins}\n**Losses:** {user_losses}\n**Matches:** {user_matches}", 
            color = 33023
        )
        embed.set_author(name = user_name, icon_url = user.avatar_url)
    
        # // Return the embed
        return embed

    # // Check if user exists
    @staticmethod
    def exists(guild_id: int, user_id: int) -> bool:
        return user_id in Cache.fetch("users", guild_id)
    
    # // Register a new user
    @staticmethod
    async def register(user: discord.Member, user_name: str) -> None:
        # // Update the cache and the database
        await Cache.update("users", guild_id=user.guild.id, data={
            user.id: {
                "user_name": user_name, 
                "elo": 0, 
                "wins": 0, 
                "losses": 0
            }
        }, sqlcmds=[
            f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, losses) VALUES ({user.guild.id}, {user.id}, '{user_name}', 0, 0, 0)"
        ])

        # // Add the register role to the user
        register_role: int = Settings.get(user.guild.id, "register_role")
        if register_role == 0:
            return
        
        # // Get the role
        role: discord.Role = user.guild.get_role(register_role)
        if role is None:
            return Settings.update(user.guild.id, reg_role=0)
        
        # // Add the role to the user
        try: await user.add_roles(user.guild.get_role(register_role))
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
    async def add_elo_role(user: discord.Member, elo: int) -> None:
        roles: list = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level <= {elo} AND guild_id = {user.guild.id}")
        
        # // Check roles and add them
        if len(roles) <= 0:
            return
        
        # // Iterate over the roles
        for role_id in roles:
            role = user.guild.get_role(role_id[0])

            # // Add the role to the user
            if role not in user.roles:
                await Users.add_role(user, role)
    
    # // Remove an elo role from the user
    @staticmethod
    async def remove_elo_role(user: discord.Member, elo: int) -> None:
        roles: list = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level > {elo} AND guild_id = {user.guild.id}")
        
        # // Check roles and add them
        if len(roles) <= 0:
            return
        
        # // Iterate over the roles
        for role_id in roles:
            role: discord.Role = user.guild.get_role(role_id[0])

            # // Add the role to the user
            if role in user.roles:
                await Users.remove_role(user, role)

    # // Delete an user
    @staticmethod
    async def delete(guild_id: int, user_id: int) -> None:
        await Cache.delete_user(guild_id, user_id)

    # // Reset an users stats
    @staticmethod
    async def reset(guild_id: int, user_id: int) -> None:
        await Users.update(guild_id, user_id, elo=0, wins=0, losses=0)
        
    # // Check mod role or mod permissions
    @staticmethod
    def is_mod(user: discord.Member) -> bool:
        # // If the user has admin role, return true
        if Users.is_admin(user.guild, user):
            return True
        
        # // Else, check for whether the user has mod role
        mod_role: int = Settings.get(user.guild.id, "mod_role")
        return user.guild.get_role(mod_role) in user.roles
    
    
    # // Check admin role or admin permissions
    @staticmethod
    def is_admin(user: discord.Member) -> bool:
        # // Get the admin role from settings
        admin_role: int = Settings.get(user.guild.id, "admin_role")
        
        # // Check admin permissions
        if admin_role == 0 or user.guild_permissions.administrator:
            return user.guild_permissions.administrator
        return user.guild.get_role(admin_role) in user.roles
    
    # // Check if member is still in the server
    @staticmethod
    async def verify(guild: discord.Guild, user_id: int) -> discord.Member:
        member: discord.Member = guild.get_member(user_id)
        
        # // If the member is not valid (meaning they left the server, etc.)
        if member is not None:
            return member
        
        # // If the user is not in the database, return None
        if not Users.exists(guild.id, user_id):
            return None
        
        # // Delete the user from the database
        await Users.delete(guild.id, user_id)

        # // Return None
        return None
    
    # // Give an user a win
    @staticmethod
    async def win(user: discord.Member, lobby: int) -> discord.Embed:
        # // Get the user data
        user_info: dict = Users.info(user.guild.id, user.id)
        user_wins: int = user_info.get("wins")
        user_elo: int = user_info.get("elo")

        # // Get the lobby settings
        win_elo: int = Lobby(user.guild.id, lobby).get("win_elo")
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_info is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Update the user
        await Users.update(
            user.guild.id, user.id, 
            elo = user_elo + win_elo, 
            wins = user_wins + 1
        )

        # // Edit the users elo roles
        await Users.add_elo_role(user.guild, user, user_elo)
        
        # // Edit the users nickname
        await Users.change_nickname(user, f"[{user_elo + win_elo}] {user.name}")

        # // Return the success embed
        return discord.Embed(
            description = f"{user.mention} has won and gained **{win_elo}** elo", 
            color = 3066993
        )
    
    # // Give an user a loss
    @staticmethod
    async def lose(user: discord.Member, lobby: int) -> discord.Embed:
        # // Get the user data
        user_info: dict = Users.info(user.guild.id, user.id)
        user_losses: int = user_info.get("losses")
        user_elo: int = user_info.get("elo")

        # // Get the lobby settings
        loss_elo: int = Lobby(user.guild.id, lobby).get("loss_elo")
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_info is None:
            return discord.Embed(
                description = f"{user.mention} is not registered", 
                color = 15158588
            )
        
        # // Update the user
        await Users.update(
            user.guild.id, user.id,
            elo = user_elo - loss_elo, 
            losses = user_losses + 1
        )

        # // Edit the users elo roles
        await Users.remove_elo_role(user.guild, user, user_elo)
        
        # // Edit the users nickname
        await Users.change_nickname(user, f"[{user_elo - loss_elo}] {user.name}")

        # // Return the success embed
        return discord.Embed(
            description = f"{user.mention} has lost and lost **{loss_elo}** elo", 
            color = 15158332
        )

    # // Update user data
    @staticmethod
    async def update(guild_id: int, user_id: int, user_name = None, elo = None, wins = None, losses = None) -> None:
        # // Update user name
        if user_name is not None:
            await Cache.update("users", guild_id=guild_id, data={"user_name": user_name}, sqlcmds=[
                f"UPDATE users SET user_name = '{user_name}' WHERE guild_id = {guild_id} AND user_id = {user_id}"
            ])

        # // Update user elo
        if elo is not None:
            await Cache.update("users", guild_id=guild_id, data={"elo": elo}, sqlcmds=[
                f"UPDATE users SET elo = {elo} WHERE guild_id = {guild_id} AND user_id = {user_id}"
            ])

        # // Update user wins
        if wins is not None:
            await Cache.update("users", guild_id=guild_id, data={"wins": wins}, sqlcmds=[
                f"UPDATE users SET wins = {wins} WHERE guild_id = {guild_id} AND user_id = {user_id}"
            ])

        # // Update user losses
        if losses is not None:
            await Cache.update("users", guild_id=guild_id, data={"losses": losses}, sqlcmds=[
                f"UPDATE users SET losses = {losses} WHERE guild_id = {guild_id} AND user_id = {user_id}"
            ])
