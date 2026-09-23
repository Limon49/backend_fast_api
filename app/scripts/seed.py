"""
Insert demo products, so there is something to buy.

    uv run python -m app.scripts.seed

Running it twice is harmless: products that already exist (same name) are
skipped. Nothing here touches users or orders.
"""

from decimal import Decimal

from sqlmodel import Session, select

from app.core.database import engine
from app.models.product import Product

DEMO_PRODUCTS: list[dict] = [
    {
        "name": "FastAPI 101",
        "description": "Build your first API: routes, models, and automatic docs.",
        "price": Decimal("19.99"),
        "stock": 25,
    },
    {
        "name": "SQLModel Deep Dive",
        "description": "Tables, relationships and queries that never surprise you.",
        "price": Decimal("29.50"),
        "stock": 15,
    },
    {
        "name": "Docker for Beginners",
        "description": "Package the app once, run it anywhere.",
        "price": Decimal("24.00"),
        "stock": 10,
    },
    {
        "name": "Git & GitHub Workflow",
        "description": "Branches, pull requests and reviews without the drama.",
        "price": Decimal("14.75"),
        "stock": 0,  # sold out on purpose: handy for testing the stock rule
    },
]


def seed_products(session: Session) -> tuple[list[Product], list[Product]]:
    """Insert the demo products that are missing.

    Returns ``(created, skipped)``.
    """
    created: list[Product] = []
    skipped: list[Product] = []

    for data in DEMO_PRODUCTS:
        existing = session.exec(select(Product).where(Product.name == data["name"])).first()
        if existing is not None:
            skipped.append(existing)
            continue
        product = Product(**data)
        session.add(product)
        created.append(product)

    if created:
        session.commit()
        for product in created:
            session.refresh(product)

    return created, skipped


def print_products(session: Session) -> None:
    """Print the current shelf as a small text table."""
    products = session.exec(select(Product).order_by(Product.id)).all()
    print()
    print(f"{'id':>3}  {'name':<24} {'price':>8}  {'stock':>5}  active")
    print("-" * 55)
    for product in products:
        print(
            f"{product.id:>3}  {product.name[:24]:<24} {float(product.price):>8.2f}  "
            f"{product.stock:>5}  {'yes' if product.is_active else 'no'}"
        )
    print()


def main() -> None:  # pragma: no cover - manual helper
    with Session(engine) as session:
        created, skipped = seed_products(session)
        print(f"Created {len(created)} product(s), skipped {len(skipped)} that already existed.")
        print_products(session)


if __name__ == "__main__":  # pragma: no cover
    main()
