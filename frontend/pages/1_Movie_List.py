# pages/1_Movie_List.py
import streamlit as st
import requests
import math

from datetime import datetime
from pathlib import Path
from api_client import (
    get_movies, create_movie, get_movie, update_movie, delete_movie,
    get_reviews_by_movie, create_review, delete_review,
    get_movie_rating, ApiError,
)

st.set_page_config(page_title="영화 목록", page_icon="🎬")

GENRE_OPTIONS = [
    "액션", "코미디", "드라마", "로맨스", "스릴러",
    "공포", "SF", "판타지", "애니메이션", "다큐멘터리", "기타",
]

NO_IMAGE_PATH = Path(__file__).resolve().parent.parent / "noimage" / "no-img-text.png"
POSTER_WIDTH = 150


def render_poster_placeholder():
    st.image(str(NO_IMAGE_PATH), width=POSTER_WIDTH)


@st.cache_data(ttl=300)
def is_image_accessible(url: str, timeout: float = 2.0) -> bool:
    try:
        res = requests.head(url, timeout=timeout, allow_redirects=True)
        content_type = res.headers.get("Content-Type", "")
        return res.status_code == 200 and content_type.startswith("image/")
    except requests.RequestException:
        return False


def render_poster(poster_url: str | None):
    if poster_url and is_image_accessible(poster_url):
        st.image(poster_url, width=POSTER_WIDTH)
    else:
        render_poster_placeholder()


@st.cache_data(ttl=30)
def get_cached_rating(movie_id: int):
    return get_movie_rating(movie_id)


# ---------------------------------------------------------
# 버튼 콜백 함수들 (반복문/화면 함수 안에서 재정의하지 않도록 파일 최상단에 한 번만 정의)
# ---------------------------------------------------------
def go_prev_page():
    st.session_state.movie_list_page -= 1

def go_next_page():
    st.session_state.movie_list_page += 1

def go_to_detail(movie_id):
    st.session_state.selected_movie_id = movie_id
    st.session_state.view = "detail"

def go_to_list():
    st.session_state.view = "list"

def toggle_register_form():
    st.session_state.show_register_form = not st.session_state.show_register_form

def toggle_edit_form():
    st.session_state.show_edit_form = not st.session_state.get("show_edit_form", False)


# ---------------------------------------------------------
# 화면 상태 초기화
# ---------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "list"
if "show_register_form" not in st.session_state:
    st.session_state.show_register_form = False


# ===========================================================
# 화면 1: 영화 목록 (+ 등록 버튼)
# ===========================================================
def render_list_view():
    st.title("🎬 영화 목록")

    st.button("➕ 영화 등록", on_click=toggle_register_form)

    if st.session_state.show_register_form:
        with st.form("movie_create_form", clear_on_submit=True):
            title = st.text_input("제목 *")
            release_date_str = st.text_input(
                "개봉일 * (YYYY-MM-DD 형식으로 입력)",
                placeholder="예: 1994-03-15",
            )
            director = st.text_input("감독 *")
            genre = st.selectbox("장르 *", options=GENRE_OPTIONS)
            poster_url = st.text_input("포스터 URL (선택)", placeholder="https://example.com/poster.jpg")
            submitted = st.form_submit_button("등록")

        if submitted:
            if not title or not director or not release_date_str:
                st.warning("제목, 개봉일, 감독은 필수입니다.")
            else:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    st.error("날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 다시 입력해주세요. (예: 1994-03-15)")
                    st.stop()

                cleaned_poster_url = poster_url.strip().strip('"').strip("'") if poster_url else None
                if cleaned_poster_url and not cleaned_poster_url.startswith(("http://", "https://")):
                    st.error("포스터 URL 형식이 올바르지 않습니다. 'http://' 또는 'https://'로 시작하는 주소를 다시 입력해주세요.")
                    st.stop()

                payload = {
                    "title": title,
                    "release_date": release_date.isoformat(),
                    "director": director,
                    "genre": genre,
                    "poster_url": cleaned_poster_url,
                }
                try:
                    create_movie(payload)
                    st.success("등록 완료!")
                    st.session_state.show_register_form = False
                    st.rerun()
                except ApiError as e:
                    st.error(f"등록 실패: {e.detail}")

    st.divider()

    PAGE_SIZE = 6
    if "movie_list_page" not in st.session_state:
        st.session_state.movie_list_page = 0
    skip = st.session_state.movie_list_page * PAGE_SIZE

    try:
        response = get_movies(skip=skip, limit=PAGE_SIZE)
        movies = response["items"]
        total_movies = response["total"]
    except ApiError as e:
        if e.status_code == 404:
            st.info("등록된 영화가 없습니다.")
        else:
            st.error(f"영화 목록을 불러오지 못했습니다: {e.detail}")
        movies = []
        total_movies = 0

    if not movies:
        st.info("등록한 영화가 없습니다.")
    else:
        for movie in movies:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])

                with col_img:
                    render_poster(movie.get("poster_url"))

                with col_info:
                    st.subheader(movie["title"])
                    st.caption(f"감독: {movie['director']} · 장르: {movie['genre']}")
                    st.caption(f"개봉일: {movie['release_date']}")

                    try:
                        rating = get_cached_rating(movie["id"])
                        avg = rating.get("average_rating")
                        count = rating.get("review_count", 0)
                        if avg is not None:
                            st.caption(f"⭐ {avg:.2f} / 5.0  (리뷰 {count}개)")
                        else:
                            st.caption("⭐ 아직 리뷰 없음")
                    except ApiError:
                        st.caption("⭐ 아직 리뷰 없음")

                    st.button(
                        "상세보기",
                        key=f"detail_{movie['id']}",
                        on_click=go_to_detail,
                        args=(movie["id"],),
                    )

    st.divider()
    total_pages = max(1, math.ceil(total_movies / PAGE_SIZE))
    current_page_num = st.session_state.movie_list_page + 1

    col_prev, col_page, col_next = st.columns(3)
    with col_prev:
        st.button("이전", disabled=st.session_state.movie_list_page == 0, on_click=go_prev_page)
    with col_page:
        st.write(f"페이지 {current_page_num} / {total_pages}")
    with col_next:
        st.button("다음", disabled=current_page_num >= total_pages, on_click=go_next_page)


