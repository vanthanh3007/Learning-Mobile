# Leadership & Mentoring — Tư duy Senior

## Senior khác Middle ở điểm gì?

| | **Middle** | **Senior** |
|---|---|---|
| Focus | Hoàn thành task được giao | Đảm bảo team deliver đúng hướng |
| Scope | Feature/module | System/product |
| Problem solving | Fix bug được giao | Phát hiện và ngăn ngừa vấn đề từ sớm |
| Communication | Báo cáo khi xong | Chủ động cập nhật, escalate khi cần |
| Code review | Viết code sạch | Đảm bảo cả team viết code sạch |
| Decision | Hỏi trước khi làm | Đề xuất trade-off, tự ra quyết định |

---

## Thiết kế kiến trúc — Quy trình

### 1. Thu thập requirements
```
Hỏi trước khi design:
- DAU (Daily Active Users) là bao nhiêu?
- Cần support offline không?
- Data có thay đổi real-time không?
- Cần support nhiều platform không?
- Timeline là bao lâu?
```

### 2. Đề xuất Architecture Decision Record (ADR)
```markdown
# ADR-001: State Management Choice

## Context
App có 15 màn hình, 3 dev, cần viết test.

## Decision
Dùng BLoC + Clean Architecture

## Consequences
(+) Dễ test, separation of concerns rõ ràng
(+) Chuẩn cho team lớn, nhất quán
(-) Boilerplate nhiều hơn GetX
(-) Learning curve cho dev mới

## Alternatives considered
- GetX: nhanh hơn nhưng khó test, scale kém
- Riverpod: tốt nhưng team chưa quen
```

---

## Code Review — Checklist Senior

### Khi nhận PR để review:
```
□ Logic có đúng không? (test đã cover chưa?)
□ Performance có vấn đề không? (N+1 query, unbounded loop?)
□ Security: có expose sensitive data không?
□ Error handling có đủ không?
□ Code có follow architecture của project không?
□ Naming có rõ ràng không?
□ Có cần thêm test không?
```

### Cách review constructive:
```
❌ "Code này sai"
✅ "Đoạn này có thể gây memory leak vì... Bạn có thể thêm dispose() ở đây không?"

❌ "Sao không dùng X?"
✅ "Nếu dùng X thay Y ở đây thì sẽ tránh được rebuild không cần thiết — bạn thấy trade-off thế nào?"
```

---

## Làm việc với Product Owner / Designer

### Khi nhận requirement mơ hồ:
```
PO: "Làm screen này load nhanh hơn"

Senior hỏi:
- "Hiện tại load mất bao lâu? Target là bao nhiêu?"
- "User complain ở màn hình nào cụ thể?"
- "Có data về bottleneck chưa hay cần profiling?"
```

### Khi technical constraint ảnh hưởng design:
```
Designer: "Animation này transition smooth trong 0.3s"
Senior: "Với data load async, chúng ta có 2 option:
  1. Skeleton screen → animation sau khi data về: UX tốt nhưng phức tạp hơn
  2. Optimistic UI → show cached data trước: nhanh nhưng có thể lệch data
  Bạn prefer option nào?"
```

---

## Mentoring Junior/Mid

### Phong cách mentoring hiệu quả:
```
❌ Làm thay luôn
✅ Hướng dẫn tìm cách, review sau

❌ "Sai rồi, làm lại đi"
✅ "Đoạn này có vẻ chưa xử lý trường hợp X, bạn thử debug xem sao?"

Socratic method:
- "Em nghĩ vấn đề ở đây là gì?"
- "Có cách nào khác để handle case này không?"
- "Trade-off của cách em chọn là gì?"
```

### Onboarding người mới:
```
Tuần 1: Setup môi trường, đọc README, làm quen codebase
Tuần 2: Fix bug nhỏ với guidance
Tuần 3-4: Feature nhỏ end-to-end
Tháng 2: Feature medium, PR review có support
Tháng 3: Feature độc lập, bắt đầu review PR người khác
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Kể một lần bạn thiết kế architecture cho một feature lớn. Bạn tiếp cận như thế nào?**
> Cấu trúc trả lời STAR (Situation, Task, Action, Result):
> "Dự án cần thêm offline mode cho tính năng... (S). Tôi cần design data sync layer (T). Tôi đề xuất Repository pattern với cache-first strategy, sync queue cho conflict resolution, và viết ADR để team align (A). Kết quả: giảm 80% complaint về UX khi mạng kém (R)."

**Q: Làm thế nào bạn handle khi Junior push code có vấn đề?**
> Không reject PR mà không giải thích. Comment cụ thể vấn đề + suggest solution + link tài liệu nếu cần. Nếu critical issue, pair programming trực tiếp. Mục tiêu là junior hiểu WHY, không chỉ fix theo lệnh.

**Q: Khi technical debt quá nhiều, bạn làm gì?**
> Không refactor toàn bộ cùng lúc — quá rủi ro. Ưu tiên theo impact: những module thường xuyên thay đổi nhất nên refactor trước. Pitch với PO bằng business impact: "Debt ở module X đang làm mỗi feature mới tốn gấp đôi thời gian, nếu ta dành 1 sprint refactor sẽ tiết kiệm X ngày trong 3 tháng tới."
