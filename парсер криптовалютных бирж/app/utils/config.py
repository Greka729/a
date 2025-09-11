import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crypto.db")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
SUPPORTED_SYMBOLS = os.getenv(
    "SUPPORTED_SYMBOLS",
    "BTC,ETH,BNB,ADA,XRP,SOL,DOT,DOGE,AVAX,MATIC",
).split(",")


