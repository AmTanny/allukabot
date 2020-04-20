import html
import json
import random
import time
import pyowm
from pyowm import timeutils, exceptions
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram import Update, Bot
from telegram.ext import run_async

from stella.modules.disable import DisableAbleCommandHandler
from stella import dispatcher

from requests import get


@run_async
def ping(bot: Bot, update: Update):
    start_time = time.time()
    requests.get('http://meanii.me')
    end_time = time.time()
    ms = float(end_time - start_time)
    update.effective_message.reply_text("Pong!! {0:.2f}s 🏓".format(round(ms, 2) % 60), parse_mode=ParseMode.MARKDOWN)


__mod_name__ = "Ping"

PING_HANDLER = DisableAbleCommandHandler("ping", ping)

dispatcher.add_handler(PING_HANDLER)
