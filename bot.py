from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from threading import Timer

import os
import logging
import requests

import feedparser

TOKEN = os.environ["TOKEN"]
ADD_FEED = os.environ["ADD_FEED"]

from urllib.parse import urlparse, urlunparse

import base64
import hashlib

bot = None

f = open("fu.txt", "r")
s = f.read()
urls = s.split()
f.close()

parsers = [feedparser.parse(url) for url in urls]

f = open("fc.txt", "r")
s = f.read()
chats = [int(i) for i in s.split()]
f.close()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

logger = logging.getLogger(__name__)

f = open("fh.txt", "r")
s = f.read()
hashes = [int(i) for i in s.split()]
f.close()

forbidden_symbols = ["\\", "*", "_", "[", "(" "`"]

fu = open("fu.txt", "a")
fc = open("fc.txt", "a")
fh = open("fh.txt", "a")

def remove_get_data(link):
    res = list(urlparse(link))
    res[4] = ""
    return urlunparse(res)

def check(entry):
    s = remove_get_data(entry["link"])
    d = hashlib.sha1(s.encode("utf-8")).hexdigest()
    hsh = int(d[:10], 16)
    for i in range(len(hashes) - 1, -1, -1):
        if hashes[i] == hsh:
            return False
    hashes.append(hsh)
    print(hsh, file=fh)
    fh.flush()
    return True

def replacement(char):
    if 8210 <= ord(char) <= 8213 or 11834 <= ord(char) <= 11835 or ord(char) == 45 or ord(char) == 32: # тире))
        return "_"
    if char == "!" or char == "?" or char == "." or char == "&" or char == "+" or char == "(" or char == ")": # special
        return ""
    if char == "#":
        return "sharp"
    return char.lower()

def escape(string):
    res = ""
    for symbol in string:
        if symbol in forbidden_symbols:
            res += "\\"
        res += symbol
    return res 

def to_hash_tag(string):
    res = ""
    if string[0].isdigit():
        res += "_"
    for char in string:
        res += replacement(char)
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

def format_entry(parser_number, entry_number):
    parser = parsers[parser_number]
    feed = parser["feed"]
    entry = parser["entries"][entry_number]
    categories = get_categories(entry)
    feed_title = "[" + feed["title"] + "]\n" if "title" in feed.keys() else ""
    entry_title = entry["title"] + "\n"
    entry_link = "\n" + entry["link"] + "\n"
    res = escape(feed_title) + "*" + escape(entry_title) + "*" + escape(categories) + escape(entry_link)
    return res

def send_entry(chat_id, parser_number, entry_number):
    r = requests.post("https://api.telegram.org/bot" + TOKEN + "/sendMessage", {"chat_id": chat_id, "text": format_entry(parser_number, entry_number), "parse_mode": "Markdown"})

def tick():
    for parser_number in range(0, len(parsers)):
        parsers[parser_number] = feedparser.parse(urls[parser_number])
        parser = parsers[parser_number]
        for entry_number in range(len(parser.entries)):
            entry = parser["entries"][entry_number]
            if check(entry):
                for id in chats:
                    send_entry(id, parser_number, entry_number)
    t = Timer(10.0, tick)
    t.start()

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def start(update, context):
    update.message.reply_text("Hi!")

def add_feed(update, context):
    if (len(context.args) == 0):
        update.message.reply_text("Send me feed URL")
    else:
        name = context.args[0]
        if (urlparse(name)):
            parsers.append(feedparser.parse(name))
            urls.append(name)
            print(name, file=fu)
            fu.flush()
            update.message.reply_text("Done.")
        else:
            print("Not a URL. Try again.")

def add_chat_id(update, context):
    if (len(context.args) == 0):
        update.message.reply_text("Send me chat id")
    else:
        try:
            if int(context.args[0]) // -1000000000000 != 1:
                raise Exception("Not an id")
            chats.append(int(context.args[0]))
            print(context.args[0], file=fc)
            fc.flush()
            update.message.reply_text("Done")
        except:
            update.message.reply_text("It seems, that this isn't an id")

def main():
    global bot
    updater = Updater(TOKEN, use_context=True, request_kwargs={'read_timeout': 120, 'connect_timeout': 60})
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler(ADD_FEED, add_feed))
    dp.add_handler(CommandHandler("add_chat_id", add_chat_id))
    bot = updater.bot
    updater.start_polling()
    tick()
    updater.idle()

main()
