# 위키 원본 백업

- `wiki-original-YYYY-MM-DD/` 는 그 날짜의 GitHub Wiki 원본 그대로다. **수정·삭제하지 않는다.**
- `MANIFEST.sha256` 으로 변조를 검사한다 (PR마다 자동).
- 원본이 바뀌면 기존 폴더를 고치지 않고 새 날짜 폴더로 다시 백업한다.

```bash
bash .agents/skills/ktb4-docs/scripts/backup_wiki.sh
python .agents/skills/ktb4-docs/scripts/verify_backup.py backup
```
