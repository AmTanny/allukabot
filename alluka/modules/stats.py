import html
import re
from typing import List

import requests
from telegram import Bot, Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from alluka import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, DEV_USERS, WHITELIST_USERS
from alluka.__main__ import STATS, USER_INFO, TOKEN
from alluka.modules.disable import DisableAbleCommandHandler
from alluka.modules.helper_funcs.chat_status import user_admin, sudo_plus
from alluka.modules.helper_funcs.extraction import extract_user

@run_async
@sudo_plus
def stats(bot: Bot, update: Update):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)

STATS_HANDLER = CommandHandler("stats", stats)
dispatcher.add_handler(STATS_HANDLER)




