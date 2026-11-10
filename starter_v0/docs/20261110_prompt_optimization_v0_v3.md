# Ghi chép: Tối ưu Prompt & Tool Declaration (v0 → v3)

- **Ngày thực hiện:** 2026-11-10
- **Người thực hiện:** Vũ Nhật Minh
- **Hạng mục:** Tối ưu `artifacts/system_prompt.md` và `artifacts/tools.yaml` qua 3 vòng, đo bằng base eval (`data/eval_base.json`, 20 case)
- **Provider/model:** `openai` / `gpt-4o-mini`

---

## 1. Tổng quan kết quả

| Version | Thay đổi | Artifact | case_accuracy | routing | args | multiturn | Run file |
|---|---|---|---:|---:|---:|---:|---|
| v0 | Baseline (starter gốc) | — | 0.65 | 0.75 | 0.65 | 1.00 | `runs/v0_B_base_openai_20261110T094753905559.json` |
| v1 | Bỏ chỉ dẫn xấu, thêm rule clarify / xác nhận / phạm vi / nhiều phần | `system_prompt.md` | 0.80 | 0.95 | 0.80 | 0.83 | `runs/v1_B_base_openai_20261110T100827131986.json` |
| v2 | Viết lại description 10 tool (làm gì / khi nào dùng / khi nào không dùng) | `tools.yaml` | 0.95 | 0.95 | 0.95 | 0.83 | `runs/v2_B_base_openai_20261110T103200117783.json` |
| v3 | Thêm rule hội thoại nhiều lượt | `system_prompt.md` | **1.00** | 1.00 | 1.00 | 1.00 | `runs/v3_B_base_openai_20261110T103916785988.json` |

Mỗi version chỉ đổi **một** artifact. Hash xác nhận điều này:

| Version | prompt_hash | tools_hash |
|---|---|---|
| v0 | `eb1c8179815b…` | `5b22a2476d41…` |
| v1 | `d86ff3b9f977…` (đổi) | `5b22a2476d41…` (giữ) |
| v2 | `d86ff3b9f977…` (giữ) | `184467aa7fe5…` (đổi) |
| v3 | `90938016e27e…` (đổi) | `184467aa7fe5…` (giữ) |

Hành trình sửa từng case:

| Case | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| R03 tin AI hôm nay | ❌ | ✅ | ✅ | ✅ |
| R08 tích phân (out of scope) | ❌ | ✅ | ✅ | ✅ |
| R10 thiếu tài khoản | ❌ | ✅ | ✅ | ✅ |
| R11 thiếu URL | ❌ | ⚠️ | ✅ | ✅ |
| R12 xác nhận trước khi gửi | ❌ | ⚠️ | ✅ | ✅ |
| R13 web + tweet song song | ❌ | ⚠️ | ✅ | ✅ |
| R14 viết code (out of scope) | ❌ | ✅ | ✅ | ✅ |
| M06 bỏ Twitter, chuyển web | ✅ | ❌ (regression) | ❌ | ✅ |

---

## 2. v0 — Baseline

### 2.1. Prompt gốc

```text
You are a fast, proactive research assistant with access to tools.

The user is busy and hates being asked questions. Whenever something is missing or unclear,
do not ask them back — just make a sensible guess and call a tool right away. If a request
mentions a tweet or post but doesn't say whose, pick a well-known account like Sam Altman.
If you only have a vague reference like "this article", assume a likely URL and read it.

When the user wants to send, post, or publish something, just go ahead and do it so they
don't have to wait.

Always finish the request in a single step. Pick one tool and fill in its arguments using
your best judgment.
```

`tools.yaml` gốc có description một dòng, mơ hồ (ví dụ `clarify`: "Gửi một câu hỏi cho người dùng.", `send`: "Gửi một đoạn văn bản đi.").

### 2.2. Phân tích: vì sao prompt gốc sai

