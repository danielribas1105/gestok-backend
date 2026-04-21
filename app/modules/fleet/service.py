from datetime import datetime, timezone
from app.modules.fleet.schema import PositionCreate, PositionBroadcast
from app.modules.fleet.manager import manager


async def handle_position_update(data: PositionCreate):
    """
    Processa atualização de posição:
    - normaliza timestamp
    - salva (futuro)
    - envia via websocket
    """

    timestamp = data.timestamp or datetime.now(timezone.utc)

    payload = PositionBroadcast(
        vehicle_id=data.vehicle_id,
        lat=data.lat,
        lng=data.lng,
        speed=data.speed,
        heading=data.heading,
        timestamp=timestamp,
    )

    # 🔥 broadcast em tempo real
    await manager.broadcast(payload.model_dump())

    return payload
