import re
from typing import Dict, List


def normalize_text(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text or "").strip()


def extract_bullets(text: str) -> List[str]:
    lines = normalize_text(text).split("\n")
    items: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*", "•")):
            items.append(stripped[1:].strip())
        else:
            items.append(stripped)
    return items


def parse_candidate_text(candidate_text: str) -> Dict[str, List[str] | str]:
    """
    轻量解析候选人文本，尽量提取技能、项目和经历片段。
    当格式不规范时，保底返回全文分段。
    """
    text = normalize_text(candidate_text)
    sections = re.split(r"\n(?=#{1,3}\s|\w+[:：])", text)
    skill_hits: List[str] = []
    project_hits: List[str] = []
    experience_hits: List[str] = []

    for sec in sections:
        low = sec.lower()
        bullets = extract_bullets(sec)
        if any(k in low for k in ["技能", "skill", "tech stack", "技术栈"]):
            skill_hits.extend(bullets)
        elif any(k in low for k in ["项目", "project"]):
            project_hits.extend(bullets)
        elif any(k in low for k in ["经历", "experience", "工作", "实习"]):
            experience_hits.extend(bullets)

    if not skill_hits:
        skill_hits = []
    if not project_hits:
        project_hits = extract_bullets(text)[:8]
    if not experience_hits:
        experience_hits = extract_bullets(text)[:8]

    return {
        "raw_text": text,
        "skills": dedupe_keep_order(skill_hits),
        "projects": dedupe_keep_order(project_hits),
        "experiences": dedupe_keep_order(experience_hits),
        "missing_items": [],
    }


def dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result

