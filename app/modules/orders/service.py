from datetime import datetime, timezone
import hashlib
import uuid
from fastapi_async_sqlalchemy import db
from sqlalchemy import tuple_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from app.modules.clients.model import Client, Store
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schema import OrderCreatePayload, OrderResponse, OrderUpdate
from app.modules.products.model import Product
from app.modules.salesperson.model import Salesperson, SalespersonProfile


def _build_row_hash(order_code: str, item_number: str | None, product_code: str) -> str:
    raw = f"{order_code}|{item_number or ''}|{product_code}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _get_or_create_clients(codes: set[str]) -> dict[str, Client]:
    codes = {c for c in codes if c}
    if not codes:
        return {}
    existing = (
        (await db.session.execute(select(Client).where(Client.code.in_(codes))))
        .scalars()
        .all()
    )
    mapping = {c.code: c for c in existing}
    missing = codes - mapping.keys()
    new_clients = [Client(code=code, name=f"Cliente {code}") for code in missing]
    if new_clients:
        db.session.add_all(new_clients)
        for c in new_clients:
            mapping[c.code] = (
                c  # id já existe (default_factory=uuid.uuid4 roda na criação)
            )
    return mapping


async def _get_or_create_stores(
    pairs: set[tuple[uuid.UUID, str]],
) -> dict[tuple[uuid.UUID, str], Store]:
    """pairs: {(client_id, store_code), ...}"""
    pairs = {p for p in pairs if p[1]}
    if not pairs:
        return {}
    existing = (
        (
            await db.session.execute(
                select(Store).where(tuple_(Store.client_id, Store.code).in_(pairs))
            )
        )
        .scalars()
        .all()
    )
    mapping = {(s.client_id, s.code): s for s in existing}
    missing = pairs - mapping.keys()
    new_stores = [Store(client_id=client_id, code=code) for client_id, code in missing]
    if new_stores:
        db.session.add_all(new_stores)
        for s in new_stores:
            mapping[(s.client_id, s.code)] = s
    return mapping


async def _get_or_create_products(
    items: dict[str, tuple[str, float]],
) -> dict[str, Product]:
    """items: {product_code: (unit, weight)}"""
    codes = {c for c in items if c}
    if not codes:
        return {}
    existing = (
        (await db.session.execute(select(Product).where(Product.name_code.in_(codes))))
        .scalars()
        .all()
    )
    mapping = {p.name_code: p for p in existing}
    missing = codes - mapping.keys()
    new_products = [
        Product(
            name_code=code,
            name=code.replace("_", " ").strip().title(),
            unit=items[code][0] or "UN",
            unit_weight=items[code][1],
        )
        for code in missing
    ]
    if new_products:
        db.session.add_all(new_products)
        for p in new_products:
            mapping[p.name_code] = p
    return mapping


async def _get_or_create_sallers(codes: set[str]) -> dict[str, Salesperson]:
    codes = {c for c in codes if c}
    if not codes:
        return {}
    existing = (
        (
            await db.session.execute(
                select(Salesperson).where(Salesperson.code.in_(codes))
            )
        )
        .scalars()
        .all()
    )
    mapping = {p.code: p for p in existing}
    missing = codes - mapping.keys()
    new_sallers = [
        Salesperson(code=code, profile=SalespersonProfile.SELLER) for code in missing
    ]
    if new_sallers:
        db.session.add_all(new_sallers)
        for p in new_sallers:
            mapping[p.code] = p
    return mapping


async def _get_supervisors_and_managers(codes: set[str]) -> dict[str, Salesperson]:
    """Apenas busca — supervisor/gerente já devem existir no cadastro."""
    codes = {c for c in codes if c}
    if not codes:
        return {}
    existing = (
        (
            await db.session.execute(
                select(Salesperson).where(Salesperson.code.in_(codes))
            )
        )
        .scalars()
        .all()
    )
    return {p.code: p for p in existing}


