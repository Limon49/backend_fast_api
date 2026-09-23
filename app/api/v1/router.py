"""The v1 router: one include per resource, so ``app/main.py`` stays readable."""

from fastapi import APIRouter

from app.api.v1 import examples, health, orders, products, reports, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(reports.router)
api_router.include_router(examples.router)
