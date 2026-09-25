# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| Khóa/Lớp          | K4                                                                        |
| Tên nhóm          | Loc Phat                                                                  |
| Repository        | https://github.com/phamquan123158/K4-L3-DAY10-LocPhat-DataPipeline        |
| Ngày hoàn thành   | 2026-09-25                                                                |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | **Nguyễn Minh Tuấn** | **2A202602850** | Trưởng nhóm & Pipeline Integrator | Ingestion (`crossref.py`), Cleaning (`cleaning.py`), Quality Gate (`quality.py`), Corruption (`corruption.py`), Reporting (`reporting.py`), Orchestration (`phase1.py`, `corruption_flow.py`) |
| 2 | **Chung Văn Duy** | **2A202602854** | Data Foundation & Baseline Pipeline | Ingestion (`crossref.py`), Cleaning (`cleaning.py`), Raw Snapshot (`data/raw/`), Phase 1 End-to-End Integration (`phase1.py`) |
| 3 | **Phạm Quân** | **2A202602890** | Data Quality & Benchmark Evaluation | Evaluation set (`testset.py`), retrieval smoke test (`index.py`, `qa.py`), baseline verification (`run_phase1.py`) |


---

## 2. Tóm tắt kết quả

Nhóm Loc Phat đã hoàn thành 100% các yêu cầu từ Checkpoint 0 đến Checkpoint 6 của bài lab Day 10: Data Pipeline & Data Observability for RAG. 

1. **Baseline Pipeline:** Thu thập 24 bản ghi học thuật từ Crossref API (hỗ trợ Dual-Mode offline fallback), làm sạch văn bản, tính toán tuổi đời `age_days`, tạo `text_for_embedding`, lưu trữ vector vào ChromaDB với mô hình nhúng `all-MiniLM-L6-v2`. Thiết lập bộ test set chuẩn gồm 10 câu hỏi bao phủ 4 dạng bài toán (`summary`, `authors`, `date`, `categories`). Baseline đạt **Retrieval Hit Rate = 100.0%**, **Mean Token F1 = 76.6%**, và vượt qua trạm kiểm định chất lượng Great Expectations 1.x (`PASSED`) cùng Freshness SLA (`FRESH`).
2. **Data Corruption & Silent Failure:** Triển khai 6 kịch bản tiêm lỗi thực tế (`drop_latest_records`, `blank_summary`, `inject_text_noise`, `truncate_title`, `stale_date`, `duplicate_rows`). Kết quả kiểm định chứng minh chốt chặn Observability phát hiện vi phạm ngay lập tức (`Quality Gate = False`, `Freshness SLA = False` với tỷ lệ bài cũ 41.7%). Đồng thời, hiệu năng của RAG Agent sụt giảm nghiêm trọng (**Hit Rate tụt xuống 60.0%**, **Mean Token F1 tụt xuống 53.1%**).
3. **Idempotent Repair:** Kích hoạt cơ chế tự phục hồi an toàn từ bản sao lưu thô ban đầu (`data/raw/`), tái tạo dữ liệu sạch và re-index ChromaDB. Toàn bộ chỉ số hiệu năng được khôi phục trọn vẹn về mức ban đầu (**Hit Rate = 100.0%**, **Mean Token F1 = 76.6%**).

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Nguồn Crossref API (hoặc Snapshot Offline data/raw/)
    ├── 1. Kéo dữ liệu & Lưu bản gốc (Raw Preservation) -> data/raw/crossref_records.json
    ├── 2. Làm sạch & Chuẩn hóa (Transformation)        -> data/clean/papers_clean.csv (.json)
    ├── 3. Trạm kiểm soát chất lượng (Quality Gate)     -> Great Expectations 1.x & Freshness SLA
    ├── 4. Nhúng ngữ nghĩa & Lưu Vector (Index)         -> all-MiniLM-L6-v2 + ChromaDB
    ├── 5. Đánh giá chất lượng RAG (Benchmark)          -> Hit Rate, Token F1, LLM Judge Score
    ├── 6. Thử thách tiêm lỗi dữ liệu (Corruption)      -> Giả lập 6 lỗi thực tế -> data/results/corruption_log.json
    └── 7. Phục hồi an toàn & Đối chiếu (Repair)        -> Tái tạo từ Raw & Báo cáo 3 trạng thái
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | Crossref REST API / `crossref_response.json` | Fetch, retry/fallback, parse fields, raw preservation | `data/raw/crossref_records.json` | Nguyễn Minh Tuấn, Chung Văn Duy |
| **Cleaning** | `data/raw/crossref_records.json` | Khử thẻ XML, tính `age_days`, tạo `text_for_embedding`, dedup `paper_id` | `data/clean/papers_clean.csv`, `papers_clean.json` | Nguyễn Minh Tuấn, Chung Văn Duy |
| **Embedding/index** | Cleaned DataFrame | MiniLM 384-dim vector embedding, Persistent ChromaDB | `data/chroma/`, `data/embeddings/` | Nhóm / hợp tác chung |
| **Evaluation** | Cleaned DataFrame & Chroma index | Sinh 10 câu test set, tính Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `baseline_metrics.json` | Phạm Quân |
| **Observability** | DataFrame sạch / lỗi | Ephemeral context GX 1.x, 4 Expectations, Freshness SLA | `data/quality/*_quality_report.json` | Nguyễn Minh Tuấn, Chung Văn Duy |
| **Corruption/repair**| `papers_clean.json` & raw records | Tiêm 6 kịch bản lỗi, log lỗi, idempotent restore từ raw | `corruption_log.json`, `papers_clean_repaired.csv` | Nguyễn Minh Tuấn |
| **Orchestration** | Toàn bộ pipeline | Điều phối Baseline và Corruption-Repair flow | `phase1_report.md`, `corruption_report.md` | Nguyễn Minh Tuấn |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `gemini` (hoặc `mock` cho local evaluator) |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 bài báo |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày (ngưỡng vi phạm SLA: > 25% bài cũ) |
| Random seed | Cố định logic determinism theo chỉ mục bài báo |

