import json
from typing import Any, Dict


def to_pretty_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)

