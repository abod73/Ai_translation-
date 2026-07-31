"syntax-keyword">import asyncio
"syntax-keyword">import logging
"syntax-keyword">from bot "syntax-keyword">import Bot
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger

logger = setup_logger("Main")

"syntax-keyword">def main():
    logger.info("Starting AI Turkish Video Translator Bot...")
    logger.info(f"Python Version: 3.12")
    logger.info(f"GPU Support: {'Enabled' ">if Config.USE_GPU ">else 'Disabled'}")
    
    "syntax-keyword">try:
        bot = Bot()
        bot.run()
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.critical(f"Fatal Error: {e}", exc_info="syntax-keyword">True)

"syntax-keyword">if __name__ == "__main__":
    main()