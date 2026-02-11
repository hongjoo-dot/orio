"""
YouTube 영상 자막(Transcript) 추출
- 한국어 자막 우선, 영어/자동생성 fallback
- 자막 없으면 영상 description 사용
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_transcript(video_url: str, description: str = "", max_length: int = 2000) -> str:
    """
    YouTube 영상에서 자막 텍스트 추출

    Args:
        video_url: YouTube 영상 URL
        description: 영상 설명 (자막 없을 때 fallback)
        max_length: 반환할 최대 문자 수

    Returns:
        자막 텍스트 (실패 시 description fallback)
    """
    video_id = _extract_video_id(video_url)
    if not video_id:
        logger.warning(f"비디오 ID 추출 실패: {video_url}")
        return description[:max_length] if description else ""

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # 한국어 → 영어 → 자동생성 순으로 시도
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = _find_best_transcript(transcript_list)
        if not transcript:
            logger.info(f"자막 없음, description fallback: {video_id}")
            return description[:max_length] if description else ""

        # 자막 텍스트 합치기
        entries = transcript.fetch()
        text = " ".join([entry.text for entry in entries])

        # 공백 정리 및 길이 제한
        text = re.sub(r'\s+', ' ', text).strip()
        logger.info(f"YouTube 자막 추출 성공: {video_id} ({len(text)}자)")
        return text[:max_length]

    except Exception as e:
        logger.error(f"YouTube 자막 추출 오류 ({video_id}): {e}")
        return description[:max_length] if description else ""


def _extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 비디오 ID 추출"""
    patterns = [
        r'(?:v=|/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _find_best_transcript(transcript_list):
    """최적의 자막 트랙 선택"""
    # 1. 수동 한국어 자막
    try:
        return transcript_list.find_transcript(['ko'])
    except Exception:
        pass

    # 2. 수동 영어 자막
    try:
        return transcript_list.find_transcript(['en'])
    except Exception:
        pass

    # 3. 자동 생성 자막 (어떤 언어든)
    try:
        for transcript in transcript_list:
            if transcript.is_generated:
                return transcript
    except Exception:
        pass

    return None
