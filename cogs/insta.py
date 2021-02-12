import discord
from discord.ext import commands
import instaloader
from instaloader import Post
import re
import os
import json
class Insta(commands.Cog):
    def __init__(self, bot):
        self.insta = instaloader.Instaloader(download_video_thumbnails=False)
        insta_creds = json.load(open("./auth.json"))
        self.insta.login(insta_creds["username"], insta_creds["password"])
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
        try:
            if "instagram" not in shortcode.group(1):
                return
            post = Post.from_shortcode(self.insta.context, shortcode.group(2))
            self.insta.download_post(post, "instagram")
        except:
            pass

        filepath = None
        # Delete all downloaded files that aren't the image
        for filename in os.listdir(directory):
            if str(filename).endswith(".jpg'") or str(filename).endswith(".png'") or str(filename).endswith(".mp4"):
                pass
            else:
                filepath = os.path.join(directory, filename)
                os.remove(filepath)

        # Send all downloaded images into chat
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            photo = None
            if(filename).endswith(".jpg"):
                photo = discord.File(fp=filepath, filename="feonge.jpg")
            elif(filename).endswith(".png"):
                photo = discord.File(fp=filepath, filename="feonge.png")
            elif(filename.endswith(".mp4")):
                photo = discord.File(fp=filepath, filename="feonge.mp4")
            await message.channel.send(file=photo)

def setup(bot):
    bot.add_cog(Insta(bot))

