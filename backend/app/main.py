# app/main.py
# FastAPI 애플리케이션의 진입점
from fastapi import FastAPI
from app.routers import movies, reviews

app = FastAPI(
    title="영화 리뷰 서비스 API",
    description="영화 등록/조회 및 리뷰 감성분석 서비스를 위한 백엔드 API",
    version="1.0.0",
)

app.include_router(movies.router)
app.include_router(reviews.router)
