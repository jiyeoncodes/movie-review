# app/query/reviews_query.py
# 리뷰 관련 "순수 DB 접근" 함수 모음.
# 등록(감성분석 조합이 필요한 로직)은 svc 계층(reviews_svc.py)이 담당하지만,
# 나머지 단순 조회/삭제 함수들은 여기서 바로 정의하고 라우터가 직접 호출한다.

from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema import db_schemas


# 리뷰 등록 (실제 INSERT 실행부. 감성분석 자체는 svc 계층에서 미리 수행하고
# 그 결과(label, score)를 인자로 받아서 저장만 담당한다 - 책임 분리)
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


# 최근 리뷰 조회 (영화 구분 없이 전체 리뷰 대상, 최신순 페이지네이션)
async def get_recent_reviews(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(db_schemas.Review)
        .where(db_schemas.Review.is_deleted == "N")
        .order_by(db_schemas.Review.created_at.desc())   # 최신 등록 순으로 정렬
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# 삭제되지 않은 리뷰의 전체 개수. 프론트엔드의 정확한 총 페이지 수 계산에 사용.
async def count_reviews(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(db_schemas.Review).where(db_schemas.Review.is_deleted == "N")
    )
    return result.scalar_one()


# 특정 영화의 리뷰 전체 조회 (페이지네이션 없이 전부 반환, 최신순 정렬)
async def get_reviews_by_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(db_schemas.Review)
        .where(db_schemas.Review.movie_id == movie_id, db_schemas.Review.is_deleted == "N")
        .order_by(db_schemas.Review.created_at.desc())
    )
    return list(result.scalars().all())


# 특정 리뷰 단건 조회 (review_id로 조회, 삭제된 리뷰는 조회 안 됨)
async def get_review_by_id(db: AsyncSession, review_id: int) -> db_schemas.Review | None:
    result = await db.execute(
        select(db_schemas.Review).where(db_schemas.Review.id == review_id, db_schemas.Review.is_deleted == "N")
    )
    return result.scalar_one_or_none()


# 리뷰 삭제 (Soft Delete)
async def soft_delete_review(db: AsyncSession, review_id: int) -> db_schemas.Review | None:
    review = await get_review_by_id(db, review_id)
    if review is None:
        return None
    review.is_deleted = "Y"
    review.updated_at = datetime.now()  # 삭제 시각을 updated_at에 기록 (리뷰는 수정 기능이 없어서 이 용도로만 쓰임)
    await db.commit()
    await db.refresh(review)
    return review


# 특정 영화에 달린 모든 리뷰를 한꺼번에 soft delete 처리 (영화 삭제 시 cascade 용도).
# movies_query.delete_movie()에서 영화를 삭제할 때 이 함수를 호출해서,
# "삭제된 영화에 리뷰만 살아남는" 상황을 방지한다.
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
    # 주의: 여기서 commit()을 호출하지 않는다.
    # 영화 삭제 로직(movies_query.delete_movie)이 영화 자체의 변경사항과
    # 이 리뷰들의 변경사항을 "하나의 트랜잭션"으로 묶어서 한 번에 commit해야
    # 중간에 오류가 나도 영화만 삭제되고 리뷰는 안 지워지는 반쪽짜리 상태를 방지할 수 있다.
