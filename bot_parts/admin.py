from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError, CallbackQuery

from bot_parts.functions import *


def add_chat(update: Update, context: CallbackContext, session: db.Session):
    try:
        chat_id = int(update.message.text)
    except ValueError:
        update.message.reply_text('Int is required')
        return False
    if not session.query(db.Chat).filter(db.Chat.id == str(chat_id)):
        try:
            context.bot.get_chat(chat_id)
        except TelegramError:
            update.message.reply_text('First add bot to the chat')
            return True
        session.add(db.Chat(id=str(chat_id)))
        update.message.reply_text('Done')
    else:
        update.message.reply_text('Already added')
    return True


def add_feed(update: Update, context: CallbackContext, session: db.Session):
    for feed_url in update.message.text.split('\n'):
        if urlparse(feed_url):
            if not session.query(db.Feed).filter(db.Feed.link == feed_url).first():
                session.add(db.Feed(link=feed_url))
                update.message.reply_text(f'Added {feed_url}')
            else:
                update.message.reply_text(f'{feed_url} already added')
        else:
            update.message.reply_text(f'{feed_url} is not a URL')
    return True


def get_admins_keyboard(current_user_id):
    session = db.Session()
    admins = session.query(db.User).filter(db.User.is_admin & (db.User.id != current_user_id)).all()
    keyboard = []
    for user in admins:
        keyboard.append([InlineKeyboardButton(user.name, callback_data=f'rmadm_{str(user.id)}')])
    keyboard.append([InlineKeyboardButton('Add admin', callback_data='addadm')])
    session.close()
    return InlineKeyboardMarkup(keyboard)


@admin_required
@pm_required
def list_admins(update: Update, context: CallbackContext):
    update.message.reply_text('Admins:', reply_markup=get_admins_keyboard(update.effective_user.id))


def get_chats_keyboard():
    session = db.Session()
    chats = session.query(db.Chat).all()
    keyboard = []
    for chat in chats:
        keyboard.append([InlineKeyboardButton(chat.name, callback_data=f'rmchat_{str(chat.id)}')])
    keyboard.append([InlineKeyboardButton('Add chat', callback_data='addchat')])
    session.close()
    return InlineKeyboardMarkup(keyboard)


@admin_required
@pm_required
def list_chats(update: Update, context: CallbackContext):
    update.message.reply_text('Chats:', reply_markup=get_chats_keyboard())


def get_feeds_keyboard():
    session = db.Session()
    feeds = session.query(db.Feed).all()
    keyboard = []
    for feed in feeds:
        keyboard.append([InlineKeyboardButton(feed.link, callback_data=f'rmfeed_{str(feed.id)}')])
    keyboard.append([InlineKeyboardButton('Add feed', callback_data='addfeed')])
    return InlineKeyboardMarkup(keyboard)


@admin_required
@pm_required
def list_feeds(update: Update, context: CallbackContext):
    update.message.reply_text('Feeds:', reply_markup=get_feeds_keyboard())


@admin_required
def admin_process_callback_query(update: Update, context: CallbackContext):
    session = db.Session()
    query: CallbackQuery = update.callback_query

    user = session.query(db.User).filter(db.User.id == update.effective_user.id).first()
    operation = query.data.split('_', 1)[0]
    param = query.data.split('_', 1)[1] if len(query.data.split('_', 1)) > 1 else ''
    if operation == 'rmadm':
        edit_user = session.query(db.User).get(int(param)).first()
        edit_user.is_admin = False
        session.commit()
        context.bot.edit_message_reply_markup(user.id, update.effective_message.message_id,
                                              reply_markup=get_admins_keyboard(user.id))
    elif operation == 'addadm':
        user.tg_operation = operation
        context.bot.send_message(chat_id=user.id, text="Enter new admin id:")
        context.bot.delete_message(chat_id=user.id, message_id=query.message.message_id)
    elif operation == 'rmchat':
        session.delete(session.query(db.Chat).get(int(param)).first())
        session.commit()
        context.bot.edit_message_reply_markup(user.id, update.effective_message.message_id,
                                              reply_markup=get_chats_keyboard())
    elif operation == 'addchat':
        user.tg_operation = operation
        context.bot.send_message(chat_id=user.id, text="Enter new chat id:")
        context.bot.delete_message(chat_id=user.id, message_id=query.message.message_id)
    elif operation == 'rmfeed':
        session.delete(session.query(db.Feed).filter(db.Feed.id == int(param)).first())
        session.commit()
        context.bot.edit_message_reply_markup(user.id, update.effective_message.message_id,
                                              reply_markup=get_feeds_keyboard())
    elif operation == 'addfeed':
        user.tg_operation = operation
        context.bot.send_message(chat_id=user.id, text="Enter new feed url:")
        context.bot.delete_message(chat_id=user.id, message_id=query.message.message_id)
    session.commit()
    session.close()


@admin_required
@pm_required
def admin_process_messages(update: Update, context: CallbackContext):
    session = db.Session()

    user = session.query(db.User).filter(db.User.id == update.effective_user.id).first()
    operation = user.tg_operation.split('_', 1)[0]
    param = user.tg_operation.split('_', 1)[1] if len(user.tg_operation.split('_', 1)) > 1 else ''

    if operation == 'addadm':
        added_user = session.query(db.User).filter(db.User.id == int(update.message.text)).first()
        if not added_user:
            update.message.reply_text("User did not started bot!")
        else:
            added_user.is_admin = True
            update.message.reply_text("Admin added!")
        user.tg_operation = ''
    elif operation == 'addchat':
        if add_chat(update, context, session):
            user.tg_operation = ''
    elif operation == 'addfeed':
        if add_feed(update, context, session):
            user.tg_operation = ''
    session.commit()
    session.close()
