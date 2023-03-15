from ._sql_ import SqlData
import threading

# // The Global Cache Variable
cache: dict[str, dict] = {
    "settings": {}, "users": {}, "lobbies": {},
    "bans": {}, "elo_roles": {}, "matches": {}
}

# // The Cache Class that contains all the cache functions
class Cache:
    lock: threading.Lock = threading.Lock()

    # // Add all MySQL Data into a cached map
    @staticmethod
    async def load_data():
        await Cache.load_users()
        await Cache.load_lobbies()
        await Cache.load_elo_roles()
        await Cache.load_bans()
        await Cache.load_matches()
        await Cache.load_settings()
        await Cache.load_maps()

    # // Load users into the sql cache
    @staticmethod
    async def load_users():
        rows = await SqlData.select_all(f"SELECT * FROM users")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["users"]:
                cache["users"][guild] = {}

            # // Add the user to the cache
            user_id: int = row[1]
            cache["users"][guild][user_id] = {
                "user_name": row[2], 
                "elo": row[3], 
                "wins": row[4], 
                "loss": row[5]
            }

    # // Load lobby settings into the sql cache
    @staticmethod
    async def load_lobbies():
        rows = await SqlData.select_all(f"SELECT * FROM lobbies")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["lobbies"]:
                cache["lobbies"][guild] = {}

            # // Add the lobby settings to the cache
            lobby_id: int = row[1]
            cache["lobbies"][guild][lobby_id] = {
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

    # // Load elo roles into the sql cache
    @staticmethod
    async def load_elo_roles():
        rows = await SqlData.select_all(f"SELECT * FROM elo_roles")
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
            cache["settings"][guild]["elo_roles"][role_id] = {
                "role_id": role_id, 
                "elo_level": row[2], 
                "win_elo": row[3], 
                "lose_elo": row[4]
            }
    
    # // Load matches into the sql cache
    @staticmethod
    async def load_matches():
        rows = await SqlData.select_all(f"SELECT * FROM matches")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["matches"]:
                cache["matches"][guild] = {}

            # // Add the match to the cache
            match_id: int = row[1]
            cache["matches"][guild][match_id] = {
                "match_id": match_id, 
                "lobby_id": row[2], 
                "map": row[3], 
                "orange_cap": row[4], 
                "orange_team": row[5].split(","), 
                "blue_cap": row[6], 
                "blue_team": row[7].split(","), 
                "status": row[8],
                "winner": row[9]
            }

    # // Load bans into the sql cache
    @staticmethod
    async def load_bans():
        rows = await SqlData.select_all(f"SELECT * FROM bans")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["bans"]:
                cache["bans"][guild] = {}

            # // Add the ban to the cache
            user_id: int = row[1]
            cache["bans"][guild][user_id] = {
                "user_id": user_id, 
                "length": row[2], 
                "reason": row[3], 
                "banned_by": row[4]
            }
    
    # // Load settings into the sql cache
    @staticmethod
    async def load_settings():
        rows = await SqlData.select_all(f"SELECT * FROM settings")
        for row in rows:
            # // Add the setting to the cache
            guild: int = row[0]
            cache["settings"][guild] = {
                "reg_role": row[1], 
                "match_categories": row[2], 
                "reg_channel": row[3], 
                "match_logs": row[4], 
                "mod_role": row[5], 
                "admin_role": row[6], 
                "self_rename": row[7]
            }
    
    # // Load maps into the sql cache
    @staticmethod
    async def load_maps():
        rows = await SqlData.select_all(f"SELECT * FROM maps")
        for row in rows:
            # // If the guild does not exist in the cache
            guild: int = row[0]
            if guild not in cache["lobbies"]:
                cache["lobbies"][guild] = {}

            # // If the lobby does not exist in the cache
            lobby_id: int = row[1]
            if lobby_id not in cache["lobbies"][guild]:
                cache["lobbies"][guild][lobby_id] = {
                    "lobby_id": lobby_id,
                    "maps": []
                }
            
            # // If the maps do not exist in the cache
            if "maps" not in cache["lobbies"][guild][lobby_id]:
                cache["lobbies"][guild][lobby_id]["maps"] = []

            # // Add the map to the cache
            cache["lobbies"][guild][lobby_id]["maps"].append(row[2])
    

    # // Fetch a value from the cache
    @staticmethod
    def fetch(table: str, guild = None):
        # // Check if the guild exists in the cache table
        with Cache.lock.acquire():
            if guild not in cache[table]:
                cache[table][guild] = {}
            return cache[table][guild]
        

    # // Update a value in the cache
    @staticmethod
    async def update(table: str, guild: str, data: any, lobby: int = None, sqlcmds: list = []):
        # // Update the cache
        with Cache.lock.acquire():
            # // If the lobby is not provided
            if lobby is None:
                if guild not in cache[table]:
                    cache[table][guild] = {}
                cache[table][guild].update(data)

            # // If the lobby is provided
            else:
                if lobby not in cache[table][guild]:
                    cache[table][guild][lobby] = {}
                cache[table][guild][lobby].update(data)

        # // If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await SqlData.execute(cmd)


    # // Delete a ban from the cache
    @staticmethod
    async def delete_ban(guild: int, user_id: int):
        # // Delete the ban from the cache
        with Cache.lock.acquire():
            del cache["bans"][guild][user_id]

        # // Delete the ban from the database
        await SqlData.execute(f"DELETE FROM bans WHERE guild_id = {guild} AND user_id = {user_id}")


    # // Delete a lobby from the cache
    @staticmethod
    async def delete_lobby(guild: int, lobby_id: int):
        # // Delete the lobby from the cache
        with Cache.lock.acquire():
            del cache["lobbies"][guild][lobby_id]

        # // Delete the lobby from the database
        await SqlData.execute(f"DELETE FROM lobbies WHERE guild_id = {guild} AND lobby_id = {lobby_id}")

    # // Delete a match from the cache
    @staticmethod
    async def delete_match(guild: int, match_id: int):
        # // Delete the match from the cache
        with Cache.lock.acquire():
            del cache["matches"][guild][match_id]

        # // Delete the match from the database
        await SqlData.execute(f"DELETE FROM matches WHERE guild_id = {guild} AND match_id = {match_id}")

    # // Delete a map from the cache
    @staticmethod
    async def delete_map(guild: int, lobby_id: int, map: str):
        # // Delete the map from the cache
        with Cache.lock.acquire():
            cache["lobbies"][guild][lobby_id]["maps"].remove(map)

        # // Delete the map from the database
        await SqlData.execute(f"DELETE FROM maps WHERE guild_id = {guild} AND lobby_id = {lobby_id} AND map = '{map}'")

    # // Add a map to the cache
    @staticmethod
    async def add_map(guild: int, lobby_id: int, map: str):
        # // Add the map to the cache
        with Cache.lock.acquire():
            cache["lobbies"][guild][lobby_id]["maps"].append(map)

        # // Add the map to the database
        await SqlData.execute(f"INSERT INTO maps (guild_id, lobby_id, map) VALUES ({guild}, {lobby_id}, '{map}')")

    # // Delete a player from the cache
    @staticmethod
    async def delete_player(guild: int, lobby_id: int, user_id: int):
        # // Delete the player from the cache
        with Cache.lock.acquire():
            cache["lobbies"][guild][lobby_id]["players"].remove(user_id)

        # // Delete the player from the database
        await SqlData.execute(f"DELETE FROM players WHERE guild_id = {guild} AND lobby_id = {lobby_id} AND user_id = {user_id}")

    # // Delete an elo role from the cache
    @staticmethod
    async def delete_elo_role(guild: int, role_id: int):
        # // Delete the elo role from the cache
        with Cache.lock.acquire():
            del cache["settings"][guild]["elo_roles"][role_id]

        # // Delete the elo role from the database
        await SqlData.execute(f"DELETE FROM elo_roles WHERE guild_id = {guild} AND role_id = {role_id}")
