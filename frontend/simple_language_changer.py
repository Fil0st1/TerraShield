#!/usr/bin/env python3
"""
Simple Language Changer for TerraShield
Changes language via WhatsApp and saves to file
"""

import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from messages import translations

class SimpleLanguageChanger:
    def __init__(self):
        """Initialize the language changer"""
        load_dotenv()
        
        # Twilio configuration
        self.TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.TARGET_PHONE = "+918767840869"
        
        if not self.TWILIO_SID or not self.TWILIO_TOKEN:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
        
        # Initialize Twilio client
        self.twilio_client = Client(self.TWILIO_SID, self.TWILIO_TOKEN)
        
        # Current language
        self.current_language = self.get_current_language()
        
        print("✅ Simple Language Changer initialized")
        print(f"📱 Target phone: {self.TARGET_PHONE}")
        print(f"🌍 Current language: {self.current_language}")
    
    def get_current_language(self):
        """Get current language from file"""
        try:
            if os.path.exists("current_language.txt"):
                with open("current_language.txt", "r") as f:
                    language = f.read().strip()
                    if language in ["english", "hindi", "marathi"]:
                        return language
        except Exception as e:
            print(f"⚠️ Could not read language file: {e}")
        return "english"
    
    def set_language(self, language):
        """Set language and save to file"""
        valid_languages = ["english", "hindi", "marathi"]
        if language.lower() in valid_languages:
            self.current_language = language.lower()
            try:
                with open("current_language.txt", "w") as f:
                    f.write(self.current_language)
                print(f"🌍 Language set to: {self.current_language}")
                return True
            except Exception as e:
                print(f"❌ Could not save language: {e}")
        return False
    
    def get_language_selection_message(self):
        """Get language selection message"""
        return f"""🌍 **Language Selection**

Current language: **{self.current_language.title()}**

Please enter your preferred language:


"""
    
    def get_language_confirmation_message(self, language):
        """Get language confirmation message"""
        messages = {
            "english": f"✅ **Language Updated!**\n\nYour alert language has been set to: **{language.title()}**\n\nAll future landslide alerts will be sent in {language.title()}.",
            "hindi": f"✅ **भाषा अपडेट!**\n\nआपकी अलर्ट भाषा सेट की गई: **{language.title()}**\n\nभविष्य के सभी भूस्खलन अलर्ट {language.title()} में भेजे जाएंगे।",
            "marathi": f"✅ **भाषा अपडेट!**\n\nतुमची अलर्ट भाषा सेट केली: **{language.title()}**\n\nभविष्यातील सर्व मातीस्खलन अलर्ट {language.title()} मध्ये पाठवले जातील।"
        }
        return messages.get(language, messages["english"])
    
    def send_whatsapp_message(self, message):
        """Send WhatsApp message"""
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
    
    def handle_message(self, message_body):
        """Handle incoming message"""
        message = message_body.strip().lower()
        print(f"📨 Received: '{message}'")
        
        # Handle "hi" or "hello" - show language selection
        if message in ["hi", "hello", "hey", "start"]:
            selection_msg = self.get_language_selection_message()
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
            help_msg = f"""🤖 **TerraShield Language Changer**

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
    
    def run_webhook_server(self):
        """Run webhook server"""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route("/language-webhook", methods=["POST"])
        def webhook():
            try:
                incoming_msg = request.values.get("Body", "").strip()
                from_number = request.values.get("From", "").strip()
                
                print(f"📨 Webhook received from {from_number}: {incoming_msg}")
                
                if incoming_msg and from_number == f"whatsapp:{self.TARGET_PHONE}":
                    self.handle_message(incoming_msg)
                
                return jsonify({"status": "success"})
            except Exception as e:
                print(f"❌ Webhook error: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @app.route("/get-language", methods=["GET"])
        def get_language():
            """API endpoint to get current language"""
            return jsonify({"language": self.current_language})
        
        print("🚀 Starting simple language changer webhook server...")
        print("📡 Webhook URL: http://localhost:5001/language-webhook")
        print("🌍 Language API: http://localhost:5001/get-language")
        print("📱 Send 'hi' to your WhatsApp number to start")
        
        # Send initial message
        initial_msg = f"🤖 **TerraShield Language Changer Started**\n\nCurrent language: {self.current_language.title()}\n\nSend **hi** to change language"
        self.send_whatsapp_message(initial_msg)
        
        app.run(host="0.0.0.0", port=5001, debug=False)

def main():
    """Main function"""
    try:
        changer = SimpleLanguageChanger()
        changer.run_webhook_server()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
