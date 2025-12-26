"""Admin handlers package.

This package contains all admin-related handlers split by functionality.
"""
from aiogram import Router

from apps.handlers.admin.menu import router as menu_router
from apps.handlers.admin.export import router as export_router
from apps.handlers.admin.tickets import router as tickets_router
from apps.handlers.admin.wishes import router as wishes_router
from apps.handlers.admin.post import router as post_router

# Main admin router that includes all sub-routers
router = Router()
router.include_router(menu_router)
router.include_router(export_router)
router.include_router(tickets_router)
router.include_router(wishes_router)
router.include_router(post_router)
