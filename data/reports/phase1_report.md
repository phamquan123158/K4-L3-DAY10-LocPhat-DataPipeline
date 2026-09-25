# Báo Cáo Pha 1 — Baseline Data Pipeline & Observability

## 1. Tổng Quan Dữ Liệu Nguồn (Ingestion & Cleaning)
- **Nguồn dữ liệu:** Crossref REST API
- **Tổng số bản ghi:** 24
- **Trạng thái làm sạch:** Hoàn thành (chuẩn hóa schema, tính `age_days`, tạo `text_for_embedding`)

## 2. Kiểm Soát Chất Lượng Dữ Liệu (Data Observability - Great Expectations 1.x)
- **Trạng thái Quality Gate:** `PASS`
- **Giám sát độ tươi (Freshness SLA):** `FRESH` (Tỷ lệ bài quá hạn: 0.0%, ngưỡng cho phép: 25%)
- **Số bài quá hạn (>180 ngày):** 0 / 24

## 3. Đánh Giá Hiệu Năng RAG Trên Dữ Liệu Sạch (Baseline Benchmarks)
| Chỉ số (Metric) | Giá trị Baseline | Đánh giá |
| :--- | :---: | :--- |
| **Số câu hỏi kiểm thử (Samples)** | 10 | Phủ đủ 4 nhóm: summary, authors, date, categories |
| **Retrieval Hit Rate** | 100.0% | Đo lường tỷ lệ tìm đúng tài liệu Ground Truth |
| **Mean Token F1** | 76.6% | Đo lường độ trùng khớp từ ngữ câu trả lời |
| **LLM Judge Accuracy** | 70.0% | Tỷ lệ câu trả lời được LLM Judge chấm đạt |
| **Mean Judge Score (Thang 1-5)** | 3.80 / 5.0 | Điểm chất lượng trung bình từ LLM Judge |

## 4. Kết Luận Pha 1
Dữ liệu sạch đáp ứng đầy đủ các tiêu chuẩn của Data Quality Gate và Freshness SLA. Mô hình RAG đạt hiệu năng cao trên dữ liệu chuẩn, sẵn sàng bước vào Pha 2 (Controlled Corruption Challenge).
