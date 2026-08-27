import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "monologg/koelectra-small-finetuned-nsmc"

# 모듈 최상단에서 1회 로드 → 이후 모든 요청은 이 객체를 재사용한다.
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()  # 학습 모드(dropout 등 적용) 끄고 추론 전용 모드로 전환


def analyze_sentiment(text: str) -> tuple[str, float]:
    # 1) 토큰화: 한글 텍스트를 모델이 이해하는 숫자 ID로 변환
    inputs = tokenizer(
        text,
        return_tensors="pt",   # PyTorch 텐서로 반환
        truncation=True,       # 너무 긴 문장은 자름
        max_length=128,
    )

    # 2) 추론: 그래디언트 계산 끔 (학습이 아니라 예측만 하므로 메모리/속도 이득)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits  # shape: [1, 2] → [부정 logit, 긍정 logit]

    # 3) softmax로 logits을 확률로 변환 (두 값의 합 = 1)
    probs = torch.softmax(logits, dim=-1)[0]  # shape: [2] → [부정확률, 긍정확률]

    # 4) 더 높은 확률 쪽을 예측 라벨로 선택
    negative_prob = probs[0].item()
    positive_prob = probs[1].item()

    if positive_prob >= negative_prob:
        label = "긍정"
        score = positive_prob
    else:
        label = "부정"
        score = negative_prob

    return label, round(score, 4)