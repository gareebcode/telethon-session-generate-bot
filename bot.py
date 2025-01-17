# Ensure all comments and strings use ASCII-compliant quotes
from telethon.sync import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    PasswordHashInvalidError,
)
from telethon.sessions import StringSession
from telethon import TelegramClient, events
import config

# Bot token from BotFather
BOT_TOKEN = config.BOT_TOKEN

# Your API credentials from config.py
API_ID = config.API_ID
API_HASH = config.API_HASH


# Create the bot client
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handles the /start command."""
    await event.reply(
        "Welcome to the Telethon String Session Generator Bot!\n"
        "To generate your session, use the /generate command followed by your phone number (e.g., /generate +1234567890)."
    )


@bot.on(events.NewMessage(pattern=r"^/generate \+\d{10,15}$"))
async def generate_session(event):
    """Generates a string session for the provided phone number."""
    phone_number = event.text.split(" ", 1)[1].strip()  # Extract phone number
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                await event.reply("OTP sent to your phone. Please reply with the OTP.")

                @bot.on(events.NewMessage(pattern=r"^\d{5,}$"))  # Simple OTP pattern
                async def otp_handler(otp_event):
                    otp = otp_event.text.strip()
                    try:
                        await client.sign_in(phone_number, otp)
                    except SessionPasswordNeededError:
                        await otp_event.reply("Two-step verification enabled. Send your password.")

                        @bot.on(events.NewMessage)
                        async def password_handler(pwd_event):
                            password = pwd_event.text.strip()
                            try:
                                await client.sign_in(password=password)
                                session_string = client.session.save()
                                await pwd_event.reply(
                                    f"Your string session:\n\n`{session_string}`\n\n"
                                    "Keep this string session safe! Do not share it with anyone."
                                )
                            except PasswordHashInvalidError:
                                await pwd_event.reply("Invalid password. Please try again.")
                                return
                    except PhoneCodeInvalidError:
                        await otp_event.reply("Invalid OTP. Please try again.")
                        return
                    else:
                        session_string = client.session.save()
                        await otp_event.reply(
                            f"Your string session:\n\n`{session_string}`\n\n"
                            "Keep this string session safe! Do not share it with anyone."
                        )
            else:
                session_string = client.session.save()
                await event.reply(
                    f"Your string session:\n\n`{session_string}`\n\n"
                    "Keep this string session safe! Do not share it with anyone."
                )
        except PhoneNumberInvalidError:
            await event.reply("Invalid phone number. Please check and try again.")
        except Exception as e:
            await event.reply(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    print("Bot is running...")
    bot.run_until_disconnected()
