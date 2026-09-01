# pages/1_Movie_List.py
# "영화 목록" 사이드바 메뉴 전체를 담당하는 파일.
# 별도의 "등록 페이지", "상세 페이지" 파일을 따로 만들지 않고,
# session_state.view 값에 따라 "같은 페이지 안에서" 화면 내용만 바꾸는 방식으로 구현했다.
#   - view == "list"   : 영화 목록 화면 (등록 버튼 포함)
#   - view == "detail" : 선택한 영화의 상세 + 리뷰 작성/조회 화면
# (Streamlit 멀티페이지는 "사이드바 메뉴 이동"만 지원하고, "한 메뉴 안에서 화면 전환"은
#  이렇게 session_state로 직접 분기 처리해야 한다)

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

# 영화 등록/수정 폼에서 선택할 수 있는 장르 목록 (자유 입력 대신 selectbox로 오탈자 방지)
GENRE_OPTIONS = [
    "액션", "코미디", "드라마", "로맨스", "스릴러",
    "공포", "SF", "판타지", "애니메이션", "다큐멘터리", "기타",
]

# 이 파일(1_Movie_List.py)은 frontend/pages/ 안에 있으므로,
# parent(=pages/) -> parent(=frontend/) -> noimage/no-img-text.png 순으로 경로를 계산한다.
# __file__: 이 파이썬 파일 자신의 경로. resolve(): 절대경로로 변환.
NO_IMAGE_PATH = Path(__file__).resolve().parent.parent / "noimage" / "no-img-text.png"
POSTER_WIDTH = 150  # 포스터 이미지 고정 너비(px). 크기 조절은 이 숫자만 바꾸면 전체 화면에 반영됨


# ---------------------------------------------------------
# 헬퍼 함수들 (반복문/화면 함수 안에서 매번 재정의하지 않도록 파일 최상단에 한 번만 정의)
# ---------------------------------------------------------

def render_poster_placeholder():
    """포스터 URL이 없거나, 있어도 실제로 이미지를 불러올 수 없을 때 보여줄 고정 이미지."""
    st.image(str(NO_IMAGE_PATH), width=POSTER_WIDTH)


@st.cache_data(ttl=300)  # 5분(300초) 동안은 같은 URL에 대해 이 함수를 다시 실행하지 않고 캐시된 결과 재사용
def is_image_accessible(url: str, timeout: float = 2.0) -> bool:
    """
    포스터 URL이 실제로 접속 가능한 이미지인지 미리 확인한다.
    st.image()는 URL이 잘못되어도 파이썬 단에서 에러를 내지 않고
    "브라우저가 나중에" 깨진 이미지 아이콘을 보여주기 때문에, 화면이 지저분해지는 것을
    막으려면 이렇게 사전에 HEAD 요청으로 실제 접근 가능 여부를 검사해야 한다.
    """
    try:
        # HEAD 요청: 이미지 전체 데이터를 받지 않고 "존재하는지, 어떤 타입인지"만 빠르게 확인
        res = requests.head(url, timeout=timeout, allow_redirects=True)
        content_type = res.headers.get("Content-Type", "")
        return res.status_code == 200 and content_type.startswith("image/")
    except requests.RequestException:
        # 타임아웃, 연결 실패, DNS 오류 등 모든 네트워크 문제를 "접근 불가"로 간주
        return False


def render_poster(poster_url: str | None):
    """포스터를 화면에 그리되, URL이 없거나 접근 불가능하면 자동으로 placeholder 이미지로 대체."""
    if poster_url and is_image_accessible(poster_url):
        st.image(poster_url, width=POSTER_WIDTH)
    else:
        render_poster_placeholder()


@st.cache_data(ttl=30)  # 30초 동안 같은 movie_id의 평점 조회 결과를 캐시 (API 호출 횟수 절약)
def get_cached_rating(movie_id: int):
    """
    영화 목록 화면에서는 영화 개수만큼 평점 API 호출이 발생하므로(N+1 문제),
    캐싱을 걸어서 짧은 시간 안에 같은 영화를 반복 조회할 때 API를 다시 부르지 않게 한다.
    """
    return get_movie_rating(movie_id)


