import os
from dataclasses import dataclass

# Попытка загрузить .env файл, если установлен python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")


config = Config()

