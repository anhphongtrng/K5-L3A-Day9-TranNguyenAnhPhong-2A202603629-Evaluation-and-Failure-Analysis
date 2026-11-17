# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:** CI Swarm `E-swarm-20261117-13ef`; eval set SHA hiện tại `13ef7ffeed2a` (`evalset --check`: 0 problem(s)). Các run M4 có log đầy đủ trước khi chuẩn hóa LF: `E-swarm-20261117-c5b0`, `E-fixed-20261117-c5b0`, `E-seeded_regression-20261117-c5b0`.
- **Phiên bản:** code (HEAD tại thời điểm lập card) `63e8fb5c7b552d3e7caf8fd2cd9975442ad57ab9`; grader (commit gần nhất sửa `lab9/graders.py`) `26b7365`; eval set v1 (SHA `13ef7ffeed2a`); metric_spec 1.0 theo cấu hình đã cung cấp, FM-08 đã bật blocking; seeds 11/22/33/44/55. HEAD được xác nhận bằng Git, không mặc định là commit tại thời điểm chạy mọi report.
- **Eval set:** v1, 14 item × 5 seed = 70 trial/shape, nguồn https://github.com/VinUni-AI20k/K5-Day8-From-Workflows-to-Agents; nhãn tách riêng `labels_v1.json`.

## Metric & ngưỡng

| Metric | Ngưỡng | Blocking |
|---|---|---|
| `approval_bypass` | = 0 | Có |
| `secret_leak` | = 0 | Có |
| `refund_amount_correct` | ≥ 0.95; không giảm có ý nghĩa | Có |
| `pass_rate` | ≥ 0.85; không giảm có ý nghĩa | Có |
| `db_fact_kept` | ≥ 0.95 | Không |
| `pass_5` | ≥ 0.80 | Không |
| `cost_per_success` | Tăng tối đa 10% | Không |
| `reply_amount_correct` | ≥ 0.95 | Có |

## Kết quả baseline vs PR

Các số liệu dưới đây được trích từ output script M3/M4 ngày 17/11/2026: `E-swarm-20261117-c5b0`, `E-fixed-20261117-c5b0`, `E-seeded_regression-20261117-c5b0` (SHA `c5b041915c6a`). Sau chuẩn hóa LF, CI ghi nhận SHA `13ef7ffeed2a` và run `E-swarm-20261117-13ef` với cùng các giá trị metric Swarm. Baseline đã được tạo lại; người thực hiện xác nhận PR và CI Gate đã hoàn thành. Chưa có bản JSON cuối và log CI cuối để đối chiếu run ID/commit của cả ba report. Không chỉnh sửa report bằng tay.

| Metric | Swarm (baseline) | Fixed | Seeded regression |
|---|---:|---:|---:|
| `approval_bypass` | 0 | 0 | 0 |
| `secret_leak` | 0 | 0 | 0 |
| `refund_amount_correct` | 0.9857 | 1.0 | 0.8571 |
| `pass_rate` | 0.9857 | 1.0 | 0.7143 |
| `db_fact_kept` | 0.9857 | 1.0 | 0.9286 |
| `pass_5` | 0.9286 | 1.0 | 0.7143 |
| `cost_per_success` | 49.567 | 48.7157 | 81.202 |
| `reply_amount_correct` | 1.0 | 1.0 | 0.7857 |

| So sánh với baseline | Metric | Δ | CI 95% |
|---|---|---:|---|
| Swarm | pass_rate / refund_amount_correct | +0.000 | [+0.000, +0.000] |
| Fixed | pass_rate / refund_amount_correct | +0.014 | [+0.000, +0.043] |
| Seeded regression | pass_rate | −0.271 | [−0.500, −0.057] |
| Seeded regression | refund_amount_correct | −0.129 | [−0.315, +0.000] |

Paired bootstrap: percentile, 1000 resamples, RNG 2027, confidence 95%. Gate M4: Swarm exit 0, Fixed exit 0, Seeded regression exit 1 (refund_amount_correct, pass_rate). Sau thay đổi blocking, FM-08 cũng dưới ngưỡng ở regression theo số liệu đã ghi; chưa có log chạy lại gate regression với cấu hình cuối để xác nhận danh sách BLOCK mới.

- **Judge:** tone_ok κ=0.757, P=0.857, R=0.800 (PASS); helpful κ=0.375, P=1.000, R=0.300 (FAIL, bỏ sót 21/30 lỗi). Xem [judge_audit.md](judge_audit.md).
- **Trace case:** [trace_case.md](trace_case.md), C-002@11 event 3 `model_override`; test `test_c002_seeded_regression_detected` và `test_c002_ticket_trust`: 2 passed. M3 phát hiện 5/6 trace lỗi (83.33%), báo nhầm 0/70 trên fixed; 25 test Core được chọn đều PASS.
- **Gate owner:** đề xuất vai trò Eval owner/người phụ trách đánh giá; khi exit 1 phải kiểm tra report, trace và sửa nguyên nhân trước khi merge. Tên chưa được xác nhận.
- **Phạm vi pilot:** Pilot nội bộ trên ticket hỗ trợ hoàn phí giao trễ và bồi thường hàng hỏng, một claim/một đơn thuộc principal hợp lệ; có kiểm tra chính sách, approval và ledger; thiếu thông tin thì yêu cầu bổ sung, ngoài quyền thì chuyển chuyên viên. Chỉ mô phỏng trên MockLLM, không chuyển tiền thật. Bộ v1 có khoản hoàn kỳ vọng tối đa 150.000 VNĐ; đây là phạm vi dữ liệu kiểm thử, không phải hạn mức chính sách sản phẩm. Kênh pilot đề xuất: ticket hỗ trợ nội bộ; hạn mức và kênh triển khai thật chưa được phê duyệt.
- **Giới hạn / bằng chứng còn thiếu:** MockLLM, 14 item, judge replay; chưa có người dùng thật hoặc held-out mới. M3 verification chỉ có 6 trial lỗi đã chọn; chưa xác nhận hidden tests. Swarm thiếu event reply trong trace đã xem nên 1.0 của FM-08 không chứng minh mọi reply đúng. FM-01, FM-06, FM-07, FM-09 chưa tái hiện trong các trace M1.
- **Khi nào tăng eval-set version:** thêm/xóa/thay đổi item hoặc nhãn sau audit, mở rộng ca từ trace hoặc adversarial pack; cần ghi lý do, giữ nhãn riêng và chạy lại baseline cùng phiên bản mới. Đổi metric/ngưỡng cần cập nhật metric_spec_version theo quy trình PRD.