### Lệnh cài đặt

```bash
# Kích hoạt môi trường và cài đặt editable package
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Lệnh chạy

1. **Baseline Pipeline (CP3):**
   ```bash
   python script/run_phase1.py
   ```
2. **Corruption, Repair & Comparison Flow (CP4 - CP5):**
   ```bash
   python script/run_corruption_flow.py
   ```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| :--- | :--- | :--- | :--- |
| `run_phase1.py` | Thành công | 2026-09-25 16:31 UTC | `data/reports/phase1_report.md`, `baseline_metrics.json` |
| `run_corruption_flow.py` | Thành công | 2026-09-25 16:33 UTC | `data/reports/corruption_report.md`, `corruption_log.json` |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| :--- | :--- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | `query=agentic retrieval augmented generation large language model`, `filter=has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-09-25 (Bảo lưu raw snapshot tại `data/raw/`) |
| Số record nhận được | 24 bài báo |
| Cơ chế retry/backoff | Bắt exception HTTP 429 / mạng, tự động chuyển sang đọc snapshot mẫu `data/raw/crossref_response.json` |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| :--- | :--- | :--- | :--- | :--- |
| `paper_id` | `str` | Có | DOI định danh duy nhất của bài báo | Chuẩn hóa whitespace, drop record nếu null |
| `title` | `str` | Có | Tiêu đề bài báo | Chuẩn hóa khoảng trắng thừa |
| `summary` | `str` | Có | Tóm tắt nghiên cứu | Dùng regex loại bỏ các thẻ HTML/JATS XML `<jats:p>` |
| `authors` | `list[str]` | Không | Danh sách tên tác giả | Ghép họ tên dạng `{given} {family}` |
| `categories` | `list[str]` | Không | Phân loại chuyên ngành | Lấy từ `subject` hoặc gán `"General"` |
| `published` | `str` | Có | Ngày xuất bản | Parse `date-parts` về định dạng ISO 8601 `YYYY-MM-DD` |
| `age_days` | `int` | Có | Độ tuổi tính từ run_date | `(run_date - published).days` |
| `text_for_embedding`| `str` | Có | Văn bản tổng hợp 5 phần đưa vào Chroma | Template: Title + Authors + Published + Categories + Summary |

