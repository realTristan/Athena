# // MYSQL DATABASE CONNECTOR
import mysql.connector

# // AUTO CLOSE CURSOR OR CONNECTION
from contextlib import closing

class SQL():
    def __init__(self):
        self.db = self._connect()
        with closing(self.db.cursor(buffered=True)) as cur:
            pass
            #cur.execute(f"DROP TABLE bans")
            #cur.execute(f"DROP TABLE maps")
            #cur.execute(f"DROP TABLE matches")
            #cur.execute(f"DROP TABLE settings")
            #cur.execute(f"DROP TABLE users")


            # // USERS TABLE
            #if not await self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = users"):
                #cur.execute("CREATE TABLE users (guild_id BIGINT, user_id BIGINT, user_name VARCHAR(50), elo int, wins int, loss int, id int PRIMARY KEY AUTO_INCREMENT)")

            # // SETTINGS TABLE
            #if not await self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = settings"):
                #cur.execute("CREATE TABLE settings (guild_id BIGINT, reg_role BIGINT, map_pick_phase VARCHAR(10), match_categories VARCHAR(10), team_pick_phase VARCHAR(10), queue_channel BIGINT, reg_channel BIGINT, win_elo int, loss_elo int, match_logs BIGINT, queue_parties INT, id int PRIMARY KEY AUTO_INCREMENT)")

            # // MATCHES TABLE
            #if not await self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = matches"):
                #cur.execute("CREATE TABLE matches (guild_id BIGINT, match_id int, map VARCHAR(50), orange_cap VARCHAR(50), orange_team VARCHAR(200), blue_cap VARCHAR(50), blue_team VARCHAR(200), status VARCHAR(50), winners VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")

            # // MAPS TABLES
            #if not await self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = maps"):
                #cur.execute("CREATE TABLE maps (guild_id BIGINT, map_list VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")

            # // BANS TABLE
            #if not await self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = bans"):
                #cur.execute("CREATE TABLE bans (guild_id BIGINT, user_id BIGINT, length BIGINT, reason VARCHAR(50), banned_by VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")

    # // CONNECTING TO DATABASE
    # /////////////////////////////
    def _connect(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="root",
            database="main"
        )
        return self.db

    # // CHECK IF A VALUE IN A TABLE EXISTS
    # ////////////////////////////////////////
    async def exists(self, command):
        try:
            with closing(self.db.cursor(buffered=True)) as cur:
                cur.execute(command)
                if cur.fetchone() is None:
                    return False # // Doesn't exist
                return True # // Does exist
        except mysql.connector.Error:
            self.db.close()
            self.db = self._connect()



    # // RETURNS A SINGLE LIST FROM THE SELECTED TABLE
    # /////////////////////////////////////////////////
    async def select(self, command):
        try:
            with closing(self.db.cursor(buffered=True)) as cur:
                if await self.exists(command):
                    cur.execute(command)
                    return list(cur.fetchall()[0])
                return None
        except mysql.connector.Error:
            self.db.close()
            self.db = self._connect()


    # // RETURNS MULTIPLE LISTS FROM THE SELECTED TABLE
    # ///////////////////////////////////////////////////
    async def select_all(self, command):
        try:
            with closing(self.db.cursor(buffered=True)) as cur:
                if await self.exists(command):
                    cur.execute(command)
                    return list(cur.fetchall())
                return None
        except mysql.connector.Error:
            self.db.close()
            self.db = self._connect()


    # // EXECUTE A SEPERATE COMMAND
    # /////////////////////////////////////
    async def execute(self, command):
        try:
            with closing(self.db.cursor(buffered=True)) as cur:
                cur.execute(command)
                self.db.commit()
        except mysql.connector.Error:
            self.db.close()
            self.db = self._connect()