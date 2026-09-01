# frontend/api_client.py
# 백엔드 REST API 호출 전담 모듈. .env에서 API_BASE_URL을 읽어와 사용한다.
from typing import Any
from pathlib import Path
import os
import requests
from dotenv import load_dotenv

# .env 파일 로드 (frontend/.env 위치를 명시적으로 지정)
load_dotenv(Path(__file__).resolve().parent / ".env")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class ApiError(Exception):
    """API 응답이 4xx/5xx일 때 발생. 각 페이지에서 try/except로 잡아서 st.error로 표시."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


def _handle(res: requests.Response) -> Any:
    if res.status_code >= 400:
        try:
            detail = res.json().get("detail", res.text)
        except ValueError:
            detail = res.text
        raise ApiError(res.status_code, detail)
    if res.status_code == 204 or not res.content:
        return None
    return res.json()


# ---------------- 영화 ----------------
def get_movies(skip: int = 0, limit: int = 6) -> dict:
    res = requests.get(f"{API_BASE_URL}/movies", params={"skip": skip, "limit": limit})
    return _handle(res)  # {"total": ..., "items": [...]}

def get_movie(movie_id: int) -> dict:
    res = requests.get(f"{API_BASE_URL}/movies/{movie_id}")
    return _handle(res)

def create_movie(payload: dict) -> dict:
    res = requests.post(f"{API_BASE_URL}/movies", json=payload)
    return _handle(res)

def update_movie(movie_id: int, payload: dict) -> dict:
    res = requests.patch(f"{API_BASE_URL}/movies/{movie_id}", json=payload)
    return _handle(res)

def delete_movie(movie_id: int) -> None:
    res = requests.delete(f"{API_BASE_URL}/movies/{movie_id}")
    return _handle(res)


# ---------------- 리뷰 ----------------
def create_review(payload: dict) -> dict:
    res = requests.post(f"{API_BASE_URL}/reviews", json=payload)
    return _handle(res)

def get_recent_reviews(skip: int = 0, limit: int = 10) -> dict:
    res = requests.get(f"{API_BASE_URL}/reviews", params={"skip": skip, "limit": limit})
    return _handle(res)  # {"total": ..., "items": [...]}

def get_reviews_by_movie(movie_id: int) -> list[dict]:
    res = requests.get(f"{API_BASE_URL}/reviews/movie/{movie_id}")
    return _handle(res)

def get_review(review_id: int) -> dict:
    res = requests.get(f"{API_BASE_URL}/reviews/{review_id}")
    return _handle(res)

def delete_review(review_id: int) -> None:
    res = requests.delete(f"{API_BASE_URL}/reviews/{review_id}")
    return _handle(res)

def get_movie_rating(movie_id: int) -> dict:
    res = requests.get(f"{API_BASE_URL}/reviews/movie/{movie_id}/rating")
    return _handle(res)