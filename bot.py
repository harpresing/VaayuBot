from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
import openaq

updater = Updater(token='TOKEN')
dispatcher = updater.dispatcher
aq_api = openaq.OpenAQ()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s  - %(message)s',
                    level=logging.INFO)


def start(bot, update):
    logging.info(msg='Sending start message to chat_ id ' + str(update.message.chat_id))
    bot.send_message(chat_id=update.message.chat_id,
                     text='I am VaayuBot, I shall reveal to you the air quality in your area, '
                          'which is limited to Dublin city for now.')


def get_air_quality(city):
    res = aq_api.latest(city=city, df=True)
    msg = "The air quality of " + city + " is as follows: \n"
    return msg + '\n'.join(
        [r['parameter'] + ' ' + str(r['value']) + ' ' + r['unit'].decode('utf8') for i, r in res.iterrows()])


def get_location(bot, update):
    location_keyboard = KeyboardButton(text='Location', request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_keyboard]])
    bot.send_message(chat_id=update.message.chat_id, text="Would you mind sending your location?",
                     reply_markup=reply_markup)


def get_closest_location(latitude, longitude):
    # TODO
    pass


def air_quality(bot, update):
    logging.info('Latitude = ' + str(update.message.location.latitude) +
                 ' Longitude = ' + str(update.message.location.longitude))
    get_closest_location(update.message.location.latitude, update.message.location.latitude)
    logging.info(msg='Sending air_quality message to chat_ id ' + str(update.message.chat_id))
    update.message.reply_text(get_air_quality('Dublin City'))


start_handler = CommandHandler('start', start)
location_handler = CommandHandler('weather', get_location)
location_message_handler = MessageHandler(Filters.location, air_quality)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(location_handler)
dispatcher.add_handler(location_message_handler)

updater.start_polling()