| Chỉ dẫn trong prompt | Hệ quả | Case bị ảnh hưởng |
|---|---|---|
| "do not ask them back — just make a sensible guess", "pick … Sam Altman" | Thiếu tài khoản thì agent tự đoán `sama` | R10 |
| "assume a likely URL" | Agent bịa URL `example.com/article` | R11 |
| "send, post, or publish … just go ahead" | Gửi Telegram ngay, không xác nhận. Hành động ra ngoài không rút lại được | R12 |
| Không có giới hạn phạm vi, cộng với khuyến khích gửi | Agent giải tích phân / viết code rồi **gọi `send`** để trả lời | R08, R14 |
| "single step. Pick one tool" | Không làm được yêu cầu nhiều phần | R13 |
| Description `lookup` không nói quy ước `query` / `topic` | `query="AI news"` thay vì `"AI"`, thiếu `topic="news"` | R03, R13 |

### 2.3. Kết quả v0: 13/20 (0.65)

| Case | Actual tool calls | Đúng ra | Loại lỗi |
|---|---|---|---|
| R03 | `lookup(query="AI news", topic=news, timeframe=day)` | `query="AI"` | wrong_arg_value |
| R08 | `send(text="Nguyên hàm của x^2 …")` | không gọi tool, từ chối | out_of_scope |
| R10 | `timeline(screenname="sama")` | `clarify(response_type="text")` | missing_info |
| R11 | `fetch(url="https://example.com/article")` | `clarify(response_type="text")` | missing_info |
| R12 | `send(text="Bản tin này")` | `clarify(response_type="yes_no")` | wrong_boundary |
| R13 | `lookup(query="AI news", timeframe=day)` + `social_search(query="AI")` | `lookup(query="AI", topic="news", timeframe="day")` + `social_search` | wrong_arg_value |
| R14 | `send(text="def fibonacci …")` | không gọi tool, từ chối | out_of_scope |

---

## 3. v1 — Sửa system prompt

### 3.1. Giả thuyết

> Prompt gốc ra lệnh sai (đoán thay vì hỏi, gửi không xác nhận, ép một bước, không giới hạn phạm vi). Thay bằng rule đúng sẽ sửa R08, R10, R11, R12, R14.

### 3.2. Thay đổi

Thay toàn bộ prompt bằng:

```markdown
Bạn là research assistant giúp người dùng theo dõi thông tin AI/công nghệ: tweet, tin tức trên web, nội dung bài viết từ URL, paper và chính sách nội bộ công ty.

## Khi thiếu thông tin
- Nếu yêu cầu cần một tài khoản, URL hoặc dữ liệu cụ thể mà người dùng chưa cung cấp, KHÔNG được đoán. Gọi `clarify` với response_type="text" để hỏi đúng thứ còn thiếu.
- Không bao giờ tự bịa handle, URL hay nội dung.

## Gửi / đăng / publish
- Trước khi gửi bất cứ thứ gì ra ngoài (Telegram...), luôn gọi `clarify` với response_type="yes_no" để xin xác nhận.
- Chỉ gọi `send` với confirmed=true sau khi người dùng đã đồng ý ở lượt trước.

## Phạm vi
- Chỉ hỗ trợ việc research thông tin. Yêu cầu ngoài phạm vi (giải toán, viết code, làm bài tập...) thì từ chối lịch sự, nói ngắn mình làm được gì, và KHÔNG gọi tool nào.
- Câu hỏi về bản thân bạn ("bạn làm được gì?") thì trả lời trực tiếp, không gọi tool.

## Yêu cầu nhiều phần
- Nếu yêu cầu có nhiều phần (ví dụ vừa tìm web vừa tìm tweet), gọi đủ các tool cần thiết, có thể gọi song song trong cùng một lượt.
```

| Đoạn mới | Thay cho chỉ dẫn gốc | Nhắm case |
|---|---|---|
| Khi thiếu thông tin | "guess", "Sam Altman", "assume URL" | R10, R11 |
| Gửi / đăng / publish | "just go ahead" | R12 |
| Phạm vi | (gốc không có) | R08, R14 |
| Yêu cầu nhiều phần | "single step, one tool" | R13 |

