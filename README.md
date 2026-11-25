# 🔧 Local Skilled Worker Connect

A web application built with **Python** and **Streamlit** that connects customers with independent local skilled workers (Plumbers, Electricians, Painters, Roofers, Carpenters, and Tile Workers).

---

## 📌 Key Features

- **Two Role-Based Interfaces:** Separate protected dashboards and pages for **Customers** and **Workers** using `st.session_state`.
- **Secure Authentication:** Registration and login using built-in `hashlib` (SHA-256) with a unique 16-byte random salt per user.
- **Broadcast Job Allocation (Core Feature):**
  1. Customer posts a job (`Open`).
  2. The system matches all **available** workers with the same **skill** and **city/location**, creating one `'Pending'` row per worker in `job_broadcasts`.
  3. The first worker to click **Accept Job** claims it inside **one atomic SQLite transaction** (`BEGIN IMMEDIATE`), marking their broadcast `'Accepted'` and all other workers' broadcasts `'Expired'`.
  4. Any second worker who clicks Accept gets `"Sorry, this job was already taken."`
  5. Both customer and worker then see each other's name and phone number.
- **Full Job Lifecycle:** `Open` → `Accepted` → `In Progress` → `Completed` (or `Cancelled` while `Open`).
- **Ratings & Job History:** Customers can rate completed jobs (1–5 stars + review), workers see their average rating, and both roles can filter their job history by status.

---

## 🛠️ Technology Stack

- **Language:** Python 3
- **Web Interface (Presentation Layer):** Streamlit
- **Database (Data Layer):** SQLite (`sqlite3`, built into Python)
- **Security:** `hashlib` + `os.urandom` (built into Python)

---

## 🏗️ 3-Layer Architecture

1. **Presentation Layer (`app.py`, `pages/`):** Renders forms, buttons, and tables using Streamlit. Never talks to SQLite directly.
2. **Logic Layer (`services/`):** Contains business rules, validation, password hashing, and transaction logic.
3. **Data Layer (`database/db.py`):** Manages SQLite connections (`timeout=10`, `PRAGMA foreign_keys = ON`) and table creation.

---

## 📁 Folder Structure

```text
LocalSkilledWorkerConnect/
├── app.py                          # Home, login, registration, logout
├── pages/
│   ├── 1_Customer_Dashboard.py     # Customer summary metrics
│   ├── 2_Post_Job.py               # Post a job + trigger broadcast
│   ├── 3_My_Jobs.py                # Track jobs, cancel Open jobs, rate Completed jobs
│   ├── 4_Worker_Dashboard.py       # Worker metrics, avg rating, availability & profile
│   ├── 5_Available_Jobs.py         # View Pending broadcasts & accept atomically
│   └── 6_My_Work.py                # Manage accepted jobs (In Progress / Completed)
├── database/
│   └── db.py                       # SQLite connection & 5-table schema
├── services/
│   ├── auth_service.py             # Salted SHA-256 hashing, register, login
│   ├── job_service.py              # Job CRUD, worker profile, status, cancel, ratings
│   └── allocation_service.py       # Broadcast matching & atomic accept_job transaction
├── utils/
│   └── helpers.py                  # Shared SKILLS list, sidebar, require_role() guard
├── requirements.txt                # Python dependencies (Streamlit)
└── README.md                       # Project documentation
```

---

## 🗄️ Database Schema (5 Tables)

1. **`users`**: `id`, `name`, `phone` (UNIQUE), `password_hash`, `salt`, `role` (`'customer'` / `'worker'`), `location`
2. **`worker_profiles`**: `user_id` (PK, FK → `users.id`), `skill`, `experience_years`, `is_available` (`1` or `0`)
3. **`jobs`**: `id`, `customer_id` (FK), `skill_needed`, `description`, `location`, `status`, `accepted_by` (FK), `created_at`
4. **`job_broadcasts`**: `id`, `job_id` (FK), `worker_id` (FK), `response` (`'Pending'`, `'Accepted'`, `'Expired'`)
5. **`ratings`**: `id`, `job_id` (UNIQUE, FK), `customer_id` (FK), `worker_id` (FK), `rating` (1–5), `review`, `created_at`

---

## 🔒 Security Practices

- **No plain-text passwords:** Every password is salted with `os.urandom(16).hex()` and hashed with SHA-256.
- **SQL injection prevention:** Every SQL query uses `?` parameterized placeholders.
- **Role-based page protection:** Every page calls `require_role("customer")` or `require_role("worker")` and stops unauthorized access via `st.stop()`.

---

## ▶️ How to Setup & Run

```bash
# 1. Open the project folder
cd LocalSkilledWorkerConnect

# 2. Create and activate a virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Streamlit app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.
