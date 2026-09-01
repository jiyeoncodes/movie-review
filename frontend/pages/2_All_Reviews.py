# pages/2_All_Reviews.py
# "All Reviews" 사이드바 메뉴. 영화 구분 없이 최근에 등록된 리뷰들을 모아서 보여준다.

import math
import streamlit as st
from api_client import get_recent_reviews, get_movie, delete_review, ApiError

st.set_page_config(page_title="전체 리뷰", page_icon="📋")
st.title("최근 리뷰")


@st.cache_data(ttl=60)  # 60초 동안 같은 movie_id의 제목 조회 결과를 캐시 (API 호출 절약)
def get_movie_title(movie_id: int) -> str:
    """
    리뷰 목록에는 movie_id만 들어있으므로, 화면에 영화 제목을 보여주기 위해
    별도로 영화 정보를 조회한다. 영화가 이미 삭제된 경우(soft delete)에도
    화면이 깨지지 않도록 예외 처리해서 안내 문구로 대체한다.
    """
    try:
        movie = get_movie(movie_id)
        return movie["title"]
    except ApiError:
        return f"(삭제된 영화, id={movie_id})"


def go_prev_review_page():
    st.session_state.review_list_page -= 1

def go_next_review_page():
    st.session_state.review_list_page += 1


PAGE_SIZE = 10
if "review_list_page" not in st.session_state:
    st.session_state.review_list_page = 0

skip = st.session_state.review_list_page * PAGE_SIZE

try:
    # 백엔드가 {"total": 전체개수, "items": [리뷰들]} 형태로 응답
    response = get_recent_reviews(skip=skip, limit=PAGE_SIZE)
    reviews = response["items"]
    total_reviews = response["total"]
except ApiError as e:
    st.error(f"리뷰를 불러오지 못했습니다: {e.detail}")
    reviews = []
    total_reviews = 0

if not reviews:
    st.info("등록한 리뷰가 없습니다.")
else:
    for review in reviews:
        with st.container(border=True):
            movie_title = get_movie_title(review["movie_id"])
            # 가이드라인 요구사항(영화 ID 표시)과 가독성(영화 제목 표시)을 모두 만족시키기 위해
            # 제목과 ID를 함께 노출한다.
            st.write(f"**영화**: {movie_title} (영화ID: {review['movie_id']})")
            st.write(f"**리뷰 작성자**: {review['author']}")
            st.write(f"**등록일**: {review['created_at'].replace('T', ' ')}")
            st.write(f"**리뷰내용**: {review['content']}")

            label, score = review.get("sentiment_label"), review.get("sentiment_score")
            if label is not None:
                sentiment_text = f"**감성**: {label}" + (f" ({score:.2f})" if score is not None else "")
                st.write(sentiment_text)

            if st.button("삭제", key=f"del_{review['id']}"):
                try:
                    delete_review(review["id"])
                    st.rerun()
                except ApiError as e:
                    st.error(f"삭제 실패: {e.detail}")

st.divider()
# 전체 개수(total_reviews)를 이용해 정확한 총 페이지 수 계산
total_pages = max(1, math.ceil(total_reviews / PAGE_SIZE))
current_page_num = st.session_state.review_list_page + 1

col_prev, col_page, col_next = st.columns(3)
with col_prev:
    st.button(
        "이전",
        disabled=st.session_state.review_list_page == 0,
        on_click=go_prev_review_page,
    )
with col_page:
    st.write(f"페이지 {current_page_num} / {total_pages}")
with col_next:
    st.button(
        "다음",
        disabled=current_page_num >= total_pages,
        on_click=go_next_review_page,
    )
