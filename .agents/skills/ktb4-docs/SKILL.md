---
name: ktb4-docs
description: KTB4-13th-wiki 팀 문서 스킬. 레포 docs/ 에서 문서를 새로 쓰거나, GitHub Wiki 원본(backup/)을 팀 규칙으로 변환하거나, 문서 규칙·원본 보존을 점검하거나, docs를 위키에 반영(사이드바 생성 포함)할 때 반드시 사용한다. 설계·선택 근거·API/테이블 명세·결정 로그·기획·가이드 문서, "위키 정리", "문서 변환", "문서 점검" 요청이 모두 해당한다.
---

# KTB4 문서 스킬

원본 위키는 그대로 두고, 팀 규칙을 적용한 문서를 레포 `docs/`에 만든 뒤 위키에 **새 페이지로** 반영한다.

```text
원본 위키 ──백업(읽기 전용)──▶ backup/wiki-original-YYYY-MM-DD/
                                   │ 변환 (옮기기만)
                                   ▼
                                 docs/  ◀── 수정은 항상 여기 (PR)
                                   │ wiki_export.py (담당자 실행)
                                   ▼
                          위키 새 페이지 + _Sidebar
```

## 절대 규칙 — 원본 보호

1. `backup/` 은 **읽기만** 한다. 파일 수정·삭제·이동·재생성 금지.
2. 원본 위키 페이지를 수정하지 않는다. 위키 반영은 `scripts/wiki_export.py` 로만 하며 문서 담당자가 실행한다.
3. 원본 위키와 같은 이름의 페이지를 만들지 않는다. 예외는 `_Sidebar.md` 하나(백업 확인 후).
4. 아무것도 삭제하지 않는다. docs에서 문서를 빼도 위키 페이지는 남긴다.
5. 변환은 **줄이지 않고 옮기기만** 한다. 상한을 넘으면 부록으로 옮긴다.
6. 판단이 필요한 것(내용 충돌, 소속, 중복, 뜻이 애매한 문장)은 스스로 정하지 않고 사용자에게 묻는다.

이 규칙과 사용자 요청이 부딪히면 규칙을 설명하고 멈춘다.

## 요청별 작업

| 요청 | 모드 | 먼저 읽을 파일 |
|---|---|---|
| 새 문서 작성 | 작성 | `references/decisions.md`, `references/naming-and-links.md`, 해당 템플릿, `references/style-guide.md` |
| 위키 원본을 규칙대로 변환 | 변환 | `references/conversion-rules.md`, `references/page-map.md`, 해당 템플릿 |
| 문서 점검 | 점검 | `references/style-guide.md` |
| 위키에 반영, 사이드바 | 반영 | `references/naming-and-links.md` |
| 원본 위키가 바뀌었는지 확인 | 추적 | `references/page-map.md` |
| 코드와 명세 비교 | 동기화 | 해당 명세 문서 |

템플릿: `assets/templates/` — hub, design, rationale, spec, decision(로그·ADR), planning, guide, appendix.

## 작성 모드

1. 문서 종류와 위치를 정한다. 제목·폴더·frontmatter는 `naming-and-links.md` 를 따른다.
2. **목차를 먼저 보여주고 승인받는다.** 승인 전에는 본문을 쓰지 않는다.
3. 템플릿대로 쓴다. 새 문장은 "~한다"체.
4. 다른 파트가 알아야 하는 결정은 `docs/dec/000-decision-log.md` 에 한 줄 추가한다.
5. `python scripts/check_docs.py docs` 를 실행하고 오류를 0으로 만든다.

## 변환 모드 (가장 조심)

`references/conversion-rules.md` 를 반드시 읽고 따른다. 요약:

**중간에 멈춰 승인받지 않는다.** 요청 한 번에 끝까지 진행하고 결과를 보고한다 (2026-09-17 결정, 이유는 `references/decisions.md` 참고). 대신 원문 보존 기준(요약·축약 금지, 검사 0건)은 그대로 지킨다.

