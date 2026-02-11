"""
Gemini AI 기반 콘텐츠 요약
- 마케팅 관점 2~3문장 요약
- 긍정/부정/중립 감성 분석
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def summarize_content(text: str, brand_name: str, api_key: str) -> Tuple[str, str]:
    """
    Gemini API로 콘텐츠 요약 + 감성 분석

    Args:
        text: 요약할 텍스트 (블로그 본문 또는 YouTube 자막)
        brand_name: 브랜드명
        api_key: Gemini API 키

    Returns:
        (요약문, 감성) 튜플. 예: ("스크럽대디 수세미가...", "긍정")
        실패 시: ("", "")
    """
    if not text or not api_key:
        return ("", "")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""다음은 '{brand_name}' 브랜드와 관련된 온라인 게시글 내용입니다.

마케팅 담당자 관점에서 핵심 내용을 2~3문장으로 요약해주세요.
마지막 줄에 감성을 [긍정], [부정], [중립] 중 하나로 판정해주세요.

형식:
요약: (2~3문장 요약)
감성: [긍정/부정/중립]

게시글 내용:
{text[:2000]}"""

        response = model.generate_content(prompt)
        result = response.text.strip()

        # 응답 파싱
        summary, sentiment = _parse_response(result)
        logger.info(f"Gemini 요약 완료: {sentiment} / {summary[:50]}...")
        return (summary, sentiment)

    except Exception as e:
        logger.error(f"Gemini 요약 오류: {e}")
        return ("", "")


def _parse_response(result: str) -> Tuple[str, str]:
    """Gemini 응답에서 요약문과 감성 분리"""
    summary = ""
    sentiment = "중립"

    lines = result.strip().split("\n")

    summary_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("감성:") or line.startswith("감성 :"):
            sentiment_text = line.split(":", 1)[1].strip()
            if "긍정" in sentiment_text:
                sentiment = "긍정"
            elif "부정" in sentiment_text:
                sentiment = "부정"
            else:
                sentiment = "중립"
        elif line.startswith("요약:") or line.startswith("요약 :"):
            summary_lines.append(line.split(":", 1)[1].strip())
        else:
            if not any(keyword in line for keyword in ["감성", "[긍정]", "[부정]", "[중립]"]):
                summary_lines.append(line)

    summary = " ".join(summary_lines).strip()

    if not summary:
        summary = result.replace("감성:", "").replace("[긍정]", "").replace("[부정]", "").replace("[중립]", "").strip()

    return (summary, sentiment)
