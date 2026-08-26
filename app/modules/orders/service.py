from datetime import datetime, timezone
import hashlib
from typing import Optional
import uuid
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import func, tuple_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from app.modules.clients.model import Client, Store
from app.modules.inventory.model import Inventory
from app.modules.orders.model import Order, OrderItem, OrderStatus
from app.modules.orders.schema import (
    OrderCreatePayload,
    OrderItemStockStatus,
    OrderStockStatus,
    OrderUpdate,
    ProductQuantityCheck,
)
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
            weight_kg_per_unit=items[code][1],
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


async def _get_or_create_supervisors_and_managers(
    supervisor_codes: set[str], manager_codes: set[str]
) -> dict[str, Salesperson]:
    """
    Busca supervisores/gerentes existentes e cria os que não estiverem
    cadastrados — mesmo comportamento já aplicado a vendedores. Nome
    provisório baseado no código; cadastro completo deve ser ajustado
    depois via tela de gestão de pessoas.
    """
    supervisor_codes = {c for c in supervisor_codes if c}
    manager_codes = {c for c in manager_codes if c}
    all_codes = supervisor_codes | manager_codes
    if not all_codes:
        return {}

    existing = (
        (
            await db.session.execute(
                select(Salesperson).where(Salesperson.code.in_(all_codes))
            )
        )
        .scalars()
        .all()
    )
    mapping = {p.code: p for p in existing}

    missing_supervisors = supervisor_codes - mapping.keys()
    missing_managers = manager_codes - mapping.keys()
    # código que aparece como supervisor E gerente ao mesmo tempo, sem cadastro
    # prévio: registra como supervisor por padrão (ajuste manual depois, se for
    # o caso — não dá pra saber o papel "correto" só pelo código)
    missing_managers -= missing_supervisors

    new_people = [
        Salesperson(
            code=code, name=f"Supervisor {code}", profile=SalespersonProfile.SUPERVISOR
        )
        for code in missing_supervisors
    ] + [
        Salesperson(
            code=code, name=f"Gerente {code}", profile=SalespersonProfile.MANAGER
        )
        for code in missing_managers
    ]
    if new_people:
        db.session.add_all(new_people)
        for p in new_people:
            mapping[p.code] = p
    return mapping


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


async def _reserve_inventory_for_items(items: list[OrderItem]) -> None:
    """
    Reserva o estoque dos itens de um pedido recém-criado (reserved_quantity += qty).
    Não bloqueia a criação do pedido mesmo que isso deixe available_quantity
    negativo — isso é justamente o sinal de estoque insuficiente, já usado
    pelas telas de checagem (is_sufficient/shortage). O bloqueio de fato só
    acontece na entrega, que converte a reserva em baixa real.
    """
    if not items:
        return

    qty_by_product: dict[uuid.UUID, float] = {}
    for item in items:
        qty_by_product[item.product_id] = (
            qty_by_product.get(item.product_id, 0) + item.quantity
        )

    result = await db.session.execute(
        select(Inventory)
        .where(Inventory.product_id.in_(qty_by_product.keys()))
        .with_for_update()
    )
    inventory_map = {inv.product_id: inv for inv in result.scalars().all()}

    # produto sem registro de inventário ainda (nunca teve entrada de estoque)
    missing_ids = qty_by_product.keys() - inventory_map.keys()
    for product_id in missing_ids:
        inv = Inventory(
            product_id=product_id,
            current_quantity=0.0,
            reserved_quantity=0.0,
            available_quantity=0.0,
        )
        db.session.add(inv)
        inventory_map[product_id] = inv

    if missing_ids:
        await db.session.flush()  # garante que os novos registros existam antes de atualizar

    for product_id, qty in qty_by_product.items():
        inv = inventory_map[product_id]
        inv.reserved_quantity += qty
        inv.available_quantity = inv.current_quantity - inv.reserved_quantity
        inv.last_updated = datetime.now(timezone.utc)
        db.session.add(inv)


