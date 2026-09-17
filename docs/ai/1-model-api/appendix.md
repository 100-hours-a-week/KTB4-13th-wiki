---
wiki: AI-1 모델 API 명세 부록
type: appendix
group: ai-1
owner: 미정
status: 작성중
updated: 2026-09-17
limit_exempt: 원본 API 명세 8개 엔드포인트의 요청·응답 예시 전체를 보존하기 위해 400줄 상한을 넘김 (변환 승인 2026-09-17)
---
**요약** `spec.md` 3장 각 항목에서 옮긴 요청·응답 예시, 그리고 원본 4장의 호출 예시 9개 전체.

## 3.1 예시 (AI 검색 `POST /search`)

**입력**

```json
{
  "query": "김영하 여행의 이유",
  "filters": {
    "category": "에세이",
    "price_min": 10000,
    "price_max": 20000,
    "pub_year_from": 2020,
    "pub_year_to": 2026,
    "in_stock_only": true
  },
  "sort": "relevance",
  "cursor": null,
  "size": 15
}
```

**출력 (200)**

```json
{
  "message": "search_success",
  "data": {
    "results": [
      {
        "book_id": 2077,
        "title": "여행의 이유",
        "author": "김영하",
        "publisher": "문학동네",
        "price": 13500,
        "in_stock": true,
        "cover_url": "https://…/2077.jpg"
      }
    ],
    "next_cursor": "eyJ…(서명됨)",
    "fallback": null
  }
}
```

**0건 응답**. 대화형 추천으로 전환할 수 있다는 신호를 함께 반환한다. 서버는 전환을 수행하지 않는다.

```json
{
  "message": "search_success",
  "data": {
    "results": [],
    "next_cursor": null,
    "fallback": {
      "message": "원하는 책을 못 찾았어요. AI 추천에게 물어볼까요?"
    }
  }
}
```

## 3.2 예시 (텍스트 임베딩 `POST /embeddings`)

**입력**

```json
{ "texts": ["쓸쓸하고 담담한 위로"], "purpose": "query" }
```

**출력 (200)**

```json
{
  "message": "embed_success",
  "data": {
    "vectors": [[0.0123, -0.0456, "…"]],
    "dim": 1024,
    "model": "bge-m3-2026q3"
  }
}
```

## 3.3 예시 (대화형 도서 추천 `POST /recommendations/chat`)

**입력**

```json
{
  "user_id": 123,
  "consented": true,
  "spec": { "…": "현재 추천 조건(6키 전체)" },
  "message": "너무 무겁지 않은 걸로",
  "recent_turns": [{ "role": "user", "text": "비 오는 날 읽을 책 추천해줘" }],
  "exclude_book_ids": [4021],
  "image_ref": null
}
```

**`spec` 스키마**. 서버가 이 형식을 검증한다.

```json
{
  "intent": "semantic",
  "exact": { "title": null, "author": null, "publisher": null },
  "filters": {
    "category": "에세이",
    "price_max": 20000,
    "in_stock_only": true
  },
  "semantic": "비 오는 날 카페에서 읽을 잔잔한 책",
  "anchor_book": null,
  "exclude": [4021]
}
```

**초기 spec**. 새 스레드의 첫 턴, 그리고 422 이후 초기화할 때 BE가 보내는 값이다.

```json
{
  "intent": "semantic",
  "exact": { "title": null, "author": null, "publisher": null },
  "filters": {},
  "semantic": null,
  "anchor_book": null,
  "exclude": []
}
```

