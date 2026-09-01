# app/svc/sentiment.py
# KoELECTRA 기반 한국어 감성분석 모듈.
# 모델은 이 파일이 "처음 import될 때 딱 1번만" 로드되고, 이후 모든 요청은 이미 로드된
# tokenizer/model 객체를 재사용한다 (요청마다 다시 로드하면 매번 몇 초씩 걸려서 비효율적).

import os

# 감성분석 기능을 켜고 끄는 환경변수 스위치.
# 개발 환경에서 torch 로딩이 어려운 상황(예: 특정 보안 프로그램이 torch DLL을 차단하는 경우)에
# 감성분석만 잠시 꺼두고 나머지 API(영화 CRUD 등) 개발을 계속 진행할 수 있게 하기 위한 장치.
SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "true").lower() == "true"

# 채택 모델: monologg/koelectra-small-finetuned-nsmc
# 채택 근거: KoELECTRA Base-v3(NSMC 정확도 90.63%) 대비 Small-v3는 89.36%로 정확도 손실이
# 1%p대로 미미한 반면, 모델 크기는 53M vs 423~431M으로 8배 이상 차이가 나서
# 경량화 관점에서 Small 모델을 채택했다.
MODEL_NAME = "monologg/koelectra-small-finetuned-nsmc"

if SENTIMENT_ENABLED:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    # 토크나이저: 텍스트를 모델이 이해하는 숫자 ID로 변환하는 도구
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    # 실제 감성분류 모델 (2개 클래스: 0=부정, 1=긍정)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    # eval(): 학습 모드가 아닌 추론(예측) 전용 모드로 전환.
    # 학습 때만 필요한 dropout 등의 동작을 끄고, 항상 같은 입력에 같은 결과가 나오게 한다.
    model.eval()
else:
    print("⚠️ SENTIMENT_ENABLED=false: 감성분석 기능 비활성화 상태로 실행")


def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    입력 텍스트(리뷰 본문)의 감성을 분석해서 (라벨, 점수)를 반환한다.
    - 라벨: "긍정" 또는 "부정"
    - 점수: 그 라벨이 맞다고 모델이 확신하는 확률 (0~1 사이, 1에 가까울수록 확신 높음)
    SENTIMENT_ENABLED=false 이면 모델을 아예 로드하지 않으므로, 더미 값을 즉시 반환한다.
    """
    if not SENTIMENT_ENABLED:
        return "미실행", 0.0

    # 1) 토큰화: 한글 텍스트를 모델이 이해하는 숫자 ID 시퀀스로 변환
    inputs = tokenizer(
        text,
        return_tensors="pt",   # PyTorch 텐서 형태로 반환
        truncation=True,        # 모델이 처리 가능한 길이를 넘으면 뒷부분을 자름
        max_length=128,          # 최대 토큰 길이 (리뷰 한 개 분량으로 충분한 길이)
    )

    # 2) 추론(예측) 실행. torch.no_grad(): 학습에 필요한 그래디언트 계산을 꺼서
    #    메모리를 아끼고 속도를 높인다 (우리는 학습이 아니라 예측만 하므로 불필요).
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits  # 모델의 원본 출력값. shape: [1, 2] -> [부정 점수, 긍정 점수] (정규화 전)

    # 3) softmax로 logits을 "합이 1이 되는 확률"로 변환.
    #    probs[0] = 부정일 확률, probs[1] = 긍정일 확률
    probs = torch.softmax(logits, dim=-1)[0]

    negative_prob = probs[0].item()  # 텐서 값을 순수 파이썬 float으로 변환
    positive_prob = probs[1].item()

    # 4) 둘 중 더 높은 확률 쪽을 최종 예측 라벨로 채택
    if positive_prob >= negative_prob:
        label, score = "긍정", positive_prob
    else:
        label, score = "부정", negative_prob

    return label, round(score, 4)
