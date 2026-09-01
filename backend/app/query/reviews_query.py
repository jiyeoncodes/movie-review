from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func

from app.schema import db_schemas

# 리뷰 등록
async def create_review(
    db: AsyncSession,
    movie_id: int,
    author: str,
    content: str,
    sentiment_label: str | None,
    sentiment_score: float | None,
):
    review = db_schemas.Review(
        movie_id=movie_id,
        author=author,
        content=content,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review

# 최근 리뷰 조회
async def get_recent_reviews(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(db_schemas.Review)
        .where(db_schemas.Review.is_deleted == "N")
        .order_by(db_schemas.Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# 특정 영화의 리뷰 전체 조회
async def get_reviews_by_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(db_schemas.Review)
        .where(db_schemas.Review.movie_id == movie_id, db_schemas.Review.is_deleted == "N")
        .order_by(db_schemas.Review.created_at.desc())
    )
    return list(result.scalars().all())

# 특정 리뷰 단건 조회
async def get_review_by_id(db: AsyncSession, review_id: int) -> db_schemas.Review | None:
    result = await db.execute(
        select(db_schemas.Review).where(db_schemas.Review.id == review_id, db_schemas.Review.is_deleted == "N")
    )
    return result.scalar_one_or_none()

# 리뷰 삭제
async def soft_delete_review(db: AsyncSession, review_id: int) -> db_schemas.Review | None:
    review = await get_review_by_id(db, review_id)
    if review is None:
        return None
    review.is_deleted = "Y"
    review.updated_at = datetime.now()
    await db.commit()
    await db.refresh(review)
    return review

# 특정 영화에 달린 모든 리뷰를 delete 처리 
async def soft_delete_reviews_by_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(db_schemas.Review).where(
            and_(db_schemas.Review.movie_id == movie_id, db_schemas.Review.is_deleted == "N")
        )
    )
    reviews = result.scalars().all()
    for review in reviews:
        review.is_deleted = "Y"
        review.updated_at = datetime.now()
    # commit은 호출하는 쪽(delete_movie)에서 한 번에 처리 -> 여기서 commit() 하면 안 됨

async def count_reviews(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(db_schemas.Review).where(db_schemas.Review.is_deleted == "N")
    )
    return result.scalar_one()