# ---------------------------------------------------------
# 버튼 콜백 함수들
#
# Streamlit은 버튼 클릭 시 스크립트를 처음부터 다시 실행하는데,
# "if st.button(...): 상태변경 + st.rerun()" 패턴을 쓰면
# ①클릭 감지 시점의 재실행에서 "이전" 상태로 한 번 렌더링된 후,
# ②상태 변경 + st.rerun()으로 "또" 재실행되어, 결과적으로 API가 불필요하게 두 번 호출된다.
#
# 반면 on_click=콜백함수 방식은 "스크립트가 처음부터 재실행되기 전에" 콜백이 먼저 실행되므로,
# 재실행이 시작되는 시점에는 이미 상태가 바뀌어 있어 클릭 한 번에 정확히 한 번만 반영된다.
# 그래서 아래처럼 상태만 바꾸는 단순 버튼들은 전부 on_click 콜백 방식으로 통일했다.
# (단, API 호출 결과에 따라 성공/실패를 분기해야 하는 버튼은 이 패턴이 아니라
#  기존 방식대로 try/except 안에서 명시적으로 st.rerun()을 호출한다)
# ---------------------------------------------------------

def go_prev_page():
    st.session_state.movie_list_page -= 1

def go_next_page():
    st.session_state.movie_list_page += 1

def go_to_detail(movie_id):
    """상세보기 버튼 콜백: 선택한 영화 id를 저장하고 화면을 상세 화면으로 전환"""
    st.session_state.selected_movie_id = movie_id
    st.session_state.view = "detail"

def go_to_list():
    """"← 목록으로" 버튼 콜백: 화면을 다시 목록 화면으로 전환"""
    st.session_state.view = "list"

def toggle_register_form():
    """"영화 등록" 버튼 콜백: 등록 폼을 펼치거나 접는 토글"""
    st.session_state.show_register_form = not st.session_state.show_register_form

def toggle_edit_form():
    """"수정" 버튼 콜백: 수정 폼을 펼치거나 접는 토글"""
    st.session_state.show_edit_form = not st.session_state.get("show_edit_form", False)


# ---------------------------------------------------------
# 화면 상태 초기화
# session_state는 브라우저 세션 동안 유지되는 저장소로, 여기 저장한 값은
# 버튼을 눌러 스크립트가 다시 실행돼도 사라지지 않고 그대로 유지된다.
# ---------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "list"           # 최초 진입 시 기본은 목록 화면
if "show_register_form" not in st.session_state:
    st.session_state.show_register_form = False


