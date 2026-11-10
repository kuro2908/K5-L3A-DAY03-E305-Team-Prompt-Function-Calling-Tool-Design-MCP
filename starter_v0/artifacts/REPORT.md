# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: E305
- Members: Vũ Nhật Minh (prompt & version), Nam (tool mới), Tùng (unit test & group eval), Vũ (UI)
- Provider/model: OpenAI / `gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Research agent tiếng Việt:** tìm tweet theo tài khoản hoặc chủ đề, tìm tin tức trên web, đọc nội dung URL, tìm paper arXiv và chính sách nội bộ công ty. Ngoài ra agent tìm được repo GitHub, xem thời tiết, quy đổi tỷ giá và kiểm tra bản nháp (đã có nguồn chưa, có lộ email hay API key không).
Thiếu thông tin thì agent **hỏi lại chứ không đoán**. Trước khi gửi gì lên Telegram, agent **luôn hỏi xác nhận**. Yêu cầu ngoài phạm vi (giải toán, viết code) thì agent **từ chối**.

**Điểm eval:** base 20/20 (1.00), group (4 tool mới) 8/10 (0.80).

**Link dùng thử (deploy):**

> URL: https://universal-pit-stated-describe.trycloudflare.com/

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận (yes/no) trước khi gửi | không |
| timeline | Lấy tweet gần đây của một tài khoản X/Twitter cụ thể | không |
| social_search | Tìm tweet theo từ khóa / chủ đề (Latest hoặc Top) | không |
| lookup | Tìm kiếm web và tin tức (lọc theo ngày / tuần / tháng / năm) | không |
| fetch | Đọc nội dung một URL do người dùng đưa | không |
| format | Trình bày kết quả thành digest markdown | không |
| send | Gửi text lên Telegram, chỉ khi đã được xác nhận | không |
| policy | Tra cứu chính sách nội bộ công ty | không |
| papers | Tìm paper trên arXiv | không |
| paper_text | Đọc nội dung PDF một paper arXiv | không |
| github_search | Tìm repository GitHub theo từ khóa, ngôn ngữ, sắp xếp theo sao / cập nhật | **có** |
| citation_check | Kiểm tra bản nháp: đã có link nguồn chưa, có lộ email / API key không | **có** |
| currency_convert | Quy đổi tiền tệ theo tỷ giá thực tế (USD, EUR, JPY, VND…) | **có** |
| weather_forecast | Thời tiết hiện tại và dự báo 1–7 ngày theo thành phố | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tìm 3 repository Python phổ biến nhất về RAG trên GitHub` → `github_search`
2. `Đổi 100 USD sang VND theo tỷ giá hiện tại` → `currency_convert`
3. `Dự báo thời tiết Đà Nẵng 3 ngày tới` → `weather_forecast`
4. `Kiểm tra bản nháp này đã có nguồn chưa: OpenAI vừa ra model mới.` → `citation_check`
5. Thử guardrail:
   - `Tóm tắt 5 tweet mới nhất giúp mình` (agent sẽ hỏi lại tài khoản nào)
   - `Đăng bản tin này lên Telegram` (agent hỏi xác nhận yes/no trước)
   - `Giải giúp mình tích phân x^2` (agent từ chối)

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
| v4 | tools.yaml (merge 4 tool mới) | Thêm 4 tool không làm nhiễu routing → base giữ 1.00; group eval baseline cho tool mới | 1.00 (base) | 1.00 (base) / 0.80 (group) | runs/v4_B_base_openai_20261110T110804374522.json, runs/v4_B_group_openai_20261110T110846236722.json |

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
| G01_github_python_stars | Tìm mã nguồn mở route tới github_search với language, sort và limit. | github_search(query=RAG, language=python, sort=stars, max_results=3) | ✅ PASS (v4) |
| G02_citation_check_privacy | Kiểm tra draft route tới citation_check, không tra policy hay web. | citation_check(draft_text=Liên hệ minh@example.com để nhận báo cáo., check_type=privacy) | ✅ PASS (v4) |
| G03_currency_usd_to_vnd | Quy đổi tiền tệ nhận diện amount và hai mã ISO. | currency_convert(amount=100, from_currency=USD, to_currency=VND) | ✅ PASS (v4) |
| G04_weather_hanoi_three_days | Dự báo thời tiết route tới weather_forecast với thành phố, ngày và đơn vị. | weather_forecast(city=Hanoi, days=3, unit=celsius) | ✅ PASS (v4) |
| G05_weather_missing_city | Không có địa điểm thì phải hỏi lại thay vì đoán. | clarify(response_type=text) | ❌ FAIL (v4): missing tool call clarify; extra tool call weather_forecast |
| M01_github_refine_query | Giữ query ban đầu và áp dụng language, sort, limit qua nhiều lượt. | github_search(query=agent, language=typescript, sort=updated, max_results=2) | ✅ PASS (v4) |
| M02_citation_after_draft | Mang draft từ lượt trước sang citation_check và chọn mode citation. | citation_check(draft_text=OpenAI công bố cập nhật mới. Nguồn: https://openai.com/news/, check_type=citation) | ✅ PASS (v4) |
| M03_currency_carryover | Giữ amount và tiền nguồn, thay đúng tiền đích được sửa. | currency_convert(amount=250, from_currency=EUR, to_currency=JPY) | ❌ FAIL (v4): to_currency: expected 'JPY', got 'VND' |
| M04_weather_unit_and_days | Mang thành phố, cập nhật số ngày và đơn vị qua ba lượt. | weather_forecast(city=Tokyo, days=5, unit=fahrenheit) | ✅ PASS (v4) |
| M05_parallel_github_and_weather | Một yêu cầu đa mục tiêu cần gọi đồng thời hai tool mới. | github_search(query=weather API, language=python, sort=stars, max_results=2) + weather_forecast(city=Da Nang, days=1, unit=celsius) | ✅ PASS (v4) |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

Transcript: `transcripts/v4_openai_20261110T111331124873.transcript.json` (`chat.py --provider openai --version v4`, artifact `v4+p90938016e27e+t44d2a3e5040f`)

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tìm 3 repository Python phổ biến nhất về RAG trên GitHub | `github_search(query="RAG", language="python", sort="stars", max_results=3)` | v4 | ✅ Trả về 3 repo thật (dify, langchain, graphify) kèm số sao và link |
| 2 | Thời tiết ngày mai thế nào? | (không gọi tool, hỏi lại bằng text) | v4 | ✅ Không đoán thành phố, hỏi lại "tên thành phố nào?". ⚠️ Hỏi bằng text chứ không qua tool `clarify` (trong eval sẽ bị chấm sai, xem G05) |
| 3 | Ở Đà Nẵng nhé | `weather_forecast(city="Đà Nẵng", days=1)` | v4 | ⚠️ Ghép đúng thành phố với câu hỏi lượt trước, tool trả dữ liệu thật. **Nhưng `days=1` chỉ trả về hôm nay (10/11), trong khi agent ghi là "ngày mai (10/11/2026)"**, tức là sai ngày |
| 4 | Đăng bản tin này lên Telegram giúp mình | `clarify(response_type="yes_no", question="Bạn có chắc muốn gửi bản tin thời tiết Đà Nẵng vào ngày mai không?")` | v4 | ✅ Không gửi ngay, hỏi xác nhận yes/no. Agent hiểu "bản tin này" là kết quả thời tiết ở lượt trước |

**Nhận xét:**
- Agent **không từ chối** câu hỏi thời tiết, dù đoạn "Phạm vi" trong prompt chỉ nhắc "research AI/công nghệ".
- Lỗi phát hiện qua chat mà eval không bắt được: `weather_forecast` dùng `days=1` để chỉ **hôm nay**, nên muốn xem ngày mai phải dùng `days=2`. Description chưa ghi rõ điều này, nên model hiểu sai và gán nhãn "ngày mai" cho dữ liệu hôm nay. Cách sửa: ghi rõ trong description của `days` ("1 = chỉ hôm nay; ngày mai cần days=2").

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v4_openai_20261110T111331124873.transcript.json` (turn 4), `tests/test_tools_todo.py::test_send_confirmed_without_env_returns_error_and_no_request` | Agent hỏi xác nhận `yes_no` trước khi gửi (R12 pass từ v2, chat turn 4) | Chưa cấu hình bot Telegram thật. `send` khi thiếu env trả về error dict, không gọi network |
| arXiv/company policy | `tests/test_tools_todo.py` (3 test policy) | Policy: lọc theo `policy_area`; dòng giống chỉ dẫn bị tách vào `untrusted_text` | Chưa có eval case riêng cho policy / papers |
| UI | `app.py` (Streamlit), link ở A1 | Chat UI dùng lại `run_model_tool_loop` của `chat.py`, hiện tool calls, ghi transcript cùng format | Link trycloudflare là tạm thời, mất khi tắt tunnel |
| Tool unit tests (`tests/`) | `pytest` output: **108 passed, 0 failed, 0 skipped** | 26 test trong `test_tools_todo.py`: 14 stub TODO đã điền + 12 test cho 4 tool mới (3 test/tool: happy path, input xấu, lỗi HTTP trả error dict) | Mọi HTTP được mock qua `fake_http`, chạy offline |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

- **Số test:** 26 test tool (14 stub TODO + 12 test cho tool mới), cộng 8 contract test và 7 example test.
- **Bug trong tool có sẵn:** chưa phát hiện.
- **Ví dụ unit test bắt được mà eval không bắt được:** `test_weather_forecast_rejects_invalid_days_without_network`. Nếu model gửi `days=10`, tool phải trả về error dict và **không gọi API**. Eval chỉ kiểm tra model chọn tool / args gì, không kiểm tra tool xử lý args xấu thế nào.
- **Ngược lại, chat bắt được mà cả unit test lẫn eval không bắt được:** `days=1` = hôm nay chứ không phải ngày mai (B4, turn 3). Tool chạy đúng theo code, model cũng gọi tool "đúng", nhưng **ý nghĩa** của tham số chưa được mô tả, nên kết quả trả cho user bị sai.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các lỗi **hành vi chung**, không gắn với tool nào: không đoán mà phải hỏi lại (R10), không gửi khi chưa xác nhận (R12), từ chối ngoài phạm vi (R08, R14), gọi nhiều tool khi yêu cầu nhiều phần (R13), và cách hiểu hội thoại nhiều lượt: lượt mới ghi đè, bỏ nguồn thì không gọi (M06, v3).
- **Which fixes belonged in `tools.yaml`?** Các lỗi **chọn tool và giá trị args**: `clarify` phải ghi `response_type` và dùng `yes_no` khi xác nhận gửi (R11, R12); `lookup` dùng cho tin tức nên `topic="news"` (R13); "khi nào không dùng" của từng tool. v2 cho thấy description tốt sửa được cả lỗi args mà không cần đụng `parameters`.
- **Which failure needed manual review instead of automatic grading?**
  - (1) Chat turn 3: model gọi `weather_forecast(days=1)` hợp lệ, nhưng trả lời "ngày mai" bằng dữ liệu hôm nay. Eval chỉ chấm tool call, không chấm nội dung câu trả lời, nên phải đọc transcript mới thấy.
  - (2) R12: "Đăng bản tin này" khi chưa có bản tin. Ở v1 model hỏi lại nội dung (`text`), cũng hợp lý với người dùng, nhưng eval yêu cầu `yes_no`. Cần người xem xét hành vi nào đúng hơn.
  - (3) Chat turn 2: model hỏi lại bằng text thay vì gọi `clarify`. Với user thì như nhau, nhưng eval chấm sai (giống G05).
  - (4) Out-of-scope (R08, R14) chỉ được chấm "không gọi tool", không kiểm tra câu trả lời có thật sự từ chối hay không.
- **What would you improve next?**
  - (1) v5: description 4 tool mới thêm "thiếu thông tin thì clarify" (G05) và ghi rõ nghĩa `days` (1 = hôm nay).
  - (2) v6: rule multi-turn "giữ X chỉ giữ X, không huỷ các chỗ đã sửa khác" (M03).
  - (3) Cập nhật đoạn "Phạm vi" trong prompt để nhắc cả GitHub, thời tiết, tỷ giá.
  - (4) Chạy mỗi version nhiều lần để đo độ dao động. Hiện mỗi version mới chạy 1 lần.

**Kết quả group eval v4 (4 tool mới): 8/10**
- G05 "Ngày mai ở đó có mưa không?": agent tự đoán `city="Hanoi"` thay vì `clarify`. Đây là lỗi cùng loại với R10 ở v0, vì rule "không đoán" trong prompt chỉ nêu ví dụ tài khoản / URL, nên model không áp dụng sang thành phố.
- M03 "250 EUR → tiền Việt → thực ra JPY → vẫn dùng số tiền ban đầu": agent quay về `to_currency="VND"`. Model hiểu "ban đầu" là cả yêu cầu ban đầu, trong khi user chỉ muốn giữ số tiền.

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
