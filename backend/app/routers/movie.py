from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.schema import schemas
from app.query import movie_query

router = APIRouter(prefix="/movie", tags=["Movies"])


@router.post(
    "",
    response_model=schemas.MovieResponse,
    status_code=201,
    summary="영화 등록",
    description="새 영화 정보를 등록합니다. 제목, 개봉일, 감독, 장르는 필수이며 포스터 URL은 선택입니다.",
    response_description="등록된 영화 정보",
)
async def create_movie(movie: schemas.MovieCreate, db: AsyncSession = Depends(get_db)):
    return await movie_query.create_movie(db, movie)


@router.get(
    "",
    response_model=list[schemas.MovieResponse],
    summary="영화 전체 조회",
    description="모든 영화 목록을 조회합니다.",
    response_description="영화 목록",
)
async def read_movies(db: AsyncSession = Depends(get_db)):
    return await movie_query.get_movies(db)


@router.get(
    "/{movie_id}",
    response_model=schemas.MovieResponse,
    summary="특정 영화 조회",
    description="movie_id로 영화를 조회합니다. 삭제된 영화는 조회되지 않습니다.",
    response_description="조회된 영화 정보",
    responses={404: {"description": "해당 movie_id의 영화가 존재하지 않거나 이미 삭제됨"}},
)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await movie_query.get_movie(db, movie_id)
    if not movie:
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
    movie = await movie_query.update_movie(db, movie_id, movie_update)
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
    movie = await movie_query.delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return {"message": f"id={movie_id} - 영화가 삭제되었습니다."}