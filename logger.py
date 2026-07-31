"syntax-keyword">import logging
"syntax-keyword">import os
"syntax-keyword">from config "syntax-keyword">import Config

"syntax-keyword">def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    "syntax-keyword">if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        os.makedirs("logs", exist_ok="syntax-keyword">True)
        fh = logging.FileHandler(f"logs/{name.lower()}.log")
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        
        logger.addHandler(ch)
        logger.addHandler(fh)
        
    "syntax-keyword">return logger