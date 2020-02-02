from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, Updater
from telegram.ext import CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from supp_classes import Group, Member
from local import get_bot_token
import logging

log = 1

if log: logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = get_bot_token()

status_response = ""
REPORT_STATUS = 1
REPORT_SYMPTOMS = 2
CONVERSATION_END = -1
HANDLE_CS_MENU = 11
FREETEXT_SYMPTOMS = 17
CONFIRM_FREETEXT_SYMPTOMS = 18
HANDLE_MGR_MENU = 21
CREATE_GROUP = 22
REVIEW_GROUPS = 23
RECV_GROUP_NAME = 24
EXIT_MENU = "EXIT"
symptom_report_db = {}
ADMINS_INFO = {}
PM_TABLE = {}

# GENERAL FUNCTIONS
def get_uid(update):
    return update.effective_user.username

def get_chat_id(update):
    return update.effective_chat.id

def make_menu(blist):
    button_list = []
    for b_txt in blist:
        entry = [InlineKeyboardButton(b_txt, callback_data = b_txt)]
        button_list.append(entry)

    done = [InlineKeyboardButton("Done", callback_data = EXIT_MENU)]
    button_list.append(done)
    menu_mu = InlineKeyboardMarkup(button_list)
    return menu_mu

# Hashes the group name + admin name into a link code
def hash_group(admin_id, group_name):
    # HASHING
    ap = admin_id
    return

join_grp_cmd_str = "join_grp"
# Creates a html link that users can click on to trigger a chat
def make_group_link(group_code):
    link_code_base = "https://api.telegram.org/" + botToken + "/" + join_grp_cmd_str
    link_code = link_code_base + "?group=" + group_code
    return link_code

# Returns True if diverted.
def direct_to_privatechat(update, context):
    chat_ID = get_chat_id(update)
    chat_type = update.effective_chat.type
    user = update.effective_user
    firstname = user.first_name
    user_ID = get_uid(update)
    print("CHAT TYPE", chat_type)
    if not chat_type == "private":
        if is_registered(user_ID):
            msg = "Hi, {}!\n Please talk to me here so as to avoid spamming groups".format(firstname)
            private_chat_ID = get_private_chat_id(user_ID)
            context.bot.send_message(chat_id=private_chat_ID, text=msg)
            return True
        else:    
            msg = "Hi, {}!\nPlease start a private conversation with me to continue".format(firstname) 
            context.bot.send_message(chat_id=chat_ID, text=msg)
            return True
    return False

def add_to_PM_TABLE(userID, chatID):
    PM_TABLE[userID] = chatID
    return

def get_private_chat_id(userID):
    private_chat_id = PM_TABLE.get(userID)
    return private_chat_id

# Check if this user has started a private chat with bot
def is_registered(userID):
    return userID in PM_TABLE


# CORE COMPONENT
def join_group(update, context):
    print("JOIN GROUP CALLED")
    print(update)
    user_ID = get_uid(update)
    group_name = "<A group>"
    if not is_registered(user_ID):
        chat_ID = get_chat_id(update)
        msg = "Hello! You are not registered"
    else:
        chat_ID = get_private_chat_id(user_ID)
        msg = "Succesffuly joined {}!".format(group_name)
    context.bot.send_message(chat_id=chat_ID, text=msg)

    return

def start_message(update, context):
    chat_ID = update.effective_chat.id
    user = update.effective_user
    firstname = user.first_name
    diverted = direct_to_privatechat(update, context)
    if not diverted:
        user_ID = get_uid(update)
        add_to_PM_TABLE(user_ID, chat_ID)
        msg = "Hello, {}!\nPlease use '/report' to provide your current health status :)".format(firstname) 
    context.bot.send_message(chat_id=chat_ID, text=msg)

status_reply_buttons = ['Yes','No']
def report_status(update, context):
    diverted = direct_to_privatechat(update, context)
    if not diverted:
        status_buttonlist = [status_reply_buttons]
        status_reply = ReplyKeyboardMarkup(status_buttonlist,one_time_keyboard=True)
        update.message.reply_text("How are you today? Feeling healthy?", reply_markup=status_reply)
        return REPORT_STATUS
    return

def add_to_symptom_str(update_txt, uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        return False
    
    new = symptom_report_db[uid]["freetext"] + "\n" + update_txt + ""
    symptom_report_db[uid]["freetext"] = new
    return True

def get_symptom_str(uid):
    global symptom_report_db
    user_entry = symptom_report_db.get(uid,"")
    freetext = user_entry["freetext"]
    return freetext


def wipe_freetext_symptoms(uid):
    global symptom_report_db
    symptom_report_db[uid]["freetext"] = ""
    return

def report_symtoms_freetext_instr(update,context):
    print("FREETEXT INSTRUCTIONS")
    chat_ID = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_ID,
        text="Please describe any additional symptoms. If there are none, state 'none' or 'NA'. At the end of it, please type '/done'"
        )
    return FREETEXT_SYMPTOMS

