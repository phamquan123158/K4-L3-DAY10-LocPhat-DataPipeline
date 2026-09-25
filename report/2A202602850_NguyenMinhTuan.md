# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| Họ và tên         | Nguyễn Minh Tuấn                                                          |
| MSSV              | 2A202602850                                                               |
| Khóa/Lớp          | K4                                                                        |
| Tên nhóm          | Loc Phat                                                                  |
| Vai trò chính     | Trưởng nhóm & Pipeline Integrator (Data Foundation & Observability Lead) |
| Repository        | https://github.com/phamquan123158/K4-L3-DAY10-LocPhat-DataPipeline        |
| Ngày hoàn thành   | 2026-09-25                                                                |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Data Ingestion & Dual-Mode Fallback** | `src/ingestion/crossref.py`<br>• `parse_crossref_payload()`<br>• `fetch_source_records()`<br>• `load_raw_records()` | Crossref API JSON hoặc snapshot thô `crossref_response.json` | Danh sách 24 đối tượng `PaperRecord`, lưu `crossref_records.json` | Hoàn thành |
| **Data Cleaning & Modeling** | `src/ingestion/cleaning.py`<br>• `build_clean_dataframe()` | Danh sách `PaperRecord`, `run_date` | `data/clean/papers_clean.csv` và `.json` (24 dòng sạch, chuẩn `text_for_embedding`, `age_days`) | Hoàn thành |
| **Data Quality Gate (GX 1.x & Freshness)** | `src/observability/quality.py`<br>• `run_data_quality_checks()`<br>• `build_freshness_report()` | DataFrame sạch / lỗi, `settings` | Báo cáo GX 1.x (`test_quality_report.json`, `baseline_quality_report.json`), Freshness SLA report | Hoàn thành |
| **Synthetic Corruption Suite** | `src/ingestion/corruption.py`<br>• `corrupt_clean_dataframe()` | DataFrame sạch `papers_clean.json` | DataFrame bị lỗi 24 dòng, log chi tiết `data/results/corruption_log.json` | Hoàn thành |
| **Reporting & 3-State Comparison** | `src/observability/reporting.py`<br>• `generate_corruption_report()` | Metrics baseline, corrupted, repaired | Báo cáo đối chiếu định lượng `data/reports/corruption_report.md` | Hoàn thành |
| **Pipeline Integration & Orchestration** | `script/run_phase1.py`, `script/run_corruption_flow.py` | Toàn bộ các module trong `src/` | Chạy thông suốt end-to-end, sinh đầy đủ artifacts và metrics | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Debug lỗi múi giờ `age_days` | Module `cleaning.py` & `quality.py` | Chuẩn hóa date calculation tránh lỗi TypeError naive/aware datetime |
| Nâng cấp cú pháp GX 1.x | Cả nhóm / `quality.py` | Thay thế `context.sources.pandas_default` bằng ephemeral context chuẩn GX 1.23+ |
| Quản lý Git & Release | Toàn bộ thành viên nhóm | Kiểm tra working tree, bảo đảm không lọt secret `.env`, commit chuẩn hóa nhánh `main` |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Thu thập & parse dữ liệu học thuật | `src/ingestion/crossref.py` | 24 bài báo khoa học chuẩn hóa, bảo lưu raw snapshot | `python -c "from ingestion.crossref import fetch_source_records; ..."` $\rightarrow$ Đã nạp 24 bài báo |
| Làm sạch, tính độ tươi, khử trùng lặp | `src/ingestion/cleaning.py` | `data/clean/papers_clean.csv`, `papers_clean.json` | In `Clean thành công 24 dòng` |
| Dựng chốt kiểm dịch Great Expectations 1.x | `src/observability/quality.py` | `data/quality/test_quality_report.json` | In `Quality check status = True` |
| Tiêm 6 kịch bản làm bẩn dữ liệu | `src/ingestion/corruption.py` | `data/results/corruption_log.json` | In `Corrupted 24 dòng` |
| Điều phối phục hồi và đối chiếu 3 trạng thái | `script/run_corruption_flow.py` | `data/reports/corruption_report.md` | Console in bảng so sánh, chứng minh Hit Rate phục hồi từ 60% lên 100% |

