# app/routers/review.py
"""리뷰 라우터. 등록/평점 계산은 감성분석 조합 로직이 필요해 svc(review_svc)를 경유한다."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.query import review_query
from app.svc import review_svc
from app.schema.schemas import ReviewCreate, ReviewResponse, MovieRatingResponse

router = APIRouter(prefix="/review", tags=["Reviews"])


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=201,
    summary="리뷰 등록",
    description="리뷰를 등록하면 content(리뷰 내용)가 KoELECTRA 감성분석 모델에 자동으로 "
    "전달되어 sentiment_label(긍정/부정)과 sentiment_score(긍정 확률)가 함께 저장됩니다.",
    response_description="등록된 리뷰 정보",
)
async def create_review(review_in: ReviewCreate, db: AsyncSession = Depends(get_db)):
    return await review_svc.register_review(db, review_in)


@router.get(
    "",
    response_model=list[ReviewResponse],
    summary="최근 리뷰 N개 조회",
    description="가장 최근에 등록된 리뷰를 최신순으로 조회합니다. 영화 구분 없이 전체 리뷰 대상입니다.",
    response_description="최근 리뷰 목록",
)
async def read_recent_reviews(
    limit: int = Query(default=10, ge=1, le=100, description="조회할 리뷰 개수"),
    db: AsyncSession = Depends(get_db),
):
    return await review_query.get_recent_reviews(db, limit)


@router.get(
    "/movie/{movie_id}",
    response_model=list[ReviewResponse],
    summary="특정 영화의 리뷰 전체 조회",
    description="movie_id에 해당하는 영화의 모든 리뷰를 최신순으로 조회합니다.",
    response_description="해당 영화의 리뷰 목록",
)
async def read_reviews_by_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await review_query.get_reviews_by_movie(db, movie_id)


@router.get(
    "/movie/{movie_id}/rating",
    response_model=MovieRatingResponse,
    summary="영화 평균 평점 조회",
    description="movie_id에 해당하는 영화의 모든 리뷰에 대해 감성분석 점수(긍정 확률)의 "
    "평균을 5점 만점(★)으로 환산해 반환합니다. 리뷰가 없으면 average_rating은 null입니다.",
    response_description="평균 평점 및 리뷰 개수",
)
async def read_movie_rating(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await review_svc.get_movie_rating(db, movie_id)


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="리뷰 조회",
    description="review_id로 리뷰 단건을 조회합니다. 삭제된 리뷰는 조회되지 않습니다.",
    response_description="조회된 리뷰 정보",
    responses={404: {"description": "해당 review_id의 리뷰가 존재하지 않거나 이미 삭제됨"}},
)
async def read_review(review_id: int, db: AsyncSession = Depends(get_db)):
    review = await review_query.get_review_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    return review


@router.delete(
    "/{review_id}",
    summary="리뷰 삭제",
    description="review_id로 리뷰를 삭제합니다.",
    response_description="삭제 처리 결과 메시지",
    responses={404: {"description": "해당 review_id의 리뷰가 존재하지 않거나 이미 삭제됨"}},
)
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    review = await review_query.soft_delete_review(db, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    return {"message": f"id={review_id} - 리뷰가 삭제되었습니다."}