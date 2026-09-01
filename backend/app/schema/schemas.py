from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


# 영화 등록
class MovieCreate(BaseModel):
    title: str
    release_date: date
    director: str
    genre: str
    poster_url: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "인터스텔라",
                "release_date": "2014-11-06",
                "director": "크리스토퍼 놀란",
                "genre": "SF",
                "poster_url": "https://image.tmdb.org/t/p/w500/nBNZadXqJSdt05SHLqgT0HuC5Gm.jpg",
            }
        }
    )

# 영화 조회
class MovieResponse(BaseModel):
    id: int
    title: str
    release_date: date
    director: str
    genre: str
    poster_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: str

    model_config = ConfigDict(
        from_attributes=True,   # SQLAlchemy 모델 객체를 자동 변환
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "인터스텔라",
                "release_date": "2014-11-06",
                "director": "크리스토퍼 놀란",
                "genre": "SF",
                "poster_url": "https://example.com/poster/interstellar.jpg",
                "created_at": "2026-08-21T10:00:00",
                "updated_at": "2026-08-21T10:00:00",
                "is_deleted": "N",
            }
        },
    )
    
# 리뷰 등록
class ReviewCreate(BaseModel):
    movie_id: int
    author: str
    content: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "movie_id": 1,
                "author": "홍길동",
                "content": "영상미가 정말 뛰어난 영화였습니다. 강력 추천합니다!",
            }
        }
    )

# 리뷰 조회
class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    author: str
    content: str
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "movie_id": 1,
                "author": "홍길동",
                "content": "영상미가 정말 뛰어난 영화였습니다. 강력 추천합니다!",
                "sentiment_label": "긍정",
                "sentiment_score": 0.95,
                "created_at": "2026-08-21T10:05:00",
                "updated_at": "2026-08-21T10:05:00",
                "is_deleted": "N",
            }
        },
    )

# 영화 리뷰 감성평가 점수 조회
class MovieRatingResponse(BaseModel):
    movie_id: int
    review_count: int
    average_rating: float | None  # 리뷰가 하나도 없으면 None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "movie_id": 1,
                "review_count": 12,
                "average_rating": 3.9,
            }
        }
    )

# 영화 수정
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    release_date: Optional[date] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    poster_url: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "인터스텔라 (감독판)",
            }
        }
    )

class ReviewListResponse(BaseModel):
    total: int
    items: list[ReviewResponse]

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    total: int
    items: list[MovieResponse]

    model_config = ConfigDict(from_attributes=True)