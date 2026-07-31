"syntax-keyword">import aiosqlite
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import json

logger = setup_logger("Database")

"syntax-keyword">class Database:
    "syntax-keyword">def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_db()

    "syntax-keyword">async "syntax-keyword">def _get_conn(self):
        "syntax-keyword">return "syntax-keyword">await aiosqlite.connect(self.db_path)

    "syntax-keyword">def init_db(self):
        "syntax-keyword">import sqlite3
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT, join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS stats(id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, count INTEGER DEFAULT 0)''')
        c.execute('''INSERT OR IGNORE INTO stats(type, count) VALUES('downloads', 0)''')
        c.execute('''INSERT OR IGNORE INTO stats(type, count) VALUES('translations', 0)''')
        conn.commit()
        conn.close()

    "syntax-keyword">def add_user(self, user_id, username):
        "syntax-keyword">import sqlite3
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES(?, ?)", (user_id, username))
        conn.commit()
        conn.close()

    "syntax-keyword">def set_temp_video(self, user_id, info):
        "syntax-keyword">pass
        
    "syntax-keyword">def get_temp_video(self, user_id):
        "syntax-keyword">return "syntax-keyword">None