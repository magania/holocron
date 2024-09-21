import asyncio
from fastapi import FastAPI
from app.routers import (
    user,
    permission,
    role,
    person,
    profile,
    product,
    risk,
    blacklist,
    transaction,
)
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Routers with prefixes
app.include_router(user.router)
app.include_router(permission.router)
app.include_router(role.router)
app.include_router(person.router)
# app.include_router(profile.router, prefix="/profile", tags=["profile"])
# app.include_router(product.router, prefix="/product", tags=["product"])
# app.include_router(risk.router, prefix="/risk", tags=["risk"])
# app.include_router(blacklist.router, prefix="/blacklist", tags=["blacklist"])
# app.include_router(transaction.router, prefix="/transaction", tags=["transaction"])
