from importlib.resources import files


def load_prompt(filename: str) -> str:
    """프롬프트 패키지에서 Markdown 파일을 읽습니다.

    Args:
        filename (str): 프롬프트 패키지 기준의 Markdown 상대 경로입니다.
            예: "system.md", "common/current_time_description.md".

    Returns:
        str: 앞뒤 공백을 제거한 프롬프트 내용입니다.

    Raises:
        ValueError: 파일명이 올바르지 않거나 내용이 비어 있는 경우.
        FileNotFoundError: 지정한 파일이 없는 경우.
    """
    parts = filename.split("/")
    if (
        not filename.endswith(".md")
        or "\\" in filename
        or ":" in filename
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError("프롬프트는 패키지 내부의 .md 상대 경로로 지정하세요.")

    prompt = files(__package__).joinpath(*parts).read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"프롬프트 파일이 비어 있습니다: {filename}")
    return prompt
