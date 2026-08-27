from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.common.database import Base


class Movie(Base):
    __tablename__ = "movie"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    release_date = Column(Date, nullable=False)
    director = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    poster_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(CHAR(1), nullable=False, default="N")

    review = relationship("Review", back_populates="movie")


class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movie.id"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    sentiment_label = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(CHAR(1), nullable=False, default="N")

    movie = relationship("Movie", back_populates="review")