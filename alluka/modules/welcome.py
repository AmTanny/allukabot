import html, time
import re
from typing import Optional, List

import alluka.modules.helper_funcs.cas_api as cas

from telegram import Message, Chat, Update, Bot, User, CallbackQuery, ChatMember, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from telegram.error import BadRequest
from alluka import dispatcher, ALLUKA, KITE, HISOKA, GING, SHIZUKU, SILVA, GON, ILLUMI_ZOLDYCK, LEORIO, BISCUIT, CHROLLO, KILLUA, MERUEM
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async, CallbackQueryHandler
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown

import alluka.modules.sql.welcome_sql as sql
import alluka.modules.sql.global_bans_sql as gbansql
import alluka.modules.sql.users_sql as userssql

from alluka import dispatcher, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS
from alluka.modules.helper_funcs.chat_status import user_admin, can_delete, is_user_ban_protected
from alluka.modules.helper_funcs.misc import build_keyboard, revert_buttons, send_to_list
from alluka.modules.helper_funcs.msg_types import get_welcome_type
from alluka.modules.helper_funcs.extraction import extract_user
from alluka.modules.disable import DisableAbleCommandHandler
from alluka.modules.helper_funcs.filters import CustomFilters
from alluka.modules.helper_funcs.string_handling import markdown_parser, escape_invalid_curly_brackets
from alluka.modules.log_channel import loggable

VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'count', 'chatname', 'mention']

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


ALLUKA_BYE = 'CAACAgUAAxkBAAIH1V5ndElxrCQ7u4DArzlZEG55xEyWAAJJAQAC3pTNL9hDGCPpDeX8GAQ'
HISOKA_WELCOME = 'CAACAgUAAxkBAAIIMV5nn5yc1DYg1O1CoeJHvVAzCqthAAICAQAC3pTNL5i4rHpWUFe2GAQ'
HISOKA_BYE = "CAACAgUAAxkBAAIISl5no3bh-m5aeydeL3SCh9DxVF4YAAJDAANI39Y3nfMSlYtyINIYBA"

ALLUKA_IMG = 'https://telegra.ph/file/1ca41b5335290524eee7d.jpg'
HISOKA_IMG = "https://telegra.ph/file/4aee5cfe2ba8a3fa503d0.jpg"
GING_IMG = "https://telegra.ph/file/22a1c264865bd07af7556.png"
SHIZUKU_IMG =  "https://telegra.ph/file/31fcbda7396fb94d7fc62.png"
SILVA_IMG = "https://telegra.ph/file/37bf67a10d77b9661bec1.png"
GON_IMG = "https://telegra.ph/file/8f5d722e7f29da3226f03.png"
ILLUMI_ZOLDYCK_IMG = "https://telegra.ph/file/689f2d3b1f5f2ae4d3005.png"
LEORIO_IMG = "https://telegra.ph/file/16cc60c94d7ff535e3957.png"
BISCUIT_IMG = "https://telegra.ph/file/f3439e1ea77e6f4a2d6bb.png"
CHROLLO_IMG = "https://telegra.ph/file/d4888fcbdeb3261a2a9cf.png"
KILLUA_IMG = "https://telegra.ph/file/335efcdd8ffb462371582.png"
MEANII_IMG = "https://telegra.ph/file/633307eb7b142003c096c.jpg"
MERUEM_IMG = "https://telegra.ph/file/348ae7fcba0116a9a4314.jpg"
KITE_IMG = "https://telegra.ph/file/520c4b38b71f82e312f5b.png"


# do not async
def send(update, message, keyboard, backup_message):
    try:
        msg = update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except IndexError:
        msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                  "\nNote: the current message was "
                                                                  "invalid due to markdown issues. Could be "
                                                                  "due to the user's name."),
                                                  parse_mode=ParseMode.MARKDOWN)
    except KeyError:
        msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                  "\nNote: the current message is "
                                                                  "invalid due to an issue with some misplaced "
                                                                  "curly brackets. Please update"),
                                                  parse_mode=ParseMode.MARKDOWN)
    except BadRequest as excp:
        if excp.message == "Have no rights to send a message":
            return
        elif excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nNote: the current message has an invalid url "
                                                                      "in one of its buttons. Please update."),
                                                      parse_mode=ParseMode.MARKDOWN)
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nNote: the current message has buttons which "
                                                                      "use url protocols that are unsupported by "
                                                                      "telegram. Please update."),
                                                      parse_mode=ParseMode.MARKDOWN)
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nNote: the current message has some bad urls. "
                                                                      "Please update."),
                                                      parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! got invalid url host errors")
        else:
            if update.effective_message:
                msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                          "\nNote: An error occured when sending the "
                                                                          "custom message. Please update."),
                                                          parse_mode=ParseMode.MARKDOWN)
            LOGGER.exception()

    return msg

