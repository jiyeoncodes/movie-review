# frontend/api_client.py
# 백엔드 REST API 호출 전담 모듈. UI(Streamlit) 로직은 여기 절대 포함하지 않는다.
# 여러 페이지(pages/1_Movie_List.py, pages/2_All_Reviews.py)가 이 파일의 함수들을
# import해서 공유하므로, 재사용 가능한 통신 함수들을 한 곳에 모아둔 것.
#
# requests(동기 라이브러리)를 쓰는 이유: Streamlit은 사용자가 뭔가 조작할 때마다
# 스크립트 파일 전체를 처음부터 다시 실행하는 구조라서, 어차피 그 실행 자체가 순차적(블로킹)이다.
# 여기서 async/httpx를 쓰면 이벤트 루프를 따로 관리해야 하는 부담만 늘고 실익이 없다.

from typing import Any
from pathlib import Path
import os
import requests
from dotenv import load_dotenv

# .env 파일 로드. Path(__file__).resolve().parent: 이 파일(api_client.py)이 있는 폴더를 의미.
# 즉 frontend/.env를 정확히 지정해서, 실행 위치(터미널 현재 디렉토리)와 무관하게 항상 찾도록 함.
load_dotenv(Path(__file__).resolve().parent / ".env")
# .env에 API_BASE_URL이 없으면 로컬 개발 기본값(localhost:8000)을 사용
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiError(Exception):
    """
    API 응답이 4xx/5xx(에러)일 때 발생시키는 예외.
    각 페이지에서 try/except ApiError로 잡아서 st.error(...)로 사용자에게 보여준다.
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code   # HTTP 상태 코드 (404, 500 등)
        self.detail = detail             # 에러 상세 메시지 (백엔드가 보낸 detail 필드)
        super().__init__(f"[{status_code}] {detail}")


def _handle(res: requests.Response) -> Any:
    """
    모든 API 호출 함수가 공통으로 거치는 응답 처리기.
    - 에러 응답이면 ApiError를 발생시켜서 호출한 쪽이 try/except로 처리하게 함
    - 정상 응답이면 JSON을 파싱해서 dict/list로 반환
    """
    if res.status_code >= 400:
        try:
            # 백엔드(FastAPI)는 보통 {"detail": "에러 메시지"} 형태로 에러를 응답한다
            detail = res.json().get("detail", res.text)
        except ValueError:
            # 응답이 JSON이 아닌 경우(예: 서버가 완전히 죽어서 HTML 에러 페이지가 온 경우)
            detail = res.text
        raise ApiError(res.status_code, detail)
    if res.status_code == 204 or not res.content:
        # 204 No Content: 본문이 없는 성공 응답 (주로 DELETE 요청)
        return None
    return res.json()


# ---------------- 영화 ----------------

def get_movies(skip: int = 0, limit: int = 6) -> dict:
    """영화 목록 조회. 응답 형태: {"total": 전체개수, "items": [영화, ...]}"""
    res = requests.get(f"{API_BASE_URL}/movies", params={"skip": skip, "limit": limit})
    return _handle(res)

def get_movie(movie_id: int) -> dict:
    """영화 단건 조회"""
    res = requests.get(f"{API_BASE_URL}/movies/{movie_id}")
    return _handle(res)

def create_movie(payload: dict) -> dict:
    """영화 등록. payload: {title, release_date, director, genre, poster_url}"""
    res = requests.post(f"{API_BASE_URL}/movies", json=payload)
    return _handle(res)

def update_movie(movie_id: int, payload: dict) -> dict:
    """영화 정보 부분 수정 (PATCH)"""
    res = requests.patch(f"{API_BASE_URL}/movies/{movie_id}", json=payload)
    return _handle(res)

def delete_movie(movie_id: int) -> None:
    """영화 삭제 (백엔드에서 Soft Delete 처리, 연결된 리뷰도 함께 cascade 삭제됨)"""
    res = requests.delete(f"{API_BASE_URL}/movies/{movie_id}")
    return _handle(res)


# ---------------- 리뷰 ----------------

def create_review(payload: dict) -> dict:
    """리뷰 등록. payload: {movie_id, author, content}. 감성분석은 백엔드가 자동으로 실행."""
    res = requests.post(f"{API_BASE_URL}/reviews", json=payload)
    return _handle(res)

def get_recent_reviews(skip: int = 0, limit: int = 10) -> dict:
    """최근 리뷰 목록 조회 (영화 구분 없이 전체). 응답 형태: {"total": ..., "items": [...]}"""
    res = requests.get(f"{API_BASE_URL}/reviews", params={"skip": skip, "limit": limit})
    return _handle(res)

def get_reviews_by_movie(movie_id: int) -> list[dict]:
    """특정 영화의 리뷰 전체 조회"""
    res = requests.get(f"{API_BASE_URL}/reviews/movie/{movie_id}")
    return _handle(res)

def get_review(review_id: int) -> dict:
    """리뷰 단건 조회"""
    res = requests.get(f"{API_BASE_URL}/reviews/{review_id}")
    return _handle(res)

def delete_review(review_id: int) -> None:
    """리뷰 삭제 (Soft Delete)"""
    res = requests.delete(f"{API_BASE_URL}/reviews/{review_id}")
    return _handle(res)

def get_movie_rating(movie_id: int) -> dict:
    """영화의 평균 평점 조회 (감성분석 점수를 5점 만점으로 환산한 값)"""
    res = requests.get(f"{API_BASE_URL}/reviews/movie/{movie_id}/rating")
    return _handle(res)
