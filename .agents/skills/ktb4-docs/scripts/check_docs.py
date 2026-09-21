#!/usr/bin/env python3
"""docs/ 문서 규칙 검사. 오류가 있으면 종료 코드 1.

python check_docs.py docs
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdlib import TYPES, STATUSES, TITLE_RE, FORBIDDEN, load_docs, as_list  # noqa: E402

LIMITS = {  # (최대 줄, 최대 ## 섹션)
    "hub": (60, 4), "design": (150, 5), "rationale": (100, 5), "spec": (250, 5),
    "decision": (40, 4), "decision-log": (None, None), "planning": (80, 4),
    "guide": (100, 4), "appendix": (400, None),
}
REQUIRED = ["wiki", "type", "group", "owner", "status", "updated"]
PLACEHOLDERS = [r"your-link", r"여기에_", r"URL_삽입", r"\bTODO\b", r"<실행 링크>",
                r"@담당자", r"YYYY-MM-DD"]
BAD_LINK_TEXT = {"여기", "링크", "이것", "클릭", "here", "link", "click"}
ORIGINAL_WIKI = "github.com/100-hours-a-week/KTB4-13th-wiki/wiki/"
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
FORMAL_RE = re.compile(r"([가-힣])니다(?=[.!?]|$)")  # 문장 끝 격식체: 합니다·입니다·됩니다·있습니다…


def has_formal_ending(s: str) -> bool:
    s = re.sub(r"`[^`]*`", "", s)  # 인라인 코드 안은 문자열 데이터일 수 있다
    for m in FORMAL_RE.finditer(s):
        c = m.group(1)
        if c == "습" or (ord(c) - 0xAC00) % 28 == 17:  # '습' 또는 ㅂ받침 음절
            return True
    return False


def info_label(msg: str) -> str:
    """정보 등급 항목을 종류별로 묶는 이름."""
    if "이하" in msg:
        return "`####` 이하 제목 (원본 계층을 유지하므로 나누지 않음)"
    if "섹션" in msg:
        return "`##` 섹션 수 상한 초과 (원문을 나누지 않음)"
    return "줄 수 상한 초과 (원문을 자르지 않음, 긴 블록만 제자리에서 접기)"


def check(docs_root: Path):
    issues = []  # (level, path, line, msg)
    docs = load_docs(docs_root)
    titles = {}
    converted_groups = {d["meta"].get("group") for d in docs if as_list(d["meta"].get("sources"))}

    def add(level, d, line, msg):
        issues.append((level, d["path"], line, msg))

    for d in docs:
        m, body, start = d["meta"], d["body"], d["start"]
        converted = bool(as_list(m.get("sources"))) or m.get("group") in converted_groups

        if not m:
            add("오류", d, 1, "frontmatter 없음")
            continue
        for k in REQUIRED:
            if not m.get(k):
                add("오류", d, 1, f"frontmatter `{k}` 없음")
        t = m.get("type", "")
        if t and t not in TYPES:
            add("오류", d, 1, f"알 수 없는 type `{t}`")
        if m.get("status") and m["status"] not in STATUSES:
            add("오류", d, 1, f"status는 {'/'.join(STATUSES)} 중 하나")
        if m.get("updated") and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(m["updated"])):
            add("오류", d, 1, "updated 형식은 YYYY-MM-DD")

        title = m.get("wiki", "")
        if isinstance(title, str) and title:
            if not TITLE_RE.match(title):
                add("오류", d, 1, f"제목 규칙 위반 `{title}` (코드[-번호] 주제 종류)")
            bad = sorted(c for c in title if c in FORBIDDEN)
            if bad:
                add("오류", d, 1, f"제목 금지 문자 {''.join(bad)}")
            if len(title) > 30:
                add("오류", d, 1, f"제목 30자 초과 ({len(title)}자)")
            if t == "appendix" and not title.endswith("부록"):
                add("오류", d, 1, "부록 제목은 `부록`으로 끝나야 함")
            if title in titles:
                add("오류", d, 1, f"제목 중복: {titles[title]}")
            titles[title] = d["path"]

        lines = body.split("\n")
        in_code = False
        fence_run = 3
        nonempty = 0
        sections = 0
        in_comment = False
        for i, ln in enumerate(lines):
            no = start + i
            s = ln.strip()
            if "<!--" in s and "-->" not in s:
                in_comment = True
                continue
            if in_comment:
                if "-->" in s:
                    in_comment = False
                continue
            if s.startswith("<!--") and s.endswith("-->"):
                continue
            fm = re.match(r"^(`{3,})(.*)$", s)
            if fm:
                run, info = len(fm.group(1)), fm.group(2).strip()
                if not in_code:
                    if not info:
                        add("오류", d, no, "코드 블록 언어 지정 없음")
                    in_code, fence_run = True, run
                elif run >= fence_run:
                    if info:
                        add("오류", d, no, f"닫는 코드 펜스에 `{info}` 가 붙음 — 닫는 줄은 ``` 만 (안 닫혀서 뒤 내용이 모두 깨진다)")
                    in_code = False
                nonempty += 1
                continue
            if s:
                nonempty += 1
            if in_code:
                continue
            if re.match(r"^# ", ln):
                add("오류", d, no, "`#` 제목 사용 금지 (`##`부터)")
            if re.match(r"^#### ", ln):
                if converted:
                    add("정보", d, no, "`####` 이하 (변환 문서는 원본 계층 유지 — 나누지 않는다)")
                else:
                    add("오류", d, no, "`####` 이하 금지 (문서 분리 신호)")
            if re.match(r"^## ", ln):
                sections += 1
            for pat in PLACEHOLDERS:
                if re.search(pat, ln):
                    add("경고", d, no, f"자리표시자 의심: `{re.search(pat, ln).group(0)}`")
                    break
            for text, target in LINK_RE.findall(ln):
                if text.strip().lower() in BAD_LINK_TEXT:
                    add("경고", d, no, f"링크 텍스트가 목적지를 설명하지 않음: `{text}`")
                if target.startswith(("http://", "https://")):
                    if ORIGINAL_WIKI in target:
                        add("경고", d, no, "원본 위키 직접 링크 (변환 문서가 생기면 docs 상대 링크로)")
                    continue
                if target.startswith(("#", "mailto:")):
                    continue
                rel = target.split("#")[0]
                if rel and not (d["path"].parent / rel).resolve().exists():
                    add("오류", d, no, f"깨진 링크: {target}")
            if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", s):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) > 5 and not converted:
                    add("경고", d, no, f"표 열 {len(cells)}개 (5개 이하)")
                if any(len(c) > 60 and len(re.findall(r"[.!?](?:\s|$)", c)) >= 2 for c in cells):
                    add("경고", d, no, "긴 셀에 문장이 두 개 이상 (첫 문장 + 각주로)")
                elif not converted and any(len(c) > 80 for c in cells):
                    add("경고", d, no, "표 셀이 너무 김 (한 문장 이내)")
            if not s.startswith("|") and has_formal_ending(s):
                add("경고", d, no, "\"~한다\"체로 (변환 문서도 어미 통일, 결정 #16)")
            if s.startswith("~~~"):
                add("경고", d, no, "코드 펜스는 ``` 로")
            if s in ("---", "***") and no > start + 1:
                add("경고", d, no, "구분선 제거 (제목이 구분한다)")
            if "<br" in s:
                add("경고", d, no, "셀 안 <br> 금지 (각주로)")

        if in_code:
            add("오류", d, start + len(lines), "코드 블록이 닫히지 않음")
        max_lines, max_sec = LIMITS.get(t, (None, None))
        exempt = m.get("limit_exempt") or converted  # 변환 문서는 원본 분량 그대로라 경고만
        over = "정보" if converted else ("경고" if exempt else "오류")  # 변환 문서의 초과는 예상된 것
        if max_lines and nonempty > max_lines:
            add(over, d, 1,
                f"{nonempty}줄 > 상한 {max_lines}줄 → " + ("긴 블록을 제자리에서 접기" if converted else "부록으로 옮기기")
                + (f" (예외: {exempt})" if exempt and not converted else ""))
        if max_sec and sections > max_sec:
            add(over, d, 1, f"## 섹션 {sections}개 > 상한 {max_sec}개")
        if not re.search(r"^\*\*요약\*\*", body, re.M):
            add("경고", d, 1, "`**요약**` 줄 없음")

    return docs, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="?", default="docs")
    ap.add_argument("-v", "--verbose", action="store_true", help="정보 등급도 줄 단위로 모두 출력")
    a = ap.parse_args()
    root = Path(a.docs)
    if not root.exists():
        print(f"{root} 없음")
        return 1
    docs, issues = check(root)
    errors = [x for x in issues if x[0] == "오류"]
    warns = [x for x in issues if x[0] == "경고"]
    infos = [x for x in issues if x[0] == "정보"]
    for level, path, line, msg in sorted(issues, key=lambda x: (str(x[1]), x[2])):
        if level != "정보" or a.verbose:
            print(f"[{level}] {path}:{line} {msg}")
    if infos and not a.verbose:  # 변환 문서라 예상되는 항목은 종류별 건수만 (줄 단위는 --verbose)
        print("\n[정보] 변환 문서라 예상되는 항목 (줄 단위는 --verbose)")
        groups = {}
        for _, path, _, msg in infos:
            groups.setdefault(info_label(msg), []).append(path)
        for label, paths in sorted(groups.items(), key=lambda x: -len(x[1])):
            print(f"  · {label}: {len(paths)}건 · 문서 {len(set(paths))}개")
    print(f"\n문서 {len(docs)}개 · 오류 {len(errors)} · 경고 {len(warns)} · 정보 {len(infos)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
