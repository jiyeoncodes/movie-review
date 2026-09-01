# Home.py
# streamlit run Home.py 로 실행하는 진입점.
import streamlit as st

st.set_page_config(page_title="영화 플랫폼", page_icon="🎬", layout="wide")

st.title("🎬 영화 정보 · 리뷰 · 감성분석 플랫폼")
st.write(
    """
    왼쪽 사이드바에서 페이지를 선택하세요.

    - **Movie List**: 등록된 영화 목록을 확인하고, 영화 등록도 이 화면에서 바로 할 수 있습니다.
      목록에서 영화를 선택하면 같은 화면 안에서 상세 정보, 평균 평점, 리뷰 작성/조회로 전환됩니다.
    - **All Reviews**: 모든 영화에 달린 최근 리뷰를 한눈에 모아볼 수 있습니다.
    """
)