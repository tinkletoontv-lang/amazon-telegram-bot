import os
import gspread
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from google.oauth2.service_account import Credentials

# Global variable for Google Sheet
sheet = None

def setup_google_sheets():
    global sheet
    try:
        print("🔧 Setting up Google Sheets connection...")

        # Get credentials from environment variable
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not credentials_json:
            print("❌ GOOGLE_CREDENTIALS not set!")
            return False

        print("✅ GOOGLE_CREDENTIALS found")

        # Parse the JSON
        creds_dict = json.loads(credentials_json)

        # Setup scope and credentials
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        # Authorize and connect
        client = gspread.authorize(creds)
        sheet = client.open("product_list").sheet1

        print("✅ Successfully connected to Google Sheets")
        return True

    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hello! Send me a product number and I'll give you the link.")

def get_product(update: Update, context: CallbackContext):
    if sheet is None:
        update.message.reply_text("⚠️ Service temporarily unavailable. Please try again later.")
        return

    product_number = update.message.text.strip()

    try:
        records = sheet.get_all_records()

        for row in records:
            # Check for product number
            product_no = str(row.get("product_no", "") or
                           row.get("Product No", "") or
                           row.get("product_number", "")).strip()

            if product_no == product_number:
                link = row.get("product_link", "") or row.get("link", "") or row.get("URL", "")

                if link:
                    update.message.reply_text(f"✅ Here is your product link:\n\n🔗 {link}")
                else:
                    update.message.reply_text("❌ Link not found!")
                return

        update.message.reply_text("❌ Product not found!")

    except Exception as e:
        update.message.reply_text("⚠️ Error. Please try again later.")
        print(f"Error: {e}")

def main():
    print("🚀 Starting Telegram Bot...")

    # Check if BOT_TOKEN is set
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Error: BOT_TOKEN not set!")
        return

    # Setup Google Sheets
    if not setup_google_sheets():
        print("❌ Failed to setup Google Sheets.")
        return

    try:
        # Create updater and dispatcher
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher

        # Add handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, get_product))

        print("✅ Bot is starting...")

        # Start polling
        updater.start_polling()
        updater.idle()

    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
