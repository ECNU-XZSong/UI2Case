from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

Item = Tuple[str, str, str]


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def _ratio(a: str, b: str) -> float:
    a, b = _normalize(a), _normalize(b)
    try:
        from rapidfuzz import fuzz

        return float(fuzz.token_set_ratio(a, b))
    except Exception:
        from difflib import SequenceMatcher

        return SequenceMatcher(None, a, b).ratio() * 100.0


def flatten_test_case(node: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    pid = node.get("page_id", "")
    for area in node.get("layout", []) or []:
        text = f"{area.get('area', '')}: {area.get('detail', '')}"
        items.append(("layout", pid, text))
    for ip in node.get("interaction", []) or []:
        text = f"{ip.get('action', '')} -> {ip.get('expectation', '')}"
        items.append(("interaction", pid, text))
    for tr in node.get("transition", []) or []:
        items.append(("transition", pid, tr.get("action", "")))
        sub = tr.get("sub_page")
        if isinstance(sub, dict) and not sub.get("cyclic_ref"):
            items.extend(flatten_test_case(sub))
    return items


def load_items(obj: Any) -> List[Item]:
    if isinstance(obj, dict) and "test_case" in obj:
        return flatten_test_case(obj["test_case"])
    if isinstance(obj, dict) and "items" in obj:
        return load_items(obj["items"])
    if isinstance(obj, dict):
        return flatten_test_case(obj)
    items: List[Item] = []
    for it in obj:
        page = it.get("page") or it.get("source_page") or it.get("page_id") or ""
        text = it.get("text")
        if not text:
            if it.get("type") == "layout":
                text = f"{it.get('area', '')}: {it.get('detail', '')}"
            else:
                text = f"{it.get('action', '')} -> {it.get('expected_result') or it.get('expectation', '')}"
        items.append((it.get("type", "interaction"), page, text))
    return items


def match_sets(
    gen: List[Item], gt: List[Item], threshold: float = 80.0
) -> Tuple[Set[int], Set[int]]:
    matched_gen: Set[int] = set()
    matched_gt: Set[int] = set()
    for i, g in enumerate(gen):
        for j, t in enumerate(gt):
            if j in matched_gt or g[0] != t[0]:
                continue
            if _ratio(g[2], t[2]) >= threshold:
                matched_gen.add(i)
                matched_gt.add(j)
                break
    return matched_gen, matched_gt


def dedup_items(items: List[Item]) -> List[Item]:
    seen: Set[Tuple[str, str, str]] = set()
    out: List[Item] = []
    for it in items:
        key = (it[0], it[1], _normalize(it[2]))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def compute_metrics(
    gen: List[Item],
    gt: List[Item],
    accepted_labels: Optional[List[int]] = None,
    threshold: float = 80.0,
) -> Dict[str, Any]:
    if accepted_labels is None:
        gen, gt = dedup_items(gen), dedup_items(gt)
    matched_gen, matched_gt = match_sets(gen, gt, threshold)
    n_gen, n_gt = len(gen), len(gt)

    if accepted_labels is not None:
        if len(accepted_labels) != n_gen:
            raise ValueError(
                f"accepted label count ({len(accepted_labels)}) does not match generated item count ({n_gen})"
            )
        gar = (sum(accepted_labels) / len(accepted_labels)) if accepted_labels else 0.0
        gar_mode = "human-label"
    else:
        gar = (len(matched_gen) / n_gen) if n_gen else 0.0
        gar_mode = "auto-proxy"

    grr = (len(matched_gt) / n_gt) if n_gt else 0.0
    f1 = (2 * gar * grr / (gar + grr)) if (gar + grr) > 0 else 0.0
    return {
        "GAR": round(gar, 4),
        "GRR": round(grr, 4),
        "F1": round(f1, 4),
        "gar_mode": gar_mode,
        "n_generated": n_gen,
        "n_ground_truth": n_gt,
        "matched_generated": len(matched_gen),
        "matched_ground_truth": len(matched_gt),
    }


def compute_grouped_metrics(
    gen: List[Item],
    gt: List[Item],
    threshold: float = 80.0,
) -> Dict[str, Dict[str, Any]]:
    groups = sorted({item[0] for item in gen} | {item[0] for item in gt})
    result: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        g = [item for item in gen if item[0] == group]
        t = [item for item in gt if item[0] == group]
        result[group] = compute_metrics(g, t, threshold=threshold)
    result["overall"] = compute_metrics(gen, gt, threshold=threshold)
    return result
