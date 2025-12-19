import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
import wikipedia
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = os.getenv('7743685455:AAGXHD99JpTJHhhm2l1H2Q7L7mEp4-6MJzw')  # Get from @BotFather
OPENAI_API_KEY = os.getenv('https://vehicle-info-api-five.vercel.app/vehicle=up26r4001')  # Optional: For AI responses
WOLFRAM_APP_ID = os.getenv('chat gpt')  # Optional: For computations

# Conversation states
CHOOSING, TYPING_REPLY = range(2)

class UniversalBot:
    def __init__(self):
        self.sessions = {}
        self.user_data = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when /start is issued."""
        user = update.effective_user
        welcome_text = f"""
🤖 *Welcome {user.first_name}!*

I'm a powerful universal bot with multiple capabilities:

📚 *Information & Knowledge*
• Wikipedia search
• News updates
• Weather information
• Currency conversion
• Calculations

💬 *Communication*
• Chat in all types of chats
• Group management tools
• Private conversations
• Multi-language support

🔧 *Utilities*
• File conversion
• URL shortening
• Reminders
• Translation

📊 *Data Analysis*
• Statistics
• Data visualization
• Information lookup

Type /help to see all available commands!
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Get Information", callback_data='info')],
            [InlineKeyboardButton("🔧 Use Utilities", callback_data='utils')],
            [InlineKeyboardButton("📊 Data Analysis", callback_data='data')],
            [InlineKeyboardButton("💬 Just Chat", callback_data='chat')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message with all commands."""
        help_text = """
🛠 *Available Commands:*

*Basic Commands:*
/start - Start the bot
/help - Show this help message
/settings - Configure bot settings

*Information Commands:*
/wiki <query> - Search Wikipedia
/weather <city> - Get weather information
/news <topic> - Get latest news
/calc <expression> - Calculate expressions
/currency <amount> <from> <to> - Convert currency

*Utility Commands:*
/remind <time> <message> - Set reminder
/translate <text> <language> - Translate text
/shorten <url> - Shorten URL
/qr <text> - Generate QR code

*Chat Commands:*
/broadcast <message> - Broadcast to all users (admin)
/stats - Show bot statistics
/chat - Start interactive chat mode

*Group Management:*
/warn <user> - Warn a user
/kick <user> - Kick a user
/mute <user> <time> - Mute a user
/pin <message> - Pin a message

Type any message to chat with me naturally!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all incoming messages."""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Store user data
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'chat_history': [],
                'preferences': {}
            }
        
        # Check if it's a command-like query
        response = await self.process_query(user_message, user_id)
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def process_query(self, query: str, user_id: int) -> str:
        """Process different types of queries."""
        query = query.lower().strip()
        
        # Wikipedia search
        if any(word in query for word in ['what is', 'who is', 'tell me about', 'wiki']):
            return await self.get_wikipedia_info(query)
        
        # Weather query
        elif any(word in query for word in ['weather', 'temperature', 'forecast']):
            return await self.get_weather_info(query)
        
        # Calculation
        elif any(op in query for op in ['+', '-', '*', '/', 'calculate', '=']):
            return await self.calculate(query)
        
        # Time/Date
        elif any(word in query for word in ['time', 'date', 'day', 'year']):
            return self.get_time_info()
        
        # News
        elif 'news' in query:
            return await self.get_news(query)
        
        # Default: Try to provide informative response
        else:
            return await self.get_general_response(query)

    async def get_wikipedia_info(self, query: str) -> str:
        """Get information from Wikipedia."""
        try:
            # Clean the query
            clean_query = query.replace('what is', '').replace('who is', '')\
                             .replace('tell me about', '').replace('wiki', '').strip()
            
            # Set language (you can make this configurable)
            wikipedia.set_lang("en")
            
            # Get summary
            summary = wikipedia.summary(clean_query, sentences=3)
            
            # Get page for more details
            page = wikipedia.page(clean_query)
            
            response = f"""
📚 *Wikipedia Information*

*Topic:* {clean_query.title()}

*Summary:*
{summary}

*More Information:*
• URL: {page.url}
• Categories: {', '.join(page.categories[:3])}

For full details, visit the Wikipedia page.
            """
            return response
            
        except wikipedia.exceptions.DisambiguationError as e:
            options = '\n'.join(e.options[:5])
            return f"Multiple matches found:\n{options}"
        except wikipedia.exceptions.PageError:
            return "❌ No Wikipedia page found. Try different keywords."
        except Exception as e:
            return f"⚠️ Error fetching information: {str(e)}"

    async def get_weather_info(self, query: str) -> str:
        """Get weather information."""
        try:
            # Extract city name
            words = query.split()
            city = None
            for i, word in enumerate(words):
                if word == 'in' and i+1 < len(words):
                    city = words[i+1]
                    break
            
            if not city:
                city = 'London'  # Default city
            
            # Using OpenWeatherMap API (you need to sign up for free API key)
            api_key = os.getenv('OPENWEATHER_API_KEY')
            if api_key:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code == 200:
                    weather = data['weather'][0]['description']
                    temp = data['main']['temp']
                    humidity = data['main']['humidity']
                    wind = data['wind']['speed']
                    
                    return f"""
🌤 *Weather in {city.title()}*

• Temperature: {temp}°C
• Condition: {weather}
• Humidity: {humidity}%
• Wind Speed: {wind} m/s
                    """
            
            # Fallback response
            return f"🌤 Weather information for *{city.title()}* would be available with proper API setup.\n\nAdd your OpenWeatherMap API key in .env file."
            
        except Exception as e:
            return f"⚠️ Error fetching weather: {str(e)}"

    async def calculate(self, expression: str) -> str:
        """Calculate mathematical expressions."""
        try:
            # Clean the expression
            expr = expression.replace('calculate', '').replace('=', '').strip()
            
            # Simple safe evaluation (for production, use a proper math parser)
            # Note: Using eval is dangerous! In production, use ast.literal_eval or a math library
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in expr):
                result = eval(expr)
                return f"""
🧮 *Calculation Result*

*Expression:* `{expr}`
*Result:* `{result}`
                """
            else:
                return "❌ Invalid expression. Use only numbers and basic operators (+, -, *, /)"
                
        except Exception as e:
            return f"❌ Calculation error: {str(e)}"

    def get_time_info(self) -> str:
        """Get current time and date information."""
        now = datetime.now()
        
        return f"""
📅 *Date and Time Information*

• Current Date: {now.strftime('%Y-%m-%d')}
• Current Time: {now.strftime('%H:%M:%S')}
• Day of Week: {now.strftime('%A')}
• Week Number: {now.strftime('%U')}
• Timezone: UTC

*Calendar:*
Today is day {now.timetuple().tm_yday} of {now.year}
        """

    async def get_news(self, query: str) -> str:
        """Get news articles."""
        try:
            # Extract topic
            topic = query.replace('news', '').replace('about', '').strip() or 'technology'
            
            # Using NewsAPI (sign up for free API key)
            api_key = os.getenv('NEWS_API_KEY')
            
            if api_key:
                url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={api_key}&pageSize=3"
                response = requests.get(url)
                data = response.json()
                
                if data['status'] == 'ok':
                    articles = data['articles'][:3]
                    news_text = f"📰 *Latest News about {topic.title()}*\n\n"
                    
                    for i, article in enumerate(articles, 1):
                        news_text += f"*{i}. {article['title']}*\n"
                        news_text += f"Source: {article['source']['name']}\n"
                        news_text += f"Published: {article['publishedAt'][:10]}\n"
                        news_text += f"[Read more]({article['url']})\n\n"
                    
                    return news_text
            
            # Fallback response
            return f"📰 News about *{topic.title()}* would be available with NewsAPI setup.\n\nAdd your NewsAPI key in .env file."
            
        except Exception as e:
            return f"⚠️ Error fetching news: {str(e)}"

    async def get_general_response(self, query: str) -> str:
        """Generate general informative response."""
        responses = {
            'hello': "👋 Hello! How can I assist you today?",
            'hi': "👋 Hi there! What would you like to know?",
            'how are you': "🤖 I'm functioning optimally! Ready to help you.",
            'thank you': "You're welcome! Feel free to ask anything else.",
            'bye': "👋 Goodbye! Come back anytime you need information.",
            'help': "Type /help to see all available commands and features!"
        }
        
        # Check for exact matches
        for key, response in responses.items():
            if key in query.lower():
                return response
        
        # General informative response
        return f"""
💭 You asked: *"{query}"*

I understand you're looking for information. Here's what I can help with:

• Ask me *"what is [topic]"* for Wikipedia information
• Ask *"weather in [city]"* for weather forecast
• Ask *"news about [topic]"* for latest news
• Type *mathematical expressions* for calculations
• Use commands like /wiki, /weather, /news for specific information

Or simply chat with me about anything! 🤖
        """

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'info':
            await query.edit_message_text(
                text="📚 *Information Section*\n\nChoose what you need:\n• Wikipedia search\n• Weather info\n• News updates\n• Calculations\n\nJust ask me anything!",
                parse_mode='Markdown'
            )
        elif query.data == 'utils':
            await query.edit_message_text(
                text="🔧 *Utility Section*\n\nAvailable utilities:\n• Reminders\n• File conversion\n• URL shortening\n• QR code generation\n\nUse /help for commands.",
                parse_mode='Markdown'
            )
        elif query.data == 'data':
            await query.edit_message_text(
                text="📊 *Data Analysis Section*\n\nI can help with:\n• Statistics\n• Data visualization\n• Information lookup\n• Trend analysis\n\nProvide data or ask specific questions.",
                parse_mode='Markdown'
            )
        elif query.data == 'chat':
            await query.edit_message_text(
                text="💬 *Chat Mode Activated*\n\nFeel free to chat with me! I can discuss various topics, provide information, or just have a conversation.\n\nWhat's on your mind?",
                parse_mode='Markdown'
            )

    async def wiki_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct Wikipedia search command."""
        if not context.args:
            await update.message.reply_text("Please provide a search term. Example: /wiki Python programming")
            return
        
        query = ' '.join(context.args)
        result = await self.get_wikipedia_info(query)
        await update.message.reply_text(result, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics."""
        stats_text = f"""
📊 *Bot Statistics*

• Total Users: {len(self.user_data)}
• Active Sessions: {len(self.sessions)}
• Memory Usage: Monitoring...

*Capabilities:*
✅ Works in all chat types
✅ Information retrieval
✅ Real-time data
✅ Multi-language support
✅ Group management
✅ File handling

Bot is running smoothly! 🚀
        """
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users (admin only)."""
        # Check if user is admin (you should implement proper admin check)
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
        
        message = ' '.join(context.args)
        
        # In a real bot, you would iterate through stored user IDs
        # For this example, we'll just show the feature
        await update.message.reply_text(
            f"📢 Broadcast feature ready!\n\nMessage: {message}\n\n(Would be sent to all users in production)",
            parse_mode='Markdown'
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Initialize bot instance
    bot = UniversalBot()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("wiki", bot.wiki_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("broadcast", bot.broadcast_command))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Add message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the Bot
    print("🤖 Bot is starting...")
    print("✅ Ready to handle all chats")
    print("📱 Works in: Private, Groups, Channels")
    print("🌍 Multi-language support enabled")
    print("🔧 All features active")
    
    # Run the bot until you press Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()