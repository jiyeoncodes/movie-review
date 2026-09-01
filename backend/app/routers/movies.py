# app/routers/movies.py
# 영화 관련 API 엔드포인트 정의.
# 영화는 감성분석 같은 "조합 로직"이 없는 단순 CRUD이므로,
# svc 계층을 거치지 않고 query 계층(movies_query)을 직접 호출한다.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.schema import schemas
from app.query import movies_query

# prefix="/movies": 이 라우터의 모든 경로 앞에 자동으로 "/movies"가 붙는다.
# 예: 아래 "/{movie_id}"는 실제로는 "/movies/{movie_id}"가 됨.
router = APIRouter(prefix="/movies", tags=["Movies"])


@router.post(
    "",
    response_model=schemas.MovieResponse,
    status_code=201,   # 201 Created: 새 리소스가 성공적으로 생성됐음을 의미하는 표준 상태코드
    summary="영화 등록",
    description="새 영화 정보를 등록합니다. 제목, 개봉일, 감독, 장르는 필수이며 포스터 URL은 선택입니다.",
    response_description="등록된 영화 정보",
)
async def create_movie(movie: schemas.MovieCreate, db: AsyncSession = Depends(get_db)):
    # Depends(get_db): FastAPI가 요청마다 자동으로 DB 세션을 만들어 여기에 주입해준다.
    return await movies_query.create_movie(db, movie)


@router.get(
    "",
    response_model=schemas.MovieListResponse,
    summary="영화 전체 조회",
    description="모든 영화 목록을 조회합니다.",
    response_description="영화 목록과 전체 개수",
)
async def read_movies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    # 목록(items)과 전체 개수(total)를 함께 반환한다.
    # 프론트엔드가 total로 "전체 페이지 수"를 계산해 정확한 페이지네이션 UI를 만들 수 있게 하기 위함.
    items = await movies_query.get_movies(db, skip=skip, limit=limit)
    total = await movies_query.count_movies(db)
    return {"total": total, "items": items}


@router.get(
    "/{movie_id}",
    response_model=schemas.MovieResponse,
    summary="특정 영화 조회",
    description="movie_id로 영화를 조회합니다. 삭제된 영화는 조회되지 않습니다.",
    response_description="조회된 영화 정보",
    responses={404: {"description": "해당 movie_id의 영화가 존재하지 않거나 이미 삭제됨"}},
)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await movies_query.get_movie(db, movie_id)
    if not movie:
        # 존재하지 않거나 이미 soft delete된 영화는 404로 응답 (REST 관례)
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie


@router.patch(
    "/{movie_id}",
    response_model=schemas.MovieResponse,
    summary="영화 정보 수정",
    description="movie_id로 영화 정보를 부분 수정합니다. 요청 body에 포함된 필드만 변경되며, "
    "포함되지 않은 필드는 기존 값이 유지됩니다.",
    response_description="수정된 영화 정보",
    responses={404: {"description": "해당 movie_id의 영화가 존재하지 않거나 이미 삭제됨"}},
)
async def update_movie(
    movie_id: int, movie_update: schemas.MovieUpdate, db: AsyncSession = Depends(get_db)
):
    movie = await movies_query.update_movie(db, movie_id, movie_update)
    if not movie:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie


@router.delete(
    "/{movie_id}",
    summary="영화 삭제",
    description="movie_id로 영화를 삭제합니다.",
    response_description="삭제 처리 결과 메시지",
    responses={404: {"description": "해당 movie_id의 영화가 존재하지 않거나 이미 삭제됨"}},
)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    # 실제로는 DELETE가 아니라 Soft Delete(is_deleted='Y' 처리)이며,
    # 이 영화에 달린 리뷰들도 movies_query.delete_movie 내부에서 함께 cascade 삭제된다.
    movie = await movies_query.delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return {"message": f"id={movie_id} - 영화가 삭제되었습니다."}
