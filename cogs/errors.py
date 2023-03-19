from discord.ext import commands
import discord, datetime

class ErrorCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.client_cmds: dict = {}
        for cmd in self.client.commands:
            self.client_cmds[cmd.name] = cmd.description


    # // RUN THE COMMAND SORTER
    # //////////////////////////////
    async def _run_sorter(self, ctx: commands.Context, _user_command: str):
        sorted_cmds = await self._command_sort(_user_command)
        similar_cmds: str = ""
        
        # // CHECK IF THERE'S ANY SIMILAR COMMANDS
        if len(sorted_cmds) <= 0:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[ERROR]** {ctx.author.mention} we could not find the command you are looking for", 
                    color = 15158588
            ))
        
        # // CREATE EMBED
        for i in range(len(sorted_cmds)):
            similar_cmds+=f"**{i+1}:** {sorted_cmds[i][0].upper()+sorted_cmds[i][1:]} {self.client_cmds[sorted_cmds[i]]}\n"

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Similar Commands [{_user_command}]", 
            description = f"{similar_cmds}", 
            color = 15158588
        )

        # // Set the embed footer
        embed.set_footer(text = "Message \"tristan#2230\" for support")

        # // Send the embed
        return await ctx.send(embed = embed)

    # CHECK HOW MANY TIMES A LETTER APPEARS IN BOTH WORDS
    # //////////////////////////////////////////////////////
    async def _letter_count(self, _user_command: str):
        try:
            _result = {}
            for index in range(len(self.client.commands)):
                if str(list(self.client.commands)[index]) not in _result:
                    _result[str(list(self.client.commands)[index])] = 0

                for letter in str(list(self.client.commands)[index]):
                    if letter in list(_user_command):
                        _result[str(list(self.client.commands)[index])] += 1.09
        except Exception as e:
            print(f"Errors 44: {e}")
        return _result

    # // CHECK LETTER POSITIONING
    # ////////////////////////////////
    async def _letter_position(self, _user_command: str):
        _result = await self._letter_count(_user_command)
        for command in self.client.commands:
            for index in range(len(_user_command)):
                try:
                    if _user_command[index] == str(command)[index]:
                        _result[str(command)] += 1.509
                except Exception: 
                    pass
        return _result

    # SORT THE COMMANDS
    # /////////////////////
    async def _command_sort(self, _user_command:str):
        try:
            _command_dict: dict = await self._letter_position(_user_command)
            _sorted_command_dict: dict = {k: v for k, v in sorted(_command_dict.items(), key=lambda item: item[1], reverse=True)}
            _result: list = []
            for command in _sorted_command_dict:
                if _sorted_command_dict[command] > (len(command)*0.8509):
                    _result.append(command)
                    if len(_result) >= 6:
                        return _result
        except Exception:
            return _result
        return _result
    

    # ON COMMAND ERROR HANDLING
    # ///////////////////////////////
    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error):
        # // If the command is on cooldown
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} Slow it down! Try again in **{error.retry_after:.2f}s**", 
                    color = 15158588
            ))
        
        # // If the user is missing a role
        elif isinstance(error, commands.CommandNotFound):
            return await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
        
        # // If the user is missing permissions
        elif isinstance(error, commands.MissingPermissions):
            print(error)
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions (or Athena)", 
                    color = 15158588
            ))
        
        # // If the mentioned user is not found
        elif isinstance(error, commands.MemberNotFound):
            print(error)
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} player not found", 
                    color = 15158588
            ))
        
        # // If the user is missing a required argument
        elif isinstance(error, commands.MissingRequiredArgument):
            print(error)
            return await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
        
        else:
            # // Get my guilds error channel
            error_channel: discord.Channel = self.client.get_channel(938482543227994132)

            # // Run the command sorter
            await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))

            # // Send the error to the error channel
            await error_channel.send(f"**[{ctx.guild.name}]** `{datetime.datetime.utcnow()}`**:**  *{error}*")
            raise error

# // Setup the cog
async def setup(client: commands.Bot):
    await client.add_cog(ErrorCog(client))