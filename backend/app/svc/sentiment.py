# app/svc/sentiment.py
import os

SENTIMENT_ENABLED = os.getenv("SENTIMENT_ENABLED", "true").lower() == "true"
MODEL_NAME = "monologg/koelectra-small-finetuned-nsmc"

if SENTIMENT_ENABLED:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
else:
    print("⚠️ SENTIMENT_ENABLED=false: 감성분석 기능 비활성화 상태로 실행")


def analyze_sentiment(text: str) -> tuple[str, float]:
    if not SENTIMENT_ENABLED:
        return "미실행", 0.0

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=-1)[0]

    negative_prob = probs[0].item()
    positive_prob = probs[1].item()

    if positive_prob >= negative_prob:
        label, score = "긍정", positive_prob
    else:
        label, score = "부정", negative_prob

    return label, round(score, 4)