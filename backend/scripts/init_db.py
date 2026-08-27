import asyncio
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.database import engine, Base, DATABASE_URL
from app.schema import db_schemas

async def init_database():
    print("데이터베이스 테이블 생성을 시작합니다...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   완료: movies, reviews 테이블 생성 요청이 처리되었습니다.\n")


def verify_tables():
    print("테이블 생성 결과를 확인합니다...")
    db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   생성된 테이블 목록: {tables}\n")

    for table_name in tables:
        print(f"   [{table_name}] 테이블 컬럼 구조")
        cursor.execute(f"PRAGMA table_info({table_name});")
        for col in cursor.fetchall():
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            pk_mark = " [PK]" if is_pk else ""
            null_mark = "NOT NULL" if not_null else "NULL 허용"
            print(f"     - {col_name} ({col_type}) {null_mark}{pk_mark}")
        print()

    conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())  
    verify_tables()