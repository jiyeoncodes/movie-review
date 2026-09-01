# app/query/movie_query.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime

from app.schema import db_schemas, schemas   # DB 모델은 db_schemas, Pydantic 검증은 schemas
from app.query import reviews_query

# 영화 등록
async def create_movie(db: AsyncSession, movie: schemas.MovieCreate):  
    new_movie = db_schemas.Movie(**movie.model_dump())                 
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie

# 영화 전체 조회
# 영화 전체 조회
async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(db_schemas.Movie)
        .where(db_schemas.Movie.is_deleted == "N")
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# 삭제되지 않은 영화 전체 개수 (페이지네이션의 총 페이지 수 계산용)
async def count_movies(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(db_schemas.Movie).where(db_schemas.Movie.is_deleted == "N")
    )
    return result.scalar_one()

# 특정 영화 조회
async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(db_schemas.Movie).where(
            and_(db_schemas.Movie.id == movie_id, db_schemas.Movie.is_deleted == "N")
        )
    )
    return result.scalars().first()

# 영화 수정
async def update_movie(
    db: AsyncSession, movie_id: int, movie_update: schemas.MovieUpdate   
) -> db_schemas.Movie | None:
    movie = await get_movie(db, movie_id)
    if not movie:
        return None

    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    movie.updated_at = datetime.now()
    await db.commit()
    await db.refresh(movie)
    return movie

# 영화 삭제
async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await get_movie(db, movie_id)
    if not movie:
        return None

    movie.is_deleted = "Y"
    movie.updated_at = datetime.now()

    await reviews_query.soft_delete_reviews_by_movie(db, movie_id)  # cascade

    await db.commit()
    await db.refresh(movie)
    return movie

async def count_movies(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(db_schemas.Movie).where(db_schemas.Movie.is_deleted == "N")
    )
    return result.scalar_one()