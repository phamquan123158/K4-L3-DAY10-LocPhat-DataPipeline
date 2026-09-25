# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Chung Văn Duy |
| **MSSV** | 2A202602854 |
| **Khóa/Lớp** | K4-L3A / K4-L3-DAY10 |
| **Tên nhóm** | Loc Phat |
| **Vai trò chính** | Data Foundation & Baseline Pipeline Integrator (Pha 1: Baseline Data Pipeline & Observability) |
| **Repository** | https://github.com/phamquan123158/K4-L3-DAY10-LocPhat-DataPipeline |
| **Ngày hoàn thành** | 2026-09-25 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Data Ingestion & Fallback** | `src/ingestion/crossref.py`<br>`fetch_source_records()`<br>`parse_crossref_payload()` | Crossref REST API response hoặc snapshot thô `data/raw/crossref_response.json` | 24 bản ghi chuẩn `PaperRecord`, lưu `data/raw/crossref_records.json` | Hoàn thành |
| **Data Cleaning & Normalization** | `src/ingestion/cleaning.py`<br>`build_clean_dataframe()`<br>`_clean_title()`, `_clean_summary()` | `data/raw/crossref_records.json` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` (24 dòng sạch, có `age_days`, `text_for_embedding`) | Hoàn thành |
| **Data Quality Gate & Freshness SLA** | `src/observability/quality.py`<br>`run_data_quality_checks()`<br>`build_freshness_report()` | DataFrame đã làm sạch (`papers_clean.csv`) | `data/quality/baseline_quality_report.json` (GX 1.x suite PASS, Freshness SLA 180 ngày FRESH) | Hoàn thành |
| **Phase 1 Pipeline Orchestration** | `src/pipelines/phase1.py`<br>`script/run_phase1.py` | Config hệ thống, Raw records | End-to-end Phase 1 execution, sinh 5 artifacts chuẩn và `data/reports/phase1_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Dọn dẹp Git Conflict Markers** | Nhánh `main` chung của nhóm / `crossref.py`, `cleaning.py`, `quality.py` | Phát hiện và loại bỏ các ký tự xung đột merge dở dang (`<<<<<<< HEAD`, `=======`), khôi phục tính toàn vẹn cú pháp cho codebase |
| **Fix Bug Date Offset Calculation** | `src/ingestion/cleaning.py` & `src/observability/quality.py` | Xử lý triệt để lỗi `AttributeError` / `TypeError` khi trừ ngày tháng không đồng nhất timezone, bổ sung trường `age_days` vào dictionary trả về |
| **Xác minh Benchmark Baseline** | Hỗ trợ thành viên phụ trách RAG & Vector Index | Chạy kiểm thử baseline đạt Hit Rate 100.0%, Token F1 76.6%, tạo nền tảng vững chắc để nhóm đo độ sụt giảm ở Pha 2 |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Xây dựng module Ingestion Dual-Mode** | `src/ingestion/crossref.py` | Kéo thành công 24 bản ghi bài báo, tự động fallback về snapshot offline khi mất mạng hoặc dính `429 Too Many Requests` | `python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Da tai {len(r)} bai bao')"` in ra `Da tai 24 bai bao` |
| **Tiền xử lý & Chuẩn hóa schema** | `src/ingestion/cleaning.py` | Làm sạch thẻ XML rác, dedup `paper_id`, tính `age_days = (run_date - published).days`, sinh cột `text_for_embedding` | Kiểm tra `data/clean/papers_clean.csv` có đủ 24 dòng, không có giá trị null ở các trường bắt buộc |
| **Thiết lập Data Quality Gate GX 1.x** | `src/observability/quality.py` | Triển khai bộ 4 loại Expectation theo chuẩn Great Expectations 1.x Ephemeral context và Freshness SLA (ngưỡng 180 ngày, max 25% stale) | Chạy kiểm tra chất lượng trả về `Quality check status = True` và Freshness đạt `is_fresh = True` (0.0% quá hạn) |
| **Vận hành Pipeline Pha 1 End-to-End** | `src/pipelines/phase1.py`<br>`script/run_phase1.py` | Kết nối toàn bộ luồng từ Raw Data $\rightarrow$ Clean Data $\rightarrow$ ChromaDB Vector Store $\rightarrow$ Test Set $\rightarrow$ RAG Baseline Eval $\rightarrow$ Báo cáo Markdown | Lệnh `python script/run_phase1.py` chạy từ đầu đến cuối không lỗi (exit code 0), xuất báo cáo `data/reports/phase1_report.md` |

