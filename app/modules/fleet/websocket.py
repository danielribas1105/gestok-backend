from fastapi import WebSocket, WebSocketDisconnect
from app.modules.auth.service import decode_token
from app.modules.fleet.manager import manager


async def fleet_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        decode_token(token)
    except:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
