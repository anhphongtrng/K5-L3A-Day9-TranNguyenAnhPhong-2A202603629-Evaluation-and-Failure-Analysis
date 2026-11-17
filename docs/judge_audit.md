# Judge audit

Chạy tại `src/`:

```bash
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
python -m pytest tests/test_lab9_stats.py -v -m student -o addopts= -k "not paired_bootstrap"
```

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | PASS | Dùng cho đánh giá tone |
| helpful | 100 | 0.375 | 1.000 | 0.300 | FAIL | Loại khỏi gate |

## ≥5 case audit thủ công

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | H-008 | PASS | FAIL | Người | Xưng em, dùng nha quá suồng sã; rubric cần phân biệt thân thiện và thiếu chuyên nghiệp. |
| 2 | H-017 | PASS | FAIL | Người | Gọi khách lớn tuổi là bạn theo ghi chú CSV; rubric yêu cầu xưng hô phù hợp ngữ cảnh. |
| 3 | H-029 | PASS | FAIL | Người | Giọng ra lệnh, không cần nhắn thêm; rubric phải xét toàn bộ câu, không chỉ từ lịch sự. |
| 4 | H-042 | FAIL | PASS | Người | Câu ngắn nhưng đủ ý; không bắt buộc xin lỗi nếu ngữ cảnh không yêu cầu. |
| 5 | H-051 | FAIL | PASS | Người | Từ refund được LogiX cho phép theo ghi chú; không phạt thuật ngữ được chấp nhận. |
| 6 | H-081 | FAIL | PASS | Judge (theo ghi chú CSV) | Người đọc nhầm ticket; cần đối chiếu ticket gốc và xác nhận lại nhãn. Không tự đổi nhãn trong bộ replay. |
| 7 | HL-015 | PASS | FAIL | Người | Reply 55.000đ, ledger 40.000đ theo ghi chú; rubric không được coi câu lịch sự là đủ, số tiền phải kiểm tra bằng code. |
| 8 | HL-016 | PASS | FAIL | Người | Reply 55.000đ, ledger 35.000đ; lời xin lỗi dài không bù được lỗi dữ kiện. |
| 9 | HL-020 | PASS | FAIL | Người | Reply 90.000đ, ledger 120.000đ; đối chiếu số tiền bằng code. |
| 10 | HL-047 | PASS | FAIL | Người | Ok bạn, xử lý rồi nhé; rubric cần kiểm tra xưng hô và nội dung cụ thể. |

Các nhận định dựa trên reply, nhãn và ghi chú của hai CSV công khai, không phải một lượt gán nhãn độc lập hay đối chiếu trực tiếp ledger/ticket gốc.

## Kết luận

- FAIL là lớp dương tính. Tone có TP=24, FP=4, FN=6, TN=66; đạt cả ba ngưỡng nhưng vẫn bỏ sót 6 lỗi và báo nhầm 4 trường hợp theo nhãn hiện tại. Tỷ lệ lỗi quan sát 0.28, hiệu chỉnh Rogan–Gladen 0.30.
- Helpful có TP=9, FP=0, FN=21, TN=70; Precision=1.0 không đủ để làm gate vì Recall=0.3 và κ=0.375 đều dưới ngưỡng. Trong 21 lỗi bị bỏ sót có 18 lỗi sai tiền và 3 lỗi sai xưng hô. Tỷ lệ lỗi quan sát 0.09, hiệu chỉnh 0.30. Hiệu chỉnh tỷ lệ tổng thể không khắc phục việc bỏ sót từng case. Loại Helpful khỏi gate.
- Sửa rubric: tách tone khỏi độ đúng dữ kiện, không thưởng lời xin lỗi dài hoặc sự thân thiện quá mức; ưu tiên kiểm tra phản hồi với bằng chứng. Tiền và approval luôn chấm bằng code, không giao cho judge.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật. Cần rà soát nhãn nghi vấn như H-081 và hiệu chỉnh lại judge trên dữ liệu độc lập sau khi sửa rubric. Không thay đổi nhãn hoặc ngưỡng hiện hành để làm đẹp kết quả.
- Unit test M2 trên máy thực nghiệm: 4 passed, 2 deselected (0.04s). Hai test paired_bootstrap thuộc M4, chưa đánh giá ở M2.
