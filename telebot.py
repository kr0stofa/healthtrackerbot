from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, Updater
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = '806960355:AAHWm-LvEOI7ahMfL_Ie95DH1sN2nBe505E'

status_response = ""
REPORT_STATUS = 1
REPORT_SYMPTOMS = 2
CONVERSATION_END = 3

# Echo sent message
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def start(update, context):
    chat_ID = update.effective_chat.id
    user = update.effective_user
    firstname = user.first_name
    msg = "Hello, {}!\nPlease use '/report' to provide your current health status :)".format(firstname) 
    context.bot.send_message(chat_id=chat_ID, text=msg)

def report_status(update, context):
    status_buttonlist = [['Yes','No']]
    status_reply = ReplyKeyboardMarkup(status_buttonlist,one_time_keyboard=True)
    update.message.reply_text("How are you today? Feeling healthy?", reply_markup=status_reply)
    return REPORT_STATUS

report_count = 0
def report_symptoms(update, context):
    global report_count
    chat_ID = update.effective_chat.id
    report_count += 1
    if report_count > 3:
        report_count = 0
        context.bot.send_message(
            chat_id=chat_ID,
            text= "I got all of that. Remember to type '/done' when you are finished",
        )
    return REPORT_SYMPTOMS

def report_status_response(update, context):
    update_text = update.message.text
    chat_ID = update.effective_chat.id
    healthy_flag = (update_text == "Yes")
    print("GOT RESPONSE", healthy_flag)
    
    if healthy_flag:
        context.bot.send_message(
            chat_id=chat_ID,
            text= "That's great! Please continue to take good care of yourself! :)",
        )
        return CONVERSATION_END
    else:
        context.bot.send_message(
            chat_id=chat_ID,
            text= "I'm sorry to hear that. Please describe your symptoms. At the end of it, please type '/done'",
        )
        return REPORT_SYMPTOMS

# Literally do nothing
def cancel(update, context):
    pass

# Initalizes the handlers for ths dispatcher
def init_handlers(dis):
    global status_response
    start_handler = CommandHandler('start', start)
    status_report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_status)],
        states={
                REPORT_STATUS: [MessageHandler(Filters.regex('^(Yes|No)$'), report_status_response)],
                REPORT_SYMPTOMS: [MessageHandler(Filters.all, report_symptoms)],
                CONVERSATION_END: [MessageHandler(Filters.all, cancel)]
            },
        fallbacks=[CommandHandler('cancel', cancel)]
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