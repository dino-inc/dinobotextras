import discord
from discord.ext import commands
import instaloader
from instaloader import Post
import re
import os
class Insta(commands.Cog):
    def __init__(self, bot):
        self.insta = instaloader.Instaloader()

    @commands.Cog.listener()
    async def on_message(self, message):
        shortcode = re.search('(https://.*)/(.*)/', message.content)
        if shortcode is None:
            return
        directory = os.fsencode("./instagram/")
        # Empty the image directory of old images
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            os.remove(filepath)

        # Create and download the post
        post = Post.from_shortcode(self.insta.context, shortcode.group(2))
        try:
            self.insta.download_post(post, "instagram")
        except:
            pass

        filepath = None
        # Delete all downloaded files that aren't the image
        for filename in os.listdir(directory):
            if str(filename).endswith(".jpg'") or str(filename).endswith(".png'"):
                pass
            else:
                filepath = os.path.join(directory, filename)
                os.remove(filepath)

        # Send all downloaded images into chat
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            photo = discord.File(fp=filepath, filename="feonge.png")
            await message.channel.send(file=photo)

def setup(bot):
    bot.add_cog(Insta(bot))

