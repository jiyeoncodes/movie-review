# Home.py
# Streamlit 멀티페이지 앱의 진입점. `streamlit run Home.py`로 실행한다.
# 이 파일 자체는 화면에 안내 문구만 보여주고, 실제 기능은 pages/ 폴더의 각 파일이 담당한다.
# (사이드바에 "Movie List", "All Reviews" 메뉴가 자동으로 생기는 이유는
#  Streamlit이 pages/ 폴더 안 파일들을 자동으로 인식해서 메뉴로 만들어주기 때문)

import streamlit as st

# 브라우저 탭 제목, 아이콘, 레이아웃(wide=넓게)을 설정. 반드시 다른 st.* 호출보다 먼저 와야 함.
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