async def _get_existing_orders(pairs: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """pairs: {(branch_code, code), ...}"""
    if not pairs:
        return set()
    existing = (
        await db.session.execute(
            select(Order.branch_code, Order.code).where(
                tuple_(Order.branch_code, Order.code).in_(pairs)
            )
        )
    ).all()
    return {(row[0], row[1]) for row in existing}


async def create_orders_batch(
    payloads: list[OrderCreatePayload],
) -> tuple[list[Order], list[dict]]:
    if not payloads:
        return [], []

    errors: list[dict] = []

    # 1) resolve/cria clientes primeiro (lojas dependem do client_id)
    client_codes = {p.client_id for p in payloads}
    client_map = await _get_or_create_clients(client_codes)

    # 2) resolve/cria lojas — chave é (client_id, store_code), não só o código
    store_pairs = {
        (client_map[p.client_id].id, p.store_id)
        for p in payloads
        if p.client_id in client_map
    }
    store_map = await _get_or_create_stores(store_pairs)

    # 3) resolve/cria pessoas (vendedor/supervisor/gerente, mesma tabela)
    # 3a) vendedor: cria se não existir
    saller_codes = {p.saller_id for p in payloads}
    saller_map = await _get_or_create_sallers(saller_codes)

    # 3b) supervisor e gerente: só busca, não cria — devem já existir
    supervisor_manager_codes = {p.supervisor_id for p in payloads} | {
        p.manager_id for p in payloads
    }
    person_map = await _get_supervisors_and_managers(supervisor_manager_codes)

    # 4) resolve/cria produtos
    product_info: dict[str, tuple[str, float]] = {}
    for p in payloads:
        for item in p.items:
            if item.product_id:
                product_info[item.product_id] = (item.unit, item.weight)
    product_map = await _get_or_create_products(product_info)

    orders_to_create: list[Order] = []

    order_pairs = {(p.branch_code, p.code) for p in payloads}
    existing_pairs = await _get_existing_orders(order_pairs)
    seen_in_batch: set[tuple[str, str]] = set()

    for payload in payloads:
        pair = (payload.branch_code, payload.code)

        if pair in existing_pairs:
            errors.append(
                {
                    "code": payload.code,
                    "errors": [
                        f"pedido '{payload.code}' (filial {payload.branch_code}) já existe"
                    ],
                }
            )
            continue

        if pair in seen_in_batch:
            errors.append(
                {
                    "code": payload.code,
                    "errors": [
                        f"pedido '{payload.code}' (filial {payload.branch_code}) duplicado no lote"
                    ],
                }
            )
            continue

        seen_in_batch.add(pair)

        client = client_map.get(payload.client_id)
        store = store_map.get((client.id, payload.store_id)) if client else None
        saller = saller_map.get(payload.saller_id)
        supervisor = person_map.get(payload.supervisor_id)
        manager = person_map.get(payload.manager_id)

        # com get_or_create essas referências deveriam sempre existir;
        # mantenho a checagem só como rede de segurança contra código vazio/None
        missing: list[str] = []
        if not client:
            missing.append(f"cliente '{payload.client_id}' inválido")
        if not store:
            missing.append(f"loja '{payload.store_id}' inválida")
        if not saller:
            missing.append(f"vendedor '{payload.saller_id}' inválido")
        if not supervisor:
            missing.append(f"supervisor '{payload.supervisor_id}' não cadastrado")
        if not manager:
            missing.append(f"gerente '{payload.manager_id}' não cadastrado")

        order_items: list[OrderItem] = []
        for item in payload.items:
            product = product_map.get(item.product_id)
            if not product:
                missing.append(
                    f"produto '{item.product_id}' inválido (item {item.item_number})"
                )
                continue
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    total_price=item.total_price,
                    item_number=item.item_number,
                    row_hash=_build_row_hash(
                        payload.code, item.item_number, item.product_id
                    ),
                )
            )

        if missing:
            errors.append({"code": payload.code, "errors": missing})
            continue

        orders_to_create.append(
            Order(
                branch_code=payload.branch_code,
                code=payload.code,
                operation_type=payload.operation_type,
                release_reason=payload.release_reason,
                released_at=payload.released_at,
                issued_at=payload.issued_at,
                client_id=client.id,
                store_id=store.id,
                saller_id=saller.id,
                supervisor_id=supervisor.id,
                manager_id=manager.id,
                items=order_items,
            )
        )

    if orders_to_create:
        db.session.add_all(orders_to_create)
        await db.session.commit()
        for order in orders_to_create:
            await db.session.refresh(order)

    return orders_to_create, errors


async def list_orders(offset: int = 0, limit: int = 20) -> list[Order]:
    result = await db.session.execute(
        select(Order)
        .options(
            selectinload(Order.client),
            selectinload(Order.store),
            selectinload(Order.saller),
            selectinload(Order.supervisor),
            selectinload(Order.manager),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def create_order(data: OrderCreatePayload) -> Order:
    order = Order(
        **data.model_dump(exclude_none=True),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(order)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def get_order_by_id(order_id: uuid.UUID) -> Order:
    result = await db.session.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    return order


async def update(order_id: uuid.UUID, data: OrderUpdate) -> Order:
    order = await get_order_by_id(order_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    order.updated_at = datetime.now(timezone.utc)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def delete(order_id: uuid.UUID) -> None:
    order = await get_order_by_id(order_id)
    await db.session.delete(order)
    await db.session.commit()