### Output cụ thể tạo ra và xác minh

Báo cáo nghiệm thu Pha 1 tại `data/reports/phase1_report.md` và file số liệu nền `data/results/baseline_metrics.json`:
- **Tổng số bản ghi sạch:** 24 tài liệu.
- **Great Expectations 1.x:** Đạt 6/6 Expectations (100.0% thành công), không có lỗi schema hay dữ liệu rỗng.
- **Freshness SLA:** 0 / 24 bài quá hạn (0.0% stale ratio, thấp hơn rất nhiều so với ngưỡng cảnh báo 25%).
- **Retrieval Hit Rate:** `100.0%` (Truy xuất chính xác 10/10 tài liệu Ground Truth).
- **Mean Token F1:** `76.6%`.
- **LLM Judge Score:** `3.80 / 5.0` (Độ chính xác đạt 70.0%).

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Hệ thống RAG (Retrieval-Augmented Generation) cực kỳ nhạy cảm với chất lượng dữ liệu đầu vào theo nguyên lý **"Garbage In, Garbage Out"**. Nếu dữ liệu metadata bài báo chứa ký tự XML rác (`<i>`, `<b>`), thiếu tiêu đề, trùng lặp mã nhận diện (`paper_id`), hoặc dữ liệu đã quá cũ (temporal staleness), bộ Vector Retriever sẽ truy xuất sai ngữ cảnh, dẫn đến việc LLM sinh câu trả lời bị ảo giác (hallucination) hoặc trả về thông tin sai lệch. Nhiệm vụ của Pha 1 là xây dựng một pipeline chuẩn hóa, bảo toàn nguồn dữ liệu gốc và dựng chốt chặn kiểm dịch tự động (Data Observability Gate) trước khi dữ liệu được nạp vào Vector Database ChromaDB.

### Cách triển khai
1. **Ingestion Fallback (Dual-Mode):** Hàm `fetch_source_records` ưu tiên gọi Crossref REST API. Nếu xảy ra lỗi mạng hoặc lỗi HTTP (`requests.RequestException`), hàm tự động bắt ngoại lệ và đọc dữ liệu từ snapshot dự phòng `data/raw/crossref_response.json`, đảm bảo pipeline luôn có thể tái lập (reproducible) trong mọi điều kiện mạng.
2. **Data Cleaning & Feature Engineering:**
   - Khử trùng lặp bản ghi theo khóa chính `paper_id`.
   - Dùng biểu thức chính quy Regex loại bỏ toàn bộ thẻ định dạng HTML/XML trong `title` và `summary`.
   - Tính toán khoảng cách thời gian `age_days` chuẩn hóa về kiểu `date` thuần túy để so khớp với ngày thực thi `run_date`.
   - Tạo trường tổng hợp `text_for_embedding` bằng cách ghép nối có cấu trúc: `Title: ... | Abstract: ... | Authors: ... | Categories: ...` giúp tối ưu hóa không gian vector của mô hình nhúng `all-MiniLM-L6-v2`.
3. **Data Observability với Great Expectations 1.x:**
   - Khởi tạo context phi lưu trữ `gx.get_context(mode="ephemeral")`, thêm Pandas Data Source và Data Asset động từ DataFrame.
   - Thiết lập 4 kỳ vọng trọng yếu:
     - `ExpectTableRowCountToBeBetween`: Số dòng từ 5 đến 5000.
     - `ExpectColumnValuesToNotBeNull`: Các cột `paper_id`, `title`, `text_for_embedding` tuyệt đối không được phép rỗng.
     - `ExpectColumnValuesToBeUnique`: Đảm bảo `paper_id` là duy nhất trên toàn tập dữ liệu.
     - `ExpectColumnValueLengthsToBeBetween`: Đoạn tóm tắt `summary` phải có độ dài tối thiểu từ 30 ký tự trở lên để đảm bảo giá trị ngữ nghĩa.
