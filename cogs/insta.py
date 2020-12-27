import discord
from discord.ext import commands
import instaloader
from instaloader import Post
import re
from datetime import datetime
class Insta(commands.Cog):
    def __init__(self, bot):
        self.insta = instaloader.Instaloader()

    @commands.Cog.listener()
    async def on_message(self, message):
        shortcode = re.search('(https://.*/.*)/', message.content)
        if shortcode is None:
            return
        self.insta.download_pic("insta", shortcode.group(0), datetime.now(), )



def setup(bot):
    bot.add_cog(Insta(bot))