async def _release_inventory_for_items(items: list[OrderItem]) -> None:
    """
    Libera a reserva de estoque dos itens de um pedido que foi cancelado
    ou excluído antes de virar entrega (reserved_quantity -= qty).
    """
    if not items:
        return

    qty_by_product: dict[uuid.UUID, float] = {}
    for item in items:
        qty_by_product[item.product_id] = (
            qty_by_product.get(item.product_id, 0) + item.quantity
        )

    result = await db.session.execute(
        select(Inventory)
        .where(Inventory.product_id.in_(qty_by_product.keys()))
        .with_for_update()
    )
    inventory_map = {inv.product_id: inv for inv in result.scalars().all()}

    for product_id, qty in qty_by_product.items():
        inv = inventory_map.get(product_id)
        if not inv:
            continue
        inv.reserved_quantity = max(0.0, inv.reserved_quantity - qty)
        inv.available_quantity = inv.current_quantity - inv.reserved_quantity
        inv.last_updated = datetime.now(timezone.utc)
        db.session.add(inv)


async def _compute_item_stock_status_map(
    orders: list[Order],
) -> dict[uuid.UUID, OrderItemStockStatus]:
    """
    Retorna o status por ITEM (product_id dentro de cada pedido), pois a
    disponibilidade é calculada por produto — o pedido como um todo não é
    a unidade certa, já que dois itens do mesmo pedido podem ter produtos
    diferentes com saldos diferentes.

    Processa os pedidos em ordem cronológica (issued_at, fallback pra
    created_at) e, dentro de cada pedido, os itens na ordem em que
    aparecem. Item que cabe no saldo restante do produto desconta do
    saldo; item que não cabe fica 'insufficient' e NÃO desconta — o
    saldo continua disponível pros próximos pedidos da fila.
    """
    if not orders:
        return {}

    # pedidos em hold ficam de fora da fila de consumo — não disputam
    # saldo, mas seus itens ainda precisam de uma entrada no mapa
    active_orders = [o for o in orders if not o.stock_hold]
    held_orders = [o for o in orders if o.stock_hold]

    """ or o.created_at or datetime.min """
    ordered = sorted(active_orders, key=lambda o: o.code)
    product_ids = {item.product_id for o in ordered for item in o.items}
    item_status: dict[uuid.UUID, OrderItemStockStatus] = {}

    # itens de pedidos em hold: status fixo ON_HOLD, sem consumir saldo
    for order in held_orders:
        for item in order.items:
            item_status[item.id] = OrderItemStockStatus.ON_HOLD

    if not product_ids:
        return item_status

    result = await db.session.execute(
        select(Inventory.product_id, Inventory.available_quantity).where(
            Inventory.product_id.in_(product_ids)
        )
    )
    remaining = {row.product_id: float(row.available_quantity) for row in result.all()}

    for order in ordered:
        for item in order.items:
            available = remaining.get(item.product_id, 0.0)
            if available >= item.quantity:
                item_status[item.id] = OrderItemStockStatus.IN_STOCK
                remaining[item.product_id] = available - item.quantity
            else:
                item_status[item.id] = OrderItemStockStatus.NO_STOCK

    return item_status


def aggregate_order_stock_status(
    order: Order,
    item_statuses: list[OrderItemStockStatus],
) -> Optional[OrderStockStatus]:
    """Resume os status dos itens de um pedido em um único status pro pedido."""
    if order.stock_hold:
        return OrderStockStatus.ON_HOLD
    if not item_statuses:
        return None
    if all(s == OrderItemStockStatus.IN_STOCK for s in item_statuses):
        return OrderStockStatus.SUFFICIENT
    if all(s == OrderItemStockStatus.NO_STOCK for s in item_statuses):
        return OrderStockStatus.INSUFFICIENT
    return OrderStockStatus.PARTIAL


