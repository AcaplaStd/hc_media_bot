import hashlib
import logging
from threading import Timer
from urllib.parse import urlparse, urlunparse
from time import sleep
import sys
import feedparser
from telegram import Bot, ParseMode, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from html import escape

from secure import ADD_FEED_COMMAND, TOKEN, PROXY_URL, PROXY_USERNAME, PROXY_PASSWORD

# TODO: refator and add database
print("Loading feeds...", end=" ")
sys.stdout.flush()
f = open("fu.txt", "r")
s = f.read()
urls = s.split()
f.close()
print("Done")

print("Parsing feeds", end=" ")
sys.stdout.flush()
parsers = []
for url in urls:
    parsers.append(feedparser.parse(url))
    print(".", end="")
    sys.stdout.flush()
print(" ", end="")
f = open("fc.txt", "r")
s = f.read()
chats = [int(i) for i in s.split()]
f.close()
print("Done")

print("Loading hashes...", end=" ")
sys.stdout.flush()
f = open("fh.txt", "r")
s = f.read()
hashes = [int(i) for i in s.split()]
f.close()
print("Done")

fu = open("fu.txt", "a")
fc = open("fc.txt", "a")
fh = open("fh.txt", "a")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_get_data(link):
    res = list(urlparse(link))
    res[4] = ""
    return urlunparse(res)


# TODO: Разобраться
def filter(entry):
    s = remove_get_data(entry["link"])
    d = hashlib.sha1(s.encode("utf-8")).hexdigest()
    hsh = int(d[:10], 16)
    for i in range(len(hashes) - 1, -1, -1):
        if hashes[i] == hsh:
            return -i
    hashes.append(hsh)
    print(hsh, file=fh)
    fh.flush()
    return len(hashes)


# TODO: Refactor next 3 functions
def replacement(char):
    if ord(char) in [8210, 8211, 8212, 8213, 11834, 11835, 45, 32]:  # dash types
        return "_"
    if char in ['!', '?', '(', ')', '\'', '"', '«', '»']:  # special chars
        return ""
    if char == '&':
        return "_"
    if char == "#":
        return "sharp"
    if char == ".":
        return "dot"
    return char.lower()


def to_hash_tag(string):
    string = string.strip()
    string = string.strip(".,?!")
    res = ""
    if string[0].isdigit():
        res += "_"
    for char in string:
        res += replacement(char)
    res = res.replace("c++", "cpp")
    final_result = "#"
    for char in res:
        if char != "_":
            final_result += char
        elif final_result[-1] != "_":
            final_result += "_"
    return final_result


def get_categories(entry):
    if "tags" in entry.keys():
        lowercase_categories = map(lambda tag: tag.get("term", "").lower(), entry["tags"])
        unique_lowercase_categories = list(set(lowercase_categories))
        unique_lowercase_hashtags = list(map(to_hash_tag, unique_lowercase_categories))
        unique_lowercase_hashtags.sort()
        result_string = " ".join(unique_lowercase_hashtags)
        if len(result_string):
            result_string += "\n"
        return result_string
    else:
        return ""


# TODO: html
def format_entry(parser_number, entry_number):
    parser = parsers[parser_number]
    feed = parser["feed"]
    entry = parser["entries"][entry_number]
    categories = get_categories(entry)
    feed_title = "[" + feed["title"] + "]" if "title" in feed.keys() else ""
    entry_title = entry["title"]
    entry_link = entry["link"]
    res = escape(feed_title + "\n") + "<b>" + escape(entry_title) + "</b>" + escape("\n" + categories + "\n") + "<a href=\"" + entry_link + "\">Читать</a>"
    return res


# TODO: придумать способ получше, чем таймер. Мне кажется, что таймер не оч. Но хз
def tick(bot: Bot):
    for parser_number in range(0, len(parsers)):
        parsers[parser_number] = feedparser.parse(urls[parser_number])
        parser = parsers[parser_number]
        for entry_number in range(len(parser.entries) - 1, -1, -1):
            entry = parser["entries"][entry_number]
            if filter(entry) > 0:
                for chat_id in chats:
                        bot.send_message(chat_id, text=format_entry(parser_number, entry_number),
                                         parse_mode=ParseMode.HTML, timeout=60)
                        sleep(0.2)
    t = Timer(10, tick, [bot])
    t.start()


def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi!")


def add_feed(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Send me feed URL")
    else:
        name = context.args[0]
        if urlparse(name):
            parsers.append(feedparser.parse(name))
            urls.append(name)
            print(name, file=fu)
            fu.flush()
            update.message.reply_text("Done.")
        else:
            print("Not a URL. Try again.")


def add_chat_id(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text(f'Usage: /{ADD_FEED_COMMAND} <chat_id>')
    else:
        try:
            chats.append(int(context.args[0]))
            print(context.args[0], file=fc)
            fc.flush()
            update.message.reply_text("Done")
        except ValueError:
            update.message.reply_text(f'Usage: /{ADD_FEED_COMMAND} <chat_id>')


def main():
    updater = Updater(TOKEN, use_context=True, request_kwargs={
        'proxy_url': PROXY_URL,
        'urllib3_proxy_kwargs': {
            'username': PROXY_USERNAME,
            'password': PROXY_PASSWORD,
        }
    })
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler(ADD_FEED_COMMAND, add_feed))
    dp.add_handler(CommandHandler("add_chat_id", add_chat_id))
    updater.start_polling()
    print("Load complete.")
    tick(updater.bot)
    updater.idle()

print("Files loaded, loading network...")
if __name__ == '__main__':
    main()
