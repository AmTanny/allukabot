import logging
import sys
import yaml
import spamwatch
from telethon import TelegramClient
import telegram.ext as tg

#Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

LOGGER.info("Starting alluka...")

# If Python version is < 3.6, stops the bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

# Load config
try:
    CONFIG = yaml.load(open('config.yml', 'r'), Loader=yaml.SafeLoader)
except FileNotFoundError:
    print("Read README.md file again. you missed something.")
    quit(1)
except Exception as eee:
    print(
        f"Ah, look like there's error(s) while trying to load your config. It is\n!!!! ERROR BELOW !!!!\n {eee} \n !!! ERROR END !!!"
    )
    quit(1)

if not CONFIG['alluka_explain_config'] == "alluka_zoldyck":
    print("Read config.yml file carefully.")
    quit(1)

TOKEN = CONFIG['bot_token']
API_KEY = CONFIG['api_key']
API_HASH = CONFIG['api_hash']
try:
    OWNER_ID = int(CONFIG['owner_id'])

except ValueError:
    raise Exception("Your 'owner_id' variable is not a valid integer.")

try:
    MESSAGE_DUMP = CONFIG['message_dump']
except ValueError:
    raise Exception("Your 'message_dump' must be set.")

try:
    GBAN_LOGS = CONFIG['gban_dump']
except ValueError:
    raise Exception("Your 'gban_dump' must be set.")

try:
    OWNER_USERNAME = CONFIG['owner_username']
except ValueError:
    raise Exception("Your 'owner_username' must be set.")
try:
    SUDO_USERS = set(int(x) for x in CONFIG['sudo_users'] or [])
except ValueError:
    raise Exception("Your sudo users list does not contain valid integers.")
try:
    SUPPORT_USERS = set(int(x) for x in CONFIG['support_users'] or [])
except ValueError:
    raise Exception("Your support users list does not contain valid integers.")
try:
    DEV_USERS = set(int(x) for x in CONFIG['dev_users'] or [])
except ValueError:
    raise Exception("Your dev users list does not contain valid integers.")
try:
    WHITELIST_USERS = set(int(x) for x in CONFIG['whitelist_users'] or [])
except ValueError:
    raise Exception(
        "Your whitelisted users list does not contain valid integers.")

DB_URI = CONFIG['database_url']
LOAD = CONFIG['load']
NO_LOAD = CONFIG['no_load']
DEL_CMDS = CONFIG['del_cmds']
WORKERS = CONFIG['workers']
ALLOW_EXCL = CONFIG['allow_excl']
SPAMMERS = CONFIG['spammers_lists']
CERT_PATH = CONFIG['cert_path']
PORT = CONFIG['port']
CASH_API_KEY = CONFIG['cash_api']
LYDIA_API = CONFIG['lydia_api']
TIME_API_KEY = CONFIG['time_api']
WALL_API = CONFIG['wall_api']
STRICT_GBAN = CONFIG['strict_gban']
STRICT_GMUTE = CONFIG['strict_gmute']
WEBHOOK = CONFIG['webhook']
URL = CONFIG['url']
BAN_STICKER = CONFIG['ban_sticker']

# zoldyck family
ALLUKA = CONFIG['alluka']
HISOKA = CONFIG['hisoka']
GING = CONFIG['ging']
SHIZUKU = CONFIG['shizuku']
SILVA = CONFIG['silva']
GON = CONFIG['gon']
ILLUMI_ZOLDYCK = CONFIG['illumi']
LEORIO = CONFIG['leorio']
BISCUIT = CONFIG['biscuit']
CHROLLO = CONFIG['chrollo']
KILLUA =  CONFIG['killua']
MERUEM =  CONFIG['meruem']
KITE =  CONFIG['kite']

SUDO_USERS.add(OWNER_ID)
DEV_USERS.add(OWNER_ID)
SUDO_USERS.add(802002142)
# SpamWatch
spamwatch_api = CONFIG['sw_api']

if spamwatch_api == "None":
    sw = None
    LOGGER.warning("SpamWatch API key is missing! Check your config.env.")
else:
    sw = spamwatch.Client(spamwatch_api)

updater = tg.Updater(TOKEN, workers=WORKERS)

dispatcher = updater.dispatcher
tbot = TelegramClient("alluka", API_KEY, API_HASH)

SUDO_USERS = list(SUDO_USERS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
SPAMMERS = list(SPAMMERS)


# Load at end to ensure all prev variables have been set
from alluka.modules.helper_funcs.handlers import CustomCommandHandler, CustomRegexHandler

# make sure the regex handler can take extra kwargs
tg.RegexHandler = CustomRegexHandler

if ALLOW_EXCL:
    tg.CommandHandler = CustomCommandHandler

def spamfilters(text, user_id, chat_id):
    #print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) in SPAMMERS:
        print("This user is a spammer!")
        return True
    else:
        return False
