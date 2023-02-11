import random
import math
import os
import aiohttp

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


app = FastAPI(
    title='I Wanna Walk',
    description='Random point generator',
    version='1.0'
)

TOKEN = os.environ.get("WANNAWALK_TOKEN")


class Update(BaseModel):
    update_id: int
    message: Optional[dict] = None
    edited_message: Optional[dict] = None
    channel_post: Optional[dict] = None
    edited_channel_post: Optional[dict] = None
    inline_query: Optional[dict] = None
    chosen_inline_result: Optional[dict] = None
    callback_query: Optional[dict] = None
    shipping_query: Optional[dict] = None
    pre_checkout_query: Optional[dict] = None
    poll: Optional[dict] = None
    poll_answer: Optional[dict] = None
    my_chat_member: Optional[dict] = None
    chat_member: Optional[dict] = None
    chat_join_request: Optional[dict] = None


class Location:
    def __init__(self, location=None, text=None):
        if location:
            self.latitude = location.get('latitude')
            self.longitude = location.get('longitude')
        elif text:
            parts = text.upper().replace(' N', 'N').replace(' E', 'E').replace(' W', 'W').replace(' S', 'S')\
                .replace(',', ' ').replace('  ', ' ').split(' ')
            if len(parts) != 2:
                raise Exception
            values = []
            for part in parts:
                string = part.replace(',', '').strip()
                if string.endswith('N'):
                    string = string[:-1]
                elif string.endswith('S'):
                    string = '-' + string[:-1]
                elif string.endswith('E'):
                    string = string[:-1]
                elif string.endswith('W'):
                    string = '-' + string[:-1]
                string = string.replace('--', '-').strip()
                values.append(float(string))
            self.latitude = values[0]
            self.longitude = values[1]


class Distance:
    def __init__(self, text=None):
        if text:
            self.klix = float(text.lower().replace('k', '').replace('к', '').replace('m', '').replace('м', '').strip())


class Response:
    def __init__(self, text, generate=False):
        self.text = text
        self.generate = generate


class UserMemory:
    def __init__(self):
        self.last_location = None
        self.last_distance = None
        self.last_input = None
        self.last_output = None

    def parse_message(self, message):
        text = message.get('text')
        location = message.get('location')
        dice = message.get('dice')
        if location:
            self.last_input = Location(location=location)
        elif dice:
            self.last_input = 'REROLL'
        elif text:
            if text == 'NEW LOCATION':
                self.last_location = None
                self.last_distance = None
                self.last_input = 'CLEAR'
            elif text == 'ADJUST DISTANCE':
                self.last_distance = None
                self.last_input = 'ADJUST'
            else:
                reroll_triggers = [
                    '🎲',
                    'reroll',
                    'again',
                    'retry',
                    'еще',
                    'ещё',
                    'повтор'
                ]
                if any([s in text for s in reroll_triggers]):
                    self.last_input = 'REROLL'
                else:
                    try:
                        location = Location(text=text)
                    except:
                        location = None
                    try:
                        distance = Distance(text=text)
                    except:
                        distance = None
                    if location:
                        self.last_input = location
                    elif distance:
                        self.last_input = distance
                    else:
                        self.last_input = 'UNINTELLIGIBLE'
        else:
            self.last_input = 'UNINTELLIGIBLE'

    def generate_response(self):
        if isinstance(self.last_input, Location):
            if -90 < self.last_input.latitude < 90 and -180 < self.last_input.longitude < 180:
                self.last_location = self.last_input
                self.last_distance = None
                self.last_output = Response(text='Starting location acquired.\nHow far do you want to venture? '
                                                 '(Kilometers only, please)')
            else:
                self.last_location = None
                self.last_distance = None
                self.last_output = Response(text='Some weird ass location you got there. No can do, please remain '
                                                 'within earthly boundaries (-90...90 latitude, -180...180 longitude).')
        elif isinstance(self.last_input, Distance):
            if self.last_location is None:
                self.last_output = Response(text='Please, send me a starting location first.')
            elif 0 < self.last_input.klix < 4000:
                self.last_distance = self.last_input
                self.last_output = Response(text='Distance acquired.', generate=True)
            else:
                self.last_distance = None
                self.last_output = Response(text='I can\'t take you that far. 0 to 4000 km only, please.')
        elif self.last_input == 'REROLL':
            if self.last_location and self.last_distance:
                self.last_output = Response(text='Trying again...', generate=True)
            elif self.last_location:
                self.last_output = Response(text='I can\'t reroll, give me a distance first.')
            else:
                self.last_output = Response(text='I can\'t reroll, give me a location first.')
        elif self.last_input == 'CLEAR':
            self.last_output = Response(text='Send me your starting location.')
        elif self.last_input == 'ADJUST':
            if self.last_location:
                self.last_output = Response(text='Send me new a distance value.')
            else:
                self.last_output = Response(text='Gonna need a location first.')
        elif self.last_input == 'UNINTELLIGIBLE':
            if self.last_location and self.last_distance:
                self.last_output = Response(text='Huh? You want me to reroll for same location and distance? '
                                                 'Adjust them, if not.')
            elif self.last_location:
                self.last_output = Response(text='I\'m sorry, I only take distance as a number of kilometers '
                                                 '(like, 3, 5, 10 or 186.4).')
            else:
                self.last_output = Response(text='What? Give me a location, either as an attachable Telegram blip, '
                                                 'or as a pair of coordinates.')
        else:
            self.last_output = Response('Huh? Who goes there?')


