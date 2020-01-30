from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, Updater
from telegram.ext import ChosenInlineResultHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = '806960355:AAHWm-LvEOI7ahMfL_Ie95DH1sN2nBe505E'

status_response = ""
REPORT_STATUS = 1
REPORT_SYMPTOMS = 2
CONVERSATION_END = 3
HANDLE_CS_MENU = 11
FREETEXT_INSTRUCT = 12
FREETEXT_SYMPTOMS = 19
symptom_report_db = {}

# Echo sent message
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def start(update, context):
    chat_ID = update.effective_chat.id
    user = update.effective_user
    firstname = user.first_name
    msg = "Hello, {}!\nPlease use '/report' to provide your current health status :)".format(firstname) 
    context.bot.send_message(chat_id=chat_ID, text=msg)

status_reply_buttons = ['Yes','No']
def report_status(update, context):
    status_buttonlist = [status_reply_buttons]
    status_reply = ReplyKeyboardMarkup(status_buttonlist,one_time_keyboard=True)
    update.message.reply_text("How are you today? Feeling healthy?", reply_markup=status_reply)
    return REPORT_STATUS

def add_to_symptom_str(update_txt, uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        return False
    
    new = symptom_report_db[uid] + "\n" + update_txt
    symptom_report_db[uid] = new
    return True

def get_symptom_str(uid):
    global symptom_report_db
    return symptom_report_db.get(uid,"")

def get_uid(update):
    return update.effective_user.username

#### SYMPTOM REPORTING CALLBACKS ####

def _get_symptom_table(uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        symptom_report_db[uid]["common_symptoms"] = {}
    master_dict = symptom_report_db.get(uid)
    return master_dict["common_symptoms"]

def build_symptom_markup():
    symptom_list = ["Fever","High fever (>38)","Runny nose", "Cough", "Sore throat", "Vomiting", "Diarrhea"]
    cs_button_list = []
    i = 0
    for s in symptom_list:
        butt = [InlineKeyboardButton(s, callback_data=i)]
        cs_button_list.append(butt)
        i += 1
    
    done = [InlineKeyboardButton("Done", callback_data = -1)]
    cs_button_list.append(done)

    return InlineKeyboardMarkup(cs_button_list)

cs_mu = build_symptom_markup()

def report_common_symptoms(update, context):
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text="Which of the following symptoms do you have? (You can select multiple)",
        reply_markup = cs_mu
    )
    return HANDLE_CS_MENU

def handle_symptom_buttonpress(update, context):
    print("HANDLE SYMPTOM BUTTON")
    user_ID = get_uid
    symptom_table = _get_symptom_table(user_ID)
    cb_query = update.callback_query
    og_msg = cb_query.message
    press_value = cb_query.callback_data
    cbq_data = cb_query.data

    print("PRESSED VALUE", press_value, "CBQ DATA", cbq_data)

    is_done = (press_value == -1)
    if is_done:
        return FREETEXT_INSTRUCT
    
    
    symptom_table[press_value] = 1
    context.bot.edit_message_text(
        chat_id = og_msg.chat_id,
        message_id = og_msg.message_id,
        text= og_msg.message.text + "<{}> ".format(press_value)
        )
    return HANDLE_CS_MENU

def report_symtoms_freetext_instr(update,context):
    chat_ID = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_ID,
        text="Please describe your symptoms. At the end of it, please type '/done'"
        )
    return FREETEXT_SYMPTOMS

report_count = 0
def report_symptoms_freetext(update, context):
    global report_count
    chat_ID = update.effective_chat.id
    update_text = update.message.text
    user_ID = get_uid(update)
    add_to_symptom_str(update_text, user_ID)
    report_count += 1
    if report_count > 3:
        report_count = 0
        context.bot.send_message(
            chat_id=chat_ID,
            text= "I got all of that. Remember to type '/done' when you are finished",
        )
    return FREETEXT_SYMPTOMS

def done_reporting_symptoms(update, context):
    chat_ID = update.effective_chat.id
    update_text = update.message.text
    user_ID = get_uid(update)
    cleaned_text = update_text.replace("/done","")
    add_to_symptom_str(cleaned_text, user_ID)
    symptom_str = get_symptom_str(user_ID)

    is_blank = (symptom_str == "")
    if not is_blank:
        replymsg = "Let me see if I got all of it, you said:{}".format(symptom_str)
       
    else:
        replymsg = "You haven't told me anything yet! Please use /report to submit your daily status"
        
    context.bot.send_message(
        chat_id=chat_ID,
        text= replymsg,
    )
    return CONVERSATION_END

def create_symptom_entry(uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        d = {}
        d["common_symptoms"] = []
        d["freetext"] = ""
        symptom_report_db[uid] = d


def report_status_response(update, context):
    update_text = update.message.text
    curr_chat = update.effective_chat
    chat_type = curr_chat.type
    chat_ID = curr_chat.id
    healthy_flag = (update_text == "Yes")
    print("GOT RESPONSE", healthy_flag)
    remove_keyboard = ReplyKeyboardRemove()
    if healthy_flag:
        context.bot.send_message(
            chat_id=chat_ID,
            text= "That's great! Please continue to take good care of yourself! :)",
            reply_markup= remove_keyboard
        )
        return CONVERSATION_END
    else:
        context.bot.send_message(
            chat_id=chat_ID,
            text= "I'm sorry to hear that.",
            reply_markup= remove_keyboard
        )
        user_ID = get_uid(update)
        create_symptom_entry(user_ID)
        return report_common_symptoms(update, context)

# Literally do nothing
def cancel(update, context):
    pass

# Initalizes the handlers for ths dispatcher
def init_handlers(dis):
    global status_response
    start_handler = CommandHandler('start', start)
    done_handler = CommandHandler('done', done_reporting_symptoms)

    status_report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_status)],
        states={
                REPORT_STATUS: [MessageHandler(Filters.text(status_reply_buttons), report_status_response)],
                REPORT_SYMPTOMS: [CommandHandler('report_common',report_common_symptoms)],   
                HANDLE_CS_MENU:[ChosenInlineResultHandler(handle_symptom_buttonpress)],
                FREETEXT_INSTRUCT: [MessageHandler((Filters.all), report_symtoms_freetext_instr)],
                FREETEXT_SYMPTOMS: [MessageHandler((~Filters.command), report_symptoms_freetext)],
                CONVERSATION_END: [MessageHandler(Filters.all, cancel)]
            },
        fallbacks=[
            CommandHandler('cancel', cancel)
        ],
        allow_reentry = True
        )

    dis.add_handler(start_handler)
    dis.add_handler(status_report_handler)
    dis.add_handler(done_handler)

    return dis

def main():
    print("Hello! :)")
    ## Bot TOKEN!
    updater = Updater(token=botToken, use_context=True)

    dispatcher = updater.dispatcher
    init_handlers(dispatcher)

    updater.start_polling()

main()