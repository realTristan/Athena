from discord.ext import commands
import discord, datetime

class ErrorHandling(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.client_cmds = {}
        for cmd in self.client.commands:
            self.client_cmds[cmd.name] = cmd.description


    # // RUN THE COMMAND SORTER
    # //////////////////////////////
    async def _run_sorter(self, ctx:commands.Context, _user_command:str):
        sorted_cmds = await self._command_sort(_user_command)
        similar_cmds=""
        
        # // CHECK IF THERE'S ANY SIMILAR COMMANDS
        if len(sorted_cmds) <= 0:
            return await ctx.send(embed=discord.Embed(description=f"**[ERROR]** {ctx.author.mention} we could not find the command you are looking for", color=15158588))
        
        # // CREATE EMBED
        for i in range(len(sorted_cmds)):
            similar_cmds+=f"**{i+1}:** {sorted_cmds[i][0].upper()+sorted_cmds[i][1:]} {self.client_cmds[sorted_cmds[i]]}\n"

        embed=discord.Embed(title=f"Similar Commands [{_user_command}]", description=f"{similar_cmds}", color=15158588)
        embed.set_footer(text="Message \"tristan#2230\" for support")
        return await ctx.send(embed=embed)

    # CHECK HOW MANY TIMES A LETTER APPEARS IN BOTH WORDS
    # //////////////////////////////////////////////////////
    async def _letter_count(self, _user_command:str):
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
    async def _letter_position(self, _user_command:str):
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
            _command_dict = await self._letter_position(_user_command)
            _sorted_command_dict = {k: v for k, v in sorted(_command_dict.items(), key=lambda item: item[1], reverse=True)}
            _result = []
            for command in _sorted_command_dict:
                if _sorted_command_dict[command] > (len(command)*0.8509):
                    _result.append(command)
                    if len(_result) >= 6:
                        return _result
        except Exception as e: 
            print(f"Errors 73: {e}")
            return _result
        return _result
    

    # ON COMMAND ERROR HANDLING
    # ///////////////////////////////
    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} Slow it down! Try again in **{error.retry_after:.2f}s**", color=15158588))
            
        elif isinstance(error, commands.CommandNotFound):
            return await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
            
        elif isinstance(error, commands.MissingPermissions):
            print(error)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions (or Athena)", color=15158588))
        
        elif isinstance(error, commands.MemberNotFound):
            print(error)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=15158588))
        
        elif isinstance(error, commands.MissingRequiredArgument):
            print(error)
            return await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
        
        else:
            error_channel = self.client.get_channel(938482543227994132)
            await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
            await error_channel.send(f"**[{ctx.guild.name}]** `{datetime.datetime.utcnow()}`**:**  *{error}*")
            raise error

def setup(client: commands.Bot):
    client.add_cog(ErrorHandling(client))