**출력 (200). 일반 추천 턴**

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "비 오는 날 분위기에 맞춰 골라봤어요.",
    "spec": { "…": "갱신된 추천 조건(6키 전체)" },
    "recognition": null,
    "cards": [
      {
        "book_id": 1088,
        "rank": 1,
        "match_score": 87,
        "title": "달러구트 꿈 백화점",
        "author": "이미예",
        "price": 12420,
        "cover_url": "https://…/1088.jpg",
        "reason_short": "비 오는 날의 차분한 분위기와 어울리는 따뜻하고 가벼운 판타지예요.",
        "reason_long": "비 오는 날에 어울리는 책을 찾으셨죠. 꿈을 사고파는 상점이라는 설정을 따뜻한 문장으로 풀어내서, 창밖 빗소리와 같이 읽기 좋아요. 한 편이 짧게 끊겨 부담 없이 읽히고, 말씀하신 가격대도 넘지 않습니다.",
        "match_basis": [
          { "label": "분위기", "detail": "잔잔함" },
          { "label": "가격", "detail": "조건 충족" }
        ]
      }
    ],
    "followup": null,
    "buttons": [],
    "degraded": false
  }
}
```

> **`buttons`, `degraded`는 V1 일반 턴에도 항상 존재한다.** 일반 턴은 보통 `buttons: []`, `degraded: false`.

**출력 (200). 이미지 턴 (`image_ref` 있음) (V2)**

표지를 한 권으로 특정한 경우. 도서 소개 문장, 유사 도서 카드, 후속 동작 목록을 함께 반환한다.

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "이 책은 《달러구트 꿈 백화점》(이미예)예요. 잠든 사이 꿈을 사고파는 상점 이야기예요. 비슷한 결의 책도 함께 골라봤어요.",
    "spec": { "…": "anchor_book이 1088로 갱신된 추천 조건" },
    "recognition": { "recognized": true, "book_id": 1088, "candidates": [] },
    "cards": [{ "book_id": 4021, "rank": 1, "…": "일반 턴과 같은 카드 형식" }],
    "followup": null,
    "buttons": [
      { "label": "네", "action": "library_add", "book_id": 1088 },
      { "label": "아니요", "action": "dismiss" }
    ],
    "degraded": false
  }
}
```

**인식 후보가 여럿인 경우**. 확정하지 않고 후보를 최대 3개 제시해 사용자가 고르게 한다.

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "이 책이 맞을까요? 비슷한 표지가 몇 권 있어요.",
    "spec": { "…": "anchor_book은 아직 갱신하지 않은 추천 조건(null 유지)" },
    "recognition": {
      "recognized": false,
      "book_id": null,
      "candidates": [
        {
          "book_id": 1088,
          "title": "달러구트 꿈 백화점",
          "author": "이미예",
          "cover_url": "https://…/1088.jpg",
          "confidence": 0.62
        },
        {
          "book_id": 4021,
          "title": "…",
          "author": "…",
          "cover_url": "…",
          "confidence": 0.55
        }
      ]
    },
    "cards": [],
    "followup": null,
    "buttons": [
      {
        "label": "달러구트 꿈 백화점",
        "action": "confirm_book",
        "book_id": 1088
      },
      { "label": "다시 찍기", "action": "retake" }
    ],
    "degraded": false
  }
}
```

인식 실패면 200에 `candidates: []`와 안내 `reply`로 응답한다.

## 3.4 예시 (개인화 추천 목록 `GET /recommendations/feed`)

**입력**. 쿼리 파라미터로 받는다. 요청 본문은 없다.

```http
# 첫 요청 또는 정렬, 필터를 바꿔 처음부터 다시 조회. cursor 없음
GET /recommendations/feed?user_id=123&surface=home&sort=match&size=15

# 이어서 조회. 직전 응답의 next_cursor를 그대로 싣는다(값은 URL 인코딩)
GET /recommendations/feed?user_id=123&surface=recommend_more&sort=match
    &category=에세이&pub_year_from=2020&match_score_min=70&size=15&cursor=eyJ…
