import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open your sheet (replace with your sheet name)
sheet = client.open("product_list").sheet1

# --- Bot commands ---
def start(update, context):
    update.message.reply_text("👋 Hello! Send me a product number and I’ll give you the link.")

def get_product(update, context):
    product_number = update.message.text.strip()
    records = sheet.get_all_records()

    for row in records:
        if str(row.get("product_no")) == product_number:
            link = row.get("product_link", "No link found")
            update.message.reply_text(f"🔗 {link}")
            return
    
    update.message.reply_text("❌ Product not found!")

# --- Main function ---
def main():
    token = os.environ.get("BOT_TOKEN")  # from Render Environment Variables
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, get_product))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
