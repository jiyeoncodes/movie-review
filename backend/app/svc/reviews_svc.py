# app/svc/reviews_svc.py
# 리뷰 관련 "조합 로직" 전담 모듈.
# 설계 원칙: svc는 여러 로직을 조합해야 할 때만 사용한다.
#   - register_review: "영화 존재 검증 + 감성분석 실행 + DB 저장" 세 단계를 조합
#   - get_movie_rating: "여러 리뷰의 감성점수를 모아 평균 계산" 하는 집계 로직

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.query import reviews_query, movies_query
from app.svc.sentiment import analyze_sentiment
from app.schema.schemas import ReviewCreate
from app.schema.db_schemas import Review


# 리뷰 등록
async def register_review(db: AsyncSession, review_in: ReviewCreate):
    # 1단계: 존재하지 않는 영화에는 리뷰를 달 수 없도록 먼저 확인 (데이터 정합성 보장)
    movie = await movies_query.get_movie(db, review_in.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="등록하려는 영화가 존재하지 않습니다.")

    # 2단계: 리뷰 본문(content)을 KoELECTRA 감성분석 모델에 넣어서
    # 라벨("긍정"/"부정")과 확신도(score, 0~1 사이 확률)를 얻는다.
    label, score = analyze_sentiment(review_in.content)

    # 3단계: 분석 결과까지 포함해서 실제 DB에 저장 (저장 자체는 query 계층에 위임)
    return await reviews_query.create_review(
        db=db,
        movie_id=review_in.movie_id,
        author=review_in.author,
        content=review_in.content,
        sentiment_label=label,
        sentiment_score=score,
    )


# 영화 평균 평점
# sentiment_label + sentiment_score를 "긍정일 확률"로 변환한 뒤 평균을 5점 만점(★)으로 환산
async def get_movie_rating(db: AsyncSession, movie_id: int):
    reviews = await reviews_query.get_reviews_by_movie(db, movie_id)

    # 주의(중요): sentiment_score는 "라벨이 맞다고 확신하는 확률"이지, "긍정일 확률" 자체가 아니다.
    # 예: 어떤 리뷰가 "부정"으로 판정되고 score=0.99라면, 이는 "부정이라고 99% 확신"한다는 뜻이지
    #     "긍정 점수가 0.99"라는 뜻이 아니다. 이걸 그대로 평균 내면 부정 리뷰인데도
    #     확신도가 높을수록 평점이 오히려 높게 나오는 버그가 생긴다.
    # 따라서 평점 계산 전에 반드시 "긍정일 확률" 기준으로 통일해서 변환해야 한다.
    #   - label이 "긍정"이면 score가 이미 긍정 확률이므로 그대로 사용
    #   - label이 "부정"이면 score는 "부정 확신도"이므로, 긍정 확률로 바꾸려면 (1 - score)
    positive_probs = [
        r.sentiment_score if r.sentiment_label == "긍정" else round(1 - r.sentiment_score, 4)
        for r in reviews
        if r.sentiment_score is not None and r.sentiment_label is not None
    ]

    if not positive_probs:
        # 리뷰가 하나도 없거나, 감성분석 결과가 전혀 없는 경우 -> 평점 계산 불가능
        return {"movie_id": movie_id, "review_count": 0, "average_rating": None}

    # 긍정 확률 평균(0~1) * 5 => 5점 만점 평점으로 환산
    average_rating = round((sum(positive_probs) / len(positive_probs)) * 5, 2)
    return {
        "movie_id": movie_id,
        "review_count": len(positive_probs),
        "average_rating": average_rating,
    }
