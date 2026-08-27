from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.db_schemas import Review

# 리뷰 등록
async def create_review(
    db: AsyncSession,
    movie_id: int,
    author: str,
    content: str,
    sentiment_label: str | None,
    sentiment_score: float | None,
) -> Review:
    review = Review(
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
async def get_recent_reviews(db: AsyncSession, limit: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.is_deleted == "N")
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

# 특정 영화의 리뷰 전체 조회
async def get_reviews_by_movie(db: AsyncSession, movie_id: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.movie_id == movie_id, Review.is_deleted == "N")
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())

# 특정 리뷰 단건 조회
async def get_review_by_id(db: AsyncSession, review_id: int) -> Review | None:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.is_deleted == "N")
    )
    return result.scalar_one_or_none()

# 리뷰 삭제
async def soft_delete_review(db: AsyncSession, review_id: int) -> Review | None:
    review = await get_review_by_id(db, review_id)
    if review is None:
        return None
    review.is_deleted = "Y"
    review.updated_at = datetime.now()
    await db.commit()
    await db.refresh(review)
    return review