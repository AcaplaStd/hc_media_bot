import logging
from html import escape
from threading import Timer
from time import sleep

import feedparser
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from bot_parts.admin import *
from bot_parts.functions import *
from secure import TOKEN, PROXY_URL, PROXY_USERNAME, PROXY_PASSWORD

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
    session.close()
    if updater.running:
        t = Timer(10, tick, [bot])
        t.start()


def error(update: Update, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')


@autocreate_user
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hi!')


@chat_admin_required
def add_current_chat(update: Update, context: CallbackContext):
    session = db.Session()
    if not session.query(db.Chat).filter(db.Chat.id == str(update.effective_chat.id)).first():
        session.add(db.Chat(id=str(update.message.chat.id), name=update.message.chat.title))
        session.commit()
        session.close()
        update.message.reply_text('Done')
    else:
        update.message.reply_text('Already added')


@chat_admin_required
def remove_current_chat(update: Update, context: CallbackContext):
    session = db.Session()
    chat = session.query(db.Chat).filter(db.Chat.id == str(update.effective_chat.id)).first()
    if chat:
        session.delete(chat)
        session.commit()
        session.close()
        update.message.reply_text('Done')
    else:
        update.message.reply_text('Chat not added')


@autocreate_user
def callback(update: Update, context: CallbackContext):
    admin_process_callback_query(update, context)

    context.bot.answer_callback_query(update.callback_query.id)


@autocreate_user
def messages(update: Update, context: CallbackContext):
    session = db.Session()
    user = session.query(db.User).filter(db.User.id == update.effective_user.id).first()
    session.close()
    if user.tg_operation == '':
        return
    admin_process_messages(update, context)


def main():
    global updater
    updater = Updater(TOKEN, use_context=True, request_kwargs={
        'proxy_url': PROXY_URL,
        'urllib3_proxy_kwargs': {
            'username': PROXY_USERNAME,
            'password': PROXY_PASSWORD,
        }
    })
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('add_current_chat', add_current_chat))
    dp.add_handler(CommandHandler('rm_current_chat', remove_current_chat))

    # Admin
    dp.add_handler(CommandHandler('feeds', list_feeds))
    dp.add_handler(CommandHandler('chats', list_chats))
    dp.add_handler(CommandHandler('admins', list_admins))

    dp.add_handler(CallbackQueryHandler(callback))
    dp.add_handler(MessageHandler(Filters.text, messages))

    updater.start_polling()
    print('Load complete.')
    tick(updater.bot)
    updater.idle()


if __name__ == '__main__':
    main()