```

**출력 (200)**

```json
{
  "message": "feed_success",
  "data": {
    "items": [
      {
        "book_id": 3310,
        "title": "아무튼, 산",
        "author": "장보영",
        "price": 9900,
        "cover_url": "https://…/3310.jpg",
        "in_stock": true,
        "match_score": 84
      }
    ],
    "next_cursor": "eyJ…(서명됨)",
    "cold_start": false
  }
}
```

## 3.5 예시 (취향 기억 추출 `POST /preferences/extractions`) (V2)

**입력**

```json
{
  "user_id": 123,
  "consented": true,
  "conversation": [
    { "role": "user", "text": "비 오는 날 읽을 책 추천해줘" },
    { "role": "assistant", "text": "잔잔한 소설 위주로 골라봤어요." },
    { "role": "user", "text": "이별 후에 위로가 될 만한 걸로" }
  ],
  "conversation_id": "cv_20260903_a1",
  "existing_preferences": [
    { "type": "mood", "value": "잔잔한 에세이를 선호함" }
  ]
}
```

**출력 (200)**

```json
{
  "message": "extract_success",
  "data": {
    "extractions": [
      {
        "type": "mood",
        "value": "이별 후 위로되는 잔잔한 소설을 찾음",
        "confidence": 0.82,
        "vector": [0.01, -0.04, "…"],
        "dim": 1024,
        "source_conversation_id": "cv_20260903_a1"
      }
    ],
    "nothing_found": false
  }
}
```

## 3.6 예시 (취향 프로필 생성 `POST /preferences/profile`)

**입력**

```json
{
  "user_id": 123,
  "idempotency_key": "prof_20260904_a1b2",
  "onboarding": {
    "reading_times": ["밤"],
    "criteria": ["베스트셀러"],
    "categories": ["에세이", "한국소설"],
    "tags": ["힐링", "성장"],
    "liked_book_ids": [1088, 3310]
  },
  "memories": [
    {
      "type": "author",
      "value": "김영하의 문장을 좋아함",
      "vector": [0.02, -0.01, "…"],
      "dim": 1024
    },
    {
      "type": "mood",
      "value": "이별 후 위로되는 잔잔한 소설을 찾음",
      "vector": [0.01, -0.04, "…"],
      "dim": 1024
    }
  ]
}
```

**출력 (200)**

```json
{
  "message": "profile_success",
  "data": {
    "cold_start": false,
    "profile_version": 3
  }
}
```

## 3.7 예시 (쇼핑 에이전트 `POST /agent/act`) (V2)

**입력**

```json
{
  "user_id": 123,
  "conversation_id": "cv_…",
  "message": "3만원 안에서 2권 골라 담아줘",
  "context_cards": [
    {
      "book_id": 1088,
      "rank": 1,
      "price": 13500,
      "match_score": 92,
      "in_stock": true
    },
    {
      "book_id": 4021,
      "rank": 2,
      "price": 14000,
      "match_score": 87,
      "in_stock": true
    },
    {
      "book_id": 3310,
      "rank": 3,
      "price": 12800,
      "match_score": 81,
      "in_stock": true
    }
  ],
  "focused_book_id": 1088,
  "user_context": { "logged_in": true, "has_default_address": true },
  "allow_tools": null,
  "idempotency_key": "idem_…"
}
```

**출력 (200)**

```json
{
  "message": "agent_success",
  "data": {
    "reply": "《달러구트 꿈 백화점》 + 《아무튼, 산》 = 26,300원. 이 둘 담을까요?",
    "tool_calls": [
      {
        "name": "recommendations.candidates",
        "arguments": { "size": 20 },
        "result": {
          "count": 20,
          "candidates": [
            { "book_id": 1088, "match_score": 92 },
            { "book_id": 3310, "match_score": 81 },
            { "book_id": 4021, "match_score": 87 }
          ]
        },
        "grounded": true
      },
      {
        "name": "inventory.check",
        "arguments": { "book_ids": [1088, 3310, 4021] },
        "result": {
          "1088": { "price": 13500, "in_stock": true },
          "3310": { "price": 12800, "in_stock": true },
          "4021": { "price": 14000, "in_stock": true }
        },
        "grounded": true
      }
    ],
    "resolved_reference": {
      "ref": "3만원 2권",
      "book_ids": [1088, 3310],
      "confidence": 0.9
    },
    "selection": {
      "goal": "budget_pick",
      "constraints": { "budget_total": 30000, "count": 2, "in_stock": true },
      "chosen": [
        { "book_id": 1088, "price": 13500, "match_score": 92 },
        { "book_id": 3310, "price": 12800, "match_score": 81 }
      ],
      "total_price": 26300,
      "alternatives_considered": 3
    },
    "buttons": [
      {
        "label": "담기",
        "action": "confirm_selection",
        "book_ids": [1088, 3310]
      },
      { "label": "다른 조합", "action": "reselect" }
    ]
  }
}
```

**출력 예시. 유형별**

**시키는 대로 실행, 담기**

```json
{
  "message": "agent_success",
  "data": {
    "reply": "《달러구트 꿈 백화점》을 장바구니에 담았어요.",
    "tool_calls": [
      {
        "name": "cart.add",
        "arguments": { "book_id": 1088, "qty": 1 },
        "result": { "cart_count": 3 },
        "grounded": true
      }
    ],
    "resolved_reference": {
      "ref": "1번",
      "book_ids": [1088],
      "confidence": 0.97
    },
    "selection": null,
    "buttons": [
      { "label": "장바구니 보기", "action": "navigate", "target": "CART-001" }
    ]
  }
}
```

**되물음 (confidence 낮음, tool 미실행)**

```json
{
  "message": "agent_success",
  "data": {
    "reply": "어떤 책 말씀이실까요? 방금 추천한 1번 《달러구트 꿈 백화점》이 맞을까요?",
    "tool_calls": [],
    "resolved_reference": {
      "ref": "그 책",
      "book_ids": [],
      "confidence": 0.41
    },
    "selection": null,
    "buttons": [
      { "label": "네, 1번", "action": "confirm_reference", "book_id": 1088 },
      { "label": "아니요", "action": "dismiss" }
    ]
  }
}
```

**비교** (`book.detail` 읽기 tool 사용)

```json
{
  "message": "agent_success",
  "data": {
    "reply": "1번은 문장이 담백해 부담이 적고, 3번은 화제작인데 호흡이 무거워요. 가격은 700원 차이(1번 13,500 / 3번 12,800), 별점은 1번 4.6, 3번 4.4예요.",
    "tool_calls": [
      {
        "name": "book.detail",
        "arguments": { "book_id": 1088 },
        "result": { "price": 13500, "rating_avg": 4.6 },
        "grounded": true
      },
      {
        "name": "book.detail",
        "arguments": { "book_id": 3310 },
        "result": { "price": 12800, "rating_avg": 4.4 },
        "grounded": true
      }
    ],
    "resolved_reference": {
      "ref": "1번, 3번",
      "book_ids": [1088, 3310],
      "confidence": 0.95
    },
    "selection": null,
    "buttons": [
      { "label": "1번 담기", "action": "confirm_reference", "book_id": 1088 }
    ]
  }
}
```

**배송 문의, 범위 밖 (tool 없음, 딥링크)**

```json
{
  "message": "agent_success",
  "data": {
    "reply": "주문 상태는 주문내역에서 확인하실 수 있어요.",
    "tool_calls": [],
    "resolved_reference": null,
    "selection": null,
    "buttons": [
      { "label": "주문내역", "action": "navigate", "target": "ORDER-LIST-001" }
    ]
  }
}
```

## 3.8 예시 (서버 상태 점검 `GET /health`)

**출력 (200)**

```json
{
  "status": "degraded",
  "version": "a1b2c3d",
  "replication_lag_seconds": 4,
  "components": {
    "gateway": "ok",
    "database": "ok",
    "vector_index": "ok",
    "llm": "unavailable",
    "embedding": "ok"
  }
}
```

## 4. API 호출 예시와 예시 응답

원본 4장 전체. 서버 구현 전이라 응답은 **명세 기준 예상 응답**이다. 구현 직후 고정 질문 30개 × 3회로 실측해 실제 응답으로 교체한다.

### 예시 1: AI 검색 `POST /search`

```bash
curl -X POST <https://ai.internal.bookjeok.com/search> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -H "X-Request-Id: req_20260907_0001" \
  -d '{"query":"쓸쓸하고 담담한 위로","filters":{"category":"에세이"},"sort":"relevance","size":15}'
