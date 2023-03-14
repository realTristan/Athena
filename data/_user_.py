from ._cache_ import Cache

class User:
    def __init__(self, guild: int, user_id: int):
        self.guild = guild
        self.user_id = user_id

    # // Get user info
    def get(self):
        return Cache.fetch("users", self.guild)[self.user_id]
    
    # // Check if user exists
    def exists(self):
        return self.user_id in Cache.fetch("users", self.guild)
    
    # // Create user
    async def create(self, user_id: int, user_name: str):
        # // Update the cache and the database
        await Cache.update("users", guild=self.guild, data={
            user_id: {
                "user_name": user_name, 
                "elo": 0, 
                "wins": 0, 
                "loss": 0
            }
        }, sqlcmds=[
            f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({self.guild}, {user_id}, '{user_name}', 0, 0, 0)"
        ])

    # // Delete user
    async def delete(self):
        # // Fetch the current users
        users = Cache.fetch("users", self.guild)

        # // Delete the user
        del users[self.user_id]

        # // Update the cache and the database
        await Cache.update("users", guild=self.guild, data=users, sqlcmds=[
            f"DELETE FROM users WHERE guild_id = {self.guild} AND user_id = {self.user_id}"
        ])


    # // Update user data
    async def update(self, user_name=None, elo=None, wins=None, loss=None):
        # // Update user name
        if user_name is not None:
            await Cache.update("users", guild=self.guild, data={"user_name": user_name}, sqlcmds=[
                f"UPDATE users SET user_name = '{user_name}' WHERE guild_id = {self.guild} AND user_id = {self.user_id}"
            ])

        # // Update user elo
        if elo is not None:
            await Cache.update("users", guild=self.guild, data={"elo": elo}, sqlcmds=[
                f"UPDATE users SET elo = {elo} WHERE guild_id = {self.guild} AND user_id = {self.user_id}"
            ])

        # // Update user wins
        if wins is not None:
            await Cache.update("users", guild=self.guild, data={"wins": wins}, sqlcmds=[
                f"UPDATE users SET wins = {wins} WHERE guild_id = {self.guild} AND user_id = {self.user_id}"
            ])

        # // Update user losses
        if loss is not None:
            await Cache.update("users", guild=self.guild, data={"loss": loss}, sqlcmds=[
                f"UPDATE users SET loss = {loss} WHERE guild_id = {self.guild} AND user_id = {self.user_id}"
            ])
