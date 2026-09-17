# 설치 (메인 레포 KTB4-13th-wiki 에서 1회)

## 1. 파일 넣기
이 폴더 내용을 메인 레포 루트에 복사한다.
```text
AGENTS.md  CLAUDE.md  .agents/skills/ktb4-docs/  .github/workflows/docs-check.yml
docs/  backup/README.md
```

## 2. Claude Code 연결
Claude Code는 `.claude/skills/` 에서 스킬을 찾는다. 원본은 하나만 두고 연결한다.
```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/ktb4-docs .claude/skills/ktb4-docs
```
Windows에서 링크가 깨져도 `CLAUDE.md` 가 스킬 경로를 안내하므로 동작한다.

## 3. 첫 백업 (문서 담당자)
```bash
bash .agents/skills/ktb4-docs/scripts/backup_wiki.sh
python .agents/skills/ktb4-docs/scripts/verify_backup.py backup
git checkout -b backup/wiki-original
git add backup && git commit -m "backup: 위키 원본"
git push origin backup/wiki-original   # → PR 머지
```
백업 후 `references/page-map.md` 의 원본 파일명을 실제 파일명과 한 번 맞춘다.

## 4. 첫 변환 (cld-3)
Codex 또는 Claude Code에서:
```text
ktb4-docs 스킬로 page-map의 cld-3 을 변환해줘. 옮김표부터 보여줘.
```

## 5. 위키 반영 (문서 담당자)
```bash
git clone https://github.com/100-hours-a-week/KTB4-13th-wiki.wiki.git ../wiki-publish
python .agents/skills/ktb4-docs/scripts/wiki_export.py --docs docs --backup-root backup --wiki ../wiki-publish --sidebar
python .agents/skills/ktb4-docs/scripts/wiki_export.py --docs docs --backup-root backup --wiki ../wiki-publish --sidebar --apply
cd ../wiki-publish && git diff && git add -A && git commit -m "docs: 반영" && git push
```

## 요구 사항
Python 3.9+, git, bash. 외부 패키지 없음.
