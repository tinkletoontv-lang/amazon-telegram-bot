import os
import gspread
import json
import tempfile
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

# Initialize global variables
sheet = None

def setup_google_sheets():
    global sheet
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Method 1: Check if environment variable exists (for Render)
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
        
        if credentials_json:
            # Parse JSON from environment variable
            creds_dict = json.loads(credentials_json)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(creds_dict, temp_file)
                temp_path = temp_file.name
            
            # Use file-based authentication
            from oauth2client.service_account import ServiceAccountCredentials
            creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
        else:
            # Method 2: Use credentials.json file (for local development)
            from oauth2client.service_account import ServiceAccountCredentials
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
        client = gspread.authorize(creds)
        sheet = client.open("product_list").sheet1
        print("✅ Successfully connected to Google Sheets")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return False

def start(update, context):
    update.message.reply_text("👋 Hello! Send me a product number and I'll give you the link.")

def get_product(update, context):
    if sheet is None:
        update.message.reply_text("⚠️ Service temporarily unavailable. Please try again later.")
        return
        
    product_number = update.message.text.strip()
    
    try:
        records = sheet.get_all_records()
        
        for row in records:
            # Check multiple possible column names
            product_no = str(row.get("product_no", "") or row.get("Product No", "") or row.get("product_number", "") or row.get("Product Number", "")).strip()
            
            if product_no == product_number:
                link = row.get("product_link", "") or row.get("Product Link", "") or row.get("link", "") or row.get("URL", "") or row.get("url", "")
                
                if link:
                    product_name = row.get("product_name", "") or row.get("Product Name", "") or row.get("name", "") or row.get("Name", "") or f"Product {product_number}"
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

def main():
    # Setup Google Sheets first
    if not setup_google_sheets():
        print("❌ Failed to setup Google Sheets. Bot will not start.")
        return
    
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Error: BOT_TOKEN environment variable not set!")
        return
    
    try:
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_product))

        print("✅ Bot is starting...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
