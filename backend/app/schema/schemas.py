# app/schema/schemas.py
# Pydantic 스키마 정의. FastAPI가 요청(request)을 검증하고 응답(response)을 직렬화할 때 사용한다.
# (참고: DB 테이블 구조 자체는 db_schemas.py의 SQLAlchemy 모델이 담당 - 역할 분리)
#
# 네이밍 규칙:
#   - ...Create : 클라이언트가 "등록" 요청 시 보내는 입력값 검증용
#   - ...Update : 클라이언트가 "수정" 요청 시 보내는 입력값 검증용 (모든 필드가 선택사항)
#   - ...Response: 서버가 클라이언트에게 돌려주는 응답 형태 검증/직렬화용

from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


# ----------------------- 영화 -----------------------

# 영화 등록 요청 바디. 포스터 URL만 선택사항(Optional)이고 나머지는 필수.
class MovieCreate(BaseModel):
    title: str
    release_date: date
    director: str
    genre: str
    poster_url: Optional[str] = None

    # json_schema_extra: Swagger UI(/docs)에 예시값으로 보여줄 샘플 데이터.
    # 실제 검증 로직에는 영향 없고, 순전히 문서화/사용 편의를 위한 설정.
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


# 영화 조회 시 클라이언트에게 돌려줄 응답 형태. DB의 모든 컬럼(감사 컬럼 포함)을 그대로 노출한다.
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
        from_attributes=True,   # SQLAlchemy 모델 객체(Movie)를 이 스키마로 자동 변환 가능하게 함
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


# 영화 수정(PATCH) 요청 바디. 모든 필드가 Optional인 이유:
# PATCH는 "부분 수정"이라, 클라이언트가 바꾸고 싶은 필드만 보내도 되게 하기 위함.
# (라우터/query 계층에서 model_dump(exclude_unset=True)로 "보낸 필드만" 골라내서 적용한다)
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


# 영화 목록 조회(GET /movies) 응답 형태.
# 단순 배열 대신 {total, items} 구조로 감싸서, 프론트엔드가 "전체 몇 개인지" 알 수 있게 하고
# 이를 이용해 "페이지 3 / 7" 같은 정확한 페이지네이션 UI를 만들 수 있게 한다.
class MovieListResponse(BaseModel):
    total: int                        # 삭제되지 않은 영화의 전체 개수
    items: list[MovieResponse]        # 현재 페이지에 해당하는 영화 목록

    model_config = ConfigDict(from_attributes=True)


# ----------------------- 리뷰 -----------------------

# 리뷰 등록 요청 바디.
# sentiment_label/score는 여기 없다 - 클라이언트가 직접 값을 보내는 게 아니라
# 서버(reviews_svc.register_review)가 감성분석 모델을 돌려서 자동으로 채워 넣기 때문.
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


# 리뷰 조회 시 클라이언트에게 돌려줄 응답 형태.
class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    author: str
    content: str
    sentiment_label: Optional[str] = None    # 감성분석이 아직 안 됐거나 비활성화된 경우 None일 수 있음
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


# 최근 리뷰 목록 조회(GET /reviews) 응답 형태. MovieListResponse와 같은 이유로
# {total, items} 구조를 써서 프론트엔드가 정확한 총 페이지 수를 계산할 수 있게 한다.
class ReviewListResponse(BaseModel):
    total: int
    items: list[ReviewResponse]

    model_config = ConfigDict(from_attributes=True)


# 영화별 평균 평점 조회(GET /reviews/movie/{id}/rating) 응답 형태.
# average_rating은 리뷰가 하나도 없을 경우 계산 자체가 불가능하므로 None을 허용한다.
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
