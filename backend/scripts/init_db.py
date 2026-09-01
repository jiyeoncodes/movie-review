# scripts/init_db.py
# 데이터베이스 테이블을 생성하고, 실제로 잘 만들어졌는지 구조를 검증하는 스크립트.
# 실행 방법: backend 폴더에서 `uv run python scripts/init_db.py`

import asyncio
import sqlite3
import sys
import os

# 이 스크립트는 backend/scripts/ 안에 있는데, app 패키지(backend/app/...)를 import해야 하므로
# 상위 폴더(backend/)를 파이썬 모듈 검색 경로에 추가해준다.
# 이렇게 안 하면 "from app.common.database import ..."가 실패한다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.database import engine, Base, DATABASE_URL
from app.schema import db_schemas   # Movie, Review 모델을 import해야 Base.metadata에 등록됨


async def init_database():
    """
    Base를 상속한 모든 모델(Movie, Review)의 정의를 바탕으로
    실제 DB에 테이블을 생성한다. 이미 테이블이 있으면 아무 일도 하지 않는다(안전하게 재실행 가능).
    """
    print("데이터베이스 테이블 생성을 시작합니다...")
    async with engine.begin() as conn:
        # run_sync: SQLAlchemy의 동기 함수(create_all)를 비동기 컨텍스트 안에서 실행하기 위한 브릿지
        await conn.run_sync(Base.metadata.create_all)
    print("   완료: movies, reviews 테이블 생성 요청이 처리되었습니다.\n")


def verify_tables():
    """
    실제로 테이블이 생성됐는지, 컬럼 구조가 의도한 대로인지 직접 SQLite에 접속해서 확인한다.
    (비동기 엔진과 별개로, 검증 목적으로는 sqlite3 표준 라이브러리를 동기 방식으로 사용)
    """
    print("테이블 생성 결과를 확인합니다...")
    # DATABASE_URL 형태: "sqlite+aiosqlite:///./movies.db" -> 실제 파일 경로만 추출
    db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # SQLite 내장 메타테이블(sqlite_master)에서 사용자가 만든 테이블 이름 목록을 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   생성된 테이블 목록: {tables}\n")

    for table_name in tables:
        print(f"   [{table_name}] 테이블 컬럼 구조")
        # PRAGMA table_info: 해당 테이블의 컬럼명, 타입, NOT NULL 여부, 기본키 여부 등을 반환
        cursor.execute(f"PRAGMA table_info({table_name});")
        for col in cursor.fetchall():
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            pk_mark = " [PK]" if is_pk else ""
            null_mark = "NOT NULL" if not_null else "NULL 허용"
            print(f"     - {col_name} ({col_type}) {null_mark}{pk_mark}")
        print()

    conn.close()


if __name__ == "__main__":
    # 1) 비동기 함수인 init_database()를 asyncio.run으로 실행 (테이블 생성)
    asyncio.run(init_database())
    # 2) 생성 결과를 동기 방식으로 검증 (콘솔에 컬럼 구조 출력)
    verify_tables()
