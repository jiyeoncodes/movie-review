from sqlalchemy.ext.asyncio import AsyncSession

from app.schema import schemas
from app.query import movie_query

# 영화 등록
async def register_movie(db: AsyncSession, movie: schemas.MovieCreate):
    return await movie_query.create_movie(db, movie)

# 영화 전체 조회
async def list_movies(db: AsyncSession):
    return await movie_query.get_movies(db)

# 특정 영화 조회    
async def get_movie_detail(db: AsyncSession, movie_id: int):
    return await movie_query.get_movie(db, movie_id)

# 영화 수정
async def modify_movie(db: AsyncSession, movie_id: int, movie_update: schemas.MovieUpdate):
    return await movie_query.update_movie(db, movie_id, movie_update)

# 영화 삭제
async def remove_movie(db: AsyncSession, movie_id: int):
    return await movie_query.delete_movie(db, movie_id)