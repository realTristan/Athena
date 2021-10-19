# // MYSQL DATABASE CONNECTOR
import mysql.connector

# // AUTO CLOSE CURSOR OR CONNECTION
from contextlib import closing

# // CONNECTING TO DATABASE
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",
    database="main"
)

class SQL():
    def __init__(self):
        with closing(db.cursor(buffered=True)) as cur:
            pass
            #cur.execute(f"DROP TABLE bans")
            #cur.execute(f"DROP TABLE maps")
            #cur.execute(f"DROP TABLE matches")
            #cur.execute(f"DROP TABLE settings")
            #cur.execute(f"DROP TABLE users")


            # // USERS TABLE
            #if not self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = users"):
                #cur.execute("CREATE TABLE users (guild_id BIGINT, user_id BIGINT, user_name VARCHAR(50), elo int, wins int, loss int, id int PRIMARY KEY AUTO_INCREMENT)")

            # // SETTINGS TABLE
            #if not self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = settings"):
                #cur.execute("CREATE TABLE settings (guild_id BIGINT, reg_role BIGINT, map_pick_phase VARCHAR(10), team_categories VARCHAR(10), picking_phase VARCHAR(10), queue_channel BIGINT, reg_channel BIGINT, win_elo int, loss_elo int, match_logs BIGINT, id int PRIMARY KEY AUTO_INCREMENT)")

            # // MATCHES TABLE
            #if not self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = matches"):
                #cur.execute("CREATE TABLE matches (guild_id BIGINT, match_id int, map VARCHAR(50), orange_cap VARCHAR(50), orange_team VARCHAR(100), blue_cap VARCHAR(50), blue_team VARCHAR(100), status VARCHAR(50), winners VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")

            # // MAPS TABLES
            #if not self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = maps"):
                #cur.execute("CREATE TABLE maps (guild_id BIGINT, map_list VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")

            # // BANS TABLE
            #if not self.exists("SELECT *  FROM information_schema WHERE TABLE_NAME = bans"):
                #cur.execute("CREATE TABLE bans (guild_id BIGINT, user_id BIGINT, length BIGINT, reason VARCHAR(50), banned_by VARCHAR(50), id int PRIMARY KEY AUTO_INCREMENT)")


    # // CHECK IF A VALUE IN A TABLE EXISTS
    # ////////////////////////////////////////
    def exists(self, command):
        with closing(db.cursor(buffered=True)) as cur:
            cur.execute(command)
            if cur.fetchone() is None:
                return False # // Doesn't exist
            return True # // Does exist


    # // RETURNS A SINGLE LIST FROM THE SELECTED TABLE
    # /////////////////////////////////////////////////
    def select(self, command):
        with closing(db.cursor(buffered=True)) as cur:
            if self.exists(command):
                cur.execute(command)
                return list(cur.fetchall()[0])


    # // RETURNS MULTIPLE LISTS FROM THE SELECTED TABLE
    # ///////////////////////////////////////////////////
    def select_all(self, command):
        with closing(db.cursor(buffered=True)) as cur:
            if self.exists(command):
                cur.execute(command)
                return list(cur.fetchall())


    # // EXECUTE A SEPERATE COMMAND
    # /////////////////////////////////////
    def execute(self, command):
        with closing(db.cursor(buffered=True)) as cur:
            cur.execute(command)
            db.commit()