class Memory:
    def __init__(self):
        self.values = {}
    def find_user(self, uid):
        if self.values.get(uid) is None:
            self.values[uid] = UserMemory()
        return self.values.get(uid)


memory = Memory()


async def send_message(chid, text):
    async with aiohttp.ClientSession() as session:
        for line in text.split('\n'):
            async with session.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage', json={'chat_id': chid,
                                                                                              'text': line}) as response:
                pass


async def send_location(chid, start, distance):
    distance_swing = max(1, 0.1 * distance.klix)
    distance_frame = (max(0, distance.klix-distance_swing), distance.klix)
    distance_value = random.uniform(*distance_frame)
    direction = math.radians(random.uniform(0, 360))
    current_long = start.longitude
    current_lat = start.latitude
    while abs(distance_value) > 0.01:
        step = min(distance_value, 10)
        step_lat = step * math.cos(direction)
        step_long = step * math.sin(direction)
        step_lat = step_lat / 111.1
        step_long = step_long / (6371 * math.cos(math.radians(current_lat)) * math.pi / 180)
        current_lat = current_lat - step_lat
        current_long = current_long - step_long
        distance_value -= step

    async with aiohttp.ClientSession() as session:
        async with session.post(f'https://api.telegram.org/bot{TOKEN}/sendLocation',
                                json={'chat_id': chid, 'latitude': current_lat, 'longitude': current_long}) as response:
            print(await response.text())
        async with session.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                                json={'chat_id': chid,
                                      'text': f'Your location is:\n\n`{current_lat}, {current_long}`'
                                              f'\n\nYou can now enter another starting point, '
                                              f'adjust distance or reroll with previous settings\.',
                                      'parse_mode': 'MarkdownV2',
                                      'reply_markup': {
                                          'keyboard': [[{'text': 'NEW LOCATION'},
                                                        {'text': '🎲'},
                                                        {'text': 'ADJUST DISTANCE'}]],
                                          'one_time_keyboard': True
                                      }}) as response:
            print(await response.text())


@app.post('/',
          description='Update receiver')
async def respond(update: Update):
    if not update.message:
        return 422
    print(update.message)
    uid = update.message.get('from', {}).get('id')
    if not uid:
        return 401
    chid = update.message.get('chat', {}).get('id')
    if not chid:
        return 400
    status = memory.find_user(uid)
    status.parse_message(update.message)
    status.generate_response()
    await send_message(chid, status.last_output.text)
    if status.last_output.generate:
        await send_location(chid, status.last_location, status.last_distance)
    return 200
