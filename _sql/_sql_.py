from contextlib import closing
import mysql.connector

db = mysql.connector.connect(
    host="localhost", port="3306", user="root", password="root", database="main"
)

class SqlData:
    def __init__(self):
        pass
        #with closing(db.cursor()) as cur:
            # cur.execute(f"DROP TABLE bans")
            #cur.execute(f"DROP TABLE maps")
            # cur.execute(f"DROP TABLE matches")
            #cur.execute(f"DROP TABLE settings")
            # cur.execute(f"DROP TABLE users")
            #cur.execute(f"DROP TABLE lobbies")
            #cur.execute(f"DROP TABLE lobby_settings")

            # // USERS TABLE
            # cur.execute("CREATE TABLE users (guild_id BIGINT, user_id BIGINT, user_name VARCHAR(50), elo INT, wins INT, loss INT, id INT PRIMARY KEY AUTO_INCREMENT)")

            # // SETTINGS TABLE
            #cur.execute("CREATE TABLE settings (guild_id BIGINT, reg_role BIGINT, match_categories INT, reg_channel BIGINT, match_logs BIGINT, mod_role BIGINT, admin_role BIGINT, self_rename INT, id INT PRIMARY KEY AUTO_INCREMENT)")

            # // LOBBY SETTINGS
            #cur.execute("CREATE TABLE lobby_settings (guild_id BIGINT, lobby_id BIGINT, map_pick_phase INT, team_pick_phase INT, win_elo int, loss_elo INT, party_size INT, negative_elo INT, queue_size INT, id INT PRIMARY KEY AUTO_INCREMENT)")

            # // MATCHES TABLE
            # cur.execute("CREATE TABLE matches (guild_id BIGINT, match_id INT, lobby_id BIGINT, map VARCHAR(50), orange_cap BIGINT, orange_team VARCHAR(200), blue_cap BIGINT, blue_team VARCHAR(200), status VARCHAR(20), winners VARCHAR(10), id INT PRIMARY KEY AUTO_INCREMENT)")

            # // MAPS TABLES
            #cur.execute("CREATE TABLE maps (guild_id BIGINT, lobby_id BIGINT, map VARCHAR(30), id INT PRIMARY KEY AUTO_INCREMENT)")

            # // BANS TABLE
            # cur.execute("CREATE TABLE bans (guild_id BIGINT, user_id BIGINT, length BIGINT, reason VARCHAR(50), banned_by VARCHAR(50), id INT PRIMARY KEY AUTO_INCREMENT)")
            
            # // ELO ROLE TABLE
            # cur.execute("CREATE TABLE elo_roles (guild_id BIGINT, role_id BIGINT, elo_level INT, win_elo INT, lose_elo INT, id INT PRIMARY KEY AUTO_INCREMENT)")
    
    # Connect to the database
    @staticmethod
    async def db_connect():
        return mysql.connector.connect(
            host="localhost", port="3306", user="root", password="root", database="main"
        )
        
    # Check if value exists
    @staticmethod
    async def exists(command: str):
        global db
        try:
            with closing(db.cursor(buffered=True)) as cur:
                cur.execute(command)
                if cur.fetchone() is None:
                    return False  # // Doesn't exist
                return True  # // Does exist
        except mysql.connector.Error as e:
            print(f"SqlData (exists): {e}")
            db.close()
            db = await SqlData.db_connect()

    # Returns a single list of results
    @staticmethod
    async def select(command: str):
        global db
        try:
            with closing(db.cursor()) as cur:
                if await SqlData.exists(command):
                    cur.execute(command)
                    return list(cur.fetchone())
                return None
        except mysql.connector.Error as e:
            print(f"SqlData (select): {e}")
            db.close()
            db = await SqlData.db_connect()

    # Returns multiple lists of results
    @staticmethod
    async def select_all(command: str):
        global db
        try:
            with closing(db.cursor(buffered=True)) as cur:
                cur.execute(command)
                return [list(i) for i in cur.fetchall()]
        except mysql.connector.Error as e:
            print(f"SqlData (select_all): {e}")
            db.close()
            db = await SqlData.db_connect()

    # Execute a command
    @staticmethod
    async def execute(command: str):
        global db
        try:
            with closing(db.cursor()) as cur:
                cur.execute(command)
                db.commit()
        except mysql.connector.Error as e:
            print(f"SqlData (execute): {e}")
            db.close()
            db = await SqlData.db_connect()
