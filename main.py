import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions 
from PIL import Image
from keep_alive import keep_alive

load_dotenv()
D_Token = os.getenv('DISCORD_TOKEN')
G_Token = os.getenv('GOOGLE_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!!', intents=intents)


def image_cap(image_path):
    print("--- Starting image_cap ---")
    try:
        if not G_Token:
            print("[DEBUG] ERROR: GOOGLE_TOKEN is missing!")
            return "Error: GOOGLE_TOKEN environment variable not set."

        genai.configure(api_key=G_Token)
        
        print("[DEBUG] Initializing model: gemma-3-27b-it")
        model = genai.GenerativeModel('gemma-3-27b-it')
        
        print(f"[DEBUG] Opening image at path: {image_path}")
        img = Image.open(image_path)
        print("[DEBUG] Image opened successfully.")

        with open("Guidelines for AI Model Generating.txt", 'r', encoding='utf-8') as f:
            guidelines = f.read()
        
        prompt = (f"{guidelines}\n\n"
                  "Using the guidelines provided, caption this image for people who are hard of seeing. "
                  "Only respond with the caption. Limit yourself to a few sentences.")

        print("[DEBUG] Calling Google API to generate content...")
        response = model.generate_content([prompt, img])
        print("[DEBUG] Received response from Google API.")
        
        return response.text

    except FileNotFoundError:
        print("[DEBUG] ERROR: Guidelines file not found!")
        return "Error: 'Guidelines for AI Model Generating.txt' not found."
    except google_exceptions.GoogleAPICallError as e:
        print(f"[DEBUG] ERROR: A Google API call error occurred: {e}")
        return "Sorry, there was a problem with the AI model provider."
    except Exception as e:
        print(f"[DEBUG] ERROR: An unexpected error occurred in image_cap: {e}")
        return f"An unexpected error occurred: {e}"


@bot.event
async def on_ready():
    print(f"We are ready to run as {bot.user}!")
    logging.info(f"Bot has logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith('image/'):
                processing_message = await message.channel.send("The Caption bot is thinking...")
                temp_image_path = f"temp_{attachment.filename}"
                try:
                    await attachment.save(temp_image_path)
                    
                    caption = await bot.loop.run_in_executor(
                        None, image_cap, temp_image_path
                    )
                    await processing_message.edit(content=caption)

                except Exception as e:
                    await processing_message.edit(content=f"An error occurred: {e}")
                    print(f"Error in on_message: {e}")

                finally:
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                break 


keep_alive()

print("Starting bot...")
if D_Token:
    bot.run(D_Token, log_handler=handler, log_level=logging.DEBUG)
else:
    print("FATAL ERROR: DISCORD_TOKEN not found in environment variables.")