4. **Giám sát Freshness SLA:** Duyệt qua các mốc xuất bản, đếm số bài có `age_days > 180 ngày`. Nếu tỷ lệ vượt ngưỡng 25%, gắn cờ vi phạm `is_fresh = False`.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Dữ liệu JSON thô từ Crossref API hoặc file local `data/raw/crossref_response.json` chứa danh sách các bài báo với schema chuẩn Dublin Core / Crossref work items. |
| **Output** | `data/clean/papers_clean.csv` và `data/clean/papers_clean.json` gồm 24 dòng với các cột: `paper_id`, `title`, `summary`, `authors`, `published`, `age_days`, `text_for_embedding`. |
| **Module phụ thuộc** | `core/config.py` (cấu hình đường dẫn), `ingestion/crossref.py` (nguồn nạp thô). |
| **Module sử dụng output** | `retrieval/index.py` (tạo Chroma collection `papers-baseline`), `evaluation/testset.py` (sinh 10 câu hỏi benchmark), `observability/quality.py` (chạy GX suite). |
| **Điều kiện lỗi cần xử lý** | Mất kết nối Internet, lỗi HTTP 429 rate limit, ngày xuất bản không đúng định dạng ISO, dữ liệu chứa thẻ HTML rác hoặc chuỗi rỗng. |

### Cách xác minh

```bash
# 1. Kích hoạt môi trường và set encoding UTF-8
$env:PYTHONIOENCODING="utf-8"

# 2. Xác minh Ingestion thô tải đủ 24 bài báo
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"

# 3. Xác minh Data Cleaning chuẩn hóa 24 dòng
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"

# 4. Xác minh Quality Gate Great Expectations 1.x
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res.get('success'))"

# 5. Chạy toàn bộ chu trình Pha 1
python script/run_phase1.py
```

- **Kết quả mong đợi:** Ingestion tải đủ 24 bài báo; Cleaning xuất đủ 24 dòng; Quality check trả về `status = True`; Script `run_phase1.py` chạy qua 7 bước, kết thúc thành công với mã 0.
- **Kết quả thực tế:** Mọi lệnh đều in đúng chuỗi tín hiệu hoàn thành; báo cáo `data/reports/phase1_report.md` được sinh ra với Hit Rate 100.0%.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/quality/baseline_quality_report.json`, `data/results/baseline_metrics.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi xây dựng chốt kiểm soát chất lượng dữ liệu ở Checkpoint 1, cần lựa chọn cơ chế kiểm tra tính đúng đắn của dữ liệu sau bước làm sạch trước khi đổ vào Vector Database.
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Viết mã kiểm tra thủ công bằng các câu lệnh `assert` hoặc `if/else` của Python (ví dụ: `assert df['paper_id'].is_unique`, `assert df['summary'].str.len().min() >= 30`).
  - *Phương án B:* Triển khai thư viện chuẩn công nghiệp **Great Expectations 1.x** sử dụng chế độ `ephemeral context` kết hợp tính toán Freshness SLA chuyên biệt.
- **Phương án đã chọn:** Phương án B (Great Expectations 1.x Ephemeral Mode).
- **Lý do:**
  1. *Tính chuyên nghiệp & Khả năng mở rộng:* Phương án A chỉ báo lỗi bằng Exception đột ngột làm sập luồng, không xuất được báo cáo phân tích chi tiết. Phương án B cho phép cấu hình Expectation mang tính khai báo (declarative), tự động xuất kết quả chi tiết từng bản ghi vi phạm vào file JSON (`validation_results`) phục vụ Data Observability.
  2. *Không gây rác repository:* Chọn chế độ `mode="ephemeral"` giúp GX chạy hoàn toàn trong bộ nhớ RAM, không sinh ra cây thư mục cấu hình cồng kềnh `gx/` hay `great_expectations/` gây xung đột Git cho nhóm.
  3. *Tương thích chuẩn mới:* Sử dụng đúng API GX 1.x Fluent (`context.data_sources.add_pandas`) thay thế API cũ đã lỗi thời.