**Output cụ thể:**
File báo cáo `data/reports/corruption_report.md` với bảng đối chiếu định lượng 3 trạng thái rõ ràng, chứng minh Data Quality Gate và Freshness SLA lập tức phát hiện khi dữ liệu bị lỗi, đồng thời cơ chế Idempotent Repair tái tạo thành công dữ liệu sạch từ bản sao lưu thô ban đầu.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong hệ thống RAG phục vụ AI Agent, khi dữ liệu đầu vào bị lỗi (dữ liệu rỗng, tiêu đề cắt cụt, bài báo cũ, bản ghi nhân bản), mô hình ngôn ngữ lớn (LLM) không báo lỗi đỏ mà tự tin bịa đặt câu trả lời (Silent Failure). Cần xây dựng một hệ thống Data Pipeline tự động hóa với trạm kiểm dịch chất lượng (Data Quality Gate) và cơ chế tự phục hồi an toàn (Self-healing).

### Cách triển khai
1. **Raw Preservation & Dual-Mode:** Kéo metadata từ Crossref REST API. Nếu gặp HTTP 429 hoặc mất mạng, tự động fallback sang đọc `data/raw/crossref_response.json`. Dùng regex loại bỏ thẻ `<jats:p>` và chuẩn hóa ngày theo chuẩn ISO 8601.
2. **Data Cleaning:** Tính tuổi đời `age_days = (run_date - published).days`. Tạo chuỗi ngữ cảnh nhúng `text_for_embedding` gồm 5 trường chuẩn (`Title`, `Authors`, `Published`, `Categories`, `Summary`). Khử trùng lặp bản ghi theo khóa duy nhất `paper_id`.
3. **Data Observability (GX 1.x):** Khởi tạo ephemeral context chạy trên RAM. Thiết lập 4 kỳ vọng bắt buộc (`ExpectTableRowCountToBeBetween`, `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique`, `ExpectColumnValueLengthsToBeBetween`). Thiết lập Freshness SLA cảnh báo `is_fresh = False` nếu tỷ lệ bài cũ (`age_days > 180`) vượt quá 25%.
4. **Controlled Corruption Suite:** Triển khai 6 kịch bản thử thách (`drop_latest_records`, `blank_summary`, `inject_text_noise`, `truncate_title`, `stale_date`, `duplicate_rows`), ghi nhật ký lỗi chi tiết ra file JSON.
5. **Idempotent Repair:** Phục hồi dữ liệu sạch bằng cách đọc lại bản sao lưu thô gốc `data/raw/crossref_records.json` để ghi đè dữ liệu hỏng, tái tạo lại index ChromaDB và xác minh lại hiệu năng.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Raw JSON snapshot từ Crossref API (`crossref_response.json`) |
| **Output** | `papers_clean.csv`, `papers_clean.json`, `test_set.json`, `corruption_log.json`, `phase1_report.md`, `corruption_report.md` |
| **Module phụ thuộc** | `core.config`, `core.utils`, `retrieval.index`, `evaluation.metrics` |
| **Module sử dụng output** | `retrieval/qa.py`, `retrieval/agent.py`, ChromaDB vector database |
| **Điều kiện lỗi cần xử lý** | Lỗi mạng / HTTP 429 Crossref; timezone naive vs aware khi trừ datetime; chuỗi rỗng / null; dữ liệu nhân bản |

### Cách xác minh

