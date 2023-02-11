from fastapi import FastAPI

app = FastAPI(
    title='Wanna Walk',
    description='Random point generator',
    version='1.0'
)


@app.post('/',
          description='Update receiver')
async def respond(update):
    print('Got some')
