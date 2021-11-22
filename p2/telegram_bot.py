import time
import datetime
import random

import pyfiglet
import logging
import logging.config
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    PollHandler,
)
import telegram

from _model import *


def get_chat_id(update, context):
    chat_id = -1

    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        chat_id = context.bot_data[update.poll.id]

    return chat_id


def get_user(update):
    user: User = None

    _from = None

    if update.message is not None:
        _from = update.message.from_user
    elif update.callback_query is not None:
        _from = update.callback_query.from_user

    if _from is not None:
        user = User()
        user.id = _from.id
        user.first_name = _from.first_name if _from.first_name is not None else ""
        user.last_name = _from.last_name if _from.last_name is not None else ""
        user.lang = _from.language_code if _from.language_code is not None else "n/a"

    logging.info(f"from {user}")

    return user

N_ANS = 6
answered_answers = 0
correct_ans_count = 0

def start_command_handler(update, context):
    """Send a message when the command /start is issued."""
    add_typing(update, context)

    preguntas = [
    ["¿Que es git?",["Una plataforma de repositorios remotos", "Un sistema de control de versiones", "Un lenguaje de script"],
    1, "Un sistemas de control de versiones"],
    ["¿Cuál es el comando para obtener el estado actual del repositorio git?",["git status", "git current", "git currentStatus"],
    0, "git status"],
    ["¿Cuál es el comando para inicializar un repositorio git?", ["git start", "git now", "git init"],
    2, "git init"],
    ["¿Cuál es el comando para obtener el historial de commits?", ["git commits", "git log", "git all commits"],
    1, "git log"],
    ["¿Cuál es el comando para pushear a remote origin?", ["git remote", "git remote push", "git push origin"],
    2, "git push origin"],
    ["Git pull es una combinación de", ["add y commit", "fetch y merge", "branch y commit"],
    1, "fetch y merge"],
    ["¿Cual opcion de git reset no altera el directorio de trabajo?", ["--soft", "--mixed", "--hard"],
    [0, 1], ["--soft", "--mixed"]],
    ["¿Que tipo de merge ocurre cuando hay desarrollo lineal entre las ramas a fusionar?", ["fastforward", "recursive", "linear"],
    0, "fastforward"],
    ["¿Que comando se usa para crear una nueva rama?", ["checkout -b 'nombre-rama'", "create branch 'nombre-rama'", "new branch 'nombre-rama'"],
    0, "checkout -b 'nombre-rama'"],
    ["¿Que comando se usa para cambiar de rama?", ["checkout -c 'nombre-rama'", "checkout 'nombre-rama'", "change branch 'nombre-rama'"],
    1, "checkout 'nombre-rama'"],
    ["¿Que comando sirve para introducir un commit de una rama a otra?", ["git get commit", "git add commit","git cherrypick commit"],
    2, "git cherrypick commit"],
    ["¿Que comando sirve para revertir los cambios hechos en una rama?", ["git revert", "git goback","git reset"],
    [0, 2], ["git revert","git reset"]]

    ]

    randoms = random.sample(range(len(preguntas)), N_ANS)

    for i in randoms:
        quiz_question = QuizQuestion()
        quiz_question.question = preguntas[i][0]
        quiz_question.answers = preguntas[i][1]
        quiz_question.correct_answer_position = preguntas[i][2]
        quiz_question.correct_answer = preguntas[i][3]

        add_quiz_question(update, context, quiz_question)


def help_command_handler(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Type /start")


def new_member(update, context):
    logging.info(f"new_member : {update}")


    add_typing(update, context)
    add_text_message(update, context, f"New user")


def main_handler(update, context):
    logging.info(f"update : {update}")

    if update.message is not None:
        user_input = get_text_from_message(update)
        logging.info(f"user_input : {user_input}")

        # reply
        add_typing(update, context)
        add_text_message(update, context, f"You said: {user_input}")


        # ban member
        # m = context.bot.kick_chat_member(
        #     chat_id="-1001572091573", #get_chat_id(update, context),
        #     user_id='1041389347',
        #     timeout=int(time.time() + 86400))
        #
        # logging.info(f"kick_chat_member : {m}")


def poll_handler(update, context):
    global N_ANS
    global answered_answers
    global correct_ans_count

    logging.info(f"question : {update.poll.question}")
    logging.info(f"correct option : {update.poll.correct_option_id}")
    logging.info(f"option #1 : {update.poll.options[0]}")
    logging.info(f"option #2 : {update.poll.options[1]}")
    logging.info(f"option #3 : {update.poll.options[2]}")

    user_answer = get_answer(update)
    logging.info(f"correct option {is_answer_correct(update)}")
    
    answered_answers+=1
    correct_ans_count = correct_ans_count+1 if is_answer_correct(update) else correct_ans_count

    #add_text_message(update, context, f"Correct answer is {update.poll.correct_option_id}")

    if answered_answers == N_ANS:
        add_typing(update, context)
        add_text_message(update, context, f"Nota: {correct_ans_count+1}")
        answered_answers = 0
        correct_ans_count = 0


def add_typing(update, context):
    context.bot.send_chat_action(
        chat_id=get_chat_id(update, context),
        action=telegram.ChatAction.TYPING,
        timeout=1,
    )
    time.sleep(1)


def add_text_message(update, context, message):
    context.bot.send_message(chat_id=get_chat_id(update, context), text=message)


def add_suggested_actions(update, context, response):
    options = []

    for item in response.items:
        options.append(InlineKeyboardButton(item, callback_data=item))

    reply_markup = InlineKeyboardMarkup([options])

    context.bot.send_message(
        chat_id=get_chat_id(update, context),
        text=response.message,
        reply_markup=reply_markup,
    )


def add_quiz_question(update, context, quiz_question):
    message = context.bot.send_poll(
        chat_id=get_chat_id(update, context),
        question=quiz_question.question,
        options=quiz_question.answers,
        type=Poll.QUIZ,
        correct_option_id=quiz_question.correct_answer_position,
        #open_period=20,
        is_anonymous=True,
        explanation="Well, honestly that depends on what you eat",
        explanation_parse_mode=telegram.ParseMode.MARKDOWN_V2,
    )

    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    context.bot_data.update({message.poll.id: message.chat.id})


def add_poll_question(update, context, quiz_question):
    message = context.bot.send_poll(
        chat_id=get_chat_id(update, context),
        question=quiz_question.question,
        options=quiz_question.answers,
        type=Poll.REGULAR,
        allows_multiple_answers=True,
        is_anonymous=False,
    )


def get_text_from_message(update):
    return update.message.text


def get_answer(update):
    answers = update.poll.options

    ret = ""

    for answer in answers:
        if answer.voter_count == 1:
            ret = answer.text

    return ret


# determine if user answer is correct
def is_answer_correct(update):
    answers = update.poll.options

    ret = False
    counter = 0

    for answer in answers:
        if answer.voter_count == 1 and update.poll.correct_option_id == counter:
            ret = True
            break
        counter = counter + 1

    return ret


def get_text_from_callback(update):
    return update.callback_query.data


def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" ', update)
    logging.exception(context.error)


def main():
    updater = Updater(DefaultConfig.TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher

    # command handlers
    dp.add_handler(CommandHandler("help", help_command_handler))
    dp.add_handler(CommandHandler("start", start_command_handler))

    # message handler
    dp.add_handler(MessageHandler(Filters.text, main_handler))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))

    # suggested_actions_handler
    dp.add_handler(
        CallbackQueryHandler(main_handler, pass_chat_data=True, pass_user_data=True)
    )

    # quiz answer handler
    dp.add_handler(PollHandler(poll_handler, pass_chat_data=True, pass_user_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    if DefaultConfig.MODE == "webhook":

        updater.start_webhook(
            listen="0.0.0.0",
            port=int(DefaultConfig.PORT),
            url_path=DefaultConfig.TELEGRAM_TOKEN,
        )
        updater.bot.setWebhook(DefaultConfig.WEBHOOK_URL + DefaultConfig.TELEGRAM_TOKEN)

        logging.info(f"Start webhook mode on port {DefaultConfig.PORT}")
    else:
        updater.start_polling()
        logging.info(f"Start polling mode")

    updater.idle()


class DefaultConfig:
    PORT = int(os.environ.get("PORT", 3978))
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "2111440831:AAFxnThXiOA2UHx86kB61fqXBGtZeX49gvs")
    MODE = os.environ.get("MODE", "polling")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def init_logging():
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=DefaultConfig.LOG_LEVEL,
        )


if __name__ == "__main__":
    ascii_banner = pyfiglet.figlet_format("SampleTelegramQuiz")
    print(ascii_banner)

    # Enable logging
    DefaultConfig.init_logging()

    main()
