from .database import Database
import functools

# // The Global Cache Variable
cache: dict[str, dict] = {
    "settings": {}, "users": {}, "lobbies": {},
    "bans": {}, "matches": {}
}

# // The Cache Class that contains all the cache functions
class Cache:
    # // Add all MySQL Data into a cached map
    @staticmethod
    async def load_data() -> None:
        await Cache.load_settings()
        await Cache.load_elo_roles()
        await Cache.load_users()
        await Cache.load_lobbies()
        await Cache.load_maps()
        await Cache.load_bans()
        await Cache.load_matches()
        print(cache)

    # // Load users into the sql cache
    @staticmethod
    async def load_users() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM users")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["users"]:
                cache["users"][guild] = {}

            # // Add the user to the cache
            user_id: int = row[1]
            cache["users"][guild].update({
                user_id: {
                    "user_name": row[2], 
                    "elo": row[3], 
                    "wins": row[4], 
                    "losses": row[5]
                }
            })

    # // Load lobby settings into the sql cache
    @staticmethod
    async def load_lobbies() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM lobbies")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["lobbies"]:
                cache["lobbies"][guild] = {}

            # // Add the lobby settings to the cache
            lobby_id: int = row[1]
            cache["lobbies"][guild].update({
                lobby_id: {
                    "lobby_id": lobby_id, 
                    "maps": [], 
                    "map_pick_phase": row[2], 
                    "team_pick_phase": row[3], 
                    "win_elo": row[4], 
                    "loss_elo": row[5], 
                    "party_size": row[6], 
                    "negative_elo": row[7], 
                    "queue_size": row[8]
                }
            })

    # // Load elo roles into the sql cache
    @staticmethod
    async def load_elo_roles() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM elo_roles")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["settings"]:
                cache["settings"][guild] = {}

            # // If the elo roles do not exist in the cache
            if "elo_roles" not in cache["settings"][guild]:
                cache["settings"][guild]["elo_roles"] = {}

            # // Add the elo roles to the cache
            role_id: int = row[1]
            cache["settings"][guild]["elo_roles"].update({
                role_id: {
                    "role_id": role_id, 
                    "elo_level": row[2], 
                    "win_elo": row[3], 
                    "lose_elo": row[4]
                }
            })
    
    # // Load matches into the sql cache
    @staticmethod
    async def load_matches() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM matches")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["matches"]:
                cache["matches"][guild] = {}

            # // Add the match to the cache
            match_id: int = row[1]
            cache["matches"][guild].update({
                match_id: {
                    "match_id": match_id, 
                    "lobby_id": row[2], 
                    "map": row[3], 
                    "orange_cap": row[4], 
                    "orange_team": row[5].split(",", maxsplit=4), 
                    "blue_cap": row[6], 
                    "blue_team": row[7].split(",", maxsplit=4), 
                    "status": row[8],
                    "winner": row[9]
                }
            })

    # // Load bans into the sql cache
    @staticmethod
    async def load_bans() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM bans")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["bans"]:
                cache["bans"][guild] = {}

            # // Add the ban to the cache
            user_id: int = row[1]
            cache["bans"][guild].update({
                user_id: {
                    "user_id": user_id, 
                    "length": row[2], 
                    "reason": row[3], 
                    "banned_by": row[4]
                }
            })
    
    # // Load settings into the sql cache
    @staticmethod
    async def load_settings() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM settings")
        for row in rows:
            # // Add the setting to the cache
            guild_id: int = row[0]
            cache["settings"].update({
                guild_id: {
                    "is_premium": row[1],
                    "reg_role": row[2], 
                    "match_categories": row[3], 
                    "reg_channel": row[4], 
                    "match_logs": row[5], 
                    "mod_role": row[6], 
                    "admin_role": row[7], 
                    "self_rename": row[8]
                }
            })
    
    # // Load maps into the sql cache
    @staticmethod
    async def load_maps() -> None:
        rows: list = await Database.select_all(f"SELECT * FROM maps")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["lobbies"]:
                cache["lobbies"][guild] = {}

            # // If the lobby does not exist in the cache
            lobby_id: int = row[1]
            if lobby_id not in cache["lobbies"][guild]:
                cache["lobbies"][guild].update({
                    lobby_id: {
                        "lobby_id": lobby_id,
                        "maps": []
                    }
                })
            
            # // If the maps do not exist in the cache
            if "maps" not in cache["lobbies"][guild][lobby_id]:
                cache["lobbies"][guild][lobby_id]["maps"] = []

            # // Add the map to the cache
            cache["lobbies"][guild][lobby_id]["maps"].append(row[2])
    

    # // Fetch a value from the cache
    @staticmethod
    def fetch(table: str, guild_id: int = None) -> any:
        if guild_id not in cache[table]:
            cache[table][guild_id] = {}
        return cache[table][guild_id]
        

    # // Update a value in the cache
    @staticmethod
    async def update(table: str, guild_id: int, data: any, key: int = None, sqlcmds: list = []) -> None:
        # // If the lobby is not provided
        if key is None:
            if guild_id not in cache[table]:
                cache[table][guild_id] = {}
            cache[table][guild_id].update(data)

        # // If the lobby is provided
        else:
            if key not in cache[table][guild_id]:
                cache[table][guild_id][key] = {}
            cache[table][guild_id][key].update(data)

        # // If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await Database.execute(cmd)


    # // Delete a ban from the cache
    @staticmethod
    async def delete_ban(guild_id: int, user_id: int) -> None:
        # // Delete the ban from the cache
        del cache["bans"][guild_id][user_id]

        # // Delete the ban from the database
        await Database.execute(f"DELETE FROM bans WHERE guild_id = {guild_id} AND user_id = {user_id}")

    # // Delete a lobby from the cache
    @staticmethod
    async def delete_lobby(guild_id: int, lobby_id: int) -> None:
        # // Delete the lobby from the cache
        del cache["lobbies"][guild_id][lobby_id]

        # // Delete the lobby from the database
        await Database.execute(f"DELETE FROM lobbies WHERE guild_id = {guild_id} AND lobby_id = {lobby_id}")

    # // Delete a match from the cache
    @staticmethod
    async def delete_match(guild_id: int, match_id: int) -> None:
        # // Delete the match from the cache
        del cache["matches"][guild_id][match_id]

        # // Delete the match from the database
        await Database.execute(f"DELETE FROM matches WHERE guild_id = {guild_id} AND match_id = {match_id}")

    # // Delete a map from the cache
    @staticmethod
    async def delete_map(guild_id: int, lobby_id: int, map: str) -> None:
        # // Delete the map from the cache
        cache["lobbies"][guild_id][lobby_id]["maps"].remove(map)

        # // Delete the map from the database
        await Database.execute(f"DELETE FROM maps WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND map = '{map}'")

    # // Add a map to the cache
    @staticmethod
    async def add_map(guild_id: int, lobby_id: int, map: str) -> None:
        # // Add the map to the cache
        cache["lobbies"][guild_id][lobby_id]["maps"].append(map)

        # // Add the map to the database
        await Database.execute(f"INSERT INTO maps (guild_id, lobby_id, map) VALUES ({guild_id}, {lobby_id}, '{map}')")

    # // Delete a player from the cache
    @staticmethod
    async def delete_user(guild_id: int, user_id: int) -> None:
        # // Delete the player from the cache
        del cache["users"][guild_id][user_id]

        # // Delete the player from the database
        await Database.execute(f"DELETE FROM users WHERE guild_id = {guild_id} AND user_id = {user_id}")

    # // Delete an elo role from the cache
    @staticmethod
    async def delete_elo_role(guild_id: int, role_id: int) -> None:
        # // Delete the elo role from the cache
        del cache["settings"][guild_id]["elo_roles"][role_id]

        # // Delete the elo role from the database
        await Database.execute(f"DELETE FROM elo_roles WHERE guild_id = {guild_id} AND role_id = {role_id}")
