import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Use environment variable for credentials (more secure)
credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
if credentials_json:
    # For Render environment variable
    import json
    creds_dict = json.loads(credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    # For local development with file
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

# Open your sheet (replace with your sheet name)
sheet = client.open("product_list").sheet1

# --- Bot commands ---
def start(update, context):
    update.message.reply_text("👋 Hello! Send me a product number and I'll give you the link.")

def get_product(update, context):
    product_number = update.message.text.strip()
    
    try:
        records = sheet.get_all_records()
        
        for row in records:
            # Check both string and number formats
            if str(row.get("product_no", "")).strip() == product_number or str(row.get("Product No", "")).strip() == product_number:
                link = row.get("product_link", "") or row.get("Product Link", "") or row.get("URL", "") or row.get("Link", "")
                
                if link:
                    product_name = row.get("product_name", "") or row.get("Product Name", "") or row.get("Name", "") or f"Product {product_number}"
                    message = f"✅ Here is your product link:\n\n"
                    message += f"📦 Product: {product_name}\n"
                    message += f"🔢 Number: {product_number}\n"
                    message += f"🔗 Link: {link}"
                    
                    update.message.reply_text(message)
                else:
                    update.message.reply_text("❌ Link not found for this product!")
                return
        
        update.message.reply_text("❌ Product not found! Please check the product number.")
        
    except Exception as e:
        update.message.reply_text("⚠️ Error accessing product database. Please try again later.")
        print(f"Error: {e}")

# --- Main function ---
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN environment variable not set!")
        return
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_product))

    print("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