report_count = 0
def report_symptoms_freetext(update, context):
    print("REPORT SYMPTOMS FREETEXT")
    global report_count
    chat_ID = update.effective_chat.id
    update_text = update.message.text
    print("CAPTURED TEXT", update_text)
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

def done_reporting_symptoms_freetext(update, context):
    def build_yesno_markup():
        yesno = [[InlineKeyboardButton("Yes", callback_data = "yes")],[InlineKeyboardButton("No", callback_data = "no")]]
        return InlineKeyboardMarkup(yesno)

    chat_ID = update.effective_chat.id
    update_text = update.message.text
    user_ID = get_uid(update)
    cleaned_text = update_text.replace("/done","")
    add_to_symptom_str(cleaned_text, user_ID)
    symptom_str = get_symptom_str(user_ID)

    is_blank = (symptom_str == "")
    if not is_blank:
        replymsg = "Let me see if I got all of it, you said:{}".format(symptom_str)
        yesno_mu = build_yesno_markup()
       
    else:
        replymsg = "You haven't told me anything yet! Please use /report to submit your daily status"
        yesno_mu = None
        
    context.bot.send_message(
        chat_id=chat_ID,
        text= replymsg,
        reply_markup = yesno_mu
    )
    return CONFIRM_FREETEXT_SYMPTOMS

def confirm_freetext_symptoms(update, context):
    print("CONFIRMING FREETEXT SYMPTOMS")
    cb_query = update.callback_query
    button_press = cb_query.data
    og_msg = cb_query.message
    # Remove keyboard from old msg
    context.bot.edit_message_text(
        chat_id = og_msg.chat_id,
        message_id = og_msg.message_id,
        text = og_msg.text
        )
    if button_press == "yes":
        context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = "Got it. If there are any changes to your condition, notify us as soon as possible. Please take care of yourself and get well soon!"
        )
        return CONVERSATION_END
    else:
        user_ID = get_uid(update)
        wipe_freetext_symptoms(user_ID)
        print("RESETTED USER STUFF")
        context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = "Okay, I'll forget whatever was said earlier."
        )
        next_state = report_symtoms_freetext_instr(update, context)
        print("CONFIRM NO")
        return next_state


#### SYMPTOM REPORTING CALLBACKS ####
def _get_symptom_table(uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        symptom_report_db[uid] = {}
        symptom_report_db[uid]["common_symptoms"] = {}
    master_dict = symptom_report_db.get(uid)
    return master_dict["common_symptoms"]
    
class Symp:
    def __init__(self):
        self.symptom_list = ["Fever","High fever (>38)","Runny nose", "Cough", "Sore throat", "Vomiting", "Diarrhea"]

    def get_symptom_list(self):
        return self.symptom_list.copy()

symp = Symp()

# Works like a poll bot. Pressing the same value a second time will remove it.
def toggle_symptom_in_table(s, uid):
    symptom_table = _get_symptom_table(uid)
    if not s in symp.symptom_list:
        print("UNSUPPORTED SYMPTOM {}".format(s))
        return False
    
    if not s in symptom_table:
        # Create
        symptom_table[s] = 1
    else:
        # Toggle
        symptom_table[s] = 1 - symptom_table[s]

    return

def get_listed_symptoms_text(uid):
    symptom_table = _get_symptom_table(uid)
    out = ""
    for sym, v in symptom_table.items():
        if v > 0:
            if out == "":
                out = sym
            else:
                out = out + "\n" + sym
    return out

cs_mu = make_menu(symp.get_symptom_list())

def report_common_symptoms(update, context):
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text="Which of the following symptoms do you have? (You can select multiple):",
        reply_markup = cs_mu
    )
    return HANDLE_CS_MENU

def handle_symptom_buttonpress(update, context):
    user_ID = get_uid(update)
    cb_query = update.callback_query
    og_msg = cb_query.message
    # press_value = cb_query.callback_data
    press_value = cb_query.data

    is_done = (press_value == EXIT_MENU)
    if is_done:
        done_line = "\n-----END-----"
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text + done_line
            )
        return report_symtoms_freetext_instr(update, context)

    s_name = press_value

    toggle_symptom_in_table(s_name, user_ID)
    listed_symptoms_text = get_listed_symptoms_text(user_ID)
    header = og_msg.text.split(":")[0] + ":\n"
    new_text = header + listed_symptoms_text
    context.bot.edit_message_text(
        chat_id = og_msg.chat_id,
        message_id = og_msg.message_id,
        text = new_text,
        reply_markup = cs_mu
        )
    
    return HANDLE_CS_MENU

def create_symptom_entry(uid):
    global symptom_report_db
    if not uid in symptom_report_db:
        d = {}
        d["common_symptoms"] = {}
        d["freetext"] = ""
        symptom_report_db[uid] = d