---

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| :--- | :--- |
| Số câu hỏi | 10 câu hỏi chuẩn hóa |
| Các `question_type` | `summary` (4 câu), `authors` (2 câu), `date` (2 câu), `categories` (2 câu) |
| Ground-truth document ID | DOI chính xác của bài báo trong corpus |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store / collection | ChromaDB collections: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 documents |
| Test set dùng chung | `data/eval/test_set.json` (dùng cố định cho cả 3 trạng thái) |

---

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| :--- | :--- | :--- | :--- |
| Raw response/records | `data/raw/` | Có | Đầy đủ `crossref_response.json` và `crossref_records.json` |
| Cleaned dataset | `data/clean/` | Có | `papers_clean.csv` và `papers_clean.json` (24 dòng) |
| Embedding manifest/index | `data/embeddings/` | Có | `papers_embeddings.json` (ChromaDB collection `papers-baseline`) |
| Evaluation set | `data/eval/` | Có | `data/eval/test_set.json` (10 câu hỏi chuẩn) |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit Rate = 1.0 (100%), Token F1 = 0.766 |
| Quality/freshness | `data/quality/` | Có | `baseline_quality_report.json`, `freshness_report.json` |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo Markdown chi tiết Pha 1 |

### Baseline metrics

| Metric | Giá trị Baseline | Diễn giải |
| :--- | :---: | :--- |
| `retrieval_hit_rate` | **100.0%** | Toàn bộ 10/10 câu hỏi tìm đúng tài liệu Ground Truth |
| `mean_token_f1` | **76.6%** | Độ trùng khớp từ ngữ câu trả lời đạt mức xuất sắc |
| `judge_accuracy` | **70.0%** | Tỷ lệ câu trả lời được LLM Judge công nhận đạt |
| `mean_judge_score` | **3.80 / 5.0** | Điểm chất lượng trung bình từ LLM Judge |

---

## 8. Data quality và freshness

### Quality checks (Great Expectations 1.x)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| :--- | :--- | :--- | :---: | :--- |
| `ExpectTableRowCountToBeBetween` | Completeness | [5, 5000] dòng | **PASS** (Observed: 24) | `test_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` | Completeness | `paper_id`, `title`, `text_for_embedding` không rỗng | **PASS** (Unexpected: 0) | `test_quality_report.json` |
| `ExpectColumnValuesToBeUnique` | Uniqueness | `paper_id` là khóa duy nhất | **PASS** (Duplicates: 0) | `test_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` | Validity | `summary` độ dài tối thiểu $\ge 30$ ký tự | **PASS** (Min observed: 201) | `test_quality_report.json` |

### Freshness

| Thuộc tính | Giá trị |
| :--- | :--- |
| Freshness được đo tại | `data/clean/papers_clean.json` qua trường `age_days` |
| Timestamp mới nhất | `2026-07-22` |
| Timestamp cũ nhất | `2026-03-28` |
| Ngưỡng freshness | `age_days > 180 ngày` (ngưỡng vi phạm: > 25% tổng số dòng) |
| Trạng thái baseline | **FRESH (✅ Đạt chuẩn)** |
| Tỷ lệ bài quá hạn | **4.17%** (1/24 bài), nằm sâu dưới ngưỡng cảnh báo 25% |

---

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `drop_latest_records` | Bỏ rơi 4 bài mới nhất | 4 bài | Thiếu dữ liệu tươi | Giảm Hit Rate của câu hỏi liên quan | Re-fetch / nạp lại từ raw records |
| `blank_summary` | Xóa trắng tóm tắt | 3 bài | Vi phạm độ dài summary $\ge 30$ | Agent không có context để tóm tắt | Tái tạo từ raw abstract |
| `inject_text_noise` | Chèn token rác vô nghĩa | 3 bài | Nhiễu ngữ nghĩa | Làm loãng embedding, giảm F1 score | Khôi phục template text chuẩn |
| `truncate_title` | Cắt tiêu đề $< 10$ ký tự | 4 bài | Mất thông tin tiêu đề | Hỏng cơ chế exact lookup theo tên | Gán lại title gốc từ raw records |
| `stale_date` | Lùi ngày về 5 năm trước | 10 bài | Freshness SLA cảnh báo STALE | Tỷ lệ bài cũ tăng lên 41.7% (> 25%) | Tính lại `age_days` từ ngày gốc |
| `duplicate_rows` | Nhân đôi 4 dòng | 4 bài | Vi phạm tính duy nhất `paper_id` | Gây loãng vector space, hallucination | Deduplicate theo `paper_id` |

