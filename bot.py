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
import database as db

from secure import ADD_FEED_COMMAND, TOKEN, PROXY_URL, PROXY_USERNAME, PROXY_PASSWORD, ADD_CHAT_ID_COMMAND

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO: Refactor next 3 functions
def replacement(char):
    if ord(char) in [8210, 8211, 8212, 8213, 11834, 11835, 45, 32]:  # dash types
        return '_'
    if char in ['!', '?', '(', ')', '\'', "'", '«', '»']:  # special chars
        return ''
    if char == '&':
        return '_'
    if char == '#':
        return 'sharp'
    if char == '.':
        return 'dot'
    return char.lower()


def to_hash_tag(string):
    string = string.strip()
    string = string.strip('.,?!')
    res = ''
    if string[0].isdigit():
        res += '_'
    for char in string:
        res += replacement(char)
    res = res.replace('c++', 'cpp')
    final_result = '#'
    for char in res:
        if char != '_':
            final_result += char
        elif final_result[-1] != '_':
            final_result += '_'
    return final_result


def get_categories(entry):
    if 'tags' in entry.keys():
        lowercase_categories = map(lambda tag: tag.get('term', '').lower(), entry['tags'])
        unique_lowercase_categories = list(set(lowercase_categories))
        unique_lowercase_hashtags = list(map(to_hash_tag, unique_lowercase_categories))
        unique_lowercase_hashtags.sort()
        result_string = ' '.join(unique_lowercase_hashtags)
        if len(result_string):
            result_string += '\n'
        return result_string
    else:
        return ''


def format_entry(entry, feed_title=None):
    categories = get_categories(entry)
    feed_title = '[' + feed_title + ']' if feed_title else ''
    entry_title = entry['title']
    entry_link = entry['link']
    res = escape(feed_title + '\n') + '<b>' + escape(entry_title) + '</b>' + escape(
        '\n' + categories + '\n') + '<a href=\'' + entry_link + '\'>Читать</a>'
    return res


# TODO: придумать способ получше, чем таймер. Мне кажется, что таймер не оч. Но хз
def tick(bot: Bot):
    session = db.Session()
    session.autoflush = True
    feeds = session.query(db.Feed).all()
    chats = session.query(db.Chat).all()
    for feed in feeds:
        parsed_feed = feedparser.parse(feed.link)
        feed_entries = parsed_feed.entries
        feed_title = parsed_feed.title if 'title' in parsed_feed.keys() else None
        for feed_entry in feed_entries:
            if session.query(db.Entry).filter(db.Entry.link == feed_entry.link).first() is None:
                for chat in chats:
                    bot.send_message(chat.id, text=format_entry(feed_entry, feed_title),
                                     parse_mode=ParseMode.HTML, timeout=60)
                    sleep(0.1)
                session.add(db.Entry(title=feed_entry.title, link=feed_entry.link))
    session.commit()
    t = Timer(10, tick, [bot])
    t.start()


def error(update: Update, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')


def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hi!')


def add_feed(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text(f'Usage: /{ADD_FEED_COMMAND} <chat_id>')
    else:
        url = context.args[0]
        if urlparse(url):
            session = db.Session()
            if session.query(db.Feed).filter(db.Feed.link == url).first() is None:
                session.add(db.Feed(link=url))
                session.commit()
                update.message.reply_text('Done')
            else:
                update.message.reply_text('Already added')
        else:
            print('Not a URL. Try again')


def add_chat_id(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text(f'Usage: /{ADD_CHAT_ID_COMMAND} <chat_id>')
    else:
        try:
            chat_id = int(context.args[0])
        except ValueError:
            update.message.reply_text(f'Usage: /{ADD_CHAT_ID_COMMAND} <chat_id>')
            return
        session = db.Session()
        if session.query(db.Chat).filter(db.Chat.id == chat_id) is not None:
            session.add(db.Chat(id=chat_id))
            session.commit()
            update.message.reply_text('Done')
        else:
            update.message.reply_text('Already added')


def main():
    updater = Updater(TOKEN, use_context=True, request_kwargs={
        'proxy_url': PROXY_URL,
        'urllib3_proxy_kwargs': {
            'username': PROXY_USERNAME,
            'password': PROXY_PASSWORD,
        }
    })
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler(ADD_FEED_COMMAND, add_feed))
    dp.add_handler(CommandHandler(ADD_CHAT_ID_COMMAND, add_chat_id))
    updater.start_polling()
    print('Load complete.')
    tick(updater.bot)
    updater.idle()


if __name__ == '__main__':
    main()
