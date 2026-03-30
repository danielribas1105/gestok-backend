from fastapi import APIRouter
import app.modules.auth.route as auth
import app.modules.user.route as user


router = APIRouter(prefix="/api/v1")

# Register all routers
router.include_router(auth.router)
router.include_router(user.router)
