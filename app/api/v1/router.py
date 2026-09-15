"""Aggregates all v1 route modules under a single APIRouter."""
from fastapi import APIRouter

from app.routes import auth_routes, dashboard_routes, file_routes, payment_routes, project_routes, user_routes

api_router = APIRouter()

api_router.include_router(auth_routes.router)
api_router.include_router(user_routes.router)
api_router.include_router(project_routes.router)
api_router.include_router(payment_routes.router)
api_router.include_router(file_routes.router)
api_router.include_router(dashboard_routes.router)
