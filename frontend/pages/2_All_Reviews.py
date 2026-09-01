# pages/2_All_Reviews.py
import math
import streamlit as st
from api_client import get_recent_reviews, get_movie, delete_review, ApiError

st.set_page_config(page_title="전체 리뷰", page_icon="📋")
st.title("최근 리뷰")


@st.cache_data(ttl=60)
def get_movie_title(movie_id: int) -> str:
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
total_pages = max(1, math.ceil(total_reviews / PAGE_SIZE))
current_page_num = st.session_state.review_list_page + 1

col_prev, col_page, col_next = st.columns(3)
with col_prev:
    st.button("이전", disabled=st.session_state.review_list_page == 0, on_click=go_prev_review_page)
with col_page:
    st.write(f"페이지 {current_page_num} / {total_pages}")
with col_next:
    st.button("다음", disabled=current_page_num >= total_pages, on_click=go_next_review_page)