import discord
from discord.ext import commands
import instaloader
from instaloader import Post
import re
import os
import json
import requests
from lxml import html
import io

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
        if "instagram" not in shortcode.group(1) and "deviantart" not in shortcode.group(1):
            print("no valid site")
            return
        # Create and download the post
        async with message.channel.typing():
            if "instagram" in shortcode.group(1):
                await instagram_rip(self, shortcode, message)
            elif "deviantart" in shortcode.group(1):
                await deviantart_rip(self, message)
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

async def instagram_rip(self, shortcode, message):
    try:
        post = Post.from_shortcode(self.insta.context, shortcode.group(2))
        self.insta.download_post(post, "instagram")
        return True
    except Exception as e:
        await message.channel.send(f"Unable to download instagram post; error is {e}")
        return False

async def deviantart_rip(self, message):
    try:
        page = requests.get(message.content)
        raw_html = html.fromstring(page.content)
        image = raw_html.xpath('//*[@id="root"]/main/div/div[1]/div[1]/div/div[2]/div[1]/div/img/@src')
        title = raw_html.xpath('//*[@id="root"]/main/div/div[1]/div[1]/div/div[2]/div[1]/div/img/@alt')
        #compile image from chunks
        image_request = requests.get(image[0], stream=True).raw.data
        raw_image = io.BytesIO(image_request)
        discord_file = discord.File(fp=raw_image, filename=title[0]+'.png')
        await message.channel.send(file=discord_file)
        print(f"Successfully posted image {title[0]}.")
        return True
    except Exception as e:
        await message.channel.send(f"Unable to download deviantart post; error is {e}")
        return False

def setup(bot):
    bot.add_cog(Insta(bot))

