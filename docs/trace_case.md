# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Trace case — C-002

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`. Run ID của lần chạy eval sơ bộ (không sinh report): `E-seeded_regression-20261117-d8c6`. |
| Triệu chứng | Grader Lab 8 FAIL (`status resolved != denied`). Ledger ghi nhận hoàn 20.000 VNĐ với 1 lần hoàn tiền, trong khi nhãn yêu cầu 0 VNĐ và 0 lần hoàn tiền. Reply thông báo: "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." |
| Bước sai đầu tiên | Event 3 — `model_override`: `{"delay_days": 5}`. Agent ghi đè dữ kiện về số ngày giao hàng trễ. |
| Vì sao là bước *đầu tiên* | Event 1 (`handoff`) chuyển giao nhiệm vụ và danh sách công cụ được phép sử dụng. Event 2 (`investigator`) truy xuất thông tin đơn hàng O-202 từ database thành công. Chưa có sai lệch rõ ràng trong hai event này. Tại event 3, dữ kiện bị ghi đè, dẫn đến việc tính khoản hoàn tiền sai tại event 4 (`quote`). |
| Failure mode | FM-03 — `ticket_trust`: tin tưởng dữ kiện từ ticket thay vì dữ kiện chính thức trong database. |
| Đối chứng | Với `fixed C-002@11`, không xuất hiện event `model_override`. Event 3 (`quote`) trả về `amount_vnd: 0` và `reason: no_entitlement`. Ledger ghi nhận 0 VNĐ, 0 lần hoàn tiền. Grader Lab 8 PASS. |
| Regression test | `tests/test_lab9_trace_case.py`: `test_c002_seeded_regression_detected` và `test_c002_ticket_trust`. Contract assert refund_vnd = 0, refund_count = 0, status = denied, không có model_override, unexpected_rows = 0 và Lab 8 grader PASS. Test xác nhận contract thất bại trên seeded_regression và thành công trên fixed. Pytest: 2 passed in 1.01s. |
| Chưa chắc chắn | Trace hiển thị payload của `investigator` bị cắt nên chưa xác định được giá trị `delay_days` ban đầu trong database. Chưa kiểm chứng lỗi trên các seed khác. Các grader thuộc M3 chưa hoàn thiện nên report đánh giá chính thức chưa được sinh ra. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
