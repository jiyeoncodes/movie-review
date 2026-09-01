# app/schema/db_schemas.py
# SQLAlchemy ORM 모델 정의. 실제 DB 테이블 구조와 1:1로 매핑되는 파이썬 클래스들이다.

from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.common.database import Base


class Movie(Base):
    """영화 테이블. 리뷰 테이블(Review)과 1(영화):N(리뷰) 관계를 가진다."""

    __tablename__ = "movie"

    # 기본키. autoincrement로 새 영화가 등록될 때마다 1씩 자동 증가.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String, nullable=False)          # 영화 제목 (필수)
    release_date = Column(Date, nullable=False)      # 개봉일 (필수)
    director = Column(String, nullable=False)        # 감독 (필수)
    genre = Column(String, nullable=False)            # 장르 (필수)
    poster_url = Column(String, nullable=True)         # 포스터 이미지 URL (선택, 없어도 됨)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(CHAR(1), nullable=False, default="N")
    
    review = relationship("Review", back_populates="movie")


class Review(Base):
    """리뷰 테이블. 반드시 하나의 Movie에 속한다(movie_id는 Movie.id를 참조하는 외래키)."""

    __tablename__ = "review"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 외래키(FK): 이 리뷰가 어느 영화에 대한 것인지 movie 테이블의 id를 참조한다.
    movie_id = Column(Integer, ForeignKey("movie.id"), nullable=False)
    author = Column(String, nullable=False)   # 리뷰 작성자 이름 (필수)
    content = Column(Text, nullable=False)     # 리뷰 본문 (필수, 길이 제한 없는 텍스트 타입)

    # 감성분석 결과. 리뷰 등록 시 자동으로 채워지므로 등록 직후엔 항상 값이 있지만,
    # 혹시 분석이 스킵된 경우(SENTIMENT_ENABLED=false)를 대비해 nullable=True로 둠.
    sentiment_label = Column(String, nullable=True)    # "긍정" 또는 "부정"
    sentiment_score = Column(Float, nullable=True)      # 예측 확신도(0~1 사이 확률값)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(CHAR(1), nullable=False, default="N")

    movie = relationship("Movie", back_populates="review")