### 3.3. Phát hiện: comment `<!-- -->` vẫn được model đọc

Lần chạy v1 đầu tiên giữ prompt gốc trong `<!-- … -->` ngay trên prompt mới. Kết quả: **0.75**, và R10 **vẫn tự đoán `timeline(sama)`**, đúng theo câu "pick a well-known account like Sam Altman" nằm trong comment (`runs/v1_B_base_openai_20261110T100230964417.json`).

Nguyên nhân: `run_eval.py` đọc nguyên văn file (`read_text`) và gửi toàn bộ làm system message, không bỏ comment. Model nhận **hai bộ chỉ dẫn mâu thuẫn**.

Xoá comment và chạy lại thì đạt **0.80**, R10 đúng. Kết luận: **mọi text trong file prompt đều là chỉ dẫn với model.** Muốn lưu prompt cũ thì để ở tài liệu, không để trong file prompt.

### 3.4. Kết quả v1 (bản sạch): 16/20 (0.80)

| Case | Thay đổi so với v0 | Giải thích |
|---|---|---|
| R08, R14 | ❌ → ✅ | Rule "Phạm vi": agent từ chối, không gọi tool |
| R10 | ❌ → ✅ | Rule "không được đoán": agent gọi `clarify` |
| R03 | ❌ → ✅ | `query="AI"`. Chưa có rule riêng, có thể do bỏ áp lực "đoán nhanh" |
| R11 | ❌ → ⚠️ | Đã gọi `clarify` nhưng **thiếu `response_type`** |
| R12 | ❌ → ⚠️ | Không còn gửi bừa, nhưng hỏi lại nội dung bản tin (`text`) thay vì xác nhận (`yes_no`) |
| R13 | ❌ → ⚠️ | Đã gọi đủ 2 tool, `query` đúng, nhưng `lookup` **thiếu `topic="news"`** |
| M06 | ✅ → ❌ | **Regression:** user bảo "bỏ Twitter, chuyển sang web", agent vẫn gọi thêm `social_search` |

**Nhận xét:**
- Sửa prompt có tác dụng rõ với lỗi **hành vi** (đoán, gửi bừa, ngoài phạm vi).
- Rule "gọi đủ các tool" làm agent hăng quá, gây regression ở M06. Cần chạy lại toàn bộ eval sau mỗi lần sửa, không chỉ xem các case nhắm tới.
- Còn lại là lỗi **chi tiết args** (R11, R12, R13): prompt chung chung chưa đủ, cần sửa ở khai báo tool.

---

## 4. v2 — Viết lại description của tool

### 4.1. Giả thuyết

> Description tool quá mơ hồ, nên model không biết khi nào dùng / không dùng từng tool, và không biết `clarify` phải ghi rõ `response_type`. Viết lại theo mẫu "làm gì / khi nào dùng / khi nào không dùng" sẽ sửa R11, R12, M06.

### 4.2. Thay đổi

Chỉ sửa trường `description` của 10 tool trong `tools.yaml`, không đụng `parameters`. Các thay đổi quan trọng nhất:

| Tool | Description cũ | Điểm chính của description mới |
|---|---|---|
| `clarify` | "Gửi một câu hỏi cho người dùng." | **LUÔN ghi rõ response_type.** `text` khi thiếu thông tin; `yes_no` khi user yêu cầu gửi/đăng: hỏi xác nhận, không hỏi lại nội dung |
| `timeline` | "Lấy các bài đăng gần đây." | Tweet của **một tài khoản cụ thể**; không dùng cho chủ đề; chưa biết tài khoản thì gọi clarify |
| `social_search` | "Tìm trên mạng xã hội." | Tweet theo **chủ đề**; không dùng cho tài khoản cụ thể, tin web, hoặc khi user đã bảo bỏ Twitter |
| `lookup` | "Tra cứu thông tin trên internet." | Web search, dùng cho **tin tức** và thông tin chung; không dùng để đọc URL hay tìm tweet |
| `fetch` | "Lấy nội dung từ một địa chỉ." | Chỉ đọc URL user **đã cung cấp**; không bịa URL |
| `send` | "Gửi một đoạn văn bản đi." | Hành động ra ngoài, không rút lại được; **chỉ gọi khi đã xác nhận**, `confirmed=true`; không dùng để trả lời câu hỏi |
| `format`, `policy`, `papers`, `paper_text` | một dòng chung chung | Ghi rõ phạm vi dùng / không dùng |