- **Bằng chứng quyết định phù hợp:** Chốt kiểm dịch chạy rất nhanh (~1 giây), trả về báo cáo JSON chi tiết 6/6 kỳ vọng vượt qua với `success_percent: 100.0%`, ngăn chặn hoàn toàn việc nạp dữ liệu sai cấu trúc vào ChromaDB.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  AttributeError: 'datetime.date' object has no attribute 'days'
  ```
- **Lệnh hoặc bước tái hiện:** Chạy kiểm thử hàm `build_freshness_report` trong `src/observability/quality.py` khi đối tượng ngày tháng được truyền vào để tính độ tuổi bài báo.
- **Nguyên nhân gốc:**
  1. Trong file `src/ingestion/cleaning.py`, hàm `build_clean_dataframe` đã tính toán giá trị `age_days` nhưng lại quên thêm cặp khóa - giá trị `"age_days": age_days` vào dictionary được lưu vào danh sách bản ghi trả về, khiến DataFrame sạch bị thiếu cột này.
  2. Tại hàm `build_freshness_report` trong `src/observability/quality.py`, đoạn code dự phòng (fallback) tự tính tuổi bài báo lại thực hiện phép toán `(today - pub_date).days` trong khi biến `pub_date` đã bị ép kiểu thành `datetime.date`, và trong một số nhánh xử lý đối tượng bị hiểu nhầm là `date` không hỗ trợ thuộc tính `.days` trực tiếp do lỗi đóng mở ngoặc biểu thức.
- **Cách xử lý:**
  1. Cập nhật `src/ingestion/cleaning.py`: Bổ sung rõ ràng trường `"age_days": age_days` vào dictionary trả về của mỗi bản ghi trong hàm `build_clean_dataframe`.
  2. Cập nhật `src/observability/quality.py`: Viết lại hàm trợ giúp `_calc_age(row)` đảm bảo cả `today` và `pub_date` đều là đối tượng `datetime.date` chuẩn, thực hiện phép trừ giữa hai đối tượng `date` để thu được một `datetime.timedelta`, sau đó mới truy xuất thuộc tính `.days`:
     ```python
     delta = today - pub_date
     return delta.days
     ```
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_phase1.py`, bước 6 Freshness SLA chạy mượt mà, in ra `Quality Gate Status: True, Freshness: True` mà không còn bất kỳ ngoại lệ nào.
- **Điều học được:** Khi làm việc với dữ liệu thời gian trong pipeline, luôn phải chuẩn hóa kiểu dữ liệu (`datetime` vs `date`) và quản lý chặt chẽ schema hợp đồng giữa các tầng tiền xử lý và tầng observability.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - *Bước 1 (Ingestion):* Kéo payload thô từ Crossref REST API (hoặc snapshot offline), bóc tách thành danh sách các thực thể `PaperRecord` và lưu bản sao thô vào `data/raw/crossref_records.json`.
   - *Bước 2 (Cleaning):* Loại bỏ thẻ XML, khử trùng lặp theo `paper_id`, tính toán độ tuổi `age_days` và ghép chuỗi đại diện ngữ nghĩa `text_for_embedding`.
   - *Bước 3 (Quality Inspection):* Đưa DataFrame qua chốt kiểm định Great Expectations 1.x và Freshness SLA. Nếu dữ liệu không đạt chuẩn, pipeline sẽ cảnh báo hoặc từ chối nạp.
   - *Bước 4 (Vector Indexing):* Sử dụng mô hình nhúng `sentence-transformers/all-MiniLM-L6-v2` chuyển đổi `text_for_embedding` thành các vector 384 chiều và nạp kèm metadata vào collection `papers-baseline` của ChromaDB.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Bộ `test_set.json` gồm 10 câu hỏi đa dạng thuộc 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`). Mỗi câu hỏi đều gắn kèm danh sách `ground_truth_doc_ids` (mã định danh tài liệu chứa câu trả lời đúng) và chuỗi `ground_truth` (nội dung đáp án mẫu).
   - Khi đo lường **Retrieval Quality**: So sánh các `doc_id` mà ChromaDB truy xuất được với `ground_truth_doc_ids`. Nếu tài liệu chuẩn nằm trong danh sách top-k trả về, tính là 1 Hit. Tỷ lệ hit trên toàn bộ tập câu hỏi tạo nên chỉ số **Retrieval Hit Rate**.
   - Khi đo lường **Answer Quality**: Câu trả lời sinh ra từ LLM được đối chiếu với `ground_truth` thông qua chỉ số trùng khớp từ vựng (**Token F1**) và được một mô hình giám khảo (**LLM Judge**) chấm điểm chất lượng theo thang từ 1 đến 5.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (Great Expectations 1.x):** Tập trung kiểm định **tính toàn vẹn về mặt cấu trúc và cú pháp của dữ liệu** (Structural & Schema Integrity). Chẳng hạn: bảng có bị rỗng không, khóa chính có bị trùng lặp không, các trường quan trọng có bị gán giá trị `null` hay quá ngắn không.
   - **Freshness monitoring (Data Staleness SLA):** Tập trung đo lường **tính hợp thời của dữ liệu theo trục thời gian** (Temporal Drift). Một bản ghi có thể hoàn toàn hợp lệ về mặt cấu trúc (không null, tiêu đề dài), nhưng nếu ngày xuất bản đã cách hiện tại hơn 180 ngày và tỷ lệ bài cũ vượt quá 25%, hệ sinh thái RAG sẽ cảnh báo vi phạm SLA vì nguy cơ trả về thông tin lỗi thời cho người dùng.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Đây là nguyên tắc cốt lõi của phương pháp thực nghiệm có kiểm soát (Controlled Experiment). Việc giữ nguyên vẹn một bộ câu hỏi kiểm thử chuẩn (Benchmark Test Set) cố định xuyên suốt cả 3 trạng thái giúp đảm bảo tính khách quan: mọi sự thay đổi về điểm số (Hit Rate giảm từ 100% xuống 60%, Token F1 giảm từ 76.6% xuống 53.1%) hoàn toàn bắt nguồn từ **sự suy giảm chất lượng của dữ liệu** (Data Corruption) chứ không phải do sự thay đổi độ khó của câu hỏi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - **Về mặt Artifact:** Quá trình phục hồi phải có tính **Idempotent Repair**, nghĩa là tái tạo dữ liệu sạch một cách an toàn từ nguồn tin cậy bất biến ban đầu (`data/raw/crossref_records.json` $\rightarrow$ `data/clean/papers_clean_repaired.csv`), không phải sửa chắp vá cục bộ trên tập dữ liệu hỏng.
   - **Về mặt Observability:** Chốt kiểm dịch Great Expectations 1.x trên tập phục hồi phải chuyển từ `FAILED` trở lại `PASSED`, và Freshness SLA phải đạt chuẩn `FRESH`.
   - **Về mặt AI Performance Metrics:** Retrieval Hit Rate phải khôi phục hoàn toàn từ 60.0% trở lại mức Baseline 100.0%, và Mean Token F1 phải hồi phục về mức ban đầu (~76.6%).

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | **100.0%** | 60.0% | **100.0%** | Ở Baseline, 10/10 tài liệu đều được truy xuất chính xác; khi bị tiêm lỗi giảm 40% và được phục hồi 100% sau repair |
| `mean_token_f1` | **76.6%** | 53.1% | **76.6%** | Độ trùng khớp từ ngữ câu trả lời đạt mức cao ở Baseline, phản ánh context truyền cho LLM rất sạch và giàu thông tin |
| `judge_accuracy` | **70.0%** | 50.0% | **70.0%** | Tỷ lệ câu trả lời đạt yêu cầu của LLM Judge đạt 7/10 câu ở điều kiện dữ liệu chuẩn |
| `mean_judge_score` | **3.80 / 5.0** | 3.00 / 5.0 | **3.80 / 5.0** | Điểm trung bình đánh giá chất lượng câu trả lời đạt mức khá tốt (3.80) |
| **Quality checks** | **PASSED (100%)** | FAILED | **PASSED (100%)** | 6/6 Expectations của Great Expectations 1.x đều đạt ở dữ liệu sạch Pha 1 |
| **Freshness status** | **FRESH** | STALE | **FRESH** | Tỷ lệ bài quá hạn 180 ngày bằng 0.0%, hoàn toàn nằm trong ngưỡng cho phép (<25%) |

### Kết luận từ số liệu
1. **Chuỗi sụt giảm chất lượng:** Khi dữ liệu bị tiêm lỗi cắt ngắn tiêu đề (`truncate_title`), xóa tóm tắt (`blank_summary`) và nhân bản dòng (`duplicate_rows`) $\rightarrow$ Great Expectations lập tức báo động FAILED (vi phạm tính duy nhất và độ dài tóm tắt), Freshness SLA báo động STALE $\rightarrow$ Hiệu năng RAG sụt giảm nghiêm trọng (Hit Rate giảm từ 100% xuống 60%, Token F1 giảm 23.5%). Đây là minh chứng rõ nét cho hiện tượng **Silent Failure**.
2. **Chuỗi phục hồi an toàn:** Nhờ duy trì bản sao lưu thô bất biến `data/raw/` $\rightarrow$ Luồng Idempotent Repair tái tạo lại DataFrame sạch $\rightarrow$ Quality Gate và Freshness SLA lập tức quay lại trạng thái PASSED $\rightarrow$ Retrieval Hit Rate khôi phục trọn vẹn về 100.0% và Token F1 trở lại 76.6%.

- **Hiện tượng đáng chú ý nhất:** Việc cắt ngắn tiêu đề bài báo dưới 8 ký tự làm suy giảm nặng nề nhất đến khả năng tìm kiếm vector, do tiêu đề chứa các từ khóa định danh chính của bài báo khoa học.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Nguyên tắc Data Lineage & Raw Preservation:** Tuyệt đối không bao giờ làm sạch hay chỉnh sửa trực tiếp trên dữ liệu gốc. Luôn bảo toàn bản sao thô (Raw Snapshot) ở trạng thái bất biến (Immutable) để làm điểm tựa khôi phục hệ thống khi xảy ra sự cố.
2. **Sự nguy hiểm của Silent Failure trong AI:** Dữ liệu bẩn không gây ra crash ứng dụng hay lỗi runtime đỏ ở tầng server, nhưng làm cho AI trả lời ngô nghê và sai lệch. Nếu không có hệ thống Data Observability đo lường định lượng, kỹ sư sẽ hoàn toàn mù mờ trước sự suy giảm chất lượng này.
3. **Data Observability là tuyến phòng thủ hàng đầu:** Việc cài đặt Great Expectations 1.x và Freshness SLA ngay tại cửa ngõ Pipeline giúp phát hiện sớm và ngăn chặn dữ liệu bẩn xâm nhập vào Vector Database, tiết kiệm chi phí tính toán và bảo vệ uy tín của hệ thống AI.

### Nếu có thêm thời gian
Tôi sẽ xây dựng một cơ chế **Automated Schema Evolution & Circuit Breaker**: Khi dữ liệu từ nguồn bên thứ ba (như Crossref API) đột ngột thay đổi cấu trúc hoặc vi phạm Quality Gate quá 3 lần liên tiếp, hệ thống sẽ tự động ngắt kết nối nạp, chuyển sang sử dụng bộ nhớ đệm an toàn và gửi cảnh báo qua Webhook tới đội ngũ kỹ sư dữ liệu.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Chung Văn Duy  
**MSSV:** 2A202602854  
**Ngày xác nhận:** 2026-09-25
