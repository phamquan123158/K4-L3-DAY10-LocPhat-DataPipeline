# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Loc Phat`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `https://github.com/phamquan123158/K4-L3-DAY10-LocPhat-DataPipeline`

---

## 1. Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | **Nguyễn Minh Tuấn** | **2A202602850** | `tuannm.23bi14441@usth.edu.vn` | Trưởng nhóm / Pipeline Integrator (`core/`, `ingestion/`, `quality.py`, `corruption.py`, `reporting.py`, orchestration) | `report/2A202602850_NguyenMinhTuan.md` |
| 2 | [Họ và tên TV2] | [MSSV TV2] | [Email TV2] | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) | `report/<MSSV2>_HoTen.md` |
| 3 | [Họ và tên TV3] | [MSSV TV3] | [Email TV3] | RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/<MSSV3>_HoTen.md` |
| 4 | [Họ và tên TV4] | [MSSV TV4] | [Email TV4] | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, reporting) | `report/<MSSV4>_HoTen.md` |

---

## 2. Cá nhân

### Nguyễn Minh Tuấn - 2A202602850
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline (Pipeline Integrator & Data Observability Lead).
- **Công việc chi tiết đã hoàn thành:**
  - Hoàn thiện module Ingestion và cơ chế Dual-Mode offline fallback (`src/ingestion/crossref.py`).
  - Xây dựng quy trình làm sạch dữ liệu, tính `age_days`, tạo `text_for_embedding` và dedup `paper_id` (`src/ingestion/cleaning.py`).
  - Triển khai Data Quality Gate Great Expectations 1.x ephemeral mode và Freshness SLA (`src/observability/quality.py`).
  - Xây dựng bộ thử thách tiêm 6 kịch bản lỗi dữ liệu và log chi tiết (`src/ingestion/corruption.py`).
  - Xuất báo cáo đối chiếu 3 trạng thái và điều phối toàn bộ luồng thực thi (`phase1.py`, `corruption_flow.py`, `reporting.py`).
- **Điều học được / Đóng góp chính:**
  - Nắm vững kiến trúc Idempotent Data Pipeline cho hệ thống RAG và kỹ thuật thiết lập trạm kiểm định dữ liệu tự động ngăn chặn Silent Failure.

### [Họ và tên TV2 - MSSV2]
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu.
- **Công việc chi tiết đã hoàn thành:**
  - [Thành viên 2 tự cập nhật phần việc chi tiết]
- **Điều học được / Đóng góp chính:**
  - [Thành viên 2 tự cập nhật thu hoạch cá nhân]

### [Họ và tên TV3 - MSSV3]
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - [Thành viên 3 tự cập nhật phần việc chi tiết]
- **Điều học được / Đóng góp chính:**
  - [Thành viên 3 tự cập nhật thu hoạch cá nhân]

### [Họ và tên TV4 - MSSV4]
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - [Thành viên 4 tự cập nhật phần việc chi tiết]
- **Điều học được / Đóng góp chính:**
  - [Thành viên 4 tự cập nhật thu hoạch cá nhân]
