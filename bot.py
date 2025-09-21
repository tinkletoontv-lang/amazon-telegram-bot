import os
import gspread
import json
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from oauth2client.service_account import ServiceAccountCredentials

# Initialize global variables
sheet = None

def setup_google_sheets():
    global sheet
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        print("🔧 Setting up Google Sheets connection...")

        # Get credentials from environment variable
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS")

        if not credentials_json:
            print("❌ GOOGLE_CREDENTIALS environment variable not set!")
            return False

        print("✅ GOOGLE_CREDENTIALS found")

        # Parse JSON from environment variable
        creds_dict = json.loads(credentials_json)

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump(creds_dict, temp_file)
            temp_path = temp_file.name

        # Use file-based authentication
        creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)

        # Clean up temporary file
        os.unlink(temp_path)

        print("🔑 Credentials loaded, authorizing...")
        client = gspread.authorize(creds)
        print("✅ Authorized with Google Sheets API")

        # Open your sheet (must match Google Sheet name!)
        sheet = client.open("product_list").sheet1
        print("✅ Successfully connected to Google Sheets")
        return True

    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me a product number and I'll give you the link.")


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheet is None:
        await update.message.reply_text("⚠️ Service temporarily unavailable. Please try again later.")
        return

    product_number = update.message.text.strip()

    try:
        records = sheet.get_all_records()

        for row in records:
            # Accept multiple possible column names
            product_no = str(
                row.get("product_no", "")
                or row.get("Product No", "")
                or row.get("product_number", "")
                or row.get("Product Number", "")
            ).strip()

            if product_no == product_number:
                link = (
                    row.get("product_link", "")
                    or row.get("Product Link", "")
                    or row.get("link", "")
                    or row.get("URL", "")
                    or row.get("url", "")
                )

                if link:
                    product_name = (
                        row.get("product_name", "")
                        or row.get("Product Name", "")
                        or row.get("name", "")
                        or row.get("Name", "")
                        or f"Product {product_number}"
                    )
                    message = f"✅ Here is your product link:\n\n"
                    message += f"📦 Product: {product_name}\n"
                    message += f"🔢 Number: {product_number}\n"
                    message += f"🔗 Link: {product_link}"

                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("❌ Link not found for this product!")
                return

        await update.message.reply_text("❌ Product not found! Please check the product number.")

    except Exception as e:
        await update.message.reply_text("⚠️ Error accessing product database. Please try again later.")
        print(f"Error: {e}")


def main():
    print("🚀 Starting Telegram Bot...")

    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Error: BOT_TOKEN environment variable not set!")
        return

    if not setup_google_sheets():
        print("❌ Failed to setup Google Sheets. Bot will not start.")
        return

    try:
        app = Application.builder().token(token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_product))

        print("✅ Bot is running...")
        app.run_polling()

    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    main()
