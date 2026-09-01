# 🎬 Movie Platform

영화 정보 등록/조회와 리뷰 작성, 그리고 AI 감성분석을 결합한 풀스택 웹 서비스입니다.
FastAPI 백엔드와 Streamlit 프론트엔드로 구성되어 있으며, 리뷰 작성 시 한국어 감성분석 모델(KoELECTRA)이 자동으로 긍정/부정을 판별하고 그 결과를 평균 평점으로 환산해 보여줍니다.

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [기술 스택](#기술-스택)
- [폴더 구조](#폴더-구조)
- [ERD](#erd)
- [주요 기능](#주요-기능)
- [API 명세](#api-명세)
- [감성분석 모델](#감성분석-모델)
- [빠른 시작](#빠른-시작)
- [배포](#배포)

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 서비스명 | Movie Platform |
| 목적 | 영화 정보 관리 + 리뷰 작성 + AI 기반 감성분석/평점 제공 |
| 배포 링크 | (배포 후 URL 추가 예정) |

## 기술 스택

**백엔드**
- FastAPI
- SQLAlchemy (비동기, `AsyncSession`)
- SQLite + aiosqlite
- Pydantic v2

**프론트엔드**
- Streamlit (멀티페이지, `pages/` 폴더 방식)

**감성분석**
- `monologg/koelectra-small-finetuned-nsmc` (Hugging Face `transformers`, PyTorch)

**패키지 관리**
- `uv` — 백엔드/프론트엔드 각각 독립 프로젝트로 분리 관리

**배포**
- 백엔드: (Render 등)
- 프론트엔드: Streamlit Cloud

## 폴더 구조

```
movie-review/
├── backend/                    # FastAPI 백엔드 (독립 uv 프로젝트)
│   ├── app/
│   │   ├── main.py             # FastAPI 앱 생성 + 라우터 등록
│   │   ├── common/
│   │   │   └── database.py     # engine, get_db, 환경변수 로드
│   │   ├── schema/
│   │   │   ├── db_schemas.py   # SQLAlchemy 모델 (Movie, Review)
│   │   │   └── schemas.py      # Pydantic 스키마 (요청/응답 검증)
│   │   ├── query/
│   │   │   ├── movies_query.py # 영화 DB 접근 (단순 CRUD)
│   │   │   └── reviews_query.py# 리뷰 DB 접근 (단순 CRUD)
│   │   ├── svc/
│   │   │   ├── sentiment.py    # KoELECTRA 감성분석
│   │   │   └── reviews_svc.py  # 감성분석 + 저장 조합 로직
│   │   └── routers/
│   │       ├── movies.py       # 영화 API (query 직접 호출)
│   │       └── reviews.py      # 리뷰 API (svc 경유)
│   └── scripts/
│       └── init_db.py          # 테이블 생성 스크립트
│
└── frontend/                    # Streamlit 프론트엔드 (독립 uv 프로젝트)
    ├── Home.py                 # 진입점 (streamlit run Home.py)
    ├── api_client.py           # 백엔드 REST API 호출 모듈
    └── pages/
        ├── 1_Movie_List.py     # 영화 목록 + 등록 + 상세 + 리뷰
        └── 2_All_Reviews.py    # 전체 리뷰 목록
```

## ERD

**movies (1) : reviews (N)**

### movies

| 논리명 | 물리명 | 타입 | 비고 |
|---|---|---|---|
| 영화ID | id | INTEGER | PK, AUTOINCREMENT |
| 제목 | title | VARCHAR | NOT NULL |
| 개봉일 | release_date | DATE | NOT NULL |
| 감독 | director | VARCHAR | NOT NULL |
| 장르 | genre | VARCHAR | NOT NULL |
| 포스터URL | poster_url | VARCHAR | NULL 허용 |
| 생성일시 | created_at | DATETIME | 기본값 현재시각 |
| 수정일시 | updated_at | DATETIME | onupdate 자동갱신 |
| 삭제여부 | is_deleted | CHAR(1) | 기본값 'N' (Soft Delete) |

### reviews

| 논리명 | 물리명 | 타입 | 비고 |
|---|---|---|---|
| 리뷰ID | id | INTEGER | PK, AUTOINCREMENT |
| 영화ID | movie_id | INTEGER | FK(movies.id) |
| 작성자 | author | VARCHAR | NOT NULL |
| 리뷰내용 | content | TEXT | NOT NULL |
| 감성라벨 | sentiment_label | VARCHAR | NULL 허용 (긍정/부정) |
| 감성점수 | sentiment_score | FLOAT | NULL 허용 |
| 생성일시 | created_at | DATETIME | 기본값 현재시각 |
| 수정일시 | updated_at | DATETIME | 삭제 시각 갱신용 |
| 삭제여부 | is_deleted | CHAR(1) | 기본값 'N' (Soft Delete) |

> 영화가 삭제되면 해당 영화에 달린 리뷰도 함께 Delete 처리됩니다 (cascade).

## 주요 기능

### 영화
- 등록 / 전체 조회 (페이지네이션) / 특정 조회 / 부분 수정 / 삭제 (Soft Delete)
- 포스터 이미지 표시 (접근 불가 시 기본 이미지로 대체)

### 리뷰
- 등록 시 KoELECTRA 모델이 자동으로 감성분석 실행 (긍정/부정 + 확률)
- 특정 영화의 리뷰 전체 조회 / 최근 리뷰 조회 (페이지네이션) / 단건 조회 / 삭제
- 영화별 평균 평점 조회 (감성분석 점수를 5점 만점으로 환산)

### 프론트엔드
- 영화 목록: 제목, 포스터, 감독/장르/개봉일, 평균 평점 표시
- 영화 등록/수정: 폼 기반 입력, 날짜 형식 검증
- 영화 상세: 정보 + 평균 평점 + 리뷰 작성/조회
- 전체 리뷰 모아보기: 영화명, 작성자, 등록일, 내용, 감성분석 결과

## API 명세

### 영화 (`/movies`)

| 기능 | 메서드 | 경로 |
|---|---|---|
| 등록 | POST | `/movies` |
| 전체조회 (페이지네이션) | GET | `/movies` |
| 단건조회 | GET | `/movies/{movie_id}` |
| 수정 (부분) | PATCH | `/movies/{movie_id}` |
| 삭제 (soft) | DELETE | `/movies/{movie_id}` |

### 리뷰 (`/reviews`)

| 기능 | 메서드 | 경로 |
|---|---|---|
| 등록 (감성분석 자동실행) | POST | `/reviews` |
| 최근 N개 조회 (페이지네이션) | GET | `/reviews` |
| 특정영화 리뷰 전체조회 | GET | `/reviews/movie/{movie_id}` |
| 영화 평균평점 조회 | GET | `/reviews/movie/{movie_id}/rating` |
| 단건조회 | GET | `/reviews/{review_id}` |
| 삭제 (soft) | DELETE | `/reviews/{review_id}` |

> 전체 API 문서는 백엔드 서버 실행 후 `/docs` (Swagger UI)에서 확인할 수 있습니다.

## 감성분석 모델

**채택 모델**: `monologg/koelectra-small-finetuned-nsmc`

| 비교 항목 | Small-v3 | Base-v3 |
|---|---|---|
| NSMC 정확도 | 89.36% | 90.63% |
| 모델 크기 | 53M | 423~431M |

정확도 손실은 1%p대로 미미한 반면, 모델 크기는 8배 이상 차이가 나기 때문에 경량화 관점에서 Small 모델을 채택했습니다. 라벨은 0(부정)/1(긍정)이며, 소프트맥스를 통해 확률로 변환하여 저장합니다.

## 빠른 시작

### 사전 준비
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 설치

### 백엔드 실행

```bash
cd backend
uv sync
uv run python scripts/init_db.py   # 테이블 생성
uv run uvicorn app.main:app --reload
```

백엔드는 `http://localhost:8000`에서 실행되며, `http://localhost:8000/docs`에서 API 문서를 확인할 수 있습니다.

### 프론트엔드 실행

```bash
cd frontend
uv sync
uv run streamlit run Home.py
```

프론트엔드는 `http://localhost:8501`에서 실행됩니다.

> 백엔드와 프론트엔드는 각각 독립된 `uv` 프로젝트이므로, 두 터미널에서 각각 실행해야 합니다.

## 배포

| 구성 요소 | 배포 플랫폼 | URL |
|---|---|---|
| 백엔드 (FastAPI) | Render | (배포 후 추가 예정) |
| 프론트엔드 (Streamlit) | Streamlit Cloud | (배포 후 추가 예정) |

---

## 설계 원칙

- **함수 기반 코드 스타일**: FastAPI 생태계 관례에 따라 클래스 기반(CBV) 대신 함수 기반으로 통일
- **Delete 패턴**: 실제 삭제 대신 `is_deleted` 컬럼(`'N'`/`'Y'`)으로 관리
- **감사 컬럼**: 모든 테이블에 `created_at`, `updated_at` 포함
- **비동기 우선**: DB 접근, API 엔드포인트 모두 `async`/`await` 사용
- **REST 원칙 준수**: URL에 동사를 넣지 않고 HTTP 메서드로 동작을 표현
- **svc 계층은 필요할 때만**: 여러 로직을 조합하는 경우에만 svc 사용 (예: 리뷰 등록 = 감성분석 + 저장 조합)
- **환경변수 분리**: DB URL, API 키 등은 하드코딩 금지, `.env`는 `.gitignore`에 포함