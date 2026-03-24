import re
from typing import Any, Dict, List


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


# ── 独立技能点提取 ──────────────────────────────────────────────────────────────

# 已知技能关键词白名单，用于从技能段落中识别独立技能点
_SKILL_TOKENS = [
    # 编程语言
    "Java", "Python", "Go", "Golang", "C++", "C#", "TypeScript", "JavaScript",
    # 框架/库
    "Spring Boot", "Spring AI", "FastAPI", "Flask", "Django", "LangChain",
    "React", "Vue",
    # 数据库/存储
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Milvus", "Faiss", "Chroma",
    "Elasticsearch",
    # AI/ML
    "RAG", "LLM", "Prompt Engineering", "Embedding", "Fine-tuning", "SFT",
    "vLLM", "Ollama", "BERT", "Transformer",
    # 工程/工具
    "Docker", "Docker Compose", "Kubernetes", "Git", "Linux", "CI/CD",
    "JWT", "RESTful API", "SSE", "gRPC",
    # 概念
    "向量检索", "文本切片", "上下文管理", "任务拆解", "多agent协作",
]

_SKILL_TOKENS_LOWER = {t.lower(): t for t in _SKILL_TOKENS}


def extract_skill_tokens(text: str) -> List[str]:
    """
    从文本中提取独立技能点（基于白名单匹配）。
    返回标准化后的技能名称列表，不含完整句子。
    """
    found: List[str] = []
    text_lower = text.lower()
    for token_lower, token_display in _SKILL_TOKENS_LOWER.items():
        if token_lower in text_lower and token_display not in found:
            found.append(token_display)
    return found


# ── 项目段落解析 ────────────────────────────────────────────────────────────────

# 时间格式：2025.12 - 至今 / 2025.10 - 2025.12 / 2024/01 - 2024/06
_PERIOD_RE = re.compile(
    r"\d{4}[./年]\d{1,2}\s*[-–—~至]\s*(?:\d{4}[./年]\d{1,2}|至今|present)",
    re.IGNORECASE,
)

# 技术栈行：包含多个逗号分隔的技术词，且行较短
_TECH_STACK_RE = re.compile(r"^[\w\s\+\./]+(?:,\s*[\w\s\+\./]+){2,}$")


_SUSPICIOUS_INSTRUCTION_PATTERNS = [
    r"忽略.*规则",
    r"帮我.*写得很厉害",
    r"多加.*数据.*成果",
    r"ignore .*instructions?",
    r"make .*resume.*strong",
]


