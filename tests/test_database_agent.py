"""
tests/test_database_agent.py
Quick test suite for the Database Agent — uses a local SQLite DB with sample data.
Run: python tests/test_database_agent.py
"""
import os, json, sqlite3

# ── Setup: create a test SQLite DB with sample data ───────────────────────────
os.environ.setdefault("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_SQLITE_PATH"] = "test_database.db"
os.environ["DB_READ_ONLY"] = "false"
os.environ["DB_AUDIT_LOG"] = "outputs/test_audit.log"

def setup_test_db():
    conn = sqlite3.connect("test_database.db")
    cur = conn.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS orders;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            city TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product TEXT,
            amount REAL,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        INSERT INTO users (name, email, age, city) VALUES
            ('Alice Johnson', 'alice@example.com', 28, 'Mumbai'),
            ('Bob Smith',     'bob@example.com',   34, 'Delhi'),
            ('Carol White',   'carol@example.com', 22, 'Bangalore'),
            ('Dave Brown',    'dave@example.com',  45, 'Mumbai'),
            ('Eve Davis',     'eve@example.com',   31, 'Chennai'),
            ('Alice Johnson', 'alice2@example.com',28, 'Mumbai');  -- duplicate name

        INSERT INTO orders (user_id, product, amount, status) VALUES
            (1, 'Laptop',     75000, 'completed'),
            (1, 'Mouse',       1200, 'completed'),
            (2, 'Keyboard',    3500, 'pending'),
            (3, 'Monitor',    18000, 'completed'),
            (4, 'Headphones',  4500, 'cancelled'),
            (5, 'Webcam',      2800, 'completed'),
            (2, 'Laptop',     75000, 'pending');
    """)
    conn.commit()
    conn.close()
    print("✅ Test DB created: test_database.db (users + orders tables)\n")

setup_test_db()

# ── Import agent AFTER env is set ─────────────────────────────────────────────
from agents.database_agent import run_database_agent

def run_test(name, state_overrides):
    base_state = {
        "task": "", "research_notes": "", "final_report": "",
        "code_result": "", "github_result": "", "pdf_result": "",
        "email_result": "", "convo_result": "", "db_result": "",
        "conversation_history": [], "next": "",
        "pdf_mode": "auto", "pdf_text": "", "pdf_bytes": b"", "pdf2_bytes": b"",
        "email_mode": "auto", "email_context": {},
        "db_mode": "auto", "db_context": {},
    }
    state = {**base_state, **state_overrides}
    result = run_database_agent(state)
    parsed = json.loads(result["db_result"])
    status = "✅" if "error" not in parsed else "❌"
    print(f"{status} [{name}]")
    if "error" in parsed:
        print(f"   ERROR: {parsed['error']}")
    else:
        # Print a short summary of the result
        for k, v in parsed.items():
            if k == "rows":
                print(f"   rows returned: {len(v)}")
            elif k not in ("traceback",):
                val = str(v)[:120]
                print(f"   {k}: {val}")
    print()

# ── Run all tests ─────────────────────────────────────────────────────────────
print("=" * 55)
print("  Database Agent Test Suite")
print("=" * 55 + "\n")

# Category 1 — Connection & Setup
run_test("connect",        {"task": "connect to database", "db_mode": "connect"})
run_test("list_tables",    {"task": "list all tables", "db_mode": "list_tables"})
run_test("table_schema",   {"task": "show schema", "db_mode": "table_schema", "db_context": {"table": "users"}})
run_test("health_check",   {"task": "health check", "db_mode": "health_check"})

# Category 2 — Read & Query
run_test("query",          {"task": "run query", "db_mode": "query", "db_context": {"query": "SELECT * FROM users LIMIT 3"}})
run_test("filter",         {"task": "filter users", "db_mode": "filter", "db_context": {"table": "users", "condition": "city = 'Mumbai'"}})
run_test("search",         {"task": "search for Alice", "db_mode": "search", "db_context": {"table": "users", "keyword": "Alice"}})
run_test("aggregate",      {"task": "count orders", "db_mode": "aggregate", "db_context": {"table": "orders", "agg_func": "SUM", "column": "amount", "group_by": "status"}})
run_test("distinct",       {"task": "unique cities", "db_mode": "distinct", "db_context": {"table": "users", "column": "city"}})
run_test("paginate",       {"task": "paginate", "db_mode": "paginate", "db_context": {"table": "users", "page": 1, "page_size": 3}})
run_test("sort",           {"task": "sort by age", "db_mode": "sort", "db_context": {"table": "users", "column": "age", "order": "DESC"}})

# Category 3 — Write Operations
run_test("insert",         {"task": "insert user", "db_mode": "insert", "db_context": {"table": "users", "data": {"name": "Test User", "email": "test@example.com", "age": 25, "city": "Pune"}}})
run_test("update",         {"task": "update city", "db_mode": "update", "db_context": {"table": "users", "updates": {"city": "Hyderabad"}, "condition": "name = 'Test User'"}})
run_test("delete",         {"task": "delete test user", "db_mode": "delete", "db_context": {"table": "users", "condition": "email = 'test@example.com'"}})

# Category 4 — AI Analysis (requires GROQ_API_KEY)
if os.getenv("GROQ_API_KEY"):
    run_test("find_duplicates", {"task": "find duplicates in users", "db_mode": "find_duplicates", "db_context": {"table": "users", "columns": ["name", "age", "city"]}})
    run_test("data_quality",    {"task": "data quality for orders", "db_mode": "data_quality", "db_context": {"table": "orders"}})
    run_test("nl_to_sql",       {"task": "how many users are from Mumbai?", "db_mode": "nl_to_sql"})
    run_test("auto_insights",   {"task": "give me insights on orders", "db_mode": "auto_insights", "db_context": {"table": "orders"}})
else:
    print("⚠️  Skipping AI tests (GROQ_API_KEY not set)\n")

# Category 5 — Export
run_test("export_csv",     {"task": "export users to csv", "db_mode": "export_csv", "db_context": {"table": "users", "output_path": "outputs/test_users.csv"}})
run_test("export_json",    {"task": "export orders to json", "db_mode": "export_json", "db_context": {"table": "orders", "output_path": "outputs/test_orders.json"}})

# Category 7 — Safety
run_test("validate_safe",  {"task": "validate query", "db_mode": "validate_query", "db_context": {"query": "SELECT * FROM users"}})
run_test("validate_danger",{"task": "validate query", "db_mode": "validate_query", "db_context": {"query": "DROP TABLE users"}})
run_test("audit_log",      {"task": "show audit log", "db_mode": "audit_log", "db_context": {"limit": 10}})

print("=" * 55)
print("  Tests complete! Check outputs/ for exported files.")
print("=" * 55)