### 4.3. Kết quả v2: 19/20 (0.95)

| Case | v1 → v2 | Giải thích |
|---|---|---|
| R11 | ⚠️ → ✅ | Description `clarify` nói "LUÔN ghi rõ response_type" |
| R12 | ⚠️ → ✅ | Description `clarify` nói "gửi/đăng thì yes_no xác nhận" |
| R13 | ⚠️ → ✅ | **Ngoài dự kiến:** description `lookup` ghi "dùng cho tin tức", nên model tự đặt `topic="news"` |
| M06 | ❌ → ❌ | Thêm "không dùng khi user bảo bỏ Twitter" vào `social_search` **chưa đủ** |

**Nhận xét:**
- Description tốt sửa được cả lỗi args (R13), dù dự kiến ban đầu là phải sửa ở `parameters` trong v3.
- M06 không phải lỗi hiểu tool mà là lỗi hiểu **hội thoại**, nên sửa ở tool không ăn thua.

---

## 5. v3 — Rule hội thoại nhiều lượt

### 5.1. Phân tích M06

Input là 3 lượt user:
1. "Mọi người nói gì về OpenAI trên Twitter?"
2. "Bỏ Twitter, chuyển sang tìm trên web tin tức đi"
3. "Giữ chủ đề OpenAI"

Agent gọi **cả** `lookup` **và** `social_search`: nó cộng dồn mọi yêu cầu thay vì hiểu lượt 2 đã huỷ lượt 1. Prompt v1 có rule "gọi đủ các tool", nhưng không có rule nào cho phép lượt sau huỷ hoặc sửa lượt trước.

### 5.2. Giả thuyết

> Prompt thiếu rule multi-turn. Thêm "lượt mới nhất ghi đè; bỏ nguồn thì không gọi tool của nguồn đó" sẽ sửa M06 mà không làm hỏng M01–M05.

### 5.3. Thay đổi

Thêm vào cuối `system_prompt.md`:

```markdown
## Hội thoại nhiều lượt
- Đọc toàn bộ các lượt, nhưng lượt mới nhất được ưu tiên: nếu người dùng sửa lại (đổi người, đổi số lượng, đổi chủ đề, đổi nguồn) thì dùng giá trị mới nhất.
- Nếu người dùng bảo bỏ / không dùng / chuyển khỏi một nguồn (ví dụ "bỏ Twitter, chuyển sang web"), thì KHÔNG gọi tool của nguồn đó nữa, chỉ gọi tool của nguồn mới.
- Thông tin không bị sửa (chủ đề, timeframe, tài khoản) thì giữ nguyên từ lượt trước.
```

### 5.4. Kết quả v3: 20/20 (1.00)

- M06: ❌ → ✅.
- M01–M05 (correction, carry-over) và R13 (gọi song song) **không bị hỏng**, nên rule mới không gây regression.
- Tất cả metric đạt 1.00.

---

## 6. Bài học rút ra

1. **Lỗi hành vi sửa ở prompt, lỗi chọn tool / args sửa ở description.** v1 (prompt) sửa đoán bừa, gửi bừa, ngoài phạm vi. v2 (tools.yaml) sửa `response_type`, `topic`. v3 (prompt) sửa cách hiểu hội thoại.
2. **Model đọc mọi thứ trong file prompt, kể cả comment.** Giữ prompt cũ trong `<!-- -->` làm agent nhận chỉ dẫn mâu thuẫn (v1 lần đầu 0.75, bản sạch 0.80).
3. **Rule mới có thể gây regression.** "Gọi đủ các tool" sửa R13 nhưng làm hỏng M06. Phải chạy toàn bộ eval mỗi lần sửa.
4. **Một thay đổi có thể sửa case ngoài dự kiến.** Description `lookup` ở v2 sửa luôn R13.
5. **Đổi một biến mỗi version** thì có thể quy công cho từng thay đổi. Hash prompt/tools trong run JSON là bằng chứng.

## 7. Giới hạn

- Mỗi version chỉ chạy **một lần**. Model có độ dao động, nên kết quả có thể lệch ±1 case nếu chạy lại.
- 1.00 trên base eval chỉ có nghĩa là đã qua 20 case này, không có nghĩa agent hoàn hảo. Cần thêm group eval (`data/eval_group.json`) để kiểm tra các tình huống khác.

## 8. Trạng thái sau khi merge với nhánh tool mới

Nhánh này đã merge `main`, gồm commit "add 4 tool" (`github_search`, `citation_check`, `currency_convert`, `weather_forecast`). Sau merge:

- `tools.yaml` có **14 tool**, `pytest tests/test_tool_contract.py` pass (75 passed).
- `tools_hash` đã **khác v3** vì có thêm 4 khai báo tool. Kết quả 1.00 của v3 được đo **trước khi** có 4 tool mới.
- **Việc tiếp theo, v4:** chạy lại base eval với 14 tool để kiểm tra tool mới không làm giảm điểm, rồi chạy group eval có case route tới tool mới.

## 9. v4: gộp 4 tool mới

### 9.1. Giả thuyết

> Thêm 4 tool (`github_search`, `citation_check`, `currency_convert`, `weather_forecast`) không làm nhiễu routing của 10 tool cũ, nên base eval giữ 1.00. Group eval đo model có route đúng các tool mới không.

### 9.2. Thay đổi

Không sửa prompt (`prompt_hash` giống v3). `tools.yaml` có thêm 4 khai báo tool (`tools_hash` `44d2a3e5040f…`).

### 9.3. Kết quả

| Bộ eval | Kết quả | Run file |
|---|---|---|
| Base (20 case) | **1.00**, không regression | `runs/v4_B_base_openai_20261110T110804374522.json` |
| Group (10 case, 4 tool mới) | **0.80** (8/10) | `runs/v4_B_group_openai_20261110T110846236722.json` |

| Case sai | Agent làm | Phân tích |
|---|---|---|
| G05 "Ngày mai ở đó có mưa không?" | `weather_forecast(city="Hanoi")` | Tự đoán thành phố. Rule "không đoán" trong prompt chỉ nêu ví dụ tài khoản / URL. Description `weather_forecast` chưa có "thiếu thành phố thì clarify" |
| M03 "250 EUR → VND → thực ra JPY → vẫn dùng số tiền ban đầu" | `currency_convert(250, EUR, VND)` | "ban đầu" bị hiểu là cả yêu cầu ban đầu, nên chỗ sửa sang JPY bị huỷ |

Các rủi ro dự đoán trước nhưng **không xảy ra**: model tự ghi tên thành phố đúng dạng (`Hanoi`, `Da Nang`) và chép nguyên văn `draft_text`.

### 9.4. Phát hiện qua chat live (`transcripts/v4_openai_20261110T111331124873.transcript.json`)

- Agent không từ chối câu hỏi thời tiết, dù đoạn "Phạm vi" trong prompt chỉ nhắc AI/công nghệ.
- `weather_forecast(days=1)` chỉ trả về **hôm nay**, nhưng agent trả lời "ngày mai". Đây là lỗi ý nghĩa tham số mà cả eval lẫn unit test đều không bắt được.

### 9.5. Hướng tiếp theo (chưa làm)

- v5 (`tools.yaml`): description 4 tool mới thêm "thiếu thông tin thì clarify", và ghi rõ `days=1` là hôm nay. Nhắm G05.
- v6 (`system_prompt.md`): rule "giữ X chỉ giữ X, không huỷ các chỗ sửa khác". Nhắm M03.
