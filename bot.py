import logging
from math import radians, cos, sin, asin, sqrt

import openaq
from telegram import KeyboardButton, ReplyKeyboardMarkup, ChatAction
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext import Updater
from functools import wraps

updater = Updater(token='token')
dispatcher = updater.dispatcher
aq_api = openaq.OpenAQ()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s  - %(message)s',
    level=logging.INFO)
    
    
def send_typing_action(func):
	"""Sends typing action while processing func command."""
	
	@wraps(func)
	def command_func(*args, **kwargs):
		bot, update = args
		bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
		return func(bot, update, **kwargs)
		
	return command_func


def start(bot, update):
    logging.info(
        msg='Sending start message to chat_ id ' + str(update.message.chat_id))
    bot.send_message(chat_id=update.message.chat_id,
                     text='I am VaayuBot, I shall reveal to you the air quality in your area. \nType /weather to get started.')


def get_air_quality(location, city, country):
    res = aq_api.latest(location=location, df=True)
    msg = "The air quality measured from station " + location + " in " + city + ", " + country + " is as follows: \n"
    return msg + '\n'.join(
        [r['parameter'] + ' ' + str(r['value']) + ' ' + r['unit'].decode('utf8')
         for i, r in res.iterrows()])


def get_location(bot, update):
    location_keyboard = KeyboardButton(text='Location', request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_keyboard]])
    bot.send_message(chat_id=update.message.chat_id,
                     text="Would you mind sending your location?",
                     reply_markup=reply_markup)


def calculate_great_circle_distance(lat, long, lat1, long1):
    # Convert to radians
    lat, long, lat1, long1 = map(radians, [lat, long, lat1, long1])
    # haversine formula
    dlon = long1 - long
    dlat = lat1 - lat
    a = sin(dlat / 2) ** 2 + cos(lat) * cos(lat1) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


def get_closest_location(latitude, longitude):
    df = aq_api.locations(df=True, limit=10000)
    df.columns = df.columns.str.replace('coordinates.', '')
    shortest_distance = calculate_great_circle_distance(latitude, longitude,
                                                        df.ix[0]['latitude'],
                                                        df.ix[0]['longitude'])
    location = df.ix[0]['location']
    city = df.ix[0]['city']
    country = df.ix[0]['country']
    for _, r in df.iterrows():
        dist = calculate_great_circle_distance(latitude, longitude,
                                               r['latitude'],
                                               r['longitude'])
        if dist <= shortest_distance:
            shortest_distance = dist
            location = r['location']
            city = r['city']
            country = r['country']
    return location, city, country

@send_typing_action
def air_quality(bot, update):
    logging.info('Latitude = ' + str(update.message.location.latitude) +
                 ' Longitude = ' + str(update.message.location.longitude))
    location, city, country = get_closest_location(update.message.location.latitude,
                                update.message.location.longitude)
    logging.info(msg='Sending air_quality message to chat_ id ' + str(
        update.message.chat_id))
    update.message.reply_text(get_air_quality(location, city, country))


start_handler = CommandHandler('start', start)
location_handler = CommandHandler('weather', get_location)
location_message_handler = MessageHandler(Filters.location, air_quality)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(location_handler)
dispatcher.add_handler(location_message_handler)

updater.start_polling()
