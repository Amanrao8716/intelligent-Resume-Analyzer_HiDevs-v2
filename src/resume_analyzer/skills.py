"""Skill taxonomy and normalisation (aliases -> canonical names)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# canonical name -> list of aliases
DEFAULT_TAXONOMY: Dict[str, List[str]] = {
    "python": ["py", "python3"],
    "java": [],
    "c": [],
    "c++": ["cpp"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "html": ["html5"],
    "css": ["css3"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs"],
    "django": [],
    "flask": [],
    "fastapi": [],
    "streamlit": [],
    "sql": ["mysql", "postgresql", "postgres", "sqlite"],
    "mongodb": ["mongo"],
    "aws": ["amazon web services", "ec2", "s3", "lambda"],
    "docker": [],
    "kubernetes": ["k8s"],
    "git": ["github", "gitlab"],
    "linux": [],
    "machine learning": ["ml"],
    "deep learning": [],
    "nlp": ["natural language processing"],
    "pandas": [],
    "numpy": [],
    "scikit-learn": ["sklearn"],
    "tensorflow": [],
    "pytorch": [],
    "rest api": ["rest", "restful", "restful api", "rest apis"],
    "data structures": ["dsa", "data structures and algorithms"],
    "algorithms": [],
    "pytest": [],
    "ci/cd": ["cicd", "github actions", "jenkins"],
    "agile": ["scrum"],
}

_ws_re = re.compile(r"\s+")


def normalise_skill(raw: str) -> str:
    """Lower-case, trim and collapse whitespace; does not resolve aliases."""
    return _ws_re.sub(" ", raw.strip().lower())


def load_taxonomy(path: Optional[str] = None) -> Dict[str, List[str]]:
    if not path:
        return DEFAULT_TAXONOMY
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {normalise_skill(k): [normalise_skill(a) for a in v] for k, v in data.items()}


@lru_cache(maxsize=8)
def alias_map(path: Optional[str] = None) -> Dict[str, str]:
    """alias (or canonical) -> canonical."""
    out: Dict[str, str] = {}
    for canon, aliases in load_taxonomy(path).items():
        out[normalise_skill(canon)] = normalise_skill(canon)
        for a in aliases:
            out[normalise_skill(a)] = normalise_skill(canon)
    return out


def canonical_skill(raw: str, taxonomy_path: Optional[str] = None) -> str:
    n = normalise_skill(raw)
    return alias_map(taxonomy_path).get(n, n)


def canonicalise_many(items: Iterable[str], taxonomy_path: Optional[str] = None) -> List[str]:
    seen, out = set(), []
    for item in items:
        if not item.strip():
            continue
        c = canonical_skill(item, taxonomy_path)
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def skill_pattern(term: str) -> "re.Pattern[str]":
    """Regex matching ``term`` as a whole token (handles c++, node.js, ci/cd)."""
    return re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(term) + r"(?![A-Za-z0-9+#])", re.I)
