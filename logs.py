__all__ = ["logger", "handler"]

from datetime import datetime
import logging.handlers
import os

import pytz

JP = pytz.timezone("Asia/Tokyo")
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    f"logs/{datetime.now(JP).strftime('%Y-%m-%d %H-%M-%S')}.log")

logger = logging.getLogger("WNHHelper")

handler = logging.handlers.RotatingFileHandler(
    filename=PATH,
    encoding="utf-8",
    maxBytes=100 * 1024,  # 100 KiB
    backupCount=5,  # Rotate through 5 files
)

fmt = "[{asctime}] [{levelname:<8}] {name}: {message}"
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt, dt_fmt, style="{")

logger.setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger("discord.http").setLevel(logging.WARNING)
handler.setFormatter(formatter)
logger.addHandler(handler)
