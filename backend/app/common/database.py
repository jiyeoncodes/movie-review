# app/common/database.py
# DB 연결 설정을 담당하는 모듈.

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

# DB 접속 주소. .env에 DATABASE_URL이 없으면 로컬 SQLite 파일(movies.db)을 기본값으로 사용한다.
# 나중에 PostgreSQL 등으로 바꾸고 싶으면 이 환경변수 값만 바꾸면 되도록 설계했다.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./movies.db")

# 비동기 방식으로 DB에 접속하는 엔진 생성.
# echo=False: 실행되는 SQL 쿼리 로그를 콘솔에 출력하지 않음(디버깅 시 True로 바꾸면 유용).
engine = create_async_engine(DATABASE_URL, echo=False)

# 요청마다 새로운 비동기 DB 세션(작업 단위)을 만들어주는 팩토리.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# 이 클래스를 상속한 모델들의 정보가 Base.metadata에 모여서, 테이블 생성 시 한 번에 활용된다.
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
