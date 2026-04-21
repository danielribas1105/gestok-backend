from fastapi import APIRouter
import app.modules.auth.route as auth
import app.modules.drivers.route as car
import app.modules.clients.route as client
import app.modules.drivers.route as driver
import app.modules.fleet.route as fleet
import app.modules.inventory.route as inventory
import app.modules.orders.route as order
import app.modules.products.route as products
import app.modules.user.route as user


router = APIRouter(prefix="/api/v1")

# Register all routers
router.include_router(auth.router)
router.include_router(car.router)
router.include_router(client.router)
router.include_router(driver.router)
router.include_router(fleet.router)
router.include_router(inventory.router)
router.include_router(order.router)
router.include_router(products.router)
router.include_router(user.router)
