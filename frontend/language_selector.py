#!/usr/bin/env python3
"""
TerraShield Language Selector
Allows users to change alert language via WhatsApp
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from twilio.rest import Client

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from messages import translations

class LanguageSelector:
    def __init__(self):
        """Initialize the language selector"""
        load_dotenv()
        
        # Supabase configuration
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        # Twilio configuration
        self.TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.TARGET_PHONE = "+918767840869"  # Your phone number
        
        if not self.TWILIO_SID or not self.TWILIO_TOKEN:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables")
        
        # Initialize clients
        self.supabase = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.twilio_client = Client(self.TWILIO_SID, self.TWILIO_TOKEN)
        
        # Current language (stored in memory, you can persist this)
        self.current_language = "english"
        
        print("✅ Language Selector initialized successfully")
        print(f"📱 Target phone: {self.TARGET_PHONE}")
        print(f"🌍 Current language: {self.current_language}")
    
    def create_user_prefs_table(self):
        """Create user_prefs table if it doesn't exist"""
        try:
            # Try to create the table
            self.supabase.rpc('create_user_prefs_table').execute()
            print("✅ Created user_prefs table")
        except Exception as e:
            print(f"ℹ️ Table might already exist: {e}")
    
    def set_language(self, language):
        """Set the current language"""
        valid_languages = ["english", "hindi", "marathi"]
        if language.lower() in valid_languages:
            self.current_language = language.lower()
            print(f"🌍 Language set to: {self.current_language}")
            return True
        return False
    
    def get_language_selection_message(self, lang="english"):
        """Get language selection message in specified language"""
        messages = {
            "english": "🌍 **Language Selection**\n\nPlease select your preferred language:\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Marathi (मराठी)\n\nType: **english**, **hindi**, or **marathi**",
            "hindi": "🌍 **भाषा चयन**\n\nकृपया अपनी पसंदीदा भाषा चुनें:\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Marathi (मराठी)\n\nटाइप करें: **english**, **hindi**, या **marathi**",
            "marathi": "🌍 **भाषा निवड**\n\nकृपया आपली आवडती भाषा निवडा:\n\n1️⃣ English\n2️⃣ Hindi (हिंदी)\n3️⃣ Marathi (मराठी)\n\nटाइप करा: **english**, **hindi**, किंवा **marathi**"
        }
        return messages.get(lang, messages["english"])
    
    def get_language_confirmation_message(self, language):
        """Get language confirmation message"""
        messages = {
            "english": f"✅ **Language Updated!**\n\nYour alert language has been set to: **{language.title()}**\n\nAll future landslide alerts will be sent in {language.title()}.",
            "hindi": f"✅ **भाषा अपडेट!**\n\nआपकी अलर्ट भाषा सेट की गई: **{language.title()}**\n\nभविष्य के सभी भूस्खलन अलर्ट {language.title()} में भेजे जाएंगे।",
            "marathi": f"✅ **भाषा अपडेट!**\n\nतुमची अलर्ट भाषा सेट केली: **{language.title()}**\n\nभविष्यातील सर्व मातीस्खलन अलर्ट {language.title()} मध्ये पाठवले जातील।"
        }
        return messages.get(language, messages["english"])
    
    def send_whatsapp_message(self, message):
        """Send WhatsApp message to target phone"""
        try:
            message_obj = self.twilio_client.messages.create(
                from_=self.FROM_WHATSAPP,
                to=f"whatsapp:{self.TARGET_PHONE}",
                body=message
            )
            print(f"📤 Message sent (SID: {message_obj.sid})")
            return True
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
    
    def handle_incoming_message(self, message_body, from_number):
        """Handle incoming WhatsApp message"""
        message = message_body.strip().lower()
        
        print(f"📨 Received: '{message}' from {from_number}")
        
        # Check if it's from the target phone
        if from_number != self.TARGET_PHONE:
            print("⚠️ Message not from target phone, ignoring")
            return
        
        # Handle "hi" or "hello" - show language selection
        if message in ["hi", "hello", "hey", "start"]:
            selection_msg = self.get_language_selection_message(self.current_language)
            self.send_whatsapp_message(selection_msg)
            return
        
        # Handle language selection
        if message in ["english", "hindi", "marathi", "en", "hi", "mr"]:
            # Map short forms to full names
            lang_map = {"en": "english", "hi": "hindi", "mr": "marathi"}
            selected_lang = lang_map.get(message, message)
            
            if self.set_language(selected_lang):
                confirmation_msg = self.get_language_confirmation_message(selected_lang)
                self.send_whatsapp_message(confirmation_msg)
            else:
                error_msg = f"❌ Invalid language: {message}\n\nPlease select: english, hindi, or marathi"
                self.send_whatsapp_message(error_msg)
            return
        
        # Handle current language query
        if message in ["language", "lang", "current language"]:
            current_msg = f"🌍 **Current Language:** {self.current_language.title()}\n\nTo change language, send: **hi**"
            self.send_whatsapp_message(current_msg)
            return
        
        # Handle help
        if message in ["help", "commands"]:
            help_msg = """🤖 **TerraShield Language Selector**

**Commands:**
• **hi** - Show language selection
• **language** - Show current language
• **english/hindi/marathi** - Set language
• **help** - Show this help

**Current Language:** {self.current_language.title()}"""
            self.send_whatsapp_message(help_msg)
            return
        
        # Default response
        default_msg = f"🤖 I didn't understand that.\n\nSend **hi** to change language or **help** for commands.\n\nCurrent language: {self.current_language.title()}"
        self.send_whatsapp_message(default_msg)
    
    def get_current_language(self):
        """Get current language for use by other scripts"""
        return self.current_language
    
    def run_webhook_server(self):
        """Run a simple webhook server to receive WhatsApp messages"""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route("/language-webhook", methods=["POST"])
        def webhook():
            try:
                incoming_msg = request.values.get("Body", "").strip()
                from_number = request.values.get("From", "").strip()
                
                if incoming_msg and from_number:
                    self.handle_incoming_message(incoming_msg, from_number)
                
                return jsonify({"status": "success"})
            except Exception as e:
                print(f"❌ Webhook error: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @app.route("/get-language", methods=["GET"])
        def get_language():
            """API endpoint to get current language"""
            return jsonify({"language": self.current_language})
        
        @app.route("/set-language", methods=["POST"])
        def set_language_api():
            """API endpoint to set language"""
            try:
                data = request.get_json()
                language = data.get("language", "").lower()
                
                if self.set_language(language):
                    return jsonify({"status": "success", "language": self.current_language})
                else:
                    return jsonify({"status": "error", "message": "Invalid language"}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        print("🚀 Starting language selector webhook server...")
        print("📡 Webhook URL: http://localhost:5001/language-webhook")
        print("🌍 Language API: http://localhost:5001/get-language")
        print("📱 Send 'hi' to your WhatsApp number to start")
        
        app.run(host="0.0.0.0", port=5001, debug=False)

def main():
    """Main function"""
    try:
        selector = LanguageSelector()
        
        # Send initial message
        initial_msg = f"🤖 **TerraShield Language Selector Started**\n\nCurrent language: {selector.current_language.title()}\n\nSend **hi** to change language"
        selector.send_whatsapp_message(initial_msg)
        
        # Start webhook server
        selector.run_webhook_server()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