```bash
# Kiểm tra Baseline & Quality Gate
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(f'Quality check status = {res[\"success\"]}')"

# Chạy toàn bộ kịch bản Corruption & Repair
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Quality Gate trả về `True` trên dữ liệu sạch, phát hiện `False` trên dữ liệu lỗi, và RAG Hit Rate phục hồi đầy đủ về 100.0%.
- **Kết quả thực tế:** 100% khớp mong đợi (`[Corrupted] Hit Rate: 60.0%` $\rightarrow$ `[Repaired] Hit Rate: 100.0%`).
- **Artifact/log:** `data/quality/test_quality_report.json`, `data/results/corruption_log.json`, `data/reports/corruption_report.md`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Sử dụng thư viện Great Expectations để xây dựng trạm kiểm dịch dữ liệu, tránh việc viết code validation thủ công bằng câu lệnh `if/else` phân mảnh.
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Dùng cú pháp cũ GX 0.18 (`context.sources.pandas_default`).
  - *Phương án B:* Dùng cú pháp GX 1.x mới với ephemeral context (`gx.get_context(mode="ephemeral")`, `data_source = context.data_sources.add_pandas(...)`).
- **Phương án đã chọn:** Phương án B (chuẩn GX 1.x Ephemeral Context).
- **Lý do:** Cú pháp cũ đã bị deprecate và crash trên phiên bản GX mới (1.23+). Ephemeral Context chạy trực tiếp trong RAM, không sinh thư mục cấu hình rác `great_expectations/` trong repo, tốc độ khởi tạo và validate cực nhanh.
- **Bằng chứng quyết định phù hợp:** Chạy test kiểm dịch thành công trong ~1.5 giây, file báo cáo `data/quality/test_quality_report.json` lưu giữ đầy đủ kết quả JSON của từng expectation.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  TypeError: can't subtract offset-naive and offset-aware datetimes
  ```
