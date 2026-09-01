# app/main.py
# FastAPI 애플리케이션의 진입점
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routers import movies, reviews
from app.common.database import engine, Base
from app.schema import db_schemas

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 테이블이 없으면 자동으로 생성 (있으면 아무 일도 안 함, 안전하게 재실행 가능)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield 


app = FastAPI(
    title="영화 리뷰 서비스 API",
    description="영화 등록/조회 및 리뷰 감성분석 서비스를 위한 백엔드 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(movies.router)
app.include_router(reviews.router)
