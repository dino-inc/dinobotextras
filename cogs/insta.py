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
        async with message.channel.typing():
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
            except Exception as e:
                await message.channel.send(f"Unable to download post; error is {e}")
                return

            filepath = None
            try:
                # Delete all downloaded files that aren't the image
                for filename in os.listdir(directory):
                    name = filename.decode('utf-8')
                    if name.endswith(".jpg") or name.endswith(".png") or name.endswith(".mp4"):
                        print(f"not deleting {filename}")
                        pass
                    else:
                        filepath = os.path.join(directory, filename)
                        os.remove(filepath)
            except Exception as e:
                await message.channel.send(f"Unable  to clean the directory after downloading images; error is {e}")
                return

            # Send all downloaded images into chat
            for filename in os.listdir(directory):
                try:
                    filepath = os.path.join(directory, filename)
                    photo = discord.File(fp=filepath, filename=filename.decode('utf-8'))
                    await message.channel.send(file=photo)
                except Exception as e:
                    await message.channel.send(f"Unable to send media; error is {e}")
                    return
def setup(bot):
    bot.add_cog(Insta(bot))

