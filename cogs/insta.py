import discord
from discord.ext import commands
import instaloader
from instaloader import Post
import re
class Insta(commands.Cog):
    def __init__(self, bot):
        self.insta = instaloader.Instaloader()

    @commands.Cog.listener()
    async def on_message(self, message):
        shortcode = re.search('/.*/(.*)/', message.content)
        Post.from_shortcode(self.insta.context, shortcode.group(0))
        self.insta.download_post()


def setup(bot):
    bot.add_cog(Insta(bot))

