from fastapi import APIRouter
from app.modules.fleet.schema import PositionCreate
from app.modules.fleet.service import handle_position_update

router = APIRouter(prefix="/fleet", tags=["Fleet"])


@router.post("/position")
async def update_position(data: PositionCreate):
    result = await handle_position_update(data)
    return {"ok": True, "data": result}