```

```json
{
  "message": "search_success",
  "data": {
    "results": [
      {
        "book_id": 2091,
        "title": "슬픔을 아는 사람",
        "author": "유진목",
        "publisher": "문학동네",
        "price": 14400,
        "in_stock": true,
        "cover_url": "https://…/2091.jpg"
      }
    ],
    "next_cursor": "eyJ…(서명됨)",
    "fallback": null
  }
}
```

### 예시 2: 텍스트 임베딩 `POST /embeddings`

```bash
curl -X POST <https://ai.internal.bookjeok.com/embeddings> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"texts":["쓸쓸하고 담담한 위로"],"purpose":"query"}'
```

```json
{
  "message": "embed_success",
  "data": {
    "vectors": [[0.0123, -0.0456, "…"]],
    "dim": 1024,
    "model": "bge-m3-2026q3"
  }
}
```

### 예시 3: 챗봇 도서 추천 `POST /recommendations/chat`

```bash
curl -X POST <https://ai.internal.bookjeok.com/recommendations/chat> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"consented":true,"spec":{"intent":"semantic","exact":{"title":null,"author":null,"publisher":null},"filters":{},"semantic":"퇴근길에 읽을 짧은 소설","anchor_book":null,"exclude":[]},"message":"유머 있으면 좋겠어","recent_turns":[],"exclude_book_ids":[],"image_ref":null}'
```

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "퇴근길에 가볍게 읽히는 쪽으로 골라봤어요.",
    "spec": {
      "intent": "semantic",
      "exact": { "title": null, "author": null, "publisher": null },
      "filters": { "in_stock_only": true },
      "semantic": "퇴근길에 읽을 짧고 유머 있는 소설",
      "anchor_book": null,
      "exclude": []
    },
    "recognition": null,
    "cards": [
      {
        "book_id": 1088,
        "rank": 1,
        "match_score": 87,
        "title": "…",
        "author": "…",
        "price": 12420,
        "cover_url": "https://…/1088.jpg",
        "reason_short": "짧은 호흡에 유머가 섞인 연작이라 퇴근길 한 편씩 읽기 좋아요.",
        "reason_long": "퇴근길에 읽을 짧은 소설을 찾으셨고, 유머가 있으면 좋겠다고 하셨죠. 한 편이 지하철 몇 정거장이면 끝나는 연작이라 끊어 읽기 좋습니다. 웃기려 애쓰지 않는 건조한 유머라 피곤한 저녁에도 부담이 없어요.",
        "match_basis": [
          { "label": "분위기", "detail": "유머" },
          { "label": "분량", "detail": "짧은 호흡" }
        ]
      }
    ],
    "followup": null,
    "buttons": [],
    "degraded": false
  }
}
```

