import json
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

import royalroad as rr
import novelfull as nf

from pathlib import Path

import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def read_credentials():
    return json.load(open('credentials.json'))


async def royalroad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.effective_message.text.replace('/royalroad ', '')
    await context.bot.send_message( chat_id=update.effective_chat.id, text='I am downloading and preparing the requested novel from RoyalRoad! ')

    prepared_file = rr.Royalroad(url).download()

    await context.bot.send_document( chat_id=update.effective_chat.id, document= Path( prepared_file ) )

    os.remove(prepared_file)
    

async def novelfull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.effective_message.text.replace('/novelfull ', '')
    await context.bot.send_message( chat_id=update.effective_chat.id, text='I am downloading and preparing the requested novel from NovelFull!')

    prepared_file = nf.Novelful(url).download()

    await context.bot.send_document( chat_id=update.effective_chat.id, document= Path( prepared_file ) )

    os.remove(prepared_file)


if __name__ == '__main__':
    credentials = read_credentials()
    application = ApplicationBuilder().token(credentials['token']).build()
    
    royalroad_handler = CommandHandler('royalroad', royalroad, filters=filters.Chat(credentials['chat_id']))
    novelfull_handler = CommandHandler('novelfull', novelfull, filters=filters.Chat(credentials['chat_id']))

    application.add_handler(royalroad_handler)
    application.add_handler(novelfull_handler)
    
    application.run_polling()