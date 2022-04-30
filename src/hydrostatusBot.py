#!/usr/bin/python3

import logging
import sqlite3

from telegram import Update, ParseMode
from telegram.ext import Updater,CommandHandler,CallbackContext
from dotenv import dotenv_values

import hydrostatusReports as hsr
import hydrostatusTxt as hst

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

config = dotenv_values(".env")

def main():
    """
    Run Telegram Bot
    """

    #see: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#how-do-i-limit-who-can-use-my-bot

    updater = Updater(token=config["TOKEN"], use_context=True)

    dispatcher = updater.dispatcher
    jq = updater.job_queue

    loadAlert(jq)

    # Dispatchers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('report', report))
    dispatcher.add_handler(CommandHandler('reportnow', reportnow))
    dispatcher.add_handler(CommandHandler('reporthour', reporthour))
    dispatcher.add_handler(CommandHandler('reportday', reportday))
    dispatcher.add_handler(CommandHandler('reportweek', reportweek))
    dispatcher.add_handler(CommandHandler('reportmonth', reportmonth))
    dispatcher.add_handler(CommandHandler('graphday', graphday))
    dispatcher.add_handler(CommandHandler('graphweek', graphweek))
    dispatcher.add_handler(CommandHandler('graphmonth', graphmonth))
    dispatcher.add_handler(CommandHandler('alert', alert))
    dispatcher.add_handler(CommandHandler('alertdelay', alertdelay))
    dispatcher.add_handler(CommandHandler('auth', auth))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('about', about))

    updater.start_polling()
    
    updater.idle()


