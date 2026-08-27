from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.query import review_query, movie_query
from app.svc.sentiment import analyze_sentiment
from app.schema.schemas import ReviewCreate
from app.schema.db_schemas import Review

# 리뷰 등록
async def register_review(db: AsyncSession, review_in: ReviewCreate):
    # 존재하지 않는 영화에는 리뷰를 달 수 없도록 먼저 확인
    movie = await movie_query.get_movie(db, review_in.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="등록하려는 영화가 존재하지 않습니다.")

    label, score = analyze_sentiment(review_in.content)

    return await review_query.create_review(
        db=db,
        movie_id=review_in.movie_id,
        author=review_in.author,
        content=review_in.content,
        sentiment_label=label,
        sentiment_score=score,
    )


# 영화 평균 평점
# sentiment_score(=긍정확률) 평균을 5점 만점(★)으로 환산
async def get_movie_rating(db: AsyncSession, movie_id: int):
    reviews = await review_query.get_reviews_by_movie(db, movie_id)
    scores = [r.sentiment_score for r in reviews if r.sentiment_score is not None]

    if not scores:
        return {"movie_id": movie_id, "review_count": 0, "average_rating": None}

    average_rating = round((sum(scores) / len(scores)) * 5, 2)
    return {
        "movie_id": movie_id,
        "review_count": len(scores),
        "average_rating": average_rating,
    }