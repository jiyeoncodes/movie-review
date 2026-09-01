# app/main.py
# FastAPI 애플리케이션의 진입점.
# 이 파일이 하는 일은 딱 두 가지: (1) FastAPI 앱 객체 생성, (2) 각 도메인별 라우터 등록.
# 실제 비즈니스 로직(DB 조회, 감성분석 등)은 여기 두지 않고 routers/query/svc 계층에 위임한다.

from fastapi import FastAPI

# movies: 영화 CRUD 라우터, reviews: 리뷰 CRUD + 평점 라우터
from app.routers import movies, reviews

# FastAPI 앱 생성. title/description/version은 Swagger 문서(/docs)에 그대로 노출된다.
app = FastAPI(
    title="영화 리뷰 서비스 API",
    description="영화 등록/조회 및 리뷰 감성분석 서비스를 위한 백엔드 API",
    version="1.0.0",
)

# 각 라우터를 앱에 연결한다.
# 라우터 파일(routers/movies.py, routers/reviews.py) 안에서 이미 prefix("/movies", "/reviews")를
# 지정해뒀기 때문에, 여기서는 추가 인자 없이 등록만 하면 된다.
app.include_router(movies.router)
app.include_router(reviews.router)
