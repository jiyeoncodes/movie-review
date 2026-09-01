# app/svc/sentiment.py
# KoELECTRA 기반 한국어 감성분석 모듈.

import os

SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "true").lower() == "true"
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
    print("SENTIMENT_ENABLED=false: 감성분석 기능 비활성화 상태로 실행")


def analyze_sentiment(text: str) -> tuple[str, float]:
    # SENTIMENT_ENABLED=false 이면 모델을 아예 로드하지 않으므로, 더미 값을 즉시 반환한다.

    if not SENTIMENT_ENABLED:
        return "미실행", 0.0

    inputs = tokenizer(
        text,
        return_tensors="pt",   # PyTorch 텐서 형태로 반환
        truncation=True,        # 모델이 처리 가능한 길이를 넘으면 뒷부분을 자름
        max_length=128,          # 최대 토큰 길이 (리뷰 한 개 분량으로 충분한 길이)
    )

    # 추론(예측) 실행
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits  # 모델의 원본 출력값. shape: [1, 2] -> [부정 점수, 긍정 점수] (정규화 전)

    # softmax로 logits을 "합이 1이 되는 확률"로 변환.
    #    probs[0] = 부정일 확률, probs[1] = 긍정일 확률
    probs = torch.softmax(logits, dim=-1)[0]

    negative_prob = probs[0].item()  # 텐서 값을 순수 파이썬 float으로 변환
    positive_prob = probs[1].item()

    # 둘 중 더 높은 확률 쪽을 최종 예측 라벨로 채택
    if positive_prob >= negative_prob:
        label, score = "긍정", positive_prob
    else:
        label, score = "부정", negative_prob

    return label, round(score, 4)