@run_async
def new_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message # type: Optional[Message]
    chat_name = chat.title or chat.first or chat.username # type: Optional:[chat name]
    should_welc, cust_welcome, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    casPrefs = sql.get_cas_status(str(chat.id)) #check if enabled, obviously
    autoban = sql.get_cas_autoban(str(chat.id))
    chatbanned = sql.isBanned(str(chat.id))
    defense = sql.getDefenseStatus(str(chat.id))
    time_value = sql.getKickTime(str(chat.id))
    if chatbanned:
        bot.leave_chat(int(chat.id))
    elif casPrefs and not autoban and cas.banchecker(user.id):
        bot.restrict_chat_member(chat.id, user.id, 
                                         can_send_messages=False,
                                         can_send_media_messages=False, 
                                         can_send_other_messages=False, 
                                         can_add_web_page_previews=False)
        msg.reply_text("Warning! This user is CAS Banned. I have muted them to avoid spam. Ban is advised.")
        isUserGbanned = gbansql.is_user_gbanned(user.id)
        if not isUserGbanned:
            report = "CAS Banned user detected: <code>{}</code>".format(user.id)
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS, report, html=True)
        if defense:
            bantime = int(time.time()) + 60
            chat.kick_member(new_mem.id, until_date=bantime)
    elif casPrefs and autoban and cas.banchecker(user.id):
        chat.kick_member(user.id)
        msg.reply_text("CAS banned user detected! User has been automatically banned!")
        isUserGbanned = gbansql.is_user_gbanned(user.id)
        if not isUserGbanned:
            report = "CAS Banned user detected: <code>{}</code>".format(user.id)
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS, report, html=True)
    elif defense and (user.id not in SUDO_USERS + SUPPORT_USERS):
        bantime = int(time.time()) + 60
        chat.kick_member(user.id, until_date=bantime)
    elif should_welc:
        sent = None
        new_members = update.effective_message.new_chat_members
        for new_mem in new_members:
            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text("My master is just join your group.")
                continue
            elif new_mem.id in ALLUKA:
                update.effective_message.reply_photo(ALLUKA_IMG,"Woah! I just join this family!\n <i>If you're nice to me, you have to be nice to Nanika too!! If you're going to protect me, you have to protect Nanika too!! But if you're going to be mean to Nanika, I hate you!!</i>\n To know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                bot.send_sticker(chat.id, BAN_STICKER) 
                continue

            # Welcome SUNNY
            elif new_mem.id in HISOKA:
                update.effective_message.reply_photo(HISOKA_IMG,"blop! blop! <b>Hisoka Morow</b> join your family!\n <i>'My greatest pleasure comes when such people crumple to their knees and I look down upon their disbelieving faces as their plans fail.♥'</i>\nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                bot.send_sticker(chat.id, HISOKA_WELCOME) 
                continue
            
            # Welcome BHAVIK
            elif new_mem.id in GING:
                update.effective_message.reply_photo(GING_IMG,"haye!! <b>Ging</b> is just join your family!!\n <i>I'm enjoying the journey. So if your destination is the same as mine, enjoy the side trips. A lot. Something more important than the thing you're hunting could be right there by the side of the road.'</i>\nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue
        
            # Welcome Whitelisted
            elif new_mem.id in SHIZUKU:
                update.effective_message.reply_photo(SHIZUKU_IMG,"oh!! <b>Shizuku Murasaki</b> (シズク゠ムラサキ, Shizuku Murasaki) is just join your family!! \n<i>'Breaking the rules means rejecting the Spiders, and Chrollo, too. That I never want to do.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue        
            
            elif new_mem.id in SILVA:
                update.effective_message.reply_photo(SILVA_IMG,"Woaw!! My father is just enter!!<b>Silva Zoldyck </b> (シズク゠ムラサキ, Shizuku Murasaki) is just join this family!! \n<i>''Never overreach your limits...! Make your move only when you're 100% positive you can make the kill. Otherwise, bide your time...!! It's foolish to show your hand when the odds are against you.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue       
            
            elif new_mem.id in GON:
                update.effective_message.reply_photo(GON_IMG,"Woaw!! <b>Gon Freecss (ゴン゠フリークス, Gon Furīkusu)</b>is just join this family!! \n<i>''I can't stand being on the losing end forever!!'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue        
            
            elif new_mem.id in ILLUMI_ZOLDYCK:
                update.effective_message.reply_photo(ILLUMI_ZOLDYCK_IMG,"Haye!! My elder brother <b>Illumi Zoldyck (イルミ゠ゾルディック, Irumi Zorudikku) is just join this family!!</b> just enter here.\n<i>''Now I can tell you, that you would not make a good Hunter. Your calling is as an assassin. There's no fire in you, just darkness. It sustains you, drains you of any desire. Your only joy is in causing death, and even that is fleeting. That is how Dad and I molded you.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue       
            
            elif new_mem.id in LEORIO:
                update.effective_message.reply_photo(LEORIO_IMG,"woh!! The simple guy  <b>Leorio Paradinight</b> is just join this family!!\n<i>'I'm a simple guy. Figured I'd become a doctor... so I could cure some kid with the same disease, tell his parents they owed me nothing! Me... A doctor! Now there's a joke!! Do you know how much it costs to even try to become a doctor? The mind boggles!! It's always about money! Always!! That's why I want it!'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue        
            
            elif new_mem.id in BISCUIT:
                update.effective_message.reply_photo(BISCUIT_IMG,"Haye!! The sleeveless girl  <b>Biscuit Krueger</b> is just join this family!!\n<i>'After 50 years of lying through my teeth, I can tell whether someone's telling the truth.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue    
            
            elif new_mem.id in CHROLLO:
                update.effective_message.reply_photo(CHROLLO_IMG,"wow!! The founder and leader of the Phantom Troupe <b>Chrollo Lucilfer</b> is just join your family!!\n<i>'Making the abilities yours while exploring the darkness within the soul of the original owner... that's the true pleasure of Skill Hunter.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue      
            
            elif new_mem.id in KILLUA:
                update.effective_message.reply_photo(KILLUA_IMG,"wow!! My bro <b>Killua Zoldyck </b> is just join your family!!\n<i>'I'm so tired of killing... I just want to be a kid. Hanging out, doing stuff with Gon. That's it.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue       
          
            elif new_mem.id in MERUEM:
                update.effective_message.reply_photo(MERUEM_IMG,"wow!! <b>Meruem </b> is HERE!!\n<i>'Who am I? Why am I here? A king with no name. A borrowed castle. My subjects are mindless drones. If this is the mandate of Heaven I have been given... I fear... I fear nothing... except the tedium that it will bring!!!'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue     
             
            elif new_mem.id in KITE:
                update.effective_message.reply_photo(KITE_IMG,"wow!! <b>Kite  (カイト)</b> is HERE!!\n<i>'Kite is killed by Neferpitou, but is soon rebuilt into a manipulated puppet to train the ants. He is later captured by Knuckle and Shoot.'</i> \nTo know about my family do /familylist ",parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                continue       
            # Make bot greet admins
            elif new_mem.id == bot.id:
                update.effective_message.reply_text("Hey {}, I'm {}! Thank you for adding me to {}" 
                " and be sure to check /help in PM for more commands and tricks!".format(user.first_name, bot.first_name, chat_name))

            else:
                # If welcome message is media, send with appropriate function
                if welc_type != sql.Types.TEXT and welc_type != sql.Types.BUTTON_TEXT:
                    ENUM_FUNC_MAP[welc_type](chat.id, cust_welcome)
                    return
                # else, move on
                first_name = new_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if new_mem.last_name:
                        fullname = "{} {}".format(first_name, new_mem.last_name)
                    else:
                        fullname = first_name
                    count = chat.get_members_count()
                    mention = mention_markdown(new_mem.id, first_name)
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(cust_welcome, VALID_WELCOME_FORMATTERS)
                    res = valid_format.format(first=escape_markdown(first_name),
                                              last=escape_markdown(new_mem.last_name or first_name),
                                              fullname=escape_markdown(fullname), username=username, mention=mention,
                                              count=count, chatname=escape_markdown(chat.title), id=new_mem.id)
                    buttons = sql.get_welc_buttons(chat.id)
                    keyb = build_keyboard(buttons)
                else:
                    res = sql.DEFAULT_WELCOME.format(first=first_name)
                    keyb = []

                keyboard = InlineKeyboardMarkup(keyb)

                sent = send(update, res, keyboard,
                            sql.DEFAULT_WELCOME.format(first=first_name))  # type: Optional[Message]
            
                
                #Sudo user exception from mutes:
                if is_user_ban_protected(chat, new_mem.id, chat.get_member(new_mem.id)):
                    continue

                #Safe mode
                newMember = chat.get_member(int(new_mem.id))
                if welc_mutes == "on" and ((newMember.can_send_messages is None or newMember.can_send_messages)):
                    buttonMsg = msg.reply_text("Click the button below to prove you're human",
                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="I'm not a bot! 🤖", 
                         callback_data="userverify_({})".format(new_mem.id))]]))
                    bot.restrict_chat_member(chat.id, new_mem.id, 
                                             can_send_messages=False, 
                                             can_send_media_messages=False, 
                                             can_send_other_messages=False, 
                                             can_add_web_page_previews=False)
                        
            delete_join(bot, update)

        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest as excp:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)

@run_async
def left_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    if should_goodbye:
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            # Ignore bot being kicked
            if left_mem.id == bot.id:
                return

            # Give the owner a special goodbye
            elif left_mem.id in ALLUKA:
                update.effective_message.reply_text("My brother KILLUA is gonna kill you!!")
                bot.send_sticker(chat.id, ALLUKA_BYE)
                return

            elif left_mem.id in HISOKA:
                update.effective_message.reply_text("Don't warry I'll comeback SOON!! ")
                bot.send_sticker(chat.id, HISOKA_BYE)
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = left_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_members_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(cust_goodbye, VALID_WELCOME_FORMATTERS)
                res = valid_format.format(first=escape_markdown(first_name),
                                          last=escape_markdown(left_mem.last_name or first_name),
                                          fullname=escape_markdown(fullname), username=username, mention=mention,
                                          count=count, chatname=escape_markdown(chat.title), id=left_mem.id)
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)

@run_async
@user_admin
def welcome(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    # if no args, show current replies.
    if len(args) == 0 or args[0].lower() == "noformat":
        noformat = args and args[0].lower() == "noformat"
        pref, welcome_m, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's welcome setting set to: `{}`.\n*The welcome message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if welcome_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

        else:
            if noformat:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m)

            else:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m, parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text("I'm sulking, not saying hello anymore.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")

@run_async
@user_admin
def goodbye(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's goodbye setting set to: `{}`.\n*The goodbye  message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be sorry when people leave!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("They leave, they're dead to me.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")

@run_async
@user_admin
@loggable
def set_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_welcome(chat.id, content or text, data_type, buttons)
    msg.reply_text("Successfully set custom welcome message!")

    return "<b>{}:</b>" \
           "\n#SET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nSet the welcome message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))

@run_async
@user_admin
@loggable
def reset_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_welcome(chat.id, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text("Successfully reset welcome message to default!")
    return "<b>{}:</b>" \
           "\n#RESET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nReset the welcome message to default.".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name))

@run_async
@user_admin
@loggable
def set_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Successfully set custom goodbye message!")
    return "<b>{}:</b>" \
           "\n#SET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nSet the goodbye message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))

@run_async
@user_admin
@loggable
def reset_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text("Successfully reset goodbye message to default!")
    return "<b>{}:</b>" \
           "\n#RESET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nReset the goodbye message.".format(html.escape(chat.title),
                                                 mention_html(user.id, user.first_name))

@run_async
@user_admin
@loggable
def safemode(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message # type: Optional[Message]
    
    if len(args) >= 1:
        if  args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            msg.reply_text("I will no longer mute people on joining!")
            return "<b>{}:</b>" \
                   "\n#SAFE_MODE" \
                   "\n<b>• Admin:</b> {}" \
                   "\nHas toggled welcome mute to <b>OFF</b>.".format(html.escape(chat.title),
                                                                      mention_html(user.id, user.first_name))
        elif args[0].lower() in ("on", "yes"):
             sql.set_welcome_mutes(chat.id, "on")
             msg.reply_text("I will now mute people when they join and"
                           " click on the button to be unmuted.")
             return "<b>{}:</b>" \
                    "\n#SAFE_MODE" \
                    "\n<b>• Admin:</b> {}" \
                    "\nHas toggled welcome mute to <b>ON</b>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
        else:
            msg.reply_text("Please enter `on`/`off`!", parse_mode=ParseMode.MARKDOWN)
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = "\n Give me a setting! Choose one of `on`/`yes` or `off`/`no` only! \nCurrent setting: `{}`"
        msg.reply_text(reply.format(curr_setting), parse_mode=ParseMode.MARKDOWN)
        return ""

@run_async
@user_admin
@loggable
def clean_welcome(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text("I should be deleting welcome messages up to two days old.")
        else:
            update.effective_message.reply_text("I'm currently not deleting old welcome messages!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text("I'll try to delete old welcome messages!")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>ON</code>.".format(html.escape(chat.title),
                                                                         mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text("I won't delete old welcome messages.")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>OFF</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""

@run_async
@user_admin
@loggable
def del_joined(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        del_pref = sql.get_del_pref(chat.id)
        if del_pref:
            update.effective_message.reply_text("I should be deleting `user` joined the chat messages now.")
        else:
            update.effective_message.reply_text("I'm currently not deleting old joined messages!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_del_joined(str(chat.id), True)
        update.effective_message.reply_text("I'll try to delete old joined messages!")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>ON</code>.".format(html.escape(chat.title),
                                                                         mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_del_joined(str(chat.id), False)
        update.effective_message.reply_text("I won't delete old joined messages.")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled joined deletion to <code>OFF</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""

@run_async
def delete_join(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    join = update.effective_message.new_chat_members
    if can_delete(chat, bot.id):
        del_join = sql.get_del_pref(chat.id)
        if del_join and update.message:
            update.message.delete()
            
@run_async
def user_button(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    query = update.callback_query  # type: Optional[CallbackQuery]
    match = re.match(r"userverify_\((.+?)\)", query.data)
    message = update.effective_message  # type: Optional[Message]
    join_user =  int(match.group(1))
    
    if join_user == user.id:
        query.answer(text="Yup, you're very human, you have now the right to speak!")
        bot.restrict_chat_member(chat.id, user.id, can_send_messages=True, 
                                                   can_send_media_messages=False, 
                                                   can_send_other_messages=False, 
                                                   can_add_web_page_previews=False,
                                                   until_date=(int(time.time() + 24 * 60 * 60)))
        bot.deleteMessage(chat.id, message.message_id)
    else:
        query.answer(text="You are not new user.")

@run_async
@user_admin
def setcas(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg)!= 2:
        msg.reply_text("Invalid arguments!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_status(chat.id, True)
        msg.reply_text("Successfully updated configuration.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_status(chat.id, False)
        msg.reply_text("Successfully updated configuration.")
        return
    else:
        msg.reply_text("Invalid status to set!") #on or off ffs
        return

@run_async
@user_admin
def setban(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg)!= 2:
        msg.reply_text("Invalid arguments!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_autoban(chat.id, True)
        msg.reply_text("Successfully updated configuration.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_autoban(chat.id, False)
        msg.reply_text("Successfully updated configuration.")
        return
    else:
        msg.reply_text("Invalid autoban definition to set!") #on or off ffs
        return

@run_async
@user_admin
def get_current_setting(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    stats = sql.get_cas_status(chat.id)
    autoban = sql.get_cas_autoban(chat.id)
    rtext = "<b>CAS Preferences</b>\n\nCAS Checking: {}\nAutoban: {}".format(stats, autoban)
    msg.reply_text(rtext, parse_mode=ParseMode.HTML)
    return

@run_async
@user_admin
def getTimeSetting(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    timeSetting = sql.getKickTime(chat.id)
    text = "This group will automatically kick people in " + str(timeSetting) + " seconds."
    msg.reply_text(text)
    return

@run_async
@user_admin
def setTimeSetting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message
    if (not args) or len(args) != 1 or (not args[0].isdigit()):
        msg.reply_text("Give me a valid value to set! 30 to 900 secs")
        return
    value = int(args[0])
    if value < 30 or value > 900:
        msg.reply_text("Invalid value! Please use a value between 30 and 900 seconds (15 minutes)")
        return
    sql.setKickTime(str(chat.id), value)
    msg.reply_text("Success! Users that don't confirm being people will be kicked after " + str(value) + " seconds.")
    return

@run_async
def get_version(bot: Bot, update: Update):
    msg = update.effective_message
    ver = cas.vercheck()
    msg.reply_text("CAS API version: "+ver)
    return

@run_async
def caschecker(bot: Bot, update: Update, args: List[str]):
    #/info logic
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    if user_id and int(user_id) != 777000:
        user = bot.get_chat(user_id)
    elif user_id and int(user_id) == 777000:
        msg.reply_text("This is Telegram. Unless you manually entered this reserved account's ID, it is likely a broadcast from a linked channel.")
        return
    elif not msg.reply_to_message and not args:
        user = msg.from_user
    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        msg.reply_text("I can't extract a user from this.")
        return
    else:
        return

    text = "<b>CAS Check</b>:" \
           "\nID: <code>{}</code>" \
           "\nFirst Name: {}".format(user.id, html.escape(user.first_name))
    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))
    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))
    text += "\n\nCAS Banned: "
    result = cas.banchecker(user.id)
    text += str(result)
    if result:
        parsing = cas.offenses(user.id)
        if parsing:
            text += "\nTotal of Offenses: "
            text += str(parsing)
        parsing = cas.timeadded(user.id)
        if parsing:
            parseArray=str(parsing).split(", ")
            text += "\nDay added: "
            text += str(parseArray[1])
            text += "\nTime added: "
            text += str(parseArray[0])
            text += "\n\nAll times are in UTC"
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

#this sends direct request to combot server. Will return true if user is banned, false if
#id invalid or user not banned
@run_async
def casquery(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    try:
        user_id = msg.text.split(' ')[1]
    except:
        msg.reply_text("There was a problem parsing the query.")
        return
    text = "Your query returned: "
    result = cas.banchecker(user_id)
    text += str(result)
    msg.reply_text(text)        

WELC_HELP_TXT = "Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages" \
                " to be individually generated, like the default welcome message is, you can use *these* variables:\n" \
                " - `{{first}}`: this represents the user's *first* name\n" \
                " - `{{last}}`: this represents the user's *last* name. Defaults to *first name* if user has no " \
                "last name.\n" \
                " - `{{fullname}}`: this represents the user's *full* name. Defaults to *first name* if user has no " \
                "last name.\n" \
                " - `{{username}}`: this represents the user's *username*. Defaults to a *mention* of the user's " \
                "first name if has no username.\n" \
                " - `{{mention}}`: this simply *mentions* a user - tagging them with their first name.\n" \
                " - `{{id}}`: this represents the user's *id*\n" \
                " - `{{count}}`: this represents the user's *member number*.\n" \
                " - `{{chatname}}`: this represents the *current chat name*.\n" \
                "\nEach variable MUST be surrounded by `{{}}` to be replaced.\n" \
                "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. " \
                "Buttons are also supported, so you can make your welcomes look awesome with some nice intro " \
                "buttons.\n" \
                "To create a button linking to your rules, use this: `[Rules](buttonurl://t.me/{}?start=group_id)`. " \
                "Simply replace `group_id` with your group's id, which can be obtained via /id, and you're good to " \
                "go. Note that group ids are usually preceded by a `-` sign; this is required, so please don't " \
                "remove it.\n" \
                "If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by " \
                "replying to the desired media, and calling /setwelcome.".format(dispatcher.bot.username)

@run_async
@user_admin
def welcome_help(bot: Bot, update: Update):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)

@run_async
def gbanChat(bot: Bot, update: Update, args: List[str]):
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            send_to_list(bot, SUDO_USERS,
                     "<b>Chat Blacklist</b>" \
                     "\n#BLCHAT" \
                     "\n<b>Status:</b> <code>Blacklisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), html=True)
            sql.blacklistChat(chat_id)
            update.effective_message.reply_text("Chat has been successfully blacklisted!")
            try:
                bot.leave_chat(int(chat_id))
            except:
                pass
        except:
            update.effective_message.reply_text("Error blacklisting chat!")
    else:
        update.effective_message.reply_text("Give me a valid chat id!") 

@run_async
def ungbanChat(bot: Bot, update: Update, args: List[str]):
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            send_to_list(bot, SUDO_USERS,
                     "<b>Regression of Chat Blacklist</b>" \
                     "\n#UNBLCHAT" \
                     "\n<b>Status:</b> <code>Un-Blacklisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), html=True)
            sql.unblacklistChat(chat_id)
            update.effective_message.reply_text("Chat has been successfully un-blacklisted!")
        except:
            update.effective_message.reply_text("Error unblacklisting chat!")
    else:
        update.effective_message.reply_text("Give me a valid chat id!") 

@run_async
@user_admin
def setDefense(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message
    if len(args)!=1:
        msg.reply_text("Invalid arguments!")
        return
    param = args[0]
    if param == "on" or param == "true":
        sql.setDefenseStatus(chat.id, True)
        msg.reply_text("Defense mode has been turned on, this group is under attack. Every user that now joins will be auto kicked.")
        return
    elif param == "off" or param == "false":
        sql.setDefenseStatus(chat.id, False)
        msg.reply_text("Defense mode has been turned off, group is no longer under attack.")
        return
    else:
        msg.reply_text("Invalid status to set!") #on or off ffs
        return 

@run_async
@user_admin
def getDefense(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    stat = sql.getDefenseStatus(chat.id)
    text = "<b>Defense Status</b>\n\nCurrently, this group has the defense setting set to: <b>{}</b>".format(stat)
    msg.reply_text(text, parse_mode=ParseMode.HTML)

# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)

def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

def __chat_settings__(chat_id, user_id):
    welcome_pref2, _, _ = sql.get_welc_pref(chat_id)
    goodbye_pref, _, _ = sql.get_gdbye_pref(chat_id)
    return "This chat has it's welcome preference set to `{}`.\n" \
           "It's goodbye preference is `{}`.".format(welcome_pref2, goodbye_pref)

__help__ = """
{}
Commands:
 - /casver: Returns the API version that the bot is currently running
 - /cascheck: Checks you or another user for CAS BAN
*Admin only:*
 - /welcome <on/off>: enable/disable welcome messages.
 - /welcome: shows current welcome settings.
 - /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 - /goodbye -> same usage and args as /welcome.
 - /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
 - /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
 - /resetwelcome: reset to the default welcome message.
 - /resetgoodbye: reset to the default goodbye message.
 - /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
 - /rmjoin <on/off>: when someone joins, try to delete the *user* joined the group message.
 - /safemode <on/off>: all users that join, get muted; a button gets added to the welcome message for them to unmute themselves. This proves they aren't a bot! This will also restrict users ability to post media for 24 hours.
 - /welcomehelp: view more formatting information for custom welcome/goodbye messages.
 - /setcas <on/off/true/false>: Enables/disables CAS Checking on welcome
 - /getcas: Gets the current CAS settings
 - /setban <on/off/true/false>: Enables/disables autoban on CAS banned user detected.
 - /setdefense <on/off/true/false>: Turns on defense mode, will kick any new user automatically.
 - /getdefense: gets the current defense setting
 - /kicktime: gets the auto-kick time setting
 - /setkicktime: sets new auto-kick time value (between 30 and 900 seconds)
""".format(WELC_HELP_TXT)

__mod_name__ = "Welcomes/Goodbyes"

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
WELC_PREF_HANDLER = CommandHandler("welcome", welcome, pass_args=True, filters=Filters.group)
GOODBYE_PREF_HANDLER = CommandHandler("goodbye", goodbye, pass_args=True, filters=Filters.group)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_GOODBYE = CommandHandler("setgoodbye", set_goodbye, filters=Filters.group)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome, filters=Filters.group)
RESET_GOODBYE = CommandHandler("resetgoodbye", reset_goodbye, filters=Filters.group)
CLEAN_WELCOME = CommandHandler("cleanwelcome", clean_welcome, pass_args=True, filters=Filters.group)
SAFEMODE_HANDLER = CommandHandler("safemode", safemode, pass_args=True, filters=Filters.group)
DEL_JOINED = CommandHandler("rmjoin", del_joined, pass_args=True, filters=Filters.group)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)
BUTTON_VERIFY_HANDLER = CallbackQueryHandler(user_button, pattern=r"userverify_")
SETCAS_HANDLER = CommandHandler("setcas", setcas, filters=Filters.group)
GETCAS_HANDLER = CommandHandler("getcas", get_current_setting, filters=Filters.group)
GETVER_HANDLER = DisableAbleCommandHandler("casver", get_version)
CASCHECK_HANDLER = CommandHandler("cascheck", caschecker, pass_args=True)
CASQUERY_HANDLER = CommandHandler("casquery", casquery, pass_args=True ,filters=CustomFilters.sudo_filter)
SETBAN_HANDLER = CommandHandler("setban", setban, filters=Filters.group)
GBANCHAT_HANDLER = CommandHandler("blchat", gbanChat, pass_args=True, filters=CustomFilters.sudo_filter)
UNGBANCHAT_HANDLER = CommandHandler("unblchat", ungbanChat, pass_args=True, filters=CustomFilters.sudo_filter)
DEFENSE_HANDLER = CommandHandler("setdefense", setDefense, pass_args=True)
GETDEF_HANDLER = CommandHandler("defense", getDefense)
GETTIMESET_HANDLER = CommandHandler("kicktime", getTimeSetting)
SETTIMER_HANDLER = CommandHandler("setkicktime", setTimeSetting, pass_args=True)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(SAFEMODE_HANDLER)
dispatcher.add_handler(BUTTON_VERIFY_HANDLER)
dispatcher.add_handler(DEL_JOINED)
dispatcher.add_handler(WELCOME_HELP)
dispatcher.add_handler(SETCAS_HANDLER)
dispatcher.add_handler(GETCAS_HANDLER)
dispatcher.add_handler(GETVER_HANDLER)
dispatcher.add_handler(CASCHECK_HANDLER)
dispatcher.add_handler(CASQUERY_HANDLER)
dispatcher.add_handler(SETBAN_HANDLER)
dispatcher.add_handler(GBANCHAT_HANDLER)
dispatcher.add_handler(UNGBANCHAT_HANDLER)
dispatcher.add_handler(DEFENSE_HANDLER)
dispatcher.add_handler(GETDEF_HANDLER)
dispatcher.add_handler(GETTIMESET_HANDLER)
dispatcher.add_handler(SETTIMER_HANDLER)