def start(update: Update, context: CallbackContext):
    """
    Greet new user and check for authentication
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=hst.start_txt, parse_mode=ParseMode.MARKDOWN_V2)


def graphday(update: Update, context: CallbackContext):
    hsr.generateReports()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('graphs/report-day.png', 'rb'), caption='💧📊 Usage Chart: Last 24 Hours')


def graphweek(update: Update, context: CallbackContext):
    hsr.generateReports()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('graphs/report-week.png', 'rb'), caption='💧📊 Usage Chart: Last 7 Days')


def graphmonth(update: Update, context: CallbackContext):
    hsr.generateReports()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('graphs/report-month.png', 'rb'), caption='💧📊 Usage Chart: Last 4 Weeks')


def report(update: Update, context: CallbackContext):
    usage_report = hsr.usageMetrics()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usage_report}')


def reportnow(update: Update, context: CallbackContext):
    usage_report = hsr.generateUsage()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Water Usage Currently: {usage_report[0]:.2f} L/min ")


def reporthour(update: Update, context: CallbackContext):
    usage_report = hsr.generateUsage()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Water Usage Last Hour: {usage_report[1]:.2f} Litres")


def reportday(update: Update, context: CallbackContext):
    usage_report = hsr.generateUsage()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Water Usage Last 24 Hours: {usage_report[2]:.2f} Litres")


def reportweek(update: Update, context: CallbackContext):
    usage_report = hsr.generateUsage()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Water Usage Last 7 Days: {usage_report[3]:.2f} Litres")


def reportmonth(update: Update, context: CallbackContext):
    usage_report = hsr.generateUsage()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Water Usage Last 4 Weeks: {usage_report[4]:.2f} Litres")


def auth(update: Update, context: CallbackContext):
    try:
        auth_response = auth_challenge(context.args[0], chat_id=update.effective_chat.id)
        context.bot.send_message(chat_id=update.message.from_user.id, text=f"{auth_response}")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Try: /auth <your key>")


def alert(update: Update, context: CallbackContext):
    """
    Sets the threshold for the alert in litres per hour (120 -  3000)
    """
    try:
        alert_threshold = alert_update(context.args[0], context.args[1], chat_id=update.effective_chat.id)
        context.bot.send_message(chat_id=update.message.from_user.id, text=f"{alert_threshold}")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Try: /alert <value> <hardware-key>")


def alertdelay(update: Update, context: CallbackContext):
    """
    Sets the duration the alert should be delayed in minutes (1 - 60)
    """
    try:
        alert_delay = alert_delay_update(context.args[0], context.args[1], chat_id=update.effective_chat.id)
        context.bot.send_message(chat_id=update.message.from_user.id, text=f"{alert_delay}")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Try: /alert <value> <hardware-key>")


def alertmonitor(context: CallbackContext):
    """
    Send an alarm to the user
    """
    job = context.job
    alert_reading = job.context[2]

    if alert_reading.check_reading(hsr.checkAlert(), job.context[1]) == True:
        context.bot.send_message(chat_id=job.context[0], text=f"⚠️ Warning! You are using {hsr.checkAlert():.2f} litres per hour. Your alert level is set to: {job.context[1]:.2f} litres per hour.")
    else:
        pass

def about(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=hst.about_txt, parse_mode=ParseMode.MARKDOWN_V2)


def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=hst.help_txt, parse_mode=ParseMode.MARKDOWN_V2)


def alert_update(value, hardware_key, chat_id):
    """
    Check whether the value being given is valid
    Sets the new alert threshold value in `hydrostatus.db`
    """
    if int(value) <= 3000 and int(value) >= 120:
        with sqlite3.connect('hydrostatus.db') as conn:
            cursor = conn.cursor()
            keyquery = cursor.execute("SELECT * FROM hardwarekeys WHERE user_id = ? AND key = ?", (chat_id, hardware_key)).fetchone()

            if keyquery is None:
                alert_value_response = '⛔ User not authenticated'
                
            else:
                cursor.execute("UPDATE hardwarekeys SET alertvalue = ? WHERE user_id = ? AND key = ?", (int(value), chat_id, hardware_key))
                conn.commit()
                alert_value_response = f'✅ Updated Alert threshold to {value} litres per hour.'
    
    else:
        alert_value_response = '⛔ Threshold should be between 120 and 3000 litres per hour. Please try a different threshold value.'

    return alert_value_response


def alert_delay_update(value, hardware_key, chat_id):
    """
    Check whether the delay being given is valid
    Sets the new alert delay value in `hydrostatus.db`
    """

    if int(value) <= 60 and int(value) >= 1:
        with sqlite3.connect('hydrostatus.db') as conn:
            cursor = conn.cursor()
            keyquery = cursor.execute("SELECT * FROM hardwarekeys WHERE user_id = ? AND key = ?", (chat_id, hardware_key)).fetchone()
            
            if keyquery is None:
                alert_delay_response = '⛔ User not authenticated'
                
            else:
                cursor.execute("UPDATE hardwarekeys SET alertdelay = ? WHERE user_id = ? AND key = ?", (int(value), chat_id, hardware_key))
                conn.commit()
                alert_delay_response = f'✅ Updated Delay to {value} minutes.'
                
    else:
        alert_delay_response = '⛔ Delays should be longer than 1 minute and shorter than 1 hour. Please try a different delay value.'

    return alert_delay_response


def auth_challenge(user_auth, chat_id):
    """
    Authenticate the user by checking that their hardware key and id are valid.
    """
    with sqlite3.connect('hydrostatus.db') as conn:
        cursor = conn.cursor()

        # Check if the user's key matches any keys on record
        keyquery = cursor.execute("SELECT * FROM hardwarekeys WHERE key = ?", (user_auth,)).fetchone()

        if user_auth == keyquery[0]:
            
            user_status = cursor.execute("SELECT * FROM whitelist WHERE key = ?", (user_auth,)).fetchone()
            if user_status is None:
                cursor.execute("INSERT INTO whitelist(key, user_id) VALUES(?, ?)", (user_auth, chat_id))
                cursor.execute("UPDATE hardwarekeys SET user_id = ? WHERE key = ?", (chat_id, user_auth))
                conn.commit()
                auth_response = '✅ ACTIVATED ➡️ ADDED'

            # If the id does not match, update the existing id
            elif str(user_status[1]) != str(chat_id):
                cursor.execute("UPDATE whitelist SET user_id = ? WHERE key = ?", (chat_id, user_auth))
                cursor.execute("UPDATE hardwarekeys SET user_id = ? WHERE key = ?", (chat_id, user_auth))
                conn.commit()
                auth_response = '✅ ACTIVATED'

            # Let the user know their device is already active
            if str(user_status[0]) == str(user_auth) and str(user_status[1]) == str(chat_id):
                auth_response = '✅ ALREADY ACTIVE'

        elif keyquery is None:
            auth_response = '⛔ DECLINED'
            
    return auth_response


def loadAlert(jq):
    """
    Loads alerts from the database
    """
    try:
        current_jobs = [job.name for job in jq.jobs()]
        for job in current_jobs:
            job.schedule_removal()

    except AttributeError as e:
        pass

    with sqlite3.connect('hydrostatus.db') as conn:
        cursor = conn.cursor()

        # check `hardwarekeys` table for all keys associated with ids
        keyquery = cursor.execute("SELECT * FROM hardwarekeys").fetchall()

        for row in keyquery:
            alert_reading = str(row[3])
            alert_reading = Readings()
            jq.run_repeating(alertmonitor, interval=int(row[2])*60, first=10, context=[int(row[3]), int(row[1]), alert_reading], name=str(row[3]))

class Readings():
    """
    A little class to handle readings
    """
    def __init__(self):
        """
        creates a unique reading for every user
        """
        self.system_reading = 0
        self.prev_reading = 0


    def check_reading(self, current_value, alert_value):
        """
        calculate 
        """
        self.system_reading += current_value

        if self.prev_reading >= (alert_value * 2):
            system_alarm = True
        else:
            self.prev_reading = self.system_reading
            self.system_reading = 0
            system_alarm = False

        return system_alarm


if __name__ == '__main__':
    main()
