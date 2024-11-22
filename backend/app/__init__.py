from fastapi import FastAPI
from app.routes.strategy import strategy_router

def create_app():
    app = FastAPI()
    # ... 现有的代码 ...
    app.include_router(strategy_router, prefix="/strategy")
    return app
