# Báo Cáo Đối Chiếu 3 Trạng Thái — Baseline vs Corrupted vs Repaired

## 1. Bảng Đối Chiếu Hiệu Năng 3 Trạng Thái
| Metric / Chỉ số | Baseline (Dữ liệu Sạch) | Corrupted (Dữ liệu Bị Lỗi) | Repaired (Sau Khi Phục Hồi) | Tác động của Corruption | Mức độ phục hồi |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Data Quality Gate** | ✅ PASSED (100%) | ❌ FAILED (Phát hiện lỗi) | ✅ PASSED (Phục hồi sạch bóng) | Chặn đứng dữ liệu lỗi | Phục hồi toàn vẹn |
| **Kiểm tra Độ Tươi (Freshness)** | ✅ Đạt chuẩn | ❌ Vi phạm cảnh báo (> 180 ngày) | ✅ Đạt chuẩn | Cảnh báo dữ liệu mốc | Đạt chuẩn SLA tươi mới |
| **Retrieval Hit Rate** | 100.0% | 60.0% | 100.0% | Giảm 40.0% | Phục hồi 40.0% |
| **Mean Token F1** | 76.6% | 53.1% | 76.6% | Giảm 23.5% | Phục hồi 23.5% |
| **LLM Judge Score** | 3.80/5.0 | 3.00/5.0 | 3.80/5.0 | Giảm 0.80 điểm | Phục hồi 0.80 điểm |

## 2. Phân Tích Hiện Tượng Silent Failure & Cảnh Báo Observability
1. **Khi bị tiêm lỗi (Corrupted):**
   - Great Expectations 1.x phát hiện vi phạm tính duy nhất (`paper_id` uniqueness) do duplicate rows và trường tóm tắt bị rỗng (`ExpectColumnValueLengthsToBeBetween`).
   - Freshness SLA phát hiện tỷ lệ bài cũ tăng vọt lên (41.7%) do kịch bản `stale_date` (lùi 5 năm), vượt ngưỡng 25% và gắn cờ `is_fresh = False`.
   - Hiệu năng RAG suy giảm rõ rệt (Silent Failure): do tiêu đề bị cắt cụt (`truncate_title`) và tóm tắt bị rỗng/chèn rác (`inject_text_noise`), Agent không thể tìm đúng ngữ cảnh hoặc trả lời sai.
2. **Sau khi chạy phục hồi (Repaired):**
   - Cơ chế Idempotent Repair tái tạo lại dữ liệu sạch từ bản lưu trữ thô ban đầu (`data/raw/`).
   - Các chỉ số Hit Rate, Token F1 và Judge Score khôi phục lại mức Baseline ban đầu.