# ===========================================================
# 화면 1: 영화 목록 (+ 등록 버튼)
# ===========================================================
def render_list_view():
    st.title("🎬 영화 목록")

    st.button("➕ 영화 등록", on_click=toggle_register_form)

    # show_register_form이 True일 때만 등록 폼을 화면에 표시 (토글 방식)
    if st.session_state.show_register_form:
        with st.form("movie_create_form", clear_on_submit=True):
            title = st.text_input("제목 *")
            # 달력 위젯(st.date_input) 대신 텍스트 입력으로 받는 이유:
            # st.date_input은 기본 선택 가능 범위가 "오늘 기준 ±10년"으로 좁아서
            # 오래된 고전 영화의 개봉일을 입력하기 불편하기 때문. 대신 직접 형식을 검증한다.
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
                # 날짜 형식 검증: "YYYY-MM-DD" 틀에 안 맞으면 ValueError 발생 -> 사용자에게 안내
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    st.error("날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 다시 입력해주세요. (예: 1994-03-15)")
                    st.stop()   # 여기서 실행을 멈춰서, 아래 API 호출까지 진행되지 않게 함

                # 포스터 URL 정제: 사용자가 실수로 따옴표를 같이 붙여넣는 경우를 방어
                cleaned_poster_url = poster_url.strip().strip('"').strip("'") if poster_url else None
                if cleaned_poster_url and not cleaned_poster_url.startswith(("http://", "https://")):
                    st.error("포스터 URL 형식이 올바르지 않습니다. 'http://' 또는 'https://'로 시작하는 주소를 다시 입력해주세요.")
                    st.stop()

                payload = {
                    "title": title,
                    "release_date": release_date.isoformat(),   # date 객체 -> "YYYY-MM-DD" 문자열
                    "director": director,
                    "genre": genre,
                    "poster_url": cleaned_poster_url,
                }
                try:
                    create_movie(payload)
                    st.success("등록 완료!")
                    st.session_state.show_register_form = False
                    st.rerun()   # 등록 성공 여부에 따라 분기가 필요한 경우라 명시적으로 재실행
                except ApiError as e:
                    st.error(f"등록 실패: {e.detail}")

    st.divider()

    # ----- 영화 목록 페이지네이션 -----
    PAGE_SIZE = 6
    if "movie_list_page" not in st.session_state:
        st.session_state.movie_list_page = 0
    skip = st.session_state.movie_list_page * PAGE_SIZE

    try:
        # 백엔드가 {"total": 전체개수, "items": [영화들]} 형태로 응답하므로 둘 다 꺼내둔다.
        # total을 알아야 "페이지 1 / 3"처럼 정확한 총 페이지 수를 계산할 수 있다.
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
        # 영화 1개당 카드(테두리) 하나, 카드 안에서 왼쪽=포스터 / 오른쪽=정보+버튼 배치
        for movie in movies:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])   # 비율 1:3으로 좌우 분할

                with col_img:
                    render_poster(movie.get("poster_url"))

                with col_info:
                    st.subheader(movie["title"])
                    st.caption(f"감독: {movie['director']} · 장르: {movie['genre']}")
                    st.caption(f"개봉일: {movie['release_date']}")

                    # 목록에서도 평균 평점을 바로 보여줌 (캐싱된 함수를 사용해 API 호출 절약)
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

                    # key를 movie id 기반으로 고유하게 지정해야, 여러 영화 카드에 버튼이 있어도
                    # Streamlit이 각 버튼을 서로 다른 위젯으로 구분할 수 있다.
                    st.button(
                        "상세보기",
                        key=f"detail_{movie['id']}",
                        on_click=go_to_detail,
                        args=(movie["id"],),   # go_to_detail(movie["id"]) 형태로 호출됨
                    )

    st.divider()
    # 전체 개수(total_movies)를 이용해 정확한 총 페이지 수 계산.
    # math.ceil: 올림 처리 (예: 13개, 페이지당 6개면 13/6=2.17 -> 올림해서 3페이지)
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
        return   # 영화 정보를 못 가져오면 이후 코드(리뷰 등)를 실행할 이유가 없으므로 함수 종료

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

        # --- 수정 / 삭제 버튼을 나란히 배치 ---
        col_edit, col_delete = st.columns(2)
        with col_edit:
            st.button("수정", on_click=toggle_edit_form)
        with col_delete:
            # 삭제는 API 호출 성공/실패에 따라 다른 처리(성공 시 목록으로 이동)가 필요하므로
            # on_click 콜백이 아니라 기존 if 문 + 명시적 rerun() 방식을 유지한다.
            if st.button("삭제"):
                try:
                    delete_movie(movie_id)
                    st.success("삭제되었습니다.")
                    st.session_state.view = "list"
                    st.rerun()
                except ApiError as e:
                    st.error(f"삭제 실패: {e.detail}")

        # --- 수정 폼: show_edit_form이 True일 때만 표시 ---
        if st.session_state.get("show_edit_form", False):
            with st.form("movie_edit_form"):
                # value=에 기존 값을 넣어서, 폼이 열렸을 때 완전히 빈 칸이 아니라
                # "현재 값이 이미 채워진 채로" 보이게 함 (사용자는 바꿀 부분만 고치면 됨)
                edit_title = st.text_input("제목", value=movie["title"])
                edit_release_date_str = st.text_input(
                    "개봉일 (YYYY-MM-DD)", value=movie["release_date"]
                )
                edit_director = st.text_input("감독", value=movie["director"])

                # selectbox는 value가 아니라 index(몇 번째 항목을 기본 선택할지)로 지정한다.
                # 기존 장르가 목록에 없는 경우(DB에 직접 입력된 값 등)를 대비해 "기타"로 폴백.
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
                # st.spinner: 감성분석 모델 추론에 약간의 시간이 걸리므로, 그동안
                # 사용자에게 "처리 중"임을 시각적으로 알려주는 로딩 표시
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
# 실제 분기: session_state.view 값에 따라 위에서 만든 함수 중 하나만 실행
# 이 부분이 이 파일 전체의 "라우팅" 역할을 한다.
# ===========================================================
if st.session_state.view == "detail" and st.session_state.get("selected_movie_id"):
    render_detail_view()
else:
    render_list_view()
