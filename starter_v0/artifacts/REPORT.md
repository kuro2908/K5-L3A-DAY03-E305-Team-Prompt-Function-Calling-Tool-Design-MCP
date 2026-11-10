# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | - | - | 0.65 | runs/v0_B_base_openai_20261110T094753905559.json |
| v1 | system_prompt.md | Bỏ chỉ dẫn xấu (đoán/gửi ngay/1 bước), thêm rule clarify, xác nhận send, phạm vi → fix R08 R10 R11 R12 R14 | 0.65 | 0.80 | runs/v1_B_base_openai_20261110T100827131986.json |
| v2 | tools.yaml (description) | Description mơ hồ → viết rõ làm gì / khi nào dùng / khi nào không dùng, clarify ghi rõ response_type → fix R11 R12 M06 | 0.80 | 0.95 | runs/v2_B_base_openai_20261110T103200117783.json |
| v3 | system_prompt.md | Thiếu rule multi-turn → thêm "lượt mới nhất ghi đè, bỏ nguồn thì không gọi tool nguồn đó" → fix M06 | 0.95 | 1.00 | runs/v3_B_base_openai_20261110T103916785988.json |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_arg_value | lookup(query="AI news", topic=news, timeframe=day) | query thừa chữ "news" | v1: tự đúng (query="AI"), chưa có rule riêng; v3 sẽ thêm quy ước cho chắc |
| R08_out_of_scope | out_of_scope | send(text="Nguyên hàm của x^2...") | gọi send cho câu ngoài phạm vi | v1: rule từ chối out-of-scope |
| R10_missing_handle | missing_info | timeline(screenname="sama") | tự đoán tài khoản thay vì hỏi | v1: bỏ chỉ dẫn "cứ đoán", thêm rule clarify |
| R11_missing_url | missing_info | fetch(url="https://example.com/article") | bịa URL | v1: đã gọi clarify nhưng thiếu response_type; v2: ✅ description clarify "LUÔN ghi rõ response_type" |
| R12_confirm_before_send | wrong_boundary | send(text="Bản tin này") | gửi ngay, không xác nhận | v1: không còn gửi bừa nhưng hỏi "text"; v2: ✅ description clarify "gửi/đăng → yes_no xác nhận" |
| R13_parallel_web_and_tweets | wrong_arg_value | lookup(query="AI news", timeframe=day) + social_search(query="AI") | query sai, thiếu topic=news | v1: gọi đủ 2 tool, còn thiếu topic=news; v2: ✅ (description lookup "dùng cho tin tức" → model tự đặt topic=news) |
| R14_out_of_scope_coding | out_of_scope | send(text="def fibonacci...") | gọi send cho câu ngoài phạm vi | v1: rule từ chối out-of-scope |
| M06_switch_tool | wrong_tool | lookup(OpenAI, news) + social_search(OpenAI) | User bảo bỏ Twitter nhưng agent vẫn gọi social_search (regression do rule "gọi đủ tool" ở v1) | v2: vẫn sai (description social_search không đủ); v3: ✅ rule multi-turn trong prompt |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

**Ghi chú trong quá trình làm:**

- *v1, comment trong prompt vẫn được model đọc:* lần chạy v1 đầu tiên giữ prompt cũ trong `<!-- -->`, đạt 0.75, và R10 vẫn tự đoán `timeline(sama)` theo câu "pick a well-known account like Sam Altman" nằm trong comment (`runs/v1_B_base_openai_20261110T100230964417.json`). Xoá comment rồi chạy lại thì đạt 0.80 và R10 đúng (`runs/v1_B_base_openai_20261110T100827131986.json`). Bài học: `run_eval.py` gửi nguyên văn file prompt, nên mọi text trong file đều là chỉ dẫn với model.
- *v1, rule mới gây regression:* rule "yêu cầu nhiều phần thì gọi đủ tool" sửa được R13 (gọi đủ `lookup` + `social_search`), nhưng làm M06 hỏng (user bảo bỏ Twitter mà agent vẫn gọi `social_search`). multiturn_accuracy giảm từ 1.0 xuống 0.83.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | openai / gpt-4o-mini (cloud) | v3 | 1.00 | 1.00 | 1.00 | 1.00 | runs/v3_B_base_openai_20261110T103916785988.json |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