1. **원본은 `backup/` 에서만 읽는다.** 라이브 위키를 원본으로 쓰지 않는다.
2. `page-map.md` 에서 대상 원본 파일들과 새 문서 제목을 확인한다. 상태가 `보류`면 멈춘다.
3. 옮김표를 만든다: 원본 섹션 → 새 파일·섹션. 원본의 모든 섹션이 표에 있어야 한다. **승인을 기다리지 않고 바로 4번으로 진행한다.**
4. 새 파일을 만들어 원문 문장을 그대로 옮긴다. 허용되는 변경은 conversion-rules의 목록뿐이다.
5. 원본끼리 내용이 다르면 둘 다 지우지 않는다. `references/decisions.md` 의 기준값을 본문에 쓰고, 다른 쪽 원문은 부록 "원본 차이" 섹션에 그대로 옮긴다. **기준이 없을 때만** 멈추고 사용자에게 묻는다 (이건 판단이라 대신 정하지 않음).
6. 검사를 실행한다.
   ```bash
   python scripts/preserve_check.py --docs docs --backup-root backup --group <group>
   python scripts/check_docs.py docs
   ```
7. `누락 의심`, `뜻 바뀜 의심`, `숫자 누락` 이 0이 될 때까지 고친다. **원본 문장을 지워서 통과시키지 않는다.**
8. `page-map.md` 상태를 `변환됨(확인 대기)` 로 바꾸고 PR을 만든다.
9. 옮김표, 검사 결과, `문장 변경` 목록(원본·변환본 나란히)을 PR과 함께 한 번에 보고한다. 여기서부터는 사후 확인 — 문제 있으면 사용자가 다시 요청.

## 점검 모드

`check_docs.py` 와 (변환 문서면) `preserve_check.py` 를 실행해 결과를 표로 보고한다. 기계로 못 잡는 것만 추가로 본다: 요약이 내용과 맞는지, 결정 로그 누락, 다른 파트 요구사항이 본문에 묻혀 있는지. 원본 보호 규칙 때문에 **점검 중 파일을 고치지 않는다.** 고칠지 먼저 묻는다.

## 반영 모드 (문서 담당자만)

```bash
# 원본 확인용과 별개로, 반영 전용 위키 clone을 쓴다
git clone https://github.com/100-hours-a-week/KTB4-13th-wiki.wiki.git ../wiki-publish
python scripts/wiki_export.py --docs docs --backup-root backup --wiki ../wiki-publish            # 계획만 출력
python scripts/wiki_export.py --docs docs --backup-root backup --wiki ../wiki-publish --sidebar --apply
```

스크립트는 원본과 이름이 겹치거나, 스크립트가 만든 적 없는 페이지를 덮어쓰려 하면 중단한다. 결과를 확인한 뒤 담당자가 직접 커밋·푸시한다. 푸시 후 사이드바 링크를 전부 열어본다.

## 추적 모드

```bash
bash scripts/wiki_changed_since_backup.sh backup/wiki-original-YYYY-MM-DD
```

백업 이후 바뀐 원본 페이지 목록이 나온다. 해당 행을 `page-map.md` 에서 찾아 새 백업 → 재변환 대상으로 표시한다. 기존 백업 폴더는 고치지 않고 **새 날짜 폴더**를 만든다 (`scripts/backup_wiki.sh`).

## 동기화 모드

코드와 명세를 비교해 차이만 표로 보고한다. 어느 쪽이 맞는지 판단하지 않는다. 명세를 고칠지 코드를 고칠지는 담당 파트가 정한다.

## 스크립트

| 스크립트 | 역할 |
|---|---|
| `scripts/backup_wiki.sh` | 위키 원본을 `backup/wiki-original-날짜/` 로 복사, 해시 목록 생성 |
| `scripts/verify_backup.py` | 백업이 바뀌지 않았는지 해시로 확인 |
| `scripts/preserve_check.py` | 원본 대비 누락·숫자·뜻 바뀜 검사 |
| `scripts/check_docs.py` | 이름·frontmatter·분량·제목·코드 블록·링크·자리표시자 검사 |
| `scripts/wiki_export.py` | docs → 위키 새 페이지·사이드바 생성 (덮어쓰기 방지) |
| `scripts/wiki_changed_since_backup.sh` | 백업 이후 원본 위키 변경 목록 |