def _looks_like_prompt_injection(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return any(re.search(pattern, stripped, re.IGNORECASE) for pattern in _SUSPICIOUS_INSTRUCTION_PATTERNS)


def _is_section_header(line: str) -> bool:
    """判断是否为章节标题行（如'项目经历'、'核心技能'）"""
    stripped = line.strip()
    # 纯中文短行（≤8字），无标点，无数字
    if re.match(r"^[\u4e00-\u9fa5]{2,8}$", stripped):
        return True
    # Markdown 标题
    if stripped.startswith("#"):
        return True
    return False


def _looks_like_role_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 20:
        return False
    if any(sep in stripped for sep in ["，", ",", "；", ";", "。", ":", "："]):
        return False
    role_keywords = ["工程师", "开发", "负责人", "实习", "leader", "manager", "owner"]
    return any(keyword in stripped.lower() for keyword in role_keywords)



def _parse_project_block(lines: List[str]) -> Dict[str, Any]:
    """
    将一个项目的行列表解析为结构化对象。
    期望格式（宽松匹配）：
      第1行：项目名称 [时间]
      第2行：角色 技术栈（逗号分隔）
      后续行：• 成就描述
    """
    project: Dict[str, Any] = {
        "name": "",
        "period": "",
        "role": "",
        "tech_stack": [],
        "highlights": [],
    }

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # 提取时间段
        period_match = _PERIOD_RE.search(stripped)
        if period_match and not project["period"]:
            project["period"] = period_match.group(0).strip()
            # 项目名 = 时间段之前的部分
            name_part = stripped[: period_match.start()].strip()
            if name_part and not project["name"]:
                # 去掉括号内容作为简洁名称
                project["name"] = re.sub(r"（[^）]*）|\([^)]*\)", "", name_part).strip()
            continue

        # 技术栈行：逗号分隔的多个词，且不是成就描述
        if _TECH_STACK_RE.match(stripped) and not stripped.startswith(("•", "-", "*")):
            # 尝试分离角色和技术栈（如"核心开发者 Java 17, Spring Boot 3, ..."）
            parts = re.split(r"\s{2,}|\t", stripped, maxsplit=1)
            if len(parts) == 2:
                project["role"] = parts[0].strip()
                tech_raw = parts[1]
            else:
                # 判断第一个逗号前是否像角色名
                first_comma = stripped.find(",")
                pre = stripped[:first_comma].strip() if first_comma > 0 else ""
                if pre and len(pre.split()) <= 3 and not any(c.isdigit() for c in pre):
                    project["role"] = pre
                    tech_raw = stripped[first_comma + 1 :]
                else:
                    tech_raw = stripped
            project["tech_stack"] = [t.strip() for t in tech_raw.split(",") if t.strip()]
            continue

        # 成就描述行（以 • - * 开头）
        if stripped.startswith(("•", "-", "*")):
            highlight = stripped.lstrip("•-* ").strip()
            if highlight:
                project["highlights"].append(highlight)
            continue

        if not project["role"] and _looks_like_role_line(stripped):
            project["role"] = stripped
            continue

        # 其他非空行默认视为项目事实亮点，兼容软换行/自由排版简历
        if not project["name"] and i == 0:
            project["name"] = stripped[:60]
        else:
            project["highlights"].append(stripped)

    return project


def _split_into_sections(text: str) -> Dict[str, str]:
    """
    将简历文本按章节分割，返回 {章节名: 章节内容} 的字典。
    支持中文章节标题（项目经历、核心技能、工作经历等）。
    """
    # 章节分隔符：独占一行的中文标题，或 ## 标题
    section_pattern = re.compile(
        r"^(#{1,3}\s*.+|[\u4e00-\u9fa5]{2,10}(?:经历|技能|技术|信息|证书|附加|能力|项目|工作|实习|教育|学历))\s*$",
        re.MULTILINE,
    )

    sections: Dict[str, str] = {}
    lines = text.split("\n")
    current_section = "__preamble__"
    current_lines: List[str] = []

    for line in lines:
        if section_pattern.match(line.strip()):
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line.strip().lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


def parse_candidate_text(candidate_text: str) -> Dict[str, Any]:
    """
    结构化解析候选人简历文本。

    返回：
    {
        "raw_text": str,
        "basic_info": dict,          # 姓名、学历、语言能力等
        "skills": List[str],         # 独立技能点列表（不含完整句子）
        "projects": List[dict],      # 结构化项目列表
        "work_experiences": List[str], # 工作/实习经历（独立于项目）
        "missing_items": List[str],  # 缺失项检查结果
    }
    """
    text = normalize_text(candidate_text)
    sections = _split_into_sections(text)

    # ── 1. 技能提取 ──────────────────────────────────────────────────────────
    skill_section_text = ""
    for key, content in sections.items():
        if any(k in key for k in ["技能", "skill", "技术栈", "tech"]):
            skill_section_text += "\n" + content

    # 优先从技能段落提取，再从全文补充
    skills = extract_skill_tokens(skill_section_text or text)
    skills = dedupe_keep_order(skills)

    # ── 2. 项目解析 ──────────────────────────────────────────────────────────
    project_section_text = ""
    for key, content in sections.items():
        if any(k in key for k in ["项目", "project"]):
            project_section_text += "\n" + content

    projects = _parse_projects_from_section(project_section_text)

    # ── 3. 工作/实习经历 ─────────────────────────────────────────────────────
    work_section_text = ""
    for key, content in sections.items():
        if any(k in key for k in ["工作", "实习", "经历", "experience"]) and \
           not any(k in key for k in ["项目", "project"]):
            work_section_text += "\n" + content

    work_experiences = extract_bullets(work_section_text) if work_section_text.strip() else []
    work_experiences = [
        line for line in work_experiences
        if not _is_section_header(line) and len(line) > 5
    ]

    # ── 4. 基本信息 ──────────────────────────────────────────────────────────
    basic_info = _extract_basic_info(text, sections)

    return {
        "raw_text": text,
        "basic_info": basic_info,
        "skills": skills,
        "projects": projects,
        "work_experiences": work_experiences,
        "missing_items": [],  # 由 CandidateProfiler 填充
    }


def _parse_projects_from_section(section_text: str) -> List[Dict[str, Any]]:
    """将项目段落文本解析为结构化项目列表"""
    if not section_text.strip():
        return []

    lines = section_text.split("\n")
    project_blocks: List[List[str]] = []
    current_block: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or _looks_like_prompt_injection(stripped):
            continue
        # 新项目的开始：包含时间段的行
        if _PERIOD_RE.search(stripped) and current_block:
            project_blocks.append(current_block)
            current_block = [stripped]
        elif _is_section_header(stripped):
            # 章节标题，跳过
            continue
        else:
            current_block.append(stripped)

    if current_block:
        project_blocks.append(current_block)

    return [_parse_project_block(block) for block in project_blocks if block]


def _extract_basic_info(text: str, sections: Dict[str, str]) -> Dict[str, str]:
    """提取基本信息：学历、语言能力等"""
    info: Dict[str, str] = {}

    # 语言能力
    lang_match = re.search(r"(CET-[46]|英语[四六]级|雅思[\d.]+|托福\d+)", text, re.IGNORECASE)
    if lang_match:
        info["english_level"] = lang_match.group(0)

    # 学历（简单匹配）
    edu_match = re.search(r"(本科|硕士|博士|学士|Bachelor|Master|PhD)", text, re.IGNORECASE)
    if edu_match:
        info["education"] = edu_match.group(0)

    return info


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
