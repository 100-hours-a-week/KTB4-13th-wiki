# 이름·폴더·frontmatter·링크 규칙

## 위키 페이지 제목 (`wiki` 필드)

형식: `{코드}[-{번호}] {주제} {문서종류}`

- 예: `CLD-3 CD 파이프라인 설계`, `CLD-3 CD 파이프라인 선택 근거`, `AI-1 모델 API 명세 부록`, `DEC-000 결정 로그`, `PM 비전`
- 코드: `FE BE FS AI CLD PM REL SPR DEC TEAM`
- 허브는 번호 `0`: `CLD-0 허브`
- 30자 이내
- 금지 문자: `+ / : ? # [ ] ( ) . , ‐`(유니코드 하이픈)
- 부록은 제목 끝이 `부록`
- 원본 위키 페이지 이름과 같으면 안 된다 (반영 스크립트가 거부)

## docs 폴더

```text
docs/
├── README.md                         문서 목차
├── _preserve-overrides.tsv           (선택) 승인된 원본 변경 목록
├── dec/000-decision-log.md
├── pm/vision.md
├── fs/2-api/spec.md
├── ai/1-model-api/spec.md
├── ai/1-model-api/appendix.md
├── cld/0-hub/hub.md
└── cld/3-cd-pipeline/
    ├── design.md
    ├── rationale.md
    └── appendix.md
```

폴더: `{코드 소문자}/{번호}-{영문 슬러그}/{type}.md`. 같은 폴더 = 같은 group.

## frontmatter

```yaml
---
wiki: CLD-3 CD 파이프라인 설계     # 위키 페이지 제목
type: design                       # hub design rationale spec decision decision-log planning guide appendix
group: cld-3                       # 짝 문서끼리 같은 값
owner: 담당자 이름
status: 작성중                     # 미작성 작성중 완료 보관
updated: 2026-09-17
sources:                           # 변환 문서만. backup 폴더 안의 원본 파일명
  - 3단계.-CD(지속적-배포)-파이프라인-설계.md
limit_exempt:                      # 선택. 상한을 넘는 사유
---
```

- 상태 헤더(상태·담당·수정일·짝 문서·원본 링크)는 본문에 쓰지 않는다. 위키 반영 때 frontmatter로 자동 생성한다.
- 같은 group의 `sources` 는 한 파일에만 적어도 된다.

## 링크

| 대상 | 쓰는 법 |
|---|---|
| 다른 docs 문서 | 상대 경로: `[CD 파이프라인 선택 근거](../3-cd-pipeline/rationale.md)` |
| 섹션 | `[승인 정책](rationale.md#1-승인-정책)` — 번호 붙은 `##` 에만 |
| 아직 변환 안 된 원본 위키 | 원본 위키 전체 URL (점검 시 경고로 표시되어 나중에 바꿀 대상이 됨) |
| 없는 문서 | 링크 만들지 않음: `ERD (작성 예정)` |
| GitHub Issues·Projects | 전체 URL |

- 링크 텍스트는 목적지를 설명한다 ("여기", "링크" 금지).
- 위키 반영 때 상대 경로 링크는 위키 페이지 링크로 자동 변환된다.

## 사이드바

`wiki_export.py --sidebar` 가 docs의 frontmatter로 생성한다. 손으로 고치지 않는다.
- 묶음: 결정·참고(DEC, TEAM) / 기획(PM, REL, SPR) / 풀스택(FS, FE, BE) / AI / 클라우드(CLD)
- 같은 group은 한 줄: `3 CD 파이프라인: 설계 · 선택 근거`
- 부록은 사이드바에 넣지 않고 짝 문서 헤더에서 연결