# ===========================================================
# 화면 2: 영화 상세 + 리뷰
# ===========================================================
def render_detail_view():
    movie_id = st.session_state.get("selected_movie_id")

    st.button("← 목록으로", on_click=go_to_list)

    try:
        movie = get_movie(movie_id)
    except ApiError as e:
        st.error(f"영화 정보를 불러오지 못했습니다: {e.detail}")
        return

    col_img, col_info = st.columns([1, 2])
    with col_img:
        render_poster(movie.get("poster_url"))

    with col_info:
        st.title(movie["title"])
        st.write(f"**감독**: {movie['director']}  \n**장르**: {movie['genre']}  \n**개봉일**: {movie['release_date']}")

        try:
            rating = get_cached_rating(movie_id)
            avg = rating.get("average_rating")
            count = rating.get("review_count", 0)
            if avg is not None:
                st.metric("평균 평점", f"⭐ {avg:.2f} / 5.0", help=f"리뷰 {count}개 기준")
            else:
                st.caption("아직 리뷰가 없어 평점을 계산할 수 없습니다.")
        except ApiError:
            st.caption("아직 리뷰가 없어 평점을 계산할 수 없습니다.")

        col_edit, col_delete = st.columns(2)
        with col_edit:
            st.button("수정", on_click=toggle_edit_form)
        with col_delete:
            if st.button("삭제"):
                try:
                    delete_movie(movie_id)
                    st.success("삭제되었습니다.")
                    st.session_state.view = "list"
                    st.rerun()
                except ApiError as e:
                    st.error(f"삭제 실패: {e.detail}")

        if st.session_state.get("show_edit_form", False):
            with st.form("movie_edit_form"):
                edit_title = st.text_input("제목", value=movie["title"])
                edit_release_date_str = st.text_input(
                    "개봉일 (YYYY-MM-DD)", value=movie["release_date"]
                )
                edit_director = st.text_input("감독", value=movie["director"])

                current_genre = movie["genre"]
                genre_index = GENRE_OPTIONS.index(current_genre) if current_genre in GENRE_OPTIONS else len(GENRE_OPTIONS) - 1
                edit_genre = st.selectbox("장르", options=GENRE_OPTIONS, index=genre_index)

                edit_poster_url = st.text_input("포스터 URL", value=movie.get("poster_url") or "")

                edit_submitted = st.form_submit_button("저장")

            if edit_submitted:
                try:
                    parsed_date = datetime.strptime(edit_release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    st.error("날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 다시 입력해주세요.")
                    st.stop()

                cleaned_poster_url = edit_poster_url.strip().strip('"').strip("'") if edit_poster_url else None
                if cleaned_poster_url and not cleaned_poster_url.startswith(("http://", "https://")):
                    st.error("포스터 URL 형식이 올바르지 않습니다. 'http://' 또는 'https://'로 시작해야 합니다.")
                    st.stop()

                update_payload = {
                    "title": edit_title,
                    "release_date": parsed_date.isoformat(),
                    "director": edit_director,
                    "genre": edit_genre,
                    "poster_url": cleaned_poster_url,
                }
                try:
                    update_movie(movie_id, update_payload)
                    st.success("수정 완료!")
                    st.session_state.show_edit_form = False
                    st.rerun()
                except ApiError as e:
                    st.error(f"수정 실패: {e.detail}")

    st.divider()
    st.subheader("리뷰 작성")
    with st.form("review_form", clear_on_submit=True):
        author = st.text_input("작성자")
        content = st.text_area("리뷰 내용")
        submitted = st.form_submit_button("등록 (자동 감성분석)")

    if submitted:
        if not author or not content:
            st.warning("작성자와 내용을 모두 입력해주세요.")
        else:
            try:
                with st.spinner("감성분석 진행 중..."):
                    review = create_review({"movie_id": movie_id, "author": author, "content": content})
                st.success(f"등록 완료 (감성: {review.get('sentiment_label')})")
                st.rerun()
            except ApiError as e:
                st.error(f"리뷰 등록 실패: {e.detail}")

    st.divider()
    st.subheader("리뷰 목록")
    try:
        reviews = get_reviews_by_movie(movie_id)
    except ApiError as e:
        st.error(f"리뷰를 불러오지 못했습니다: {e.detail}")
        reviews = []

    if not reviews:
        st.info("아직 등록된 리뷰가 없습니다.")
    else:
        for review in reviews:
            with st.container(border=True):
                st.write(f"**{review['author']}**")
                st.write(review["content"])
                if st.button("삭제", key=f"del_review_{review['id']}"):
                    try:
                        delete_review(review["id"])
                        st.rerun()
                    except ApiError as e:
                        st.error(f"삭제 실패: {e.detail}")


# ===========================================================
# 실제 분기
# ===========================================================
if st.session_state.view == "detail" and st.session_state.get("selected_movie_id"):
    render_detail_view()
else:
    render_list_view()