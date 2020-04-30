import re
import json
import urllib.request
import urllib.parse
import wikipedia
import requests
import speedtest
from tswift import Song
from alluka.modules.disable import DisableAbleCommandHandler
from time import time, sleep
from coffeehouse.lydia import LydiaAI
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError
from telegram import Message, Chat, User, Update, Bot ,MessageEntity, ParseMode, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from alluka import dispatcher, LYDIA_API, OWNER_ID
import alluka.modules.sql.lydia_sql as sql
from alluka.modules.helper_funcs.filters import CustomFilters
from typing import List
from telegram import Update, Bot, ParseMode
from alluka.modules.helper_funcs.chat_status import dev_plus
from alluka import dispatcher, WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS, OWNER_ID
from alluka.modules.helper_funcs.chat_status import whitelist_plus, dev_plus
from alluka import dispatcher, LOGGER
from alluka.modules.helper_funcs.misc import sendMessage
from subprocess import Popen, PIPE
from requests import get
from wikipedia.exceptions import DisambiguationError, PageError
import requests as r
from random import randint
from time import sleep
from alluka import dispatcher,WALL_API
import random
import alluka.modules.helper_funcs.memes_strings as memes_strings
import html
from alluka.modules.helper_funcs.chat_status import is_user_admin
from alluka.modules.helper_funcs.extraction import extract_user
from alluka import dispatcher, CASH_API_KEY
import pynewtonmath as newton
import math
import re, html, time
from bs4 import BeautifulSoup
from telegram import Message, Update, Bot, User, Chat, ParseMode, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html
import os
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from telegram import ParseMode, InputMediaPhoto, Update, Bot, TelegramError
import datetime
from alluka import dispatcher, TIME_API_KEY, LOGGER
from jikanpy import Jikan
from jikanpy.exceptions import APIException
from telegram import Message, Chat, User, ParseMode, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
import yaml
from datetime import datetime
from typing import Optional, List
from hurry.filesize import size as sizee
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram.utils.helpers import escape_markdown, mention_html


MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""


jikan = Jikan()

CoffeeHouseAPI = API(LYDIA_API)
api_client = LydiaAI(CoffeeHouseAPI)

normiefont = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
weebyfont = ['卂','乃','匚','刀','乇','下','厶','卄','工','丁','长','乚','从','𠘨','口','尸','㔿','尺','丂','丅','凵','リ','山','乂','丫','乙']


GITHUB = 'https://github.com'
DEVICES_DATA = 'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json'


opener = urllib.request.build_opener()
useragent = 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
opener.addheaders = [('User-agent', useragent)]


# lyrics module 
@run_async
def lyrics(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    song = ""
    if not query:
        msg.reply_text("You haven't specified which song to look for!")
        return
    else:
        song = Song.find_song(query)
        if song:
            if song.lyrics:
                reply = song.format()
            else:
                reply = "Couldn't find any lyrics for that song!"
        else:
            reply = "Song not found!"
        if len(reply) > 4090:
            with open("lyrics.txt", 'w') as f:
                f.write(f"{reply}\n\n\nOwO UwU OmO")
            with open("lyrics.txt", 'rb') as f:
                msg.reply_document(document=f,
                caption="Message length exceeded max limit! Sending as a text file.")
        else:
            msg.reply_text(reply)

# lydia module
@run_async
def add_chat(bot: Bot, update: Update):
    global api_client
    chat_id = update.effective_chat.id
    msg = update.effective_message
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat_id, ses_id, expires)
        msg.reply_text("lydia successfully enabled for this chat!")
    else:
        msg.reply_text("lydia is already enabled for this chat!")
        
        
