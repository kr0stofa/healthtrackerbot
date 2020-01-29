from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = '806960355:AAHWm-LvEOI7ahMfL_Ie95DH1sN2nBe505E'

status_response = ""

# Echo sent message
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def start(update, context):
    chat_ID = update.effective_chat.id
    user = update.effective_user
    firstname = user.first_name
    msg = "Hello,{}!\nPlease use '\\report' to provide your current health status :)".format(firstname) 
    context.bot.send_message(chat_id=chat_ID, text=msg)

status_buttonlist = [
    [InlineKeyboardButton('No symptoms :)',
                                  callback_data='no_symptoms')],
    [InlineKeyboardButton('Have symptoms',
                                  callback_data='has_symptoms')]
]

def report_status(update, context):
    status_reply = InlineKeyboardMarkup(status_buttonlist)
    update.message.reply_text("How are you today?", reply_markup=status_reply)
    print("Callback_data: " + response)

def report_status_response(update, context):
    query = update.callback_query
    response = query.data
    bot = context.bot
    print("GOT RESPONSE", response)
    if response == 'has_symptoms':
        bot.send_message(
            chat_id=query.message.chat_id,
            text= "That's great! Please continue to take good care of yourself! :)",
        )
    elif response == 'no_symptoms':
        bot.send_message(
            chat_id=query.message.chat_id,
            text= "That's great! Please continue to take good care of yourself! :)",
        )
    else:
        bot.send_message(
            chat_id=query.message.chat_id,
            text= query.message.text + "\nRecieved unknown response: " + response,
        )

# Initalizes the handlers for ths dispatcher
def init_handlers(dis):
    global status_response
    start_handler = CommandHandler('start', start)
    status_report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_status)],
        states={
                status_response:[CallbackQueryHandler(report_status)]
            },
        fallbacks=[CommandHandler('start', start)]
        )
    dis.add_handler(start_handler)
    dis.add_handler(status_report_handler)

    return dis

def main():
    print("Hello! :)")
    ## Bot TOKEN!
    updater = Updater(token=botToken, use_context=True)

    dispatcher = updater.dispatcher
    init_handlers(dispatcher)

    updater.start_polling()

main()