### 예시 4: 표지 사진 인식 (V2). `POST /recommendations/chat` 이미지 턴

```bash
curl -X POST <https://ai.internal.bookjeok.com/recommendations/chat> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"consented":true,"spec":{"intent":"semantic","exact":{"title":null,"author":null,"publisher":null},"filters":{},"semantic":null,"anchor_book":null,"exclude":[]},"recent_turns":[],"exclude_book_ids":[],"image_ref":"<https://s3>.…/up_20260903_abc?X-Amz-Signature=…"}'
```

응답. 한 권으로 특정한 경우:

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "이 책은 《달러구트 꿈 백화점》(이미예)예요. 잠든 사이 꿈을 사고파는 상점 이야기예요. 비슷한 결의 책도 함께 골라봤어요.",
    "spec": {
      "intent": "semantic",
      "exact": { "title": null, "author": null, "publisher": null },
      "filters": {},
      "semantic": null,
      "anchor_book": 1088,
      "exclude": []
    },
    "recognition": { "recognized": true, "book_id": 1088, "candidates": [] },
    "cards": [
      {
        "book_id": 4021,
        "rank": 1,
        "match_score": 79,
        "title": "…",
        "author": "…",
        "price": 13800,
        "cover_url": "https://…/4021.jpg",
        "reason_short": "같은 결의 따뜻한 판타지예요.",
        "reason_long": "찍어 보내신 《달러구트 꿈 백화점》과 같은 결의 따뜻한 판타지예요. 일상에 작은 환상을 하나 얹는 방식이 닮았고, 분량과 호흡도 비슷해서 이어 읽기 좋습니다.",
        "match_basis": [{ "label": "분위기", "detail": "따뜻함" }]
      }
    ],
    "followup": null,
    "buttons": [
      { "label": "네", "action": "library_add", "book_id": 1088 },
      { "label": "아니요", "action": "dismiss" }
    ],
    "degraded": false
  }
}
```

응답. 후보가 여럿이라 확정하지 못한 경우(`spec.anchor_book`은 업데이트하지 않는다):

```json
{
  "message": "recommend_success",
  "data": {
    "reply": "이 책이 맞을까요? 비슷한 표지가 몇 권 있어요.",
    "spec": {
      "intent": "semantic",
      "exact": { "title": null, "author": null, "publisher": null },
      "filters": {},
      "semantic": null,
      "anchor_book": null,
      "exclude": []
    },
    "recognition": {
      "recognized": false,
      "book_id": null,
      "candidates": [
        {
          "book_id": 1088,
          "title": "달러구트 꿈 백화점",
          "author": "이미예",
          "cover_url": "https://…/1088.jpg",
          "confidence": 0.62
        },
        {
          "book_id": 4021,
          "title": "…",
          "author": "…",
          "cover_url": "…",
          "confidence": 0.55
        }
      ]
    },
    "cards": [],
    "followup": null,
    "buttons": [
      {
        "label": "달러구트 꿈 백화점",
        "action": "confirm_book",
        "book_id": 1088
      },
      { "label": "다시 찍기", "action": "retake" }
    ],
    "degraded": false
  }
}
```

### 예시 5: 개인화 추천 피드 `GET /recommendations/feed`

```bash
curl -G <https://ai.internal.bookjeok.com/recommendations/feed> \
  -H "Authorization: Bearer$SERVICE_TOKEN" \
  --data-urlencode "user_id=123" --data-urlencode "surface=home" \
  --data-urlencode "sort=match" --data-urlencode "size=15"
