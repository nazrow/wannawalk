from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title='I Wanna Walk',
    description='Random point generator',
    version='1.0'
)

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

class UserMemory:
    def __init__(self):
        self.in_middle = False
        self.last_location = None
        self.last_distance = None
    def parse_message(self, message):
        pass
    async def generate_response(self):
        pass

class Memory:
    def __init__(self):
        self.values = {}
    def find_user(self, uid):
        if self.values.get(uid) is None:
            self.values[uid] = UserMemory()
        return self.values.get(uid)

memory = Memory()

@app.post('/',
          description='Update receiver')
async def respond(update: Update):
    if not update.message:
        return 422
    print(update.message)
    uid = update.message.get('from', {}).get('id')
    if not uid:
        return 400
    status = memory.find_user(uid)
    print(f'Current status of user {uid}: {vars(status)}')
    status.parse_message(update.message)
    return await status.generate_response()
