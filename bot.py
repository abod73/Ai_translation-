"syntax-keyword">from pyrogram "syntax-keyword">import Client, filters
"syntax-keyword">from pyrogram.types "syntax-keyword">import Message, InlineKeyboardMarkup, InlineKeyboardButton
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from handlers "syntax-keyword">import start_handler, link_handler, settings_handler
"syntax-keyword">from database "syntax-keyword">import Database
"syntax-keyword">from logger "syntax-keyword">import setup_logger

logger = setup_logger("BotCore")

"syntax-keyword">class Bot:
    "syntax-keyword">def __init__(self):
        self.app = Client(
            "TurkishTranslatorBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=50,
            sleep_threshold=60
        )
        self.db = Database()
        self.register_handlers()

    "syntax-keyword">def register_handlers(self):
        @self.app.on_message(filters.command("start"))
        "syntax-keyword">async "syntax-keyword">def start(client, message):
            "syntax-keyword">await start_handler(client, message, self.db)

        @self.app.on_message(filters.text & ~filters.command(["start", "settings"]))
        "syntax-keyword">async "syntax-keyword">def handle_link(client, message):
            "syntax-keyword">await link_handler(client, message, self.db)

        @self.app.on_callback_query()
        "syntax-keyword">async "syntax-keyword">def callback_router(client, callback_query):
            "syntax-keyword">from callback "syntax-keyword">import handle_callback
            "syntax-keyword">await handle_callback(client, callback_query, self.db)

    "syntax-keyword">def run(self):
        logger.info("Bot is running...")
        self.app.run()