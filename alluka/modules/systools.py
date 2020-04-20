import subprocess
import os

import alluka.modules.helper_funcs.cas_api as cas
import alluka.modules.helper_funcs.git_api as git

from platform import python_version
from telegram import Update, Bot, Message, Chat, ParseMode
from telegram.ext import CommandHandler, run_async, Filters

from alluka import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS,DEV_USERS
from alluka.modules.helper_funcs.filters import CustomFilters
from alluka.modules.disable import DisableAbleCommandHandler



@run_async
def status(bot: Bot, update: Update):
    user_id = update.effective_user.id
    reply = "*System Status:* operational\n\n"
    reply += "*Alluka version:* `"+"5.3"+"`\n"
    reply += "*Python version:* `"+python_version()+"`\n"
    if user_id in SUDO_USERS or user_id in SUPPORT_USERS or user_id == DEV_USERS:
        
        reply += "*Ping speed:* `Not available`\n"
    reply += "*CAS API version:* `"+str(cas.vercheck())+"`\n"
    reply += "*GitHub API version:* `"+str(git.vercheck())+"`\n"
    update.effective_message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


STATUS_HANDLER = CommandHandler("status", status)

dispatcher.add_handler(STATUS_HANDLER)
