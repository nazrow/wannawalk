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

@app.post('/',
          description='Update receiver')
async def respond(update: Update):
    if not update.message:
        return 422
    uid = update.message.get('from', {}).get('id')
    if not uid:
        return 400
    chid = update.message.get('chat', {}).get('id')
    if not chid:
        return 400
    print(f'A message from {uid} in {chid}!')
    return 200