def report_status_response(update, context):
    update_text = update.message.text
    curr_chat = update.effective_chat
    chat_type = curr_chat.type
    
    healthy_flag = (update_text == "Yes")
    print("GOT STATUS RESPONSE. HEALTHY?", healthy_flag)
    chat_ID = curr_chat.id
    print("CHAT TYPE", chat_type)
    remove_keyboard = ReplyKeyboardRemove()

    if not chat_type == "private":
        # initiate_private_convo()
        return CONVERSATION_END

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

# ADMIN/GROUP controls
def add_group_for_admin(admin_id, group_name):
    global ADMINS_INFO
    if not admin_id in ADMINS_INFO:
        new_d = {}
        new_d["groups"] = {}
        ADMINS_INFO[admin_id] = new_d
    
    new_group = Group(group_name, admin_id)
    ADMINS_INFO[admin_id]["groups"][group_name] = new_group

def get_groups_as_list(admin_id):
    global ADMINS_INFO
    out = ""
    if not admin_id in ADMINS_INFO:
        return out    
    curr_admin_info = ADMINS_INFO[admin_id]
    all_groups = curr_admin_info.get("groups", {})

    for grpname in list(all_groups.keys()):
        if out == "":
            out = grpname
        else:
            out = out + "\n" + grpname
    return out

admin_menu_butts = ["Create group", "Review groups"]
def generate_group_link(update,context):    
    grp_name = update.message.text
    admin_id = get_uid(update)
    group_code = hash_group(admin_id, grp_name)
    group_link = make_group_link(group_code)
    user_id = get_uid(update)
    add_group_for_admin(user_id, grp_name)

    msg_txt = "Your code for the group '{}' has been generated:\n{}".format(grp_name, group_link)
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text = msg_txt
    )

    second_msg_text = "Whoever follows this link will be able to join the group"
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text = second_msg_text
    )
    return CONVERSATION_END

def review_groups(update, context):
    admin_id = get_uid(update)
    grouplist = get_groups_as_list(admin_id)
    if not grouplist == "":
        msg_txt = "You are the admin of the following groups:\n" + grouplist
    else:
        msg_txt = "You are currently not the admin of any groups. Use /open_manager to create one"
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text = msg_txt
    )

def open_manager(update, context):
    admin_menu_mu = make_menu(admin_menu_butts)
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text = "Here are the manager options",
        reply_markup = admin_menu_mu
    )
    return HANDLE_MGR_MENU

def create_group(update,context):
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text = "Send me the name of the group you would like to create"
    )
    return RECV_GROUP_NAME

def handle_manager_buttonpress(update,context):
    user_ID = get_uid(update)
    cb_query = update.callback_query
    og_msg = cb_query.message
    press_value = cb_query.data
    is_done = (press_value == EXIT_MENU)
    if is_done:
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return CONVERSATION_END
    if press_value == "Create group":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return create_group(update, context)
    elif press_value == "Review groups":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return review_groups(update,context)
    else:
        print("UNRECOGNIZED BUTTONPRESS")

# CHATBOT INIT
# Initalizes the handlers for this dispatcher
def init_handlers(dis):
    global status_response
    start_handler = CommandHandler('start', start_message)
    done_handler = CommandHandler('done', done_reporting_symptoms_freetext)
    symptom_button_handler = CallbackQueryHandler(handle_symptom_buttonpress)
    join_group_handler = CommandHandler(join_grp_cmd_str, join_group)

    # 
    status_report_handler = ConversationHandler(
        entry_points=[
            CommandHandler('report', report_status),
            done_handler
            ],
        states={
                REPORT_STATUS: [MessageHandler(Filters.text(status_reply_buttons), report_status_response)],
                REPORT_SYMPTOMS: [CommandHandler('report_common',report_common_symptoms)],   
                HANDLE_CS_MENU: [symptom_button_handler],
                FREETEXT_SYMPTOMS: [MessageHandler((~Filters.command), report_symptoms_freetext)],
                CONFIRM_FREETEXT_SYMPTOMS: [CallbackQueryHandler(confirm_freetext_symptoms)],
                CONVERSATION_END: [MessageHandler(Filters.all, cancel)]
            },
        fallbacks=[
            CommandHandler('cancel', cancel)
        ],
        allow_reentry = True        
        )

    admin_convo = ConversationHandler(
        entry_points = [
            CommandHandler('open_manager', open_manager)
            ],
        states = {
            HANDLE_MGR_MENU: [CallbackQueryHandler(handle_manager_buttonpress)],
            RECV_GROUP_NAME: [MessageHandler(Filters.all, generate_group_link)]
        },
        fallbacks = [
            CommandHandler('cancel', cancel)
        ],
        allow_reentry = True        
    )

    dis.add_handler(start_handler)
    dis.add_handler(status_report_handler)
    dis.add_handler(admin_convo)
    dis.add_handler(join_group_handler)

    return dis

def main():
    ## Bot TOKEN!
    updater = Updater(token=botToken, use_context=True)

    dispatcher = updater.dispatcher
    init_handlers(dispatcher)

    print("Started Polling")
    updater.start_polling()

main()