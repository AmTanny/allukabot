import html
import time
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import alluka.modules.sql.global_bans_sql as sql
from alluka import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from alluka.modules.helper_funcs.chat_status import user_admin, is_user_admin
from alluka.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from alluka.modules.helper_funcs.filters import CustomFilters
from alluka.modules.helper_funcs.misc import send_to_list
from alluka.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("I spy, with my little eye... a sudo user war! Why are you guys turning on each other?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH someone's trying to gban a support user! *grabs popcorn*")
        return

    if user_id == bot.id:
        message.reply_text("Nice try but I ain't gonna gban myself!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if user_chat.first_name == '':
        message.reply_text("That's a deleted account, no need to gban them!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text("This user is already gbanned; I'd change the reason, but you haven't given me one...")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            if old_reason == reason:
                message.reply_text("This user is already gbanned for the exact same reason!")
            else:
                message.reply_text("This user is already gbanned, for the following reason:\n"
                                   "<code>{}</code>\n"
                                   "I've gone and updated it with your new reason!".format(html.escape(old_reason)),
                                   parse_mode=ParseMode.HTML)
        else:
            message.reply_text("This user is already gbanned, but had no reason set; I've gone and updated it!")

        return

    message.reply_text("Starting a global ban for {}".format(mention_html(user_chat.id, user_chat.first_name)),
                       parse_mode=ParseMode.HTML)

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS,
                 "{} is gbanning user {} "
                 "because:\n{}".format(mention_html(banner.id, banner.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or "No reason given"),
                 html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not gban due to: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS, "Could not gban due to: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS, "Gban complete!")
    message.reply_text("Done! {} has been globally banned.".format(mention_html(user_chat.id, user_chat.first_name)),
                       parse_mode=ParseMode.HTML)

    try:
        bot.send_message(user_id, "You've been globally banned from all groups where I am admin. If this is a mistake, you can appeal your ban @allukatm or PM @zerotwopmbot",parse_mode=ParseMode.HTML)
    except:
        pass #Bot either blocked or never started by user


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("I'll give {} a second chance, globally.".format(mention_html(user_chat.id, user_chat.first_name)),
                       parse_mode=ParseMode.HTML)

    send_to_list(bot, SUDO_USERS,
                 "{} has ungbanned user {}".format(mention_html(banner.id, banner.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not un-gban due to: {}".format(excp.message))
                bot.send_message(OWNER_ID, "Could not un-gban due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS, "Un-gban complete!")

    message.reply_text("{} has been un-gbanned.".format(mention_html(user_chat.id, user_chat.first_name)),
                        parse_mode=ParseMode.HTML)


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("There aren't any gbanned users! You're kinder than I expected...")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="Here is the list of currently gbanned users.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("This is a bad person, they shouldn't be here!")


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("I've enabled gbans in this group. This will help protect you "
                                                "from spammers, unsavoury characters, and the biggest trolls.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("I've disabled gbans in this group. GBans wont affect your users "
                                                "anymore. You'll be less protected from any trolls and spammers "
                                                "though!")
    else:
        update.effective_message.reply_text("Give me some arguments to choose a setting! on/off, yes/no!\n\n"
                                            "Your current setting is: {}\n"
                                            "When True, any gbans that happen will also happen in your group. "
                                            "When False, they won't, leaving you at the possible mercy of "
                                            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


@run_async
def clear_gbans(bot: Bot, update: Update):
    '''Check and remove deleted accounts from gbanlist.
    By @TheRealPhoenix'''
    banned = sql.get_gban_list()
    deleted = 0
    for user in banned:
        id = user["user_id"]
        time.sleep(0.1) # Reduce floodwait
        try:
            acc = bot.get_chat(id)
            if not acc.first_name:
                deleted += 1
                sql.ungban_user(id)
        except BadRequest:
            deleted += 1
            sql.ungban_user(id)
    update.message.reply_text("Done! `{}` deleted accounts were removed " \
    "from the gbanlist.".format(deleted), parse_mode=ParseMode.MARKDOWN)
    

@run_async
def check_gbans(bot: Bot, update: Update):
    '''By @TheRealPhoenix'''
    banned = sql.get_gban_list()
    deleted = 0
    for user in banned:
        id = user["user_id"]
        time.sleep(0.1) # Reduce floodwait
        try:
            acc = bot.get_chat(id)
            if not acc.first_name:
                deleted += 1
        except BadRequest:
            deleted += 1
    if deleted:
        update.message.reply_text("`{}` deleted accounts found in the gbanlist! " \
        "Run /cleangb to remove them from the database!".format(deleted),
        parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("No deleted accounts in the gbanlist!")


def __stats__():
    return "{} gbanned users.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Globally banned: <b>{}</b>"
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: <code>{}</code>".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gbans*: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = """
*Admin only:*
 - /antispam <on/off/yes/no>: Check and/or change anti-spam settings.
Gbans, also known as global bans, are used by the bot owners to ban spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible. They can be disabled for your group by calling \
/antispam off.
"""

__mod_name__ = "Anti-Spam"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
CHECK_GBAN_HANDLER = CommandHandler("checkgb", check_gbans, filters=Filters.user(OWNER_ID))
CLEAN_GBAN_HANDLER = CommandHandler("cleangb", clear_gbans, filters=Filters.user(OWNER_ID))

GBAN_STATUS = CommandHandler("antispam", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)
dispatcher.add_handler(CHECK_GBAN_HANDLER)
dispatcher.add_handler(CLEAN_GBAN_HANDLER)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
