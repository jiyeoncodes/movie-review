# app/common/database.py
# DB 연결 설정을 담당하는 모듈.
# 확정된 설계 원칙에 따라 별도의 config.py를 두지 않고, 이 파일이 그 역할까지 흡수한다.
# (환경변수 로드 + SQLAlchemy 엔진/세션 생성을 한 곳에서 관리)

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# .env 파일에 적어둔 환경변수(DATABASE_URL 등)를 현재 프로세스 환경변수로 불러온다.
# 이 호출이 없으면 os.getenv()로 .env 안의 값을 읽을 수 없다.
load_dotenv()

# DB 접속 주소. .env에 DATABASE_URL이 없으면 로컬 SQLite 파일(movies.db)을 기본값으로 사용한다.
# 나중에 PostgreSQL 등으로 바꾸고 싶으면 이 환경변수 값만 바꾸면 되도록 설계했다.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./movies.db")

# 비동기 방식으로 DB에 접속하는 엔진 생성.
# echo=False: 실행되는 SQL 쿼리 로그를 콘솔에 출력하지 않음(디버깅 시 True로 바꾸면 유용).
engine = create_async_engine(DATABASE_URL, echo=False)

# 요청마다 새로운 비동기 DB 세션(작업 단위)을 만들어주는 팩토리.
# expire_on_commit=False: commit() 이후에도 이미 조회한 객체의 속성값을 계속 사용할 수 있게 함
# (기본값 True로 두면 commit 직후 객체 속성에 접근할 때 재조회가 발생해 비동기 환경에서 에러가 날 수 있음).
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# 모든 SQLAlchemy 모델(Movie, Review 등)이 상속받는 기본 클래스.
# 이 클래스를 상속한 모델들의 정보가 Base.metadata에 모여서, 테이블 생성 시 한 번에 활용된다.
Base = declarative_base()


async def get_db():
    """
    FastAPI의 Depends()로 주입되는 DB 세션 제공 함수.
    - 요청이 들어올 때마다 새 세션을 열고(async with),
    - 라우터 함수 실행이 끝나면(yield 이후) 자동으로 세션을 정리(닫기)한다.
    - 이렇게 하면 각 요청마다 독립된 DB 세션을 쓰게 되어 동시 요청 간 충돌을 방지할 수 있다.
    """
    async with AsyncSessionLocal() as session:
        yield session