```

```json
{
  "message": "feed_success",
  "data": {
    "items": [
      {
        "book_id": 3310,
        "title": "…",
        "author": "…",
        "price": 9900,
        "cover_url": "…",
        "in_stock": true,
        "match_score": 84
      }
    ],
    "next_cursor": "eyJ…(서명됨)",
    "cold_start": false
  }
}
```

### 예시 6: 취향 기억 추출 (V2) `POST /preferences/extractions`

```bash
curl -X POST <https://ai.internal.bookjeok.com/preferences/extractions> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"consented":true,"conversation":[{"role":"user","text":"비 오는 날 읽을 책 추천해줘"},{"role":"assistant","text":"잔잔한 소설 위주로 골라봤어요."},{"role":"user","text":"이별 후에 위로가 될 만한 걸로"}],"conversation_id":"cv_20260903_a1","existing_preferences":[{"type":"mood","value":"잔잔한 에세이를 선호함"}]}'
```

```json
{
  "message": "extract_success",
  "data": {
    "extractions": [
      {
        "type": "mood",
        "value": "이별 후 위로되는 잔잔한 소설을 찾음",
        "confidence": 0.86,
        "vector": [0.01, -0.04, "…"],
        "dim": 1024,
        "source_conversation_id": "cv_20260903_a1"
      }
    ],
    "nothing_found": false
  }
}
```

### 예시 7: 취향 프로필 생성 및 재계산 `POST /preferences/profile`

온보딩 완료. 응답만으로 프로필을 만들고 200 동기로 즉시 끝난다. 작가 취향은 `memories`(`type: author`)로만 들어온다. **구매, 도서관, 리뷰는 본문에 없다** — 서버가 `user_id`로 복제 테이블에서 읽는다. 가입 직후라 읽어도 비어 있다.

```bash
curl -X POST <https://ai.internal.bookjeok.com/preferences/profile> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"idempotency_key":"prof_20260904_a1b2","onboarding":{"reading_times":["밤"],"criteria":["베스트셀러"],"categories":["에세이","한국소설"],"tags":["힐링","성장"],"liked_book_ids":[1088,3310]},"memories":[{"type":"author","value":"김영하의 문장을 좋아함","vector":[0.02,-0.01,"…"],"dim":1024}]}'
```

```json
{
  "message": "profile_success",
  "data": { "cold_start": false, "profile_version": 1 }
}
```

한 달 뒤. 취향 기억이 늘어 다시 부른다. 본문은 여전히 온보딩과 기억뿐이고, 그 사이의 구매·리뷰는 서버가 복제 테이블에서 읽어 centroid에 넣는다.

```bash
curl -X POST <https://ai.internal.bookjeok.com/preferences/profile> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"idempotency_key":"prof_20261004_c3d4","onboarding":{"reading_times":["밤"],"criteria":["베스트셀러"],"categories":["에세이","한국소설"],"tags":["힐링","성장"],"liked_book_ids":[1088,3310]},"memories":[{"type":"author","value":"김영하의 문장을 좋아함","vector":[0.02,-0.01,"…"],"dim":1024},{"type":"mood","value":"이별 후 위로되는 잔잔한 소설을 찾음","vector":[0.01,-0.04,"…"],"dim":1024}]}'
```

```json
{
  "message": "profile_success",
  "data": { "cold_start": false, "profile_version": 4 }
}
```

이 사용자가 그 사이 2077을 사고 1502에 별점 2점을 줬다면, 2077은 가중치 3으로 centroid에 들어가고 1502는 centroid에서 빠진 채 추천에서도 제외된다. **호출자는 그 사실을 몰라도 된다.** 이 호출 이후에 생긴 구매·리뷰는 프로필을 다시 만들지 않아도 ③, ④가 채점할 때 반영한다.

### 예시 8: 쇼핑 에이전트 턴 (V2) `POST /agent/act`

```bash
curl -X POST <https://ai.internal.bookjeok.com/agent/act> \
  -H "Authorization: Bearer$SERVICE_TOKEN" -H "Content-Type: application/json" \
  -d '{"user_id":123,"conversation_id":"cv_20260904_x1","message":"이거 장바구니에 담아줘","context_cards":[{"book_id":1088,"rank":1,"price":13500,"match_score":92,"in_stock":true},{"book_id":4021,"rank":2,"price":14000,"match_score":87,"in_stock":true}],"focused_book_id":1088,"user_context":{"logged_in":true,"has_default_address":true},"allow_tools":null,"idempotency_key":"idem_a1b2c3"}'
```

```json
{
  "message": "agent_success",
  "data": {
    "reply": "담았어요. 장바구니에서 확인해 보세요.",
    "tool_calls": [
      {
        "name": "cart.add",
        "arguments": { "book_id": 1088, "qty": 1 },
        "result": { "cart_count": 3 },
        "grounded": true
      }
    ],
    "resolved_reference": {
      "ref": "이거",
      "book_ids": [1088],
      "confidence": 0.96
    },
    "selection": null,
    "buttons": [
      { "label": "장바구니 보기", "action": "navigate", "target": "CART-001" }
    ]
  }
}
```

### 예시 9: 서버 상태 점검 `GET /health`

```bash
curl <https://ai.internal.bookjeok.com/health>
```

```json
{
  "status": "ok",
  "version": "a1b2c3d",
  "replication_lag_seconds": 2,
  "components": {
    "gateway": "ok",
    "database": "ok",
    "vector_index": "ok",
    "llm": "ok",
    "embedding": "ok"
  }
}
```
