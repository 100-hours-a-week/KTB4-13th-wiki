#!/usr/bin/env python3
"""원본(backup) 대비 변환본(docs) 보존 검사.

원본의 모든 문장·숫자가 변환본(같은 group의 모든 파일)에 남아 있는지,
부정어·한정어·범위 표현이 사라지거나 뒤집히지 않았는지 확인한다.

사용:
  python preserve_check.py --docs docs --backup-root backup            # sources가 있는 모든 group
  python preserve_check.py --docs docs --backup-root backup --group cld-3
  python preserve_check.py --source a.md b.md --target x.md y.md       # 파일 직접 지정

결과:
  오류  누락 의심   원본 문장과 비슷한 문장이 변환본에 없음
  오류  뜻 바뀜 의심 비슷한 문장은 있으나 부정·한정·범위 표현이 빠짐
  오류  숫자 누락   원본 숫자(단위 포함)의 개수가 변환본에서 줄어듦
  경고  문장 변경   비슷한 문장이 있으나 글자가 달라짐 → 파트 확인
"""
from __future__ import annotations
import argparse
import difflib
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdlib import load_docs, latest_backup, parse_doc, as_list  # noqa: E402

RISK = {
    "부정": r"않|없[다는이음었어고지]|없$|아니|금지|불가|못\s?[하한할]",
    "한정": r"(?<=[가-힣A-Za-z0-9)\]`])만(?=[\s,.)]|$)|뿐|오직|단,",
    "범위": r"최대|최소|이내|이상|이하|초과|미만",
    "의무": r"필수|반드시|해야|필요",
    "제외": r"제외|빼고",
    "주체": r"다른\s|같은\s",
    "버전": r"\bV\d\b",
}
UNIT = r"(?:%|초|분|시간|일|주|개월|년|명|회|건|자|원|배|장|권|대|개|줄|MB|GB|KB|TB|RPS|ms|KST|달러)"
NUM_RE = re.compile(r"(?<![A-Za-z%])\$?\d+(?:[.,]\d+)*(?:\s?~\s?\d+(?:[.,]\d+)*)?\s?" + UNIT + "?")
URL_RE = re.compile(r"\]\([^)]*\)|https?://\S+")
SIM_CHANGED = 0.6


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = URL_RE.sub(" ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"^\s*#+\s*", "", s)
    s = re.sub(r"^\s*(?:[-*+]|\d+(?:[.-]\d+)*\.?)\s+", "", s)
    s = re.sub(r"^\s*(?:[-*+]\s+)?\[[ xX]\]\s+", "", s)
    s = re.sub(r"[*_`>|]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def nospace(s: str) -> str:
    return re.sub(r"[\s.,:;·\-–—]", "", s)


def units(text: str):
    """비교 단위(문장·표 셀·코드 줄) 목록."""
    _, body, _ = parse_doc(text)
    out = []
    in_code = False
    for ln in body.split("\n"):
        s = ln.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if not s or s.startswith("<!--") or re.match(r"^\|[\s:|-]+\|$", s) or s in ("---",):
            continue
        if in_code:
            out.append((s, "text"))
            continue
        if s.startswith("|"):
            out.extend((c.strip(), "text") for c in s.strip("|").split("|") if c.strip())
            continue
        if re.match(r"^#{1,6}\s", s) or (s.startswith("**") and s.endswith("**")):
            out.append((s, "heading"))
            continue
        out.extend((p, "text") for p in re.split(r"(?<=[.!?])\s+", s) if p.strip())
    res = []
    for u, kind in out:
        n = norm(u)
        if len(nospace(n)) >= 4:
            res.append((u, n, kind))
    return res


def numbers(unit_list):
    c = Counter()
    for _, n, _k in unit_list:
        for m in NUM_RE.findall(n):
            c[re.sub(r"\s", "", m)] += 1
    return c


def risks(s: str):
    return {k for k, p in RISK.items() if re.search(p, s)}


def load_overrides(docs_root: Path | None, group: str):
    phrases = []
    if not docs_root:
        return phrases
    f = docs_root / "_preserve-overrides.tsv"
    if not f.exists():
        return phrases
    for ln in f.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("#") or ln.startswith("group\t"):
            continue
        parts = ln.split("\t")
        if len(parts) >= 2 and parts[0] in (group, "*"):
            phrases.append((nospace(norm(parts[1])), parts[2] if len(parts) > 2 else ""))
    return phrases


def compare(src_texts, tgt_texts, overrides=()):
    src = [u for t in src_texts for u in units(t)]
    tgt = [u for t in tgt_texts for u in units(t)]
    tgt_joined = nospace(" ".join(n for _, n, _k in tgt))
    tgt_ns = [nospace(n) for _, n, _k in tgt]
    result = {"누락 의심": [], "뜻 바뀜 의심": [], "숫자 누락": [], "문장 변경": [],
              "제목 변경": [], "승인된 변경": []}

    seen = set()
    for raw, n, kind in src:
        key = nospace(n)
        if key in seen:
            continue
        seen.add(key)
        ov = next((r for p, r in overrides if p and p in key), None)
        if ov is not None:
            result["승인된 변경"].append((raw, ov))
            continue
        if key in tgt_joined:
            continue
        best, best_i = 0.0, -1
        for i, t in enumerate(tgt_ns):
            sm = difflib.SequenceMatcher(None, key, t, autojunk=False)
            if sm.real_quick_ratio() < best or sm.quick_ratio() < best:
                continue
            r = sm.ratio()
            if r > best:
                best, best_i = r, i
        if kind == "heading":
            result["제목 변경"].append((raw, tgt[best_i][0] if best_i >= 0 else "", best))
            continue
        if best < SIM_CHANGED:
            result["누락 의심"].append((raw, tgt[best_i][0] if best_i >= 0 else "", best))
            continue
        lost = risks(n) - risks(tgt[best_i][1])
        if lost:
            result["뜻 바뀜 의심"].append((raw, tgt[best_i][0], best, sorted(lost)))
        else:
            result["문장 변경"].append((raw, tgt[best_i][0], best))

    sc, tc = numbers(src), numbers(tgt)
    for k, v in sc.items():
        if tc[k] < v:
            result["숫자 누락"].append((k, v, tc[k]))
    return result, len(src)


def report(name, result, n_src):
    errs = sum(len(result[k]) for k in ("누락 의심", "뜻 바뀜 의심", "숫자 누락"))
    print(f"\n## {name} — 원본 단위 {n_src}개 · 오류 {errs} · 문장 변경 {len(result['문장 변경'])} · 제목 변경 {len(result['제목 변경'])}")
    for k in ("누락 의심", "뜻 바뀜 의심"):
        for item in result[k]:
            print(f"\n[오류] {k} (유사도 {item[2]:.2f})" + (f" 사라진 표현: {', '.join(item[3])}" if k == "뜻 바뀜 의심" else ""))
            print(f"  원본  : {item[0]}")
            print(f"  변환본: {item[1] or '(없음)'}")
    for k, v, t in result["숫자 누락"]:
        print(f"\n[오류] 숫자 누락 `{k}` 원본 {v}회 → 변환본 {t}회")
    for raw, tg, sim in result["문장 변경"]:
        print(f"\n[경고] 문장 변경 (유사도 {sim:.2f}) → 파트 확인")
        print(f"  원본  : {raw}")
        print(f"  변환본: {tg}")
    for raw, tg, sim in result["제목 변경"]:
        print(f"\n[경고] 제목 변경 → 원본 섹션이 옮김표에 있는지 확인")
        print(f"  원본  : {raw}")
        print(f"  가장 비슷한 변환본: {tg or '(없음)'}")
    for raw, why in result["승인된 변경"]:
        print(f"\n[정보] 승인된 변경 ({why}): {raw}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs")
    ap.add_argument("--backup-root", default="backup")
    ap.add_argument("--group")
    ap.add_argument("--source", nargs="*")
    ap.add_argument("--target", nargs="*")
    a = ap.parse_args()

    total = 0
    if a.source and a.target:
        res, n = compare([Path(p).read_text(encoding="utf-8") for p in a.source],
                         [Path(p).read_text(encoding="utf-8") for p in a.target])
        total += report("직접 비교", res, n)
        return 1 if total else 0

    if not a.docs:
        ap.error("--docs 또는 --source/--target 필요")
    docs_root = Path(a.docs)
    if not docs_root.exists():
        print("docs 없음 — 건너뜀")
        return 0
    groups = {}
    for d in load_docs(docs_root):
        g = d["meta"].get("group")
        if g:
            groups.setdefault(g, []).append(d)
    checked = 0
    for g, members in sorted(groups.items()):
        if a.group and g != a.group:
            continue
        sources = [s for d in members for s in as_list(d["meta"].get("sources"))]
        if not sources:
            continue
        bname = next((d["meta"].get("backup") for d in members if d["meta"].get("backup")), None)
        bdir = latest_backup(Path(a.backup_root), bname)
        if not bdir:
            print(f"[오류] {g}: 백업 폴더를 찾을 수 없음 ({a.backup_root})")
            total += 1
            continue
        src_texts = []
        for s in sources:
            p = bdir / s
            if not p.exists():
                print(f"[오류] {g}: 원본 파일 없음 {p}")
                total += 1
                continue
            src_texts.append(p.read_text(encoding="utf-8"))
        tgt_texts = [d["path"].read_text(encoding="utf-8") for d in members]
        res, n = compare(src_texts, tgt_texts, load_overrides(docs_root, g))
        total += report(f"{g} ({bdir.name})", res, n)
        checked += 1
    print(f"\n검사한 group {checked}개 · 오류 합계 {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
