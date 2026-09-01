# app/query/movies_query.py
# 영화 관련 "순수 DB 접근" 함수 모음.
# 영화는 단순 CRUD(등록/조회/수정/삭제)만 필요하므로, svc 계층 없이
# routers/movies.py가 이 파일의 함수들을 직접 호출하는 구조로 설계했다.
# (설계 원칙: 여러 로직을 "조합"할 때만 svc를 두고, 단순 CRUD는 query를 바로 호출)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime

from app.schema import db_schemas, schemas   # DB 모델은 db_schemas, Pydantic 검증은 schemas
from app.query import reviews_query


# 영화 등록
async def create_movie(db: AsyncSession, movie: schemas.MovieCreate):
    # movie.model_dump(): Pydantic 스키마(MovieCreate)를 파이썬 dict로 변환
    # **로 풀어서 넘기면 title=..., release_date=... 처럼 각 필드가 자동으로 매핑됨
    new_movie = db_schemas.Movie(**movie.model_dump())
    db.add(new_movie)          # 세션에 새 객체 추가 (아직 DB에 반영은 안 됨)
    await db.commit()          # 실제로 DB에 반영(INSERT 실행)
    await db.refresh(new_movie)  # DB가 자동 생성한 값(id, created_at 등)을 객체에 다시 채워 넣음
    return new_movie


# 영화 전체 조회 (페이지네이션 지원)
async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(db_schemas.Movie)
        .where(db_schemas.Movie.is_deleted == "N")   # soft delete된 영화는 제외
        .offset(skip)   # 앞에서 skip개 건너뛰기 (예: 2페이지면 6개 건너뜀)
        .limit(limit)   # 최대 limit개만 가져오기 (한 페이지 분량)
    )
    return result.scalars().all()


# 삭제되지 않은 영화의 전체 개수를 센다.
# 프론트엔드가 "전체 3페이지 중 1페이지"처럼 정확한 총 페이지 수를 계산하려면
# "전체 몇 개인지"를 알아야 하므로, 목록 조회와 별개로 개수만 세는 쿼리를 둔다.
async def count_movies(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(db_schemas.Movie).where(db_schemas.Movie.is_deleted == "N")
    )
    return result.scalar_one()


# 특정 영화 단건 조회 (movie_id로 조회, 삭제된 영화는 조회 안 됨)
async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(db_schemas.Movie).where(
            and_(db_schemas.Movie.id == movie_id, db_schemas.Movie.is_deleted == "N")
        )
    )
    return result.scalars().first()


# 영화 정보 부분 수정 (PATCH)
async def update_movie(
    db: AsyncSession, movie_id: int, movie_update: schemas.MovieUpdate
) -> db_schemas.Movie | None:
    movie = await get_movie(db, movie_id)
    if not movie:
        return None  # 없는 영화면 라우터에서 404로 처리하도록 None 반환

    # exclude_unset=True: 클라이언트가 요청 바디에 "실제로 포함한" 필드만 골라낸다.
    # 예를 들어 title만 보내면, release_date/director 등은 전혀 건드리지 않고 title만 바뀐다.
    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)  # movie.title = value 같은 동작을 동적으로 수행

    movie.updated_at = datetime.now()  # 수정 시각 갱신 (감사 컬럼)
    await db.commit()
    await db.refresh(movie)
    return movie


# 영화 삭제 (Soft Delete)
# 실제로 행을 지우지 않고 is_deleted를 'Y'로 바꾸는 방식. 확정된 설계 원칙에 따른 것.
async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await get_movie(db, movie_id)
    if not movie:
        return None

    movie.is_deleted = "Y"
    movie.updated_at = datetime.now()

    # cascade 처리: 이 영화에 달린 리뷰들도 함께 soft delete 한다.
    # 그렇지 않으면 "삭제된 영화에 달린 리뷰"가 화면(최근 리뷰 목록 등)에 계속 남아
    # 사용자가 클릭했을 때 존재하지 않는 영화를 참조하는 문제가 생긴다.
    await reviews_query.soft_delete_reviews_by_movie(db, movie_id)

    # 영화 변경사항과 리뷰 cascade 변경사항을 한 트랜잭션으로 한 번에 commit
    await db.commit()
    await db.refresh(movie)
    return movie
