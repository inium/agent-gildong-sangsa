from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CurrentTimeInput(BaseModel):
    country: str = Field(
        default="한국",
        description=(
            "변환할 국가 시간입니다. 한글 및 영문 국가명 또는 IANA 시간대 입니다."
            "예: [한국, 일본, 중국, 싱가포르, 'kr', 'jp', 'cn', 'sg', Asia/Seoul, America/New_York]"
            "기본값은 한국 입니다."
        ),
    )


@tool("get_current_time", args_schema=CurrentTimeInput)
def get_current_time(country: str = "한국") -> str:
    """지정한 국가의 현재 날짜와 시간을 반환합니다. 기본값은 한국입니다.

    country에는 한국/KR, 일본/JP, 중국/CN, 인도/IN 등의 국가명 또는
    IANA 시간대(예: Asia/Seoul, America/New_York)를 전달합니다.
    미국 등 시간대가 여러 개인 국가는 IANA 시간대로 지역을 지정하세요.
    """
    timezones = {
        "한국": "Asia/Seoul",
        "대한민국": "Asia/Seoul",
        "kr": "Asia/Seoul",
        "south korea": "Asia/Seoul",
        "일본": "Asia/Tokyo",
        "jp": "Asia/Tokyo",
        "japan": "Asia/Tokyo",
        "중국": "Asia/Shanghai",
        "cn": "Asia/Shanghai",
        "china": "Asia/Shanghai",
        "인도": "Asia/Kolkata",
        "in": "Asia/Kolkata",
        "india": "Asia/Kolkata",
        "영국": "Europe/London",
        "gb": "Europe/London",
        "uk": "Europe/London",
        "united kingdom": "Europe/London",
        "독일": "Europe/Berlin",
        "de": "Europe/Berlin",
        "germany": "Europe/Berlin",
        "싱가포르": "Asia/Singapore",
        "sg": "Asia/Singapore",
        "singapore": "Asia/Singapore",
    }
    country = country.strip()
    timezone_name = timezones.get(country.casefold(), country)
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError, ValueError:
        return (
            f"국가 또는 시간대를 확인해주세요: {country!r}. "
            "시간대가 여러 개인 국가는 America/New_York 같은 "
            "IANA 시간대로 지역을 지정해주세요."
        )

    return datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
