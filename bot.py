import os
import gspread
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
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
            # Check for product number
            product_no = str(row.get("product_no", "") or 
                           row.get("Product No", "") or 
                           row.get("product_number", "")).strip()
            
            if product_no == product_number:
                link = row.get("product_link", "") or row.get("link", "") or row.get("URL", "")
                
                if link:
                    await update.message.reply_text(f"✅ Here is your product link:\n\n🔗 {link}")
                else:
                    await update.message.reply_text("❌ Link not found!")
                return
        
        await update.message.reply_text("❌ Product not found!")
        
    except Exception as e:
        await update.message.reply_text("⚠️ Error. Please try again later.")
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
        # Create application
        application = Application.builder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_product))
        
        print("✅ Bot is starting...")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