- **Lệnh hoặc bước tái hiện:** Chạy hàm `build_clean_dataframe` khi `run_date` được truyền vào từ `datetime.now(timezone.utc)` (có timezone) trong khi chuỗi `published` được parse thành datetime không có timezone.
- **Nguyên nhân gốc:** Sự không tương thích giữa offset-aware datetime và offset-naive datetime trong chuẩn thư viện `datetime` của Python.
- **Cách xử lý:** Chuẩn hóa cả hai mốc thời gian về đối tượng `datetime.date` thuần túy (`run_date.astimezone(timezone.utc).date() - pub_date`) trước khi thực hiện phép trừ số ngày (`.days`).
- **Cách xác minh sau khi sửa:** Chạy kiểm thử Bước 2 `build_clean_dataframe(...)` in ra `Tín hiệu hoàn thành: Clean thành công 24 dòng` mượt mà, không còn lỗi TypeError.
- **Điều học được:** Luôn chuẩn hóa ngày tháng về chuẩn `date` hoặc quy ước rõ múi giờ UTC cho mọi cột thời gian trong Data Pipeline.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu JSON thô được kéo từ Crossref API (hoặc snapshot offline), bóc tách thành các đối tượng `PaperRecord`. Module cleaning lọc bỏ thẻ XML rác, tính `age_days`, ghép trường tổng hợp `text_for_embedding` và khử trùng lặp. Sau khi vượt qua chốt kiểm dịch Great Expectations 1.x, dữ liệu được chuyển qua mô hình nhúng `all-MiniLM-L6-v2` để tạo vector 384 chiều và lưu vào Persistent Client của ChromaDB kèm metadata phục vụ truy vấn.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Bộ `test_set.json` gồm 10 câu hỏi thuộc 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`). Khi Agent truy vấn, hệ thống so sánh danh sách document IDs được truy xuất từ ChromaDB với `ground_truth_doc_ids` để tính **Retrieval Hit Rate**. Đồng thời, câu trả lời sinh ra được đối chiếu với `ground_truth` text qua **Token F1** và **LLM Judge Score** (thang điểm 1-5).

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks (Great Expectations 1.x) tập trung vào tính toàn vẹn và cấu trúc của dữ liệu (Schema, Nullability, Uniqueness, Min/Max Length). Trong khi đó, Freshness monitoring đo lường thuộc tính thời gian (Data Staleness / Temporal Drift): phát hiện khi dữ liệu bị lỗi thời quá lâu (`age_days > 180`), vi phạm SLA vận hành của hệ sinh thái AI.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo tính khách quan và khoa học của thực nghiệm (controlled experiment). Giữ cố định tập đề thi giúp mọi sự thay đổi về điểm số (sụt giảm ở Corrupted và phục hồi ở Repaired) hoàn toàn phản ánh tác động của chất lượng dữ liệu, loại trừ yếu tố nhiễu do độ khó của câu hỏi thay đổi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair được coi là thành công khi:
   * **Artifact:** Dữ liệu phục hồi được tái tạo từ nguồn Raw đáng tin cậy (`crossref_records.json` $\rightarrow$ `papers_clean_repaired.csv`), không phải sửa mẹo hay vá víu thủ công.
   * **Observability:** Quality Gate quay lại trạng thái `PASSED` và Freshness SLA đạt chuẩn `FRESH`.
   * **RAG Metrics:** Retrieval Hit Rate khôi phục về mức 100.0% và Mean Token F1 khôi phục về mức Baseline (76.6%).

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | 100.0% | 60.0% | 100.0% | Giảm sâu 40% do tiêu đề bị cắt ngắn và tài liệu mới bị drop |
| `mean_token_f1` | 76.6% | 53.1% | 76.6% | Giảm 23.5% do tóm tắt bị rỗng hoặc chèn token rác |
| `judge_accuracy` | 70.0% | 50.0% | 70.0% | Tỷ lệ câu trả lời đạt chuẩn giảm mạnh khi context bị bẩn |
| `mean_judge_score` | 3.80 / 5.0 | 3.00 / 5.0 | 3.80 / 5.0 | Điểm trung bình sụt giảm 0.8 điểm |
| **Quality checks** | ✅ PASSED | ❌ FAILED | ✅ PASSED | GX 1.x bắt chính xác vi phạm uniqueness và rỗng summary |
| **Freshness status**| ✅ FRESH | ❌ STALE | ✅ FRESH | Tỷ lệ bài cũ tăng vọt lên 41.7% (vượt ngưỡng 25%) |

### Kết luận từ số liệu
1. **Chuỗi sụt giảm:** Tiêm lỗi `drop_latest` & `truncate_title` $\rightarrow$ Quality Gate báo FAILED & Freshness SLA cảnh báo STALE $\rightarrow$ Retrieval Hit Rate sụp đổ từ 100% xuống 60%.
2. **Chuỗi phục hồi:** Chạy Idempotent Repair tái tạo từ raw snapshot $\rightarrow$ Quality Gate và Freshness trở lại PASSED $\rightarrow$ Hit Rate và Token F1 phục hồi 100% về mức Baseline ban đầu.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Data Lineage là tấm khiên bảo vệ hệ thống AI:** Luôn bảo toàn dữ liệu gốc (Raw Preservation) ở định dạng bất biến trước khi làm sạch để có thể phục hồi dữ liệu (Idempotent Repair) bất cứ lúc nào.
2. **Silent Failure cực kỳ nguy hiểm:** Dữ liệu bẩn không làm sập server hay báo lỗi đỏ, nhưng làm suy giảm nghiêm trọng độ chính xác của AI Agent.
3. **Data Observability phải được đặt ở cửa ngõ (Gate):** Dùng Great Expectations 1.x và Freshness SLA chặn đứng dữ liệu lỗi trước khi nạp vào Vector Database là giải pháp phòng thủ hiệu quả nhất.

### Nếu có thêm thời gian
Xây dựng một Webhook tự động kích hoạt pipeline Re-index / Self-healing ngay khi Great Expectations phát hiện vi phạm SLA mà không cần kỹ sư phải chạy lệnh tay.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Minh Tuấn  
**Ngày xác nhận:** 2026-09-25
