from telegram import Update, Message, User
from telegram.ext import CallbackContext

import database as db


def admin_required(func):
    def decorator(update: Update, context: CallbackContext):
        session = db.Session()
        tg_user: User = update.effective_user
        message: Message = update.callback_query.message if update.callback_query else update.message
        user = session.query(db.User).filter(db.User.id == tg_user.id).first()
        session.close()
        if (not user) or (not user.is_admin):
            context.bot.send_message(message.chat_id, 'Permission denied')
        else:
            func(update, context)

    return decorator


def chat_admin_required(func):
    def decorator(update: Update, context: CallbackContext):
        tg_user: User = update.effective_user
        message: Message = update.callback_query.message if update.callback_query else update.message
        if context.bot.get_chat(message.chat.id)['type'] == 'private' or \
                context.bot.get_chat_member(message.chat.id, tg_user.id)['status'] in \
                ['creator', 'administrator']:
            func(update, context)
        else:
            context.bot.send_message(message.chat_id, 'Chat admin required')

    return decorator


def pm_required(func):
    def decorator(update: Update, context: CallbackContext):
        tg_user: User = update.effective_user
        message: Message = update.callback_query.message if update.callback_query else update.message
        if message.chat.type == 'private':
            func(update, context)

    return decorator


def autocreate_user(func):
    def decorator(update: Update, context: CallbackContext):
        session = db.Session()
        tg_user: User = update.effective_user
        if not session.query(db.User).filter(db.User.id == tg_user.id).first():
            session.add(db.User(id=tg_user.id, is_admin=False))
            session.commit()
            session.close()
        func(update, context)

    return decorator