---

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Sau phục hồi) | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Data Quality Gate** | ✅ PASSED | ❌ FAILED | ✅ PASSED | Bắt chính xác lỗi | Phục hồi sạch bóng | GX 1.x chặn đứng dữ liệu bẩn |
| **Freshness status** | ✅ FRESH | ❌ STALE | ✅ FRESH | Tỷ lệ cũ tăng lên 41.7% | Trở lại 4.17% | SLA phát hiện dữ liệu mốc |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | **Giảm 40.0%** | **Phục hồi 40.0%** | Silent Failure làm mất dữ liệu truy vấn |
| `mean_token_f1` | **76.6%** | **53.1%** | **76.6%** | **Giảm 23.5%** | **Phục hồi 23.5%** | Câu trả lời bị sai lệch ngữ cảnh |
| `mean_judge_score` | **3.80 / 5.0** | **3.00 / 5.0** | **3.80 / 5.0** | **Giảm 0.80 điểm** | **Phục hồi 0.80 điểm** | LLM Judge đánh giá điểm số suy giảm |

### Kết luận quan hệ nhân quả:
1. **Dữ liệu lỗi $\rightarrow$ Silent Failure:** Khi tiêu đề bị cắt ngắn và tóm tắt bị chèn rác, hệ thống retrieval không tìm thấy đúng tài liệu (Hit Rate giảm 40%), dẫn đến LLM trả lời mơ hồ hoặc sai sự thật mà không hề có runtime error.
2. **Idempotent Repair $\rightarrow$ Khôi phục 100%:** Khi kích hoạt cơ chế tái tạo từ bản sao lưu thô ban đầu (`data/raw/`), dữ liệu được làm sạch lại theo đúng quy chuẩn, đưa mọi chỉ số kỹ thuật và điểm chất lượng RAG quay lại đúng 100% phong độ Baseline.

---

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy `quality.py` trên môi trường Great Expectations 1.x, câu lệnh mẫu cũ `context.sources.pandas_default` gây lỗi `AttributeError` dừng chương trình.
- **Nguyên nhân:** Great Expectations 1.x đã cấu trúc lại toàn bộ API, chuyển sang quản lý `data_sources` và `data_assets` tường minh.
- **Cách xử lý:** Sử dụng chuẩn API Ephemeral Context:
  ```python
  context = gx.get_context(mode="ephemeral")
  data_source = context.data_sources.add_pandas(name="papers_source")
  data_asset = data_source.add_dataframe_asset(name="papers_asset")
  batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
  batch = batch_def.get_batch(batch_parameters={"dataframe": df})
  ```
- **Cách xác minh:** Chạy kiểm thử Bước 3 in ra `Quality check status = True` trong ~1.5 giây, không sinh file rác.

---

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| :--- | :--- | :--- |
| Corpus kích thước nhỏ (24 bài) | Độ bao phủ chuyên ngành hẹp | Mở rộng pagination kéo 500–1000 bài báo Crossref |
| Phục hồi kích hoạt thủ công qua script | Cần kỹ sư can thiệp khi có sự cố | Triển khai Airflow DAG hoặc GitHub Action tự động trigger repair khi GX fail |
| MiniLM chỉ nhúng ngữ nghĩa đơn tầng | Có thể nhầm lẫn với các khái niệm rất chuyên sâu | Bổ sung cơ chế Hybrid Search (BM25 + Dense Vector) và Reranker (Cohere/BGE) |

---

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên có thể tạo và nộp bản báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong repository, report hoặc log.
