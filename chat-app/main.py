from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import asyncio

app = FastAPI()

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redisga ulanish
redis_client = redis.Redis(
    host="suited-hawk-19847.upstash.io",
    port=6379,
    password="AU2HAAIjcDFhNzBmNGRkNTM4MDI0OTEyOWM3NzI3OWZkMGY3YzE0MXAxMA",
    ssl=True
)

connected_clients = set()
redis_task_started = False

async def broadcast_redis_messages():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("chat")
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                text = message["data"].decode()
                for client in list(connected_clients):
                    try:
                        await client.send_text(text)
                    except:
                        connected_clients.remove(client)
        except Exception as e:
            print("Redis listener error:", e)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global redis_task_started
    await websocket.accept()
    connected_clients.add(websocket)

    if not redis_task_started:
        asyncio.create_task(broadcast_redis_messages())
        redis_task_started = True

    try:
        while True:
            data = await websocket.receive_text()
            await redis_client.publish("chat", data)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        connected_clients.remove(websocket)
        print("WebSocket error:", e)