async def set_order_stock_hold(
    order_id: uuid.UUID, stock_hold: bool, reason: Optional[str]
) -> Order:
    order = await get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Pedido {order.code} está com status '{order.status}' e não "
                "pode ter o hold alterado — só pedidos pendentes podem ser "
                "colocados/retirados de hold"
            ),
        )

    order.stock_hold = stock_hold
    order.stock_hold_reason = reason if stock_hold else None
    order.stock_hold_at = datetime.now(timezone.utc) if stock_hold else None

    db.session.add(order)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def get_pending_orders_item_stock_status() -> dict[uuid.UUID, OrderStockStatus]:
    """
    Status de estoque por item para TODOS os pedidos pendentes — precisa
    rodar sobre o conjunto completo, não só a página exibida, senão a fila
    de consumo fica incorreta.
    """
    result = await db.session.execute(
        select(Order)
        .where(Order.status == OrderStatus.PENDING)
        .options(selectinload(Order.items))
    )
    orders = result.scalars().all()
    return await _compute_item_stock_status_map(orders)


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
    supervisor_codes = {p.supervisor_id for p in payloads}
    manager_codes = {p.manager_id for p in payloads}
    person_map = await _get_or_create_supervisors_and_managers(
        supervisor_codes, manager_codes
    )

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
        # await db.session.commit()
        await db.session.flush()

        all_items = [item for order in orders_to_create for item in order.items]
        await _reserve_inventory_for_items(all_items)

        await db.session.commit()
        for order in orders_to_create:
            await db.session.refresh(order)

    return orders_to_create, errors


async def get_products_quantity_check(
    item_ids: list[uuid.UUID],
) -> list[ProductQuantityCheck]:
    if not item_ids:
        return []

    # soma pedido por produto, restrita aos ITENS selecionados
    # (não mais aos pedidos inteiros — permite desmarcar 1 item sem
    # afetar os demais itens do mesmo pedido)
    ordered_qty = (
        select(
            OrderItem.product_id.label("product_id"),
            func.sum(OrderItem.quantity).label("total_quantity"),
        )
        .where(OrderItem.id.in_(item_ids))
        .group_by(OrderItem.product_id)
        .subquery()
    )

    # 2) junta produto + estoque disponível — única execução real
    stmt = (
        select(
            ordered_qty.c.product_id,
            Product.name,
            Product.name_code,
            ordered_qty.c.total_quantity,
            Inventory.available_quantity,
            Inventory.current_quantity,
            Inventory.reserved_quantity,
        )
        .join(Product, Product.id == ordered_qty.c.product_id)
        .outerjoin(Inventory, Inventory.product_id == ordered_qty.c.product_id)
    )

    result = await db.session.execute(stmt)
    rows = result.all()

    checks: list[ProductQuantityCheck] = []
    for row in rows:
        total = int(row.total_quantity)
        available = float(row.available_quantity or 0.0)
        current = float(row.current_quantity or 0.0)
        reserved = float(row.reserved_quantity or 0.0)

        checks.append(
            ProductQuantityCheck(
                product_id=row.product_id,
                name=row.name,
                name_code=row.name_code,
                total_quantity=total,
                available_quantity=available,
                current_quantity=float(row.current_quantity or 0.0),
                reserved_quantity=float(row.reserved_quantity or 0.0),
                is_sufficient=available >= total,
                shortage=max(0.0, total - available),
            )
        )

    return checks


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
    await db.session.flush()

    await _reserve_inventory_for_items(order.items)

    await db.session.commit()
    await db.session.refresh(order)
    return order


async def get_order_by_id(order_id: uuid.UUID) -> Order:
    result = await db.session.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    return order


async def update(order_id: uuid.UUID, data: OrderUpdate) -> Order:
    order = await get_order_by_id(order_id)

    update_data = data.model_dump(exclude_unset=True)

    if (
        update_data.get("status") == OrderStatus.CANCELED
        and order.status == OrderStatus.PENDING
    ):
        await _release_inventory_for_items(order.items)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    order.updated_at = datetime.now(timezone.utc)
    await db.session.commit()
    await db.session.refresh(order)
    return order


async def delete(order_id: uuid.UUID) -> None:
    order = await get_order_by_id(order_id)
    if order.status == OrderStatus.PENDING:
        await _release_inventory_for_items(order.items)
    await db.session.delete(order)
    await db.session.commit()