@run_async
def remove_chat(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        msg.reply_text("lydia isn't enabled here in the first place!")
    else:
        sql.rem_chat(chat_id)
        msg.reply_text("lydia disabled successfully!")
        
        
def check_message(bot: Bot, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "alluka":
        return True
    if reply_msg:
        if reply_msg.from_user.id == bot.get_me().id:
            return True
    else:
        return False
                
        
@run_async
def lydia(bot: Bot, update: Update):
    global api_client
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(bot, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID, f"lydia error: {e} occurred in {chat_id}!")


# pastebin

def paste(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if message.reply_to_message:
        data = message.reply_to_message.text

    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]

    else:
        message.reply_text("What am I supposed to do with this?")
        return

    key = requests.post('https://nekobin.com/api/documents', json={"content": data}).json().get('result').get('key')

    url = f'https://nekobin.com/{key}'

    reply_text = f'Nekofied to *Nekobin* : {url}'

    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


#shell 
def shell(command):
    process = Popen(command,stdout=PIPE,shell=True,stderr=PIPE)
    stdout,stderr = process.communicate()
    return (stdout,stderr)

@dev_plus
@run_async
def shellExecute(bot: Bot, update: Update):
    cmd = update.message.text.split(' ',maxsplit=1)
    if len(cmd) == 1:
        sendMessage("No command provided!", bot, update)
        return
    LOGGER.info(cmd)
    output = shell(cmd[1])
    if output[1].decode():
        LOGGER.error(f"Shell: {output[1].decode()}")
    if len(output[0].decode()) > 4000:
        with open("shell.txt",'w') as f:
            f.write(f"Output\n-----------\n{output[0].decode()}\n")
            if output[1]:
                f.write(f"STDError\n-----------\n{output[1].decode()}\n")
        with open("shell.txt",'rb') as f:
            bot.send_document(document=f, filename=f.name,
                                  reply_to_message_id=update.message.message_id,
                                  chat_id=update.message.chat_id)  
    else:
        if output[1].decode():
            sendMessage(f"<code>{output[1].decode()}</code>", bot, update)
            return
        else:
            sendMessage(f"<code>{output[0].decode()}</code>", bot, update)

#ud
@run_async
def ud(bot: Bot, update: Update):
  message = update.effective_message
  text = message.text[len('/ud '):]
  results = get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
  reply_text = f'ℹ️ *{text}*\n\n👉🏻 {results["list"][0]["definition"]}\n\n📌 _{results["list"][0]["example"]}_'
  message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

#wiki
@run_async
def wiki(bot: Bot, update: Update):
    msg = update.effective_message.reply_to_message if update.effective_message.reply_to_message else update.effective_message
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        update.message.reply_text("Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>".format(e),
        parse_mode=ParseMode.HTML)
    except PageError as e:
        update.message.reply_text("<code>{}</code>".format(e), parse_mode=ParseMode.HTML)
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", 'w') as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", 'rb') as f:
                bot.send_document(document=f, filename=f.name,
                    reply_to_message_id=update.message.message_id, chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text(result, parse_mode=ParseMode.HTML)

#weebify
@run_async
def weebify(bot: Bot, update: Update, args: List[str]):

	string = '  '.join(args).lower()
	for normiecharacter in string:
		if normiecharacter in normiefont:
			weebycharacter = weebyfont[normiefont.index(normiecharacter)]
			string = string.replace(normiecharacter, weebycharacter)

	message = update.effective_message
	if message.reply_to_message:
		message.reply_to_message.reply_text(string)
	else:
		message.reply_text(string)

#walls
@run_async
def wall(bot: Bot, update: Update, args):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    msg_id = update.effective_message.message_id
    query = " ".join(args)
    if not query:
        msg.reply_text("Please enter a query!")
        return
    else:
        caption = query
        term = query.replace(" ", "%20")
        json_rep = r.get(f"https://wall.alphacoders.com/api2.0/get.php?auth={WALL_API}&method=search&term={term}").json()
        if not json_rep.get("success"):
            msg.reply_text("An error occurred! Report this @allukabot")
        else:
            wallpapers = json_rep.get("wallpapers")
            if not wallpapers:
                msg.reply_text("No results found!")
                return
            else:
                index = randint(0, len(wallpapers)-1) # Choose random index
                wallpaper = wallpapers[index]
                wallpaper = wallpaper.get("url_image")
                wallpaper = wallpaper.replace("\\", "")
                bot.send_photo(chat_id, photo=wallpaper,
                reply_to_message_id=msg_id, timeout=60)
                bot.send_document(chat_id, document=wallpaper,
                filename='wallpaper', reply_to_message_id=msg_id,
                timeout=60)
#githubinfo
@run_async
def github(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/git '):]
    usr = get(f'https://api.github.com/users/{text}').json()
    if usr.get('login'):
        reply_text = f"""*Name:* `{usr['name']}`
*Username:* `{usr['login']}`
*Account ID:* `{usr['id']}`
*Account type:* `{usr['type']}`
*Location:* `{usr['location']}`
*Bio:* `{usr['bio']}`
*Followers:* `{usr['followers']}`
*Following:* `{usr['following']}`
*Hireable:* `{usr['hireable']}`
*Public Repos:* `{usr['public_repos']}`
*Public Gists:* `{usr['public_gists']}`
*Email:* `{usr['email']}`
*Company:* `{usr['company']}`
*Website:* `{usr['blog']}`
*Last updated:* `{usr['updated_at']}`
*Account created at:* `{usr['created_at']}`
"""
    else:
        reply_text = "User not found. Make sure you entered valid username!"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

#reactions
@run_async
def react(bot: Bot, update: Update):

    message = update.effective_message
    react = random.choice(memes_strings.REACTIONS)
    if message.reply_to_message:
      	message.reply_to_message.reply_text(react)
    else:
      	message.reply_text(react)

#memes
@run_async
def runs(bot: Bot, update: Update):
    update.effective_message.reply_text(random.choice(memes_strings.RUN_STRINGS))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message
    chat = update.effective_chat

    reply_text = message.reply_to_message.reply_text if message.reply_to_message else message.reply_text

    curr_user = html.escape(message.from_user.first_name)
    user_id = extract_user(message, args)

    if user_id == bot.id:
        temp = random.choice(memes_strings.SLAP_alluka_TEMPLATES)

        if type(temp) == list:
            if temp[2] == "tmute":
                if is_user_admin(chat, message.from_user.id):

                    reply_text(temp[1])
                    return

                mutetime = int(time.time() + 60)
                bot.restrict_chat_member(chat.id, message.from_user.id, until_date=mutetime, can_send_messages=False)
                
            reply_text(temp[0])
        else:
            reply_text(temp)
        return

    if user_id:

        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        
        user2 = html.escape(slapped_user.first_name)

    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(memes_strings.SLAP_TEMPLATES)
    item = random.choice(memes_strings.ITEMS)
    hit = random.choice(memes_strings.HIT)
    throw = random.choice(memes_strings.THROW)

    reply = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def roll(bot: Bot, update: Update):
    update.message.reply_text(random.choice(range(1, 7)))


@run_async
def toss(bot: Bot, update: Update):
    update.message.reply_text(random.choice(memes_strings.TOSS))


@run_async
def abuse(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(memes_strings.ABUSE_STRINGS))


@run_async
def shrug(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(r"¯\_(ツ)_/¯")


@run_async
def bluetext(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text("/BLUE /TEXT\n/MUST /CLICK\n/I /AM /A /STUPID /ANIMAL /THAT /IS /ATTRACTED /TO /COLORS")


@run_async
def rlg(bot: Bot, update: Update):

    eyes = random.choice(memes_strings.EYES)
    mouth = random.choice(memes_strings.MOUTHS)
    ears = random.choice(memes_strings.EARS)
    
    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    
    update.message.reply_text(repl)


@run_async
def decide(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(memes_strings.DECIDE))

    
@run_async
def table(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(memes_strings.TABLE))

# currency converter
@run_async
def convert(bot: Bot, update: Update):

    args = update.effective_message.text.split(" ", 3)
    if len(args) > 1:

        orig_cur_amount = float(args[1])

        try:
            orig_cur = args[2].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code.")
            return 

        try:
            new_cur = args[3].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code to convert into.")
            return

        request_url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={orig_cur}&to_currency={new_cur}&apikey={CASH_API_KEY}"
        response = requests.get(request_url).json()
        try:
            current_rate = float(response['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        except KeyError:
            update.effective_message.reply_text(f"Currency Not Supported.")
            return
        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        update.effective_message.reply_text(f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}")
    else:
        update.effective_message.reply_text(__help__)

#maths
@run_async
def simplify(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.simplify('{}'.format(args[0])))

@run_async
def factor(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.factor('{}'.format(args[0])))

@run_async
def derive(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.derive('{}'.format(args[0])))

@run_async
def integrate(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.integrate('{}'.format(args[0])))

@run_async
def zeroes(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.zeroes('{}'.format(args[0])))

@run_async
def tangent(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.tangent('{}'.format(args[0])))

@run_async
def area(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.area('{}'.format(args[0])))

@run_async
def cos(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.cos(int(args[0])))

@run_async
def sin(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.sin(int(args[0])))

@run_async
def tan(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.tan(int(args[0])))

@run_async
def arccos(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.acos(int(args[0])))

@run_async
def arcsin(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.asin(int(args[0])))

@run_async
def arctan(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.atan(int(args[0])))

@run_async
def abs(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.fabs(int(args[0])))

@run_async
def log(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.log(int(args[0])))

@run_async
def math_help(bot: Bot, update: Update):

    msg = update.effective_message
    msg.reply_text(""" 
Solves complex math problems using https://newton.now.sh
 - /math: Simplify `/simplify 2^2+2(2)`
 - /factor: Factor `/factor x^2 + 2x`
 - /derive: Derive `/derive x^2+2x`
 - /integrate: Integrate `/integrate x^2+2x`
 - /zeroes: Find 0's `/zeroes x^2+2x`
 - /tangent: Find Tangent `/tangent 2lx^3`
 - /area: Area Under Curve `/area 2:4lx^3`
 - /cos: Cosine `/cos pi`
 - /sin: Sine `/sin 0`
 - /tan: Tangent `/tan 0`
 - /arccos: Inverse Cosine `/arccos 1`
 - /arcsin: Inverse Sine `/arcsin 0`
 - /arctan: Inverse Tangent `/arctan 0`
 - /abs: Absolute Value `/abs -1`
 - /log: Logarithm `/log 2l8`
__Keep in mind__: To find the tangent line of a function at a certain x value, send the request as c|f(x) where c is the given x value and f(x) is the function expression, the separator is a vertical bar '|'. See the table above for an example request.
To find the area under a function, send the request as c:d|f(x) where c is the starting x value, d is the ending x value, and f(x) is the function under which you want the curve between the two x values.
To compute fractions, enter expressions as numerator(over)denominator. For example, to process 2/4 you must send in your expression as 2(over)4. The result expression will be in standard math notation (1/2, 3/4).
""",parse_mode=ParseMode.MARKDOWN)

#android 
@run_async
def magisk(bot, update):
    url = 'https://raw.githubusercontent.com/topjohnwu/magisk_files/'
    releases = ""
    for type, branch in {"Stable":["master/stable","master"], "Beta":["master/beta","master"], "Canary (release)":["canary/release","canary"], "Canary (debug)":["canary/debug","canary"]}.items():
        data = get(url + branch[0] + '.json').json()
        releases += f'*{type}*: \n' \
                    f'• [Changelog](https://github.com/topjohnwu/magisk_files/blob/{branch[1]}/notes.md)\n' \
                    f'• Zip - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["magisk"]["link"]}) \n' \
                    f'• App - [{data["app"]["version"]}-{data["app"]["versionCode"]}]({data["app"]["link"]}) \n' \
                    f'• Uninstaller - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["uninstaller"]["link"]})\n\n'
                        

    del_msg = update.message.reply_text("*Latest Magisk Releases:*\n{}".format(releases),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    time.sleep(300)
    try:
        del_msg.delete()
        update.effective_message.delete()
    except BadRequest as err:
        if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
            return

@run_async
def device(bot, update, args):
    if len(args) == 0:
        reply = f'No codename provided, write a codename for fetching informations.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    device = " ".join(args)
    db = get(DEVICES_DATA).json()
    newdevice = device.strip('lte') if device.startswith('beyond') else device
    try:
        reply = f'Search results for {device}:\n\n'
        brand = db[newdevice][0]['brand']
        name = db[newdevice][0]['name']
        model = db[newdevice][0]['model']
        codename = newdevice
        reply += f'<b>{brand} {name}</b>\n' \
            f'Model: <code>{model}</code>\n' \
            f'Codename: <code>{codename}</code>\n\n'  
    except KeyError as err:
        reply = f"Couldn't find info about {device}!\n"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@run_async
def checkfw(bot, update, args):
    if not len(args) == 2:
        reply = f'Give me something to fetch, like:\n`/checkfw SM-N975F DBT`'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    temp,csc = args
    model = f'sm-'+temp if not temp.upper().startswith('SM-') else temp
    fota = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml')
    test = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml')
    if test.status_code != 200:
        reply = f"Couldn't check for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    page1 = BeautifulSoup(fota.content, 'lxml')
    page2 = BeautifulSoup(test.content, 'lxml')
    os1 = page1.find("latest").get("o")
    os2 = page2.find("latest").get("o")
    if page1.find("latest").text.strip():
        pda1,csc1,phone1=page1.find("latest").text.strip().split('/')
        reply = f'*Latest released firmware for {model.upper()} and {csc.upper()} is:*\n'
        reply += f'• PDA: `{pda1}`\n• CSC: `{csc1}`\n'
        if phone1:
            reply += f'• Phone: `{phone1}`\n'
        if os1:
            reply += f'• Android: `{os1}`\n'
        reply += f'\n'
    else:
        reply = f'*No public release found for {model.upper()} and {csc.upper()}.*\n\n'
    reply += f'*Latest test firmware for {model.upper()} and {csc.upper()} is:*\n'
    if len(page2.find("latest").text.strip().split('/')) == 3:
        pda2,csc2,phone2=page2.find("latest").text.strip().split('/')
        reply += f'• PDA: `{pda2}`\n• CSC: `{csc2}`\n'
        if phone2:
            reply += f'• Phone: `{phone2}`\n'
        if os2:
            reply += f'• Android: `{os2}`\n'
        reply += f'\n'
    else:
        md5=page2.find("latest").text.strip()
        reply += f'• Hash: `{md5}`\n• Android: `{os2}`\n\n'
    
    update.message.reply_text("{}".format(reply),
                           parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@run_async
def getfw(bot, update, args):
    if not len(args) == 2:
        reply = f'Give me something to fetch, like:\n`/getfw SM-N975F DBT`'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    temp,csc = args
    model = f'sm-'+temp if not temp.upper().startswith('SM-') else temp
    test = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml')
    if test.status_code != 200:
        reply = f"Couldn't find any firmware downloads for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    url1 = f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/'
    url2 = f'https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/'
    url3 = f'https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'
    url4 = f'https://samfw.com/firmware/{model.upper()}/{csc.upper()}/'
    fota = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml')
    page = BeautifulSoup(fota.content, 'lxml')
    os = page.find("latest").get("o")
    reply = ""
    if page.find("latest").text.strip():
        pda,csc2,phone=page.find("latest").text.strip().split('/')
        reply += f'*Latest firmware for {model.upper()} and {csc.upper()} is:*\n'
        reply += f'• PDA: `{pda}`\n• CSC: `{csc2}`\n'
        if phone:
            reply += f'• Phone: `{phone}`\n'
        if os:
            reply += f'• Android: `{os}`\n'
    reply += f'\n'
    reply += f'*Downloads for {model.upper()} and {csc.upper()}*\n'
    reply += f'• [samfrew.com]({url1})\n'
    reply += f'• [sammobile.com]({url2})\n'
    reply += f'• [sfirmware.com]({url3})\n'
    reply += f'• [samfw.com]({url4})\n'
    update.message.reply_text("{}".format(reply),
                           parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@run_async
def twrp(bot, update, args):
    if len(args) == 0:
        reply='No codename provided, write a codename for fetching informations.'
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return

    device = " ".join(args)
    url = get(f'https://eu.dl.twrp.me/{device}/')
    if url.status_code == 404:
        reply = f"Couldn't find twrp downloads for {device}!\n"
        del_msg = update.effective_message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found" ) or (err.message == "Message can't be deleted" ):
                return
    else:
        reply = f'*Latest Official TWRP for {device}*\n'            
        db = get(DEVICES_DATA).json()
        newdevice = device.strip('lte') if device.startswith('beyond') else device
        try:
            brand = db[newdevice][0]['brand']
            name = db[newdevice][0]['name']
            reply += f'*{brand} - {name}*\n'
        except KeyError as err:
            pass
        page = BeautifulSoup(url.content, 'lxml')
        date = page.find("em").text.strip()
        reply += f'*Updated:* {date}\n'
        trs = page.find('table').find_all('tr')
        row = 2 if trs[0].find('a').text.endswith('tar') else 1
        for i in range(row):
            download = trs[i].find('a')
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
            reply += f'[{dl_file}]({dl_link}) - {size}\n'

        update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


# reverse image 
@run_async
def reverse(bot: Bot, update: Update, args: List[str]):
    if os.path.isfile("okgoogle.png"):
        os.remove("okgoogle.png")

    msg = update.effective_message
    chat_id = update.effective_chat.id
    rtmid = msg.message_id
    imagename = "okgoogle.png"

    reply = msg.reply_to_message
    if reply:
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.photo:
            file_id = reply.photo[-1].file_id
        elif reply.document:
            file_id = reply.document.file_id
        else:
            msg.reply_text("Reply to an image or sticker to lookup.")
            return
        image_file = bot.get_file(file_id)
        image_file.download(imagename)
        if args:
            txt = args[0]
            try:
                lim = int(txt)
            except:
                lim = 2
        else:
            lim = 2
    elif args and not reply:
        splatargs = msg.text.split(" ")
        if len(splatargs) == 3:                
            img_link = splatargs[1]
            try:
                lim = int(splatargs[2])
            except:
                lim = 2
        elif len(splatargs) == 2:
            img_link = splatargs[1]
            lim = 2
        else:
            msg.reply_text("/reverse <link> <amount of images to return.>")
            return
        try:
            urllib.request.urlretrieve(img_link, imagename)
        except HTTPError as HE:
            if HE.reason == 'Not Found':
                msg.reply_text("Image not found.")
                return
            elif HE.reason == 'Forbidden':
                msg.reply_text("Couldn't access the provided link, The website might have blocked accessing to the website by bot or the website does not existed.")
                return
        except URLError as UE:
            msg.reply_text(f"{UE.reason}")
            return
        except ValueError as VE:
            msg.reply_text(f"{VE}\nPlease try again using http or https protocol.")
            return
    else:
        msg.reply_markdown("Please reply to a sticker, or an image to search it!\nDo you know that you can search an image with a link too? `/reverse [picturelink] <amount>`.")
        return

    try:
        searchUrl = 'https://www.google.com/searchbyimage/upload'
        multipart = {'encoded_image': (imagename, open(imagename, 'rb')), 'image_content': ''}
        response = requests.post(searchUrl, files=multipart, allow_redirects=False)
        fetchUrl = response.headers['Location']

        if response != 400:
            xx = bot.send_message(chat_id, "Image was successfully uploaded to Google."
                                  "\nParsing it, please wait.", reply_to_message_id=rtmid)
        else:
            xx = bot.send_message(chat_id, "Google told me to go away.", reply_to_message_id=rtmid)
            return

        os.remove(imagename)
        match = ParseSauce(fetchUrl + "&hl=en")
        guess = match['best_guess']
        if match['override'] and not match['override'] == '':
            imgspage = match['override']
        else:
            imgspage = match['similar_images']

        if guess and imgspage:
            xx.edit_text(f"[{guess}]({fetchUrl})\nProcessing...", parse_mode='Markdown', disable_web_page_preview=True)
        else:
            xx.edit_text("Couldn't find anything.")
            return

        images = scam(imgspage, lim)
        if len(images) == 0:
            xx.edit_text(f"[{guess}]({fetchUrl})\n[Visually similar images]({imgspage})"
                          "\nCouldn't fetch any images.", parse_mode='Markdown', disable_web_page_preview=True)
            return

        imglinks = []
        for link in images:
            lmao = InputMediaPhoto(media=str(link))
            imglinks.append(lmao)

        bot.send_media_group(chat_id=chat_id, media=imglinks, reply_to_message_id=rtmid)
        xx.edit_text(f"[{guess}]({fetchUrl})\n[Visually similar images]({imgspage})", parse_mode='Markdown', disable_web_page_preview=True)
    except TelegramError as e:
        print(e)
    except Exception as exception:
        print(exception)

def ParseSauce(googleurl):
    """Parse/Scrape the HTML code for the info we want."""

    source = opener.open(googleurl).read()
    soup = BeautifulSoup(source, 'html.parser')

    results = {
        'similar_images': '',
        'override': '',
        'best_guess': ''
    }

    try:
         for bess in soup.findAll('a', {'class': 'PBorbe'}):
            url = 'https://www.google.com' + bess.get('href')
            results['override'] = url
    except:
        pass

    for similar_image in soup.findAll('input', {'class': 'gLFyf'}):
            url = 'https://www.google.com/search?tbm=isch&q=' + urllib.parse.quote_plus(similar_image.get('value'))
            results['similar_images'] = url

    for best_guess in soup.findAll('div', attrs={'class':'r5a77d'}):
        results['best_guess'] = best_guess.get_text()

    return results

def scam(imgspage, lim):
    """Parse/Scrape the HTML code for the info we want."""

    single = opener.open(imgspage).read()
    decoded = single.decode('utf-8')
    if int(lim) > 10:
        lim = 10

    imglinks = []
    counter = 0

    pattern = r'^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$'
    oboi = re.findall(pattern, decoded, re.I | re.M)

    for imglink in oboi:
        counter += 1
        imglinks.append(imglink)
        if counter >= int(lim):
            break

    return imglinks

#anime
@run_async
def anime(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    res = ""
    try:
        res = jikan.search("anime", query)
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    try:
        res = res.get("results")[0].get("mal_id") # Grab first result
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    if res:
        anime = jikan.anime(res)
        title = anime.get("title")
        japanese = anime.get("title_japanese")
        type = anime.get("type")
        duration = anime.get("duration")
        synopsis = anime.get("synopsis")
        source = anime.get("source")
        status = anime.get("status")
        episodes = anime.get("episodes")
        score = anime.get("score")
        rating = anime.get("rating")
        genre_lst = anime.get("genres")
        genres = ""
        for genre in genre_lst:
            genres += genre.get("name") + ", "
        genres = genres[:-2]
        studios = ""
        studio_lst = anime.get("studios")
        for studio in studio_lst:
            studios += studio.get("name") + ", "
        studios = studios[:-2]
        duration = anime.get("duration")
        premiered = anime.get("premiered")
        image_url = anime.get("image_url")
        url = anime.get("url")
        trailer = anime.get("trailer_url")
    else:
        msg.reply_text("No results found!")
        return
    rep = f"<b>{title} ({japanese})</b>\n"
    rep += f"<b>Type:</b> <code>{type}</code>\n"
    rep += f"<b>Source:</b> <code>{source}</code>\n"
    rep += f"<b>Status:</b> <code>{status}</code>\n"
    rep += f"<b>Genres:</b> <code>{genres}</code>\n"
    rep += f"<b>Episodes:</b> <code>{episodes}</code>\n"
    rep += f"<b>Duration:</b> <code>{duration}</code>\n"
    rep += f"<b>Score:</b> <code>{score}</code>\n"
    rep += f"<b>Studio(s):</b> <code>{studios}</code>\n"
    rep += f"<b>Premiered:</b> <code>{premiered}</code>\n"
    rep += f"<b>Rating:</b> <code>{rating}</code>\n\n"
    rep += f"<a href='{image_url}'>\u200c</a>"
    rep += f"<i>{synopsis}</i>\n"
    if trailer:
        keyb = [
            [InlineKeyboardButton("More Information", url=url),
           InlineKeyboardButton("Trailer", url=trailer)]
        ]
    else:
        keyb = [
             [InlineKeyboardButton("More Information", url=url)]
         ]
    
    
    msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
    

@run_async
def character(bot: Bot, update: Update, args):
    msg = update.effective_message
    res = ""
    query = " ".join(args)
    try:
        search = jikan.search("character", query).get("results")[0].get("mal_id")
    except APIException:
        msg.reply_text("No results found!")
        return ""
    if search:
        try:
            res = jikan.character(search)
        except APIException:
            msg.reply_text("Error connecting to the API. Please try again!")
            return ""
    if res:
        name = res.get("name")
        kanji = res.get("name_kanji")
        about = res.get("about")
        if len(about) > 4096:
            about = about[:4000] + "..."
        image = res.get("image_url")
        url = res.get("url")
        rep = f"<b>{name} ({kanji})</b>\n\n"
        rep += f"<a href='{image}'>\u200c</a>"
        rep += f"<i>{about}</i>\n"
        keyb = [
            [InlineKeyboardButton("More Information", url=url)]
        ]
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
        
        
@run_async
def upcoming(bot: Bot, update: Update):
    msg = update.effective_message
    rep = "<b>Upcoming anime</b>\n"
    later = jikan.season_later()
    anime = later.get("anime")
    for new in anime:
        name = new.get("title")
        url = new.get("url")
        rep += f"• <a href='{url}'>{name}</a>\n"
        if len(rep) > 2000:
            break
    msg.reply_text(rep, parse_mode=ParseMode.HTML)
    
    
@run_async
def manga(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    res = ""
    manga = ""
    try:
        res = jikan.search("manga", query).get("results")[0].get("mal_id")
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    if res:
        try:
            manga = jikan.manga(res)
        except APIException:
            msg.reply_text("Error connecting to the API. Please try again!")
            return ""
        title = manga.get("title")
        japanese = manga.get("title_japanese")
        type = manga.get("type")
        status = manga.get("status")
        score = manga.get("score")
        volumes = manga.get("volumes")
        chapters = manga.get("chapters")
        genre_lst = manga.get("genres")
        genres = ""
        for genre in genre_lst:
            genres += genre.get("name") + ", "
        genres = genres[:-2]
        synopsis = manga.get("synopsis")
        image = manga.get("image_url")
        url = manga.get("url")
        rep = f"<b>{title} ({japanese})</b>\n"
        rep += f"<b>Type:</b> <code>{type}</code>\n"
        rep += f"<b>Status:</b> <code>{status}</code>\n"
        rep += f"<b>Genres:</b> <code>{genres}</code>\n"
        rep += f"<b>Score:</b> <code>{score}</code>\n"
        rep += f"<b>Volumes:</b> <code>{volumes}</code>\n"
        rep += f"<b>Chapters:</b> <code>{chapters}</code>\n\n"
        rep += f"<a href='{image}'>\u200c</a>"
        rep += f"<i>{synopsis}</i>"
        keyb = [
            [InlineKeyboardButton("More Information", url=url)]
        ]
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
        
        
# time
def generate_time(to_find: str, findtype: List[str]) -> str:

    data = requests.get(f"http://api.timezonedb.com/v2.1/list-time-zone?key={TIME_API_KEY}&format=json&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst").json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                
                country_name = zone['countryName']
                country_zone = zone['zoneName']
                country_code = zone['countryCode']

                if zone['dst'] == 1:
                    daylight_saving = "Yes"
                else:
                    daylight_saving = "No"

                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone['gmtOffset']
                timestamp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break
    
    try:
        result = "<b>Country :</b> <code>{}</code>\n" \
                 "<b>Zone Name :</b> <code>{}</code>\n" \
                 "<b>Country Code :</b> <code>{}</code>\n" \
                 "<b>Daylight saving :</b> <code>{}</code>\n" \
                 "<b>Day :</b> <code>{}</code>\n" \
                 "<b>Current Time :</b> <code>{}</code>\n" \
                 "<b>Current Date :</b> <code>{}</code>".format(country_name, country_zone, country_code, daylight_saving, current_day, current_time, current_date)
    except:
        result = None

    return result


@run_async
def gettime(bot: Bot, update: Update):

    message = update.effective_message
    
    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text("Provide a country name/abbreviation/timezone to find.")
        return
        
    send_message = message.reply_text(f"Finding timezone info for <b>{query}</b>", parse_mode=ParseMode.HTML)

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(f"Timezone info not available for <b>{query}</b>", parse_mode=ParseMode.HTML)
        return

    send_message.edit_text(result, parse_mode=ParseMode.HTML)

#id 
@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(f"The original sender, {html.escape(user2.first_name)},"
                           f" has an ID of <code>{user2.id}</code>.\n"
                           f"The forwarder, {html.escape(user1.first_name)},"
                           f" has an ID of <code>{user1.id}</code>.",
                           parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                           parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(f"Your id is <code>{chat.id}</code>.",
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(f"This group's id is <code>{chat.id}</code>.",
                           parse_mode=ParseMode.HTML)



#covid
@run_async
def corona(bot: Bot, update: Update):
    message = update.effective_message
    device = message.text[len('/corona '):]
    fetch = get(f'https://coronavirus-tracker-api.herokuapp.com/all')

    if fetch.status_code == 200:
        usr = fetch.json()
        data = fetch.text
        parsed = json.loads(data)
        total_confirmed_global = parsed["latest"]["confirmed"]
        total_deaths_global = parsed["latest"]["deaths"]
        total_recovered_global = parsed["latest"]["recovered"]
        active_cases_covid19 = total_confirmed_global - total_deaths_global - total_recovered_global
        reply_text = ("*Corona Stats🦠:*\n"
        "Total Confirmed: `" + str(total_confirmed_global) + "`\n"
        "Total Deaths: `" + str(total_deaths_global) + "`\n"
        "Total Recovered: `" + str(total_recovered_global) +"`\n"
        "Active Cases: `"+ str(active_cases_covid19) + "`")
        message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        return

    elif fetch.status_code == 404:
        reply_text = "The API is currently down."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

# gifs id
@run_async
def gifid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
                                            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text("Please reply to a gif to get its ID.")

#markdown
@run_async
def markdown_help(bot: Bot, update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text("Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text("/save test This is a markdown test. _italics_, *bold*, `code`, "
                                        "[URL](example.com) [button](buttonurl:github.com) "
                                        "[button2](buttonurl://google.com:same)")



# lyrics module
LYRICS_HANDLER = DisableAbleCommandHandler("lyrics", lyrics, pass_args=True)
dispatcher.add_handler(LYRICS_HANDLER)

#lydia module
ADD_CHAT_HANDLER = CommandHandler("elydia", add_chat, filters=CustomFilters.dev_filter)
REMOVE_CHAT_HANDLER = CommandHandler("dlydia", remove_chat, filters=CustomFilters.dev_filter)
LYDIA_HANDLER = MessageHandler(Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                                  & ~Filters.regex(r"^s\/")), lydia)
dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(LYDIA_HANDLER)

#pastebin
PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, pass_args=True)
dispatcher.add_handler(PASTE_HANDLER)

#shell
shell_handler = CommandHandler(('sh','shell'), shellExecute)
dispatcher.add_handler(shell_handler)

#ud
ud_handle = DisableAbleCommandHandler("ud", ud)
dispatcher.add_handler(ud_handle)

#wiki
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
dispatcher.add_handler(WIKI_HANDLER)

#weebify
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify, pass_args=True)
dispatcher.add_handler(WEEBIFY_HANDLER)

#wall
WALLPAPER_HANDLER = DisableAbleCommandHandler("wall", wall, pass_args=True)
dispatcher.add_handler(WALLPAPER_HANDLER)

#githubinfo
github_handle = DisableAbleCommandHandler("git", github)
dispatcher.add_handler(github_handle)

#reactions
REACT_HANDLER = DisableAbleCommandHandler("react", react)
dispatcher.add_handler(REACT_HANDLER)

#memes
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
ROLL_HANDLER = DisableAbleCommandHandler("roll", roll)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug)
BLUETEXT_HANDLER = DisableAbleCommandHandler("bluetext", bluetext)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide)
TABLE_HANDLER = DisableAbleCommandHandler("table", table)

dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(ROLL_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(BLUETEXT_HANDLER)
dispatcher.add_handler(RLG_HANDLER)
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(TABLE_HANDLER)

# currency converter
CONVERTER_HANDLER = CommandHandler('cash', convert)
dispatcher.add_handler(CONVERTER_HANDLER)

#maths
SIMPLIFY_HANDLER = DisableAbleCommandHandler("math", simplify, pass_args=True)
FACTOR_HANDLER = DisableAbleCommandHandler("factor", factor, pass_args=True)
DERIVE_HANDLER = DisableAbleCommandHandler("derive", derive, pass_args=True)
INTEGRATE_HANDLER = DisableAbleCommandHandler("integrate", integrate, pass_args=True)
ZEROES_HANDLER = DisableAbleCommandHandler("zeroes", zeroes, pass_args=True)
TANGENT_HANDLER = DisableAbleCommandHandler("tangent", tangent, pass_args=True)
AREA_HANDLER = DisableAbleCommandHandler("area", area, pass_args=True)
COS_HANDLER = DisableAbleCommandHandler("cos", cos, pass_args=True)
SIN_HANDLER = DisableAbleCommandHandler("sin", sin, pass_args=True)
TAN_HANDLER = DisableAbleCommandHandler("tan", tan, pass_args=True)
ARCCOS_HANDLER = DisableAbleCommandHandler("arccos", arccos, pass_args=True)
ARCSIN_HANDLER = DisableAbleCommandHandler("arcsin", arcsin, pass_args=True)
ARCTAN_HANDLER = DisableAbleCommandHandler("arctan", arctan, pass_args=True)
ABS_HANDLER = DisableAbleCommandHandler("abs", abs, pass_args=True)
LOG_HANDLER = DisableAbleCommandHandler("log", log, pass_args=True)
MATH_HELP_HANDLER = DisableAbleCommandHandler("mathhelp", math_help)

dispatcher.add_handler(SIMPLIFY_HANDLER)
dispatcher.add_handler(FACTOR_HANDLER)
dispatcher.add_handler(DERIVE_HANDLER)
dispatcher.add_handler(INTEGRATE_HANDLER)
dispatcher.add_handler(ZEROES_HANDLER)
dispatcher.add_handler(TANGENT_HANDLER) 
dispatcher.add_handler(AREA_HANDLER)
dispatcher.add_handler(COS_HANDLER)
dispatcher.add_handler(SIN_HANDLER)
dispatcher.add_handler(TAN_HANDLER)
dispatcher.add_handler(ARCCOS_HANDLER)
dispatcher.add_handler(ARCSIN_HANDLER)
dispatcher.add_handler(ARCTAN_HANDLER)
dispatcher.add_handler(ABS_HANDLER)
dispatcher.add_handler(LOG_HANDLER) 
dispatcher.add_handler(MATH_HELP_HANDLER)

#android
MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk)
DEVICE_HANDLER = DisableAbleCommandHandler("device", device, pass_args=True)
TWRP_HANDLER = DisableAbleCommandHandler("twrp", twrp, pass_args=True)
GETFW_HANDLER = DisableAbleCommandHandler("getfw", getfw, pass_args=True)
CHECKFW_HANDLER = DisableAbleCommandHandler("checkfw", checkfw, pass_args=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(DEVICE_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(GETFW_HANDLER)
dispatcher.add_handler(CHECKFW_HANDLER)

# reverse image 
REVERSE_HANDLER = DisableAbleCommandHandler("reverse", reverse, pass_args=True, admin_ok=True)
dispatcher.add_handler(REVERSE_HANDLER)

# anime
ANIME_HANDLER = CommandHandler("anime", anime, pass_args=True)
CHARACTER_HANDLER = CommandHandler("character", character, pass_args=True)
UPCOMING_HANDLER = CommandHandler("upcoming", upcoming)
MANGA_HANDLER = CommandHandler("manga", manga, pass_args=True)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)

# time
TIME_HANDLER = DisableAbleCommandHandler("time", gettime)
dispatcher.add_handler(TIME_HANDLER)

# covid
CORONA_HANDLER = DisableAbleCommandHandler("covid", corona, admin_ok=True)
dispatcher.add_handler(CORONA_HANDLER)

#gif id 
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
dispatcher.add_handler(GIFID_HANDLER)

#id
ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
dispatcher.add_handler(ID_HANDLER)

#markdown
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)
dispatcher.add_handler(MD_HELP_HANDLER)

__command_list__ = ["runs", "slap", "roll", "toss", "shrug", "bluetext", "rlg", "decide", "table" ,"react" ,"cash","mathhelp","time"]
__handlers__ = [RUNS_HANDLER, SLAP_HANDLER, ROLL_HANDLER, TOSS_HANDLER, SHRUG_HANDLER, BLUETEXT_HANDLER, RLG_HANDLER, DECIDE_HANDLER, TABLE_HANDLER, REACT_HANDLER,CONVERTER_HANDLER,MATH_HELP_HANDLER,TIME_HANDLER]


MASTER_MOD = " \
 \n - /ud: {word} Type the word or expression you want to search use. like /ud telegram Word. \
 \n - /id: get the current group id. If used by replying to a message, gets that user's id. \
 \n - /info: get information about a user. \
 \n - /gifid: Get gif ID. \
 \n - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats. \
 \n - /wiki: {query} wiki your query. \
 \n - /wall: {query} to get wallpaper. \
 \n - /git:{GitHub username} Returns info about a GitHub user or organization.\
 \n - /paste: with reply a message. \
 \n - /reverse: Does a reverse image search of the media which it was replied to. \
 \n - /time: <query> : Gives information about a timezone. \
    Available queries : Country Code/Country Name/Timezone Name.  \
 \n - /tr (language code) as reply to a long message. \
 \n - /cash : currency converter \
   example syntax: /cash 1 USD INR \
 \n - /lyrics <song>: returns the lyrics of that song. \
    You can either enter just the song name or both the artist and song name. \
 \n - /react: Reacts with a random reaction.  \
 \n - /shout <keyword>: write anything you want to give loud shout. \
 \n - /feedback : You can give us your feedbacks  \
   an can see your feeds @allukabotfeeds here. \
 \n - /tts: {yourtext} will get your entered text into voice form.  \
 \n - /covid: get worldwide corona status \
 \n - /mathhelp: get all math related cmds. \
             \
 #ANDROID  \
\n - /magisk - gets the latest magisk release for Stable/Beta/Canary  \
\n - /device <codename> - gets android device basic info from its codename \
\n - /twrp <codename> -  gets latest twrp for the android device using the codename  \
\n - /checkfw <model> <csc> - Samsung only - shows the latest firmware info for the given device, taken from samsung servers \
\n - /getfw <model> <csc> - Samsung only - gets firmware download links from samfrew, sammobile and sfirmwares for the given device  \
                  \
\n *Examples:* \
\n  `/device greatlte` \
\n  `/twrp a5y17lte`    \
\n  `/checkfw SM-A305F INS` \
\n  `/getfw SM-M205FN SER`   \
                            \
\n   #RSS  \
\n - /addrss <link>: add an RSS link to the subscriptions.  \
\n - /removerss <link>: removes the RSS link from the subscriptions.  \
\n - /rss <link>: shows the link's data and the last entry, for testing purposes.  \
\n - /listrss: shows the list of rss feeds that the chat is currently subscribed to.  \
\n  \
\nNOTE: In groups, only admins can add/remove RSS links to the group's subscription  \
\n       \
\n  #MEMES  \
\n - /runs: reply a random string from an array of replies.  \
\n - /slap: slap a user, or get slapped if not a reply.  \
\n - /shrug: get shrug XD.  \
\n - /table: get flip/unflip :v.  \
\n - /decide: Randomly answers yes/no/maybe  \
\n - /toss: Tosses A coin  \
\n - /abuse: Abuses the cunt   \
\n - /bluetext: check urself :V  \
\n - /roll: Roll a dice.   \
\n - /rlg: Join ears,nose,mouth and create an emo ;-;  \
          \
\n  #ANIME   \
\n - /anime <anime>: returns information about the anime.  \
\n - /character <character>: returns information about the character. \
\n - /manga <manga>: returns information about the manga.  \
\n - /upcoming: returns a list of new anime in the upcoming seasons. "  \


__help__ = MASTER_MOD

__mod_name__ = "master mod"