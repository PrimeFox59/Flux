import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib
import uuid
import base64
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px

# --- Konfigurasi ---
st.set_page_config(
    page_title="FLUX Project Manager",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "flux.db"
UPLOAD_FOLDER = "uploads"
ADMIN_ID = "admin123"
DEFAULT_DEV_PASSWORD = "zzz"

# Opsi Dropdown untuk Registrasi (diurutkan secara alphabet)
DEPARTEMEN_OPTIONS = sorted([
    "5S-Tpm-Rationalization", "Corporate Planning", "Development & Trial",
    "Environment & Cn Promotion", "Finance & Accounting", "Foundry Ace",
    "Foundry Central", "Foundry Csm", "General Affairs", "Hrd",
    "Information System", "Internal Audit", "Iso Promoting Office",
    "Maintenance", "Production Equipment Engineering", "Production Machining",
    "Purchasing", "Quality Assurance", "Quality Control", "Sales & Marketing",
    "Safety & Health Work", "Supply Chain Management", "Training Center", "Utility"
])

SEKSI_OPTIONS = sorted([
    "5S-Tpm-Rationalization", "Cavity Making", "Casting Inspection", "Consumable",
    "Core Ace", "Customer Relation", "Despatch & Fps Store", "Development",
    "Doc. Controller", "Electricity", "Environment", "Estimator",
    "Fettling Ace", "Fettling Pms", "Fin. & Acct.", "Finishing 2 Ml",
    "Finishing 2W", "Finishing 4W", "Finishing Ace", "Finishing C/S Hollow",
    "Finishing Fcd", "Finishing Pf", "Foundry Plant Equipment",
    "Gdn & Surat Jalan", "Heat Treatment", "Heat Treatment 2Ml", "Heat Treatment Fcd",
    "Information Technology", "Internal Audit", "Kaizen", "Laboratory",
    "Machining 1", "Machining 2", "Machining 3", "Machining Equipment",
    "Machining Inspection", "Maint 2 Ml", "Maint Chill Cs", "Maint Sm 60",
    "Maint. Ace", "Maint. Disa", "Maintenance Enginering", "Maintenance Fd",
    "Maintenance Mc", "Mat. Store", "Material Inspection", "Mc Engineering",
    "Melting 2Ml", "Melting Ace", "Melting Disamatic", "Melting Fcd",
    "Melting Pms", "Melting Sm 60", "Melting Ssm", "Molding 2 Ml",
    "Molding Ace", "Molding Disamatic", "Molding Pms", "Molding Sm 60",
    "Order & Delivery Control", "Painting Ace", "Painting Mc", "Painting Pms",
    "Pattern Design", "Pattern Making", "Personnel Adm", "Planning Staff",
    "Plant Maint", "Prod. Plann. Monitoring", "Purchasing Good", "Qa Inspection",
    "Quotation", "Receiving", "Sand Reclaiming", "Sand Treatment Ace",
    "Sand Treatment Pms", "Sand Treatment Sm 60", "Scm Jakarta", "Secretary",
    "Shell Core Pms", "Shell Mold Fcd", "Shot Blasting 2 Ml", "Shot Blasting Ace",
    "Shot Blasting Fcd", "Shot Blasting Pms", "Shot Blasting Sm 60",
    "Sm C/S Hollow", "Sm C/S Solid", "Sub Cont", "Training Center",
    "Transport & Control", "Trial & Evaluation", "Water, Air & Gas Supply"
])

# --- Inisialisasi Database dan Folder Uploads ---
def create_db_and_tables():
    """Membuat database dan tabel jika belum ada."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # PENTING: Aktifkan foreign key constraints
    c.execute("PRAGMA foreign_keys = ON")

    # Create users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                fullname TEXT NOT NULL,
                departemen TEXT,
                seksi TEXT,
                role TEXT NOT NULL,
                status TEXT NOT NULL
              )""")

    # Check and add 3 default users if they don't exist
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed_dev_pw = hashlib.sha256(DEFAULT_DEV_PASSWORD.encode()).hexdigest()
        c.execute("INSERT INTO users (id, password, fullname, departemen, seksi, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (ADMIN_ID, hashed_dev_pw, "Main Admin", "Information System", "Information Technology", "Admin", "approved"))
        c.execute("INSERT INTO users (id, password, fullname, departemen, seksi, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("M123", hashed_dev_pw, "Manager", "Foundry Csm", "Foundry Central", "Manager", "approved"))
        c.execute("INSERT INTO users (id, password, fullname, departemen, seksi, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("S123", hashed_dev_pw, "Supervisor", "Foundry Csm", "Finishing 2W", "Supervisor", "approved"))

    # Create projects table first
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                part_name TEXT,
                part_number TEXT,
                customer TEXT,
                model TEXT,
                creator_id TEXT,
                created_at TEXT,
                FOREIGN KEY (creator_id) REFERENCES users(id)
              )""")
    
    # Then check and alter projects table to add new columns if they don't exist
    c.execute("PRAGMA table_info(projects)")
    columns = [col[1] for col in c.fetchall()]
    if 'created_at' not in columns:
        c.execute("ALTER TABLE projects ADD COLUMN created_at TEXT")
    if 'part_name' not in columns:
        c.execute("ALTER TABLE projects ADD COLUMN part_name TEXT")
    if 'part_number' not in columns:
        c.execute("ALTER TABLE projects ADD COLUMN part_number TEXT")
    if 'customer' not in columns:
        c.execute("ALTER TABLE projects ADD COLUMN customer TEXT")
    if 'model' not in columns:
        c.execute("ALTER TABLE projects ADD COLUMN model TEXT")

    # Create tasks table first
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                title TEXT NOT NULL,
                pic_id TEXT,
                delegator_id TEXT,
                due_date TEXT,
                status TEXT NOT NULL,
                created_at TEXT,
                completed_at TEXT,
                actual_start TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (pic_id) REFERENCES users(id),
                FOREIGN KEY (delegator_id) REFERENCES users(id)
              )""")
    
    # Then check and alter tasks table to add new columns if they don't exist
    c.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in c.fetchall()]
    if 'created_at' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
    if 'completed_at' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
    if 'actual_start' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN actual_start TEXT")

    # Create project_members table
    c.execute("""CREATE TABLE IF NOT EXISTS project_members (
                project_id INTEGER,
                user_id TEXT,
                PRIMARY KEY (project_id, user_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
              )""")

    # Create documents table
    c.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                task_id INTEGER,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                revision_of INTEGER,
                notes TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (revision_of) REFERENCES documents(id)
              )""")

    # Create audit_trail table
    c.execute("""CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                details TEXT NOT NULL
              )""")

    # Create chats (project chat) table
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                sender_id TEXT,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id)
              )""")

    # Create direct_chats (direct chat antar user) table
    c.execute("""CREATE TABLE IF NOT EXISTS direct_chats (
                id INTEGER PRIMARY KEY,
                sender_id TEXT,
                receiver_id TEXT,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
              )""")

    # Bersihkan data orphan (data project_members yang tidak ada project-nya)
    c.execute("""DELETE FROM project_members 
                 WHERE project_id NOT IN (SELECT id FROM projects)""")
    
    # Bersihkan data orphan lainnya
    c.execute("""DELETE FROM tasks 
                 WHERE project_id NOT IN (SELECT id FROM projects)""")
    
    c.execute("""DELETE FROM chats 
                 WHERE project_id NOT IN (SELECT id FROM projects)""")
    
    conn.commit()
    conn.close()

create_db_and_tables()

# --- Fungsi Dummy Data ---
def create_dummy_data():
    """Membuat data dummy lengkap untuk demo aplikasi."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Cek apakah sudah ada project
    c.execute("SELECT COUNT(*) FROM projects")
    if c.fetchone()[0] > 0:
        conn.close()
        return  # Sudah ada data, tidak perlu membuat dummy
    
    try:
        hashed_dev_pw = hashlib.sha256(DEFAULT_DEV_PASSWORD.encode()).hexdigest()
        
        # Tambah beberapa user dummy (Staff dan Supervisor)
        dummy_users = [
            ("E001", "Budi Santoso", "Production Machining", "Machining 1", "Staff"),
            ("E002", "Siti Nurhaliza", "Quality Assurance", "Qa Inspection", "Staff"),
            ("E003", "Ahmad Wijaya", "Development & Trial", "Development", "Staff"),
            ("E004", "Rina Mulyani", "Production Equipment Engineering", "Machining Equipment", "Supervisor"),
            ("E005", "Doni Prakoso", "Foundry Csm", "Melting Disamatic", "Staff"),
            ("E006", "Maya Sari", "Quality Control", "Laboratory", "Staff"),
            ("E007", "Eko Susanto", "Maintenance", "Maintenance Mc", "Supervisor"),
            ("E008", "Lina Wati", "Information System", "Information Technology", "Staff"),
        ]
        
        for user_id, fullname, dept, seksi, role in dummy_users:
            c.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO users (id, password, fullname, departemen, seksi, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (user_id, hashed_dev_pw, fullname, dept, seksi, role, "approved"))
        
        # Buat beberapa project dummy
        projects_data = [
            {
                "name": "Development Part Crankcase CB150",
                "description": "Pengembangan part crankcase untuk motor CB150 dengan material ADC12. Project ini melibatkan redesign untuk meningkatkan kekuatan dan mengurangi cacat produksi.",
                "part_name": "Crankcase Upper",
                "part_number": "CB150-CC-001",
                "customer": "PT. Astra Honda Motor",
                "model": "CB150R 2024",
                "creator_id": "M123",
                "members": ["M123", "S123", "E001", "E003", "E002"],
                "created_at": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Quality Improvement - Cylinder Head",
                "description": "Proyek perbaikan kualitas untuk mengurangi reject rate pada proses machining cylinder head. Target pengurangan reject dari 5% menjadi 2%.",
                "part_name": "Cylinder Head",
                "part_number": "YZ250-CH-008",
                "customer": "PT. Yamaha Indonesia",
                "model": "YZF-R25 2024",
                "creator_id": "M123",
                "members": ["M123", "E002", "E004", "E006", "E007"],
                "created_at": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "New Tooling Development - Transmission Case",
                "description": "Pembuatan tooling baru untuk part transmission case dengan teknologi high pressure die casting. Project ini juga melibatkan trial produksi dan validasi.",
                "part_name": "Transmission Case",
                "part_number": "KW200-TC-015",
                "customer": "PT. Kawasaki Motor Indonesia",
                "model": "Ninja 250SL",
                "creator_id": "M123",
                "members": ["M123", "S123", "E003", "E005", "E001"],
                "created_at": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Maintenance System Upgrade",
                "description": "Upgrade sistem monitoring maintenance untuk meningkatkan efisiensi downtime equipment. Implementasi IoT sensor dan dashboard realtime.",
                "part_name": "System Software",
                "part_number": "MAIN-SYS-2024",
                "customer": "Internal Project",
                "model": "Version 2.0",
                "creator_id": "admin123",
                "members": ["admin123", "E007", "E008", "M123"],
                "created_at": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        project_ids = []
        for proj_data in projects_data:
            c.execute("""INSERT INTO projects (name, description, part_name, part_number, customer, model, creator_id, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (proj_data["name"], proj_data["description"], proj_data["part_name"], 
                      proj_data["part_number"], proj_data["customer"], proj_data["model"],
                      proj_data["creator_id"], proj_data["created_at"]))
            project_id = c.lastrowid
            project_ids.append(project_id)
            
            # Tambahkan members
            for member_id in proj_data["members"]:
                c.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)", (project_id, member_id))
        
        # Buat tasks untuk setiap project
        tasks_data = [
            # Project 1: Development Part Crankcase CB150
            [
                {"title": "Design Review & Material Selection", "pic_id": "E003", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 42},
                {"title": "CAD Design & Simulation", "pic_id": "E003", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 38},
                {"title": "Pattern Making & Mold Preparation", "pic_id": "E001", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 27},
                {"title": "First Trial Production", "pic_id": "E001", "delegator_id": "S123", "due_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"), "status": "Waiting Approval", "days_ago": 16},
                {"title": "Quality Inspection & Dimensional Check", "pic_id": "E002", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), "status": "In Progress", "days_ago": 12},
                {"title": "Customer Approval & Documentation", "pic_id": "E002", "delegator_id": "M123", "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), "status": "Not Started", "days_ago": None},
            ],
            # Project 2: Quality Improvement - Cylinder Head
            [
                {"title": "Root Cause Analysis - Reject Issue", "pic_id": "E002", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 28},
                {"title": "Process Parameter Optimization", "pic_id": "E004", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 20},
                {"title": "Tooling Maintenance & Calibration", "pic_id": "E007", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d"), "status": "Waiting Approval", "days_ago": 13},
                {"title": "Trial Run dengan Parameter Baru", "pic_id": "E004", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), "status": "In Progress", "days_ago": 6},
                {"title": "Statistical Analysis & Report", "pic_id": "E006", "delegator_id": "M123", "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), "status": "Not Started", "days_ago": None},
            ],
            # Project 3: New Tooling Development - Transmission Case
            [
                {"title": "Tooling Specification & Design", "pic_id": "E003", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=55)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 57},
                {"title": "Supplier Selection & PO", "pic_id": "S123", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=50)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 52},
                {"title": "Tooling Fabrication Monitoring", "pic_id": "E003", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 32},
                {"title": "Tooling Installation & Setup", "pic_id": "E005", "delegator_id": "S123", "due_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 17},
                {"title": "First Casting Trial", "pic_id": "E005", "delegator_id": "S123", "due_date": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"), "status": "Waiting Approval", "days_ago": 9},
                {"title": "Quality Validation", "pic_id": "E001", "delegator_id": "M123", "due_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "status": "In Progress", "days_ago": 3},
                {"title": "Mass Production Preparation", "pic_id": "E001", "delegator_id": "M123", "due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"), "status": "Not Started", "days_ago": None},
            ],
            # Project 4: Maintenance System Upgrade
            [
                {"title": "System Requirement Analysis", "pic_id": "E008", "delegator_id": "admin123", "due_date": (datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 19},
                {"title": "IoT Sensor Installation", "pic_id": "E007", "delegator_id": "admin123", "due_date": (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d"), "status": "Done", "days_ago": 14},
                {"title": "Dashboard Development", "pic_id": "E008", "delegator_id": "admin123", "due_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), "status": "In Progress", "days_ago": 6},
                {"title": "User Training & Documentation", "pic_id": "E008", "delegator_id": "admin123", "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"), "status": "Not Started", "days_ago": None},
                {"title": "System Go-Live", "pic_id": "admin123", "delegator_id": "admin123", "due_date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"), "status": "Not Started", "days_ago": None},
            ]
        ]
        
        task_ids_by_project = []
        for proj_idx, project_id in enumerate(project_ids):
            task_ids = []
            for task_data in tasks_data[proj_idx]:
                created_at = (datetime.now() - timedelta(days=task_data.get("days_ago", 0))).strftime("%Y-%m-%d %H:%M:%S") if task_data.get("days_ago") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                completed_at = None
                actual_start = None
                
                if task_data["status"] == "Done":
                    completed_at = (datetime.now() - timedelta(days=task_data.get("days_ago", 0) - 2)).strftime("%Y-%m-%d %H:%M:%S")
                    actual_start = (datetime.now() - timedelta(days=task_data.get("days_ago", 0) - 1)).strftime("%Y-%m-%d %H:%M:%S")
                elif task_data["status"] == "In Progress":
                    actual_start = (datetime.now() - timedelta(days=task_data.get("days_ago", 1))).strftime("%Y-%m-%d %H:%M:%S")
                
                c.execute("""INSERT INTO tasks (project_id, title, pic_id, delegator_id, due_date, status, created_at, completed_at, actual_start) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (project_id, task_data["title"], task_data["pic_id"], task_data["delegator_id"], 
                          task_data["due_date"], task_data["status"], created_at, completed_at, actual_start))
                task_ids.append(c.lastrowid)
            task_ids_by_project.append(task_ids)
        
        # Buat chat messages untuk setiap project
        chat_messages = [
            # Project 1: Development Part Crankcase CB150
            [
                {"sender_id": "M123", "message": "Tim, kita mulai project development crankcase CB150. Silakan cek detail di task masing-masing.", "days_ago": 45, "hours_ago": 10},
                {"sender_id": "E003", "message": "Siap Pak! Saya akan mulai dari design review dan material selection.", "days_ago": 45, "hours_ago": 9},
                {"sender_id": "S123", "message": "Untuk material, apakah tetap pakai ADC12 atau ada alternatif lain?", "days_ago": 45, "hours_ago": 8},
                {"sender_id": "M123", "message": "Tetap ADC12, sudah approved dari customer. Fokus ke design optimization.", "days_ago": 45, "hours_ago": 7},
                {"sender_id": "E003", "message": "Update: Design review sudah selesai. Akan lanjut ke CAD modeling.", "days_ago": 40, "hours_ago": 14},
                {"sender_id": "E001", "message": "CAD design sudah ready ya? Saya perlu untuk persiapan pattern making.", "days_ago": 35, "hours_ago": 10},
                {"sender_id": "E003", "message": "Sudah, saya share file CAD-nya via email. Ada 3 variant design.", "days_ago": 35, "hours_ago": 9},
                {"sender_id": "E001", "message": "Pattern making selesai. Mold sudah siap untuk trial production.", "days_ago": 25, "hours_ago": 15},
                {"sender_id": "S123", "message": "Bagus! Schedule trial production untuk minggu depan ya.", "days_ago": 25, "hours_ago": 14},
                {"sender_id": "E001", "message": "Trial production sudah selesai. Ada 50 pcs sample. Menunggu QA check.", "days_ago": 15, "hours_ago": 11},
                {"sender_id": "E002", "message": "Saya sudah terima sample-nya. Akan saya inspect segera.", "days_ago": 15, "hours_ago": 10},
                {"sender_id": "E002", "message": "Update inspection: Ada minor issue di area fillet radius. Perlu sedikit adjustment.", "days_ago": 12, "hours_ago": 16},
                {"sender_id": "M123", "message": "Coordinate dengan E001 untuk adjustment. Target submit ke customer akhir bulan ini.", "days_ago": 12, "hours_ago": 15},
                {"sender_id": "E001", "message": "Adjustment sudah dilakukan. Ready untuk trial ke-2.", "days_ago": 10, "hours_ago": 9},
            ],
            # Project 2: Quality Improvement - Cylinder Head
            [
                {"sender_id": "M123", "message": "Project quality improvement dimulai. Target kita turunkan reject rate dari 5% ke 2%.", "days_ago": 30, "hours_ago": 10},
                {"sender_id": "E002", "message": "Siap Pak! Saya akan start dengan root cause analysis.", "days_ago": 30, "hours_ago": 9},
                {"sender_id": "E006", "message": "Saya bantu dari sisi laboratory testing untuk material analysis.", "days_ago": 30, "hours_ago": 8},
                {"sender_id": "E002", "message": "Root cause analysis selesai. Main issue ada di process parameter yang tidak konsisten.", "days_ago": 25, "hours_ago": 14},
                {"sender_id": "E004", "message": "Noted. Saya akan optimize parameter machining-nya.", "days_ago": 25, "hours_ago": 13},
                {"sender_id": "E007", "message": "Saya cek kondisi tooling juga ya, mungkin perlu maintenance.", "days_ago": 25, "hours_ago": 12},
                {"sender_id": "E004", "message": "Parameter optimization selesai. Sudah saya dokumentasikan di SOP baru.", "days_ago": 18, "hours_ago": 15},
                {"sender_id": "E007", "message": "Tooling maintenance & calibration sudah selesai. Semua dalam kondisi optimal.", "days_ago": 12, "hours_ago": 14},
                {"sender_id": "M123", "message": "Good job team! Sekarang kita trial run dengan parameter baru.", "days_ago": 12, "hours_ago": 13},
                {"sender_id": "E004", "message": "Trial run sedang berjalan. So far hasilnya promising, reject rate turun drastis.", "days_ago": 5, "hours_ago": 10},
                {"sender_id": "E006", "message": "Saya standby untuk statistical analysis setelah trial selesai.", "days_ago": 5, "hours_ago": 9},
            ],
            # Project 3: New Tooling Development - Transmission Case
            [
                {"sender_id": "M123", "message": "Project tooling baru untuk transmission case dimulai. Timeline ketat, 2 bulan harus selesai.", "days_ago": 60, "hours_ago": 10},
                {"sender_id": "E003", "message": "Design specification sudah saya buat. Akan koordinasi dengan supplier.", "days_ago": 60, "hours_ago": 9},
                {"sender_id": "S123", "message": "Saya handle supplier selection dan PO process.", "days_ago": 55, "hours_ago": 14},
                {"sender_id": "E003", "message": "Design final sudah approved. Supplier bisa mulai fabrication.", "days_ago": 55, "hours_ago": 13},
                {"sender_id": "S123", "message": "PO sudah keluar. Lead time 4 minggu.", "days_ago": 50, "hours_ago": 10},
                {"sender_id": "E003", "message": "Update dari supplier: Fabrication progress 50%. On schedule.", "days_ago": 40, "hours_ago": 11},
                {"sender_id": "E003", "message": "Tooling sudah sampai! Quality check OK, siap untuk installation.", "days_ago": 30, "hours_ago": 15},
                {"sender_id": "E005", "message": "Installation dan setup sudah selesai. Besok kita trial casting.", "days_ago": 15, "hours_ago": 14},
                {"sender_id": "E005", "message": "First casting trial selesai. Hasilnya bagus, menunggu approval dari QA.", "days_ago": 8, "hours_ago": 10},
                {"sender_id": "E001", "message": "Saya sedang proses quality validation. Ada beberapa point yang perlu di-verify.", "days_ago": 2, "hours_ago": 9},
                {"sender_id": "M123", "message": "Keep me updated. Kalau OK, kita bisa proceed ke mass production prep.", "days_ago": 2, "hours_ago": 8},
            ],
            # Project 4: Maintenance System Upgrade
            [
                {"sender_id": "admin123", "message": "Project upgrade sistem maintenance dimulai. Kita akan implementasi IoT dan dashboard realtime.", "days_ago": 20, "hours_ago": 10},
                {"sender_id": "E008", "message": "Saya mulai dengan requirement analysis. Butuh input dari maintenance team.", "days_ago": 20, "hours_ago": 9},
                {"sender_id": "E007", "message": "Siap! Saya list semua requirement dari sisi maintenance.", "days_ago": 20, "hours_ago": 8},
                {"sender_id": "E008", "message": "Requirement analysis selesai. Sudah saya compile jadi dokumen lengkap.", "days_ago": 18, "hours_ago": 15},
                {"sender_id": "E007", "message": "IoT sensor installation selesai di 15 equipment critical. Sudah testing connection.", "days_ago": 12, "hours_ago": 14},
                {"sender_id": "E008", "message": "Perfect! Data sensor sudah mulai masuk. Saya lanjut develop dashboard-nya.", "days_ago": 12, "hours_ago": 13},
                {"sender_id": "admin123", "message": "Progress bagus! Pastikan dashboard user-friendly untuk operator.", "days_ago": 10, "hours_ago": 11},
                {"sender_id": "E008", "message": "Dashboard development progress 60%. Fitur monitoring realtime sudah jalan.", "days_ago": 5, "hours_ago": 10},
                {"sender_id": "M123", "message": "Menarik sekali projectnya! Bisa share preview dashboard-nya?", "days_ago": 5, "hours_ago": 9},
                {"sender_id": "E008", "message": "Siap Pak! Nanti saya schedule demo untuk management.", "days_ago": 5, "hours_ago": 8},
            ]
        ]
        
        for proj_idx, project_id in enumerate(project_ids):
            for msg_data in chat_messages[proj_idx]:
                timestamp = (datetime.now() - timedelta(days=msg_data["days_ago"], hours=msg_data["hours_ago"])).strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO chats (project_id, sender_id, message, timestamp, is_read) VALUES (?, ?, ?, ?, ?)",
                         (project_id, msg_data["sender_id"], msg_data["message"], timestamp, 1))
        
        # Buat direct chat messages antara beberapa user
        direct_chats = [
            # Chat antara E001 dan E003 (koordinasi antar departemen)
            [
                {"sender_id": "E001", "receiver_id": "E003", "message": "Mas Ahmad, untuk CAD design crankcase, bisa tolong kirim file STEP-nya? Perlu untuk verifikasi pattern.", "days_ago": 36, "hours_ago": 10},
                {"sender_id": "E003", "receiver_id": "E001", "message": "Siap Mas Budi! File sudah saya kirim ke email. Ada 3 variant.", "days_ago": 36, "hours_ago": 9},
                {"sender_id": "E001", "receiver_id": "E003", "message": "Terima kasih! Saya cek dulu. Kalau ada yang perlu didiskusikan, saya kabari lagi ya.", "days_ago": 36, "hours_ago": 8},
                {"sender_id": "E003", "receiver_id": "E001", "message": "Oke siap! Kalau ada concern langsung aja chat atau telpon.", "days_ago": 36, "hours_ago": 7},
                {"sender_id": "E001", "receiver_id": "E003", "message": "Mas, ada sedikit concern di area draft angle. Bisa kita meeting sebentar?", "days_ago": 34, "hours_ago": 14},
                {"sender_id": "E003", "receiver_id": "E001", "message": "Bisa! Jam 2 siang di ruang meeting development gimana?", "days_ago": 34, "hours_ago": 13},
                {"sender_id": "E001", "receiver_id": "E003", "message": "Deal! See you there.", "days_ago": 34, "hours_ago": 13},
            ],
            # Chat antara E002 dan E006 (QA dan Lab)
            [
                {"sender_id": "E002", "receiver_id": "E006", "message": "Mba Maya, bisa bantu testing material untuk sample cylinder head? Perlu chemical composition analysis.", "days_ago": 26, "hours_ago": 11},
                {"sender_id": "E006", "receiver_id": "E002", "message": "Bisa Bu Siti! Sample-nya sudah ada? Kirim ke lab ya.", "days_ago": 26, "hours_ago": 10},
                {"sender_id": "E002", "receiver_id": "E006", "message": "Sudah saya kirim tadi pagi 5 pcs. Urgent soalnya, kalau bisa hasil-nya besok.", "days_ago": 26, "hours_ago": 9},
                {"sender_id": "E006", "receiver_id": "E002", "message": "Oke noted! Saya prioritaskan. Besok sore hasilnya ready.", "days_ago": 26, "hours_ago": 9},
                {"sender_id": "E006", "receiver_id": "E002", "message": "Bu Siti, hasil test sudah keluar. Saya kirim report via email ya. Overall composition OK sesuai spec.", "days_ago": 25, "hours_ago": 15},
                {"sender_id": "E002", "receiver_id": "E006", "message": "Terima kasih Mba Maya! Fast response banget. Sangat membantu.", "days_ago": 25, "hours_ago": 14},
            ],
            # Chat antara S123 dan E004 (Supervisor koordinasi dengan staff)
            [
                {"sender_id": "S123", "receiver_id": "E004", "message": "Mba Rina, untuk parameter optimization cylinder head, progressnya gimana?", "days_ago": 20, "hours_ago": 10},
                {"sender_id": "E004", "receiver_id": "S123", "message": "Sudah selesai Pak! SOP baru sudah saya buat dan testing awal hasilnya bagus.", "days_ago": 20, "hours_ago": 9},
                {"sender_id": "S123", "receiver_id": "E004", "message": "Bagus! Bisa presentasi ke team besok? Biar semua operator paham.", "days_ago": 20, "hours_ago": 8},
                {"sender_id": "E004", "receiver_id": "S123", "message": "Siap Pak! Saya persiapkan slide presentasi-nya.", "days_ago": 20, "hours_ago": 7},
            ],
            # Chat antara E007 dan E008 (Maintenance dan IT)
            [
                {"sender_id": "E007", "receiver_id": "E008", "message": "Lina, untuk IoT sensor yang mau dipasang, ada spesifikasi khusus ga? Biar saya persiapkan bracket-nya.", "days_ago": 15, "hours_ago": 11},
                {"sender_id": "E008", "receiver_id": "E007", "message": "Ada Pak Eko! Saya kirim spec sheet-nya via WA ya. Mostly sensor temperature dan vibration.", "days_ago": 15, "hours_ago": 10},
                {"sender_id": "E007", "receiver_id": "E008", "message": "Oke siap! Kalau ada yang perlu dikoordinasikan lagi, langsung aja.", "days_ago": 15, "hours_ago": 9},
                {"sender_id": "E008", "receiver_id": "E007", "message": "Pak Eko, sensor installation-nya sudah beres ya? Saya perlu akses ke data untuk testing.", "days_ago": 12, "hours_ago": 16},
                {"sender_id": "E007", "receiver_id": "E008", "message": "Sudah semua! Network connection juga sudah oke. Silakan di-test.", "days_ago": 12, "hours_ago": 15},
                {"sender_id": "E008", "receiver_id": "E007", "message": "Perfect! Data sudah masuk dengan baik. Thank you Pak!", "days_ago": 12, "hours_ago": 14},
            ],
            # Chat antara M123 dan admin123 (Manager level discussion)
            [
                {"sender_id": "M123", "receiver_id": "admin123", "message": "Admin, untuk dashboard maintenance system, bisa diintegrasikan dengan sistem existing ga?", "days_ago": 10, "hours_ago": 11},
                {"sender_id": "admin123", "receiver_id": "M123", "message": "Bisa Pak! Kita pakai API integration. Nanti bisa centralized di satu dashboard.", "days_ago": 10, "hours_ago": 10},
                {"sender_id": "M123", "receiver_id": "admin123", "message": "Bagus! Kalau begitu bisa jadi pilot project untuk implementasi di area lain juga.", "days_ago": 10, "hours_ago": 9},
                {"sender_id": "admin123", "receiver_id": "M123", "message": "Setuju Pak! Sekalian kita buat standard framework-nya untuk scale up.", "days_ago": 10, "hours_ago": 8},
            ]
        ]
        
        for chat_thread in direct_chats:
            for msg_data in chat_thread:
                timestamp = (datetime.now() - timedelta(days=msg_data["days_ago"], hours=msg_data["hours_ago"])).strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO direct_chats (sender_id, receiver_id, message, timestamp, is_read) VALUES (?, ?, ?, ?, ?)",
                         (msg_data["sender_id"], msg_data["receiver_id"], msg_data["message"], timestamp, 1))
        
        # Tambahkan audit trail untuk aktivitas-aktivitas penting
        audit_entries = [
            {"user_id": "M123", "action": "Create Project", "details": "Project 'Development Part Crankcase CB150' telah dibuat.", "days_ago": 45},
            {"user_id": "M123", "action": "Assign Task", "details": "Task 'Design Review & Material Selection' assigned to E003", "days_ago": 45},
            {"user_id": "E003", "action": "Complete Task", "details": "Task 'Design Review & Material Selection' telah diselesaikan.", "days_ago": 40},
            {"user_id": "M123", "action": "Create Project", "details": "Project 'Quality Improvement - Cylinder Head' telah dibuat.", "days_ago": 30},
            {"user_id": "E002", "action": "Complete Task", "details": "Task 'Root Cause Analysis - Reject Issue' telah diselesaikan.", "days_ago": 25},
            {"user_id": "admin123", "action": "Create Project", "details": "Project 'Maintenance System Upgrade' telah dibuat.", "days_ago": 20},
            {"user_id": "E008", "action": "Complete Task", "details": "Task 'System Requirement Analysis' telah diselesaikan.", "days_ago": 18},
            {"user_id": "E007", "action": "Complete Task", "details": "Task 'IoT Sensor Installation' telah diselesaikan.", "days_ago": 12},
        ]
        
        for entry in audit_entries:
            timestamp = (datetime.now() - timedelta(days=entry["days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO audit_trail (timestamp, user_id, action, details) VALUES (?, ?, ?, ?)",
                     (timestamp, entry["user_id"], entry["action"], entry["details"]))
        
        conn.commit()
        print("✅ Dummy data berhasil dibuat!")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Error saat membuat dummy data: {e}")
    finally:
        conn.close()

# --- Custom CSS untuk link download ---
st.markdown("""
<style>
    /* Style untuk link download file di chat */
    a[download] {
        color: #007bff !important;
        text-decoration: none !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    a[download]:hover {
        color: #0056b3 !important;
        text-decoration: underline !important;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- SVG Icons ---
def get_svg_icon(type, size=24):
    """Mengembalikan ikon SVG sebagai data base64."""
    if type == "project":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-folder"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>"""
    elif type == "task":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check-square"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>"""
    elif type == "done":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check-circle"><path d="M22 11.08V12a10 10 0 1 1-5.93-8.08"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>"""
    elif type == "message":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-message-square"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>"""
    else:
        svg = ""
    
    b64_svg = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64_svg}"

# --- Fungsi Manajemen Database ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")  # Aktifkan foreign key constraints
    return conn

def get_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, fullname, departemen, seksi, role, status FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "password": user[1], "fullname": user[2], "departemen": user[3], "seksi": user[4], "role": user[5], "status": user[6]}
    return None

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, fullname, departemen, seksi, role, status FROM users ORDER BY fullname")
    users = c.fetchall()
    conn.close()
    return [{"id": u[0], "fullname": u[1], "departemen": u[2], "seksi": u[3], "role": u[4], "status": u[5]} for u in users]

def get_projects(user_id, search_query="", creator_filter=None):
    conn = get_db_connection()
    c = conn.cursor()
    user_role = get_user(user_id)['role']
    
    query = """SELECT DISTINCT p.id, p.name, p.description, p.part_name, p.part_number, p.customer, p.model, p.creator_id, u.fullname
               FROM projects p 
               JOIN project_members pm ON p.id = pm.project_id 
               JOIN users u ON p.creator_id = u.id
               WHERE 1=1"""
    params = []
    
    if user_role not in ['Admin', 'Manager']:
        query += " AND pm.user_id = ?"
        params.append(user_id)
        
    if search_query:
        search_like = f"%{search_query}%"
        query += " AND (p.name LIKE ? OR p.part_name LIKE ? OR p.part_number LIKE ?)"
        params.extend([search_like, search_like, search_like])
        
    if creator_filter:
        query += " AND p.creator_id = ?"
        params.append(creator_filter)

    query += " ORDER BY p.id DESC"
    
    c.execute(query, params)
    projects = c.fetchall()
    
    project_list = []
    for p in projects:
        c.execute("SELECT COUNT(*) FROM chats WHERE project_id = ? AND sender_id != ? AND is_read = 0", (p[0], user_id))
        unread_count = c.fetchone()[0]

        project_list.append({
            "id": p[0], "name": p[1], "description": p[2], "part_name": p[3],
            "part_number": p[4], "customer": p[5], "model": p[6],
            "creator_id": p[7], "creator_name": p[8], "unread_count": unread_count
        })
    conn.close()
    return project_list
    
def get_project_members(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT u.id, u.fullname, u.role 
                 FROM users u 
                 JOIN project_members pm ON u.id = pm.user_id 
                 WHERE pm.project_id = ? AND u.status = 'approved'""", (project_id,))
    members = c.fetchall()
    conn.close()
    return [{"id": m[0], "fullname": m[1], "role": m[2]} for m in members]

def get_project_details(project_id, user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, description, part_name, part_number, customer, model, creator_id FROM projects WHERE id = ?", (project_id,))
    project = c.fetchone()
    
    c.execute("SELECT id, title, pic_id, delegator_id, due_date, status, created_at, completed_at, actual_start FROM tasks WHERE project_id = ?", (project_id,))
    tasks = c.fetchall()
    
    task_list = []
    for task in tasks:
        task_dict = {"id": task[0], "title": task[1], "pic_id": task[2], "delegator_id": task[3], "due_date": task[4], "status": task[5], "created_at": task[6], "completed_at": task[7], "actual_start": task[8]}
        
        c.execute("SELECT id, filename, filepath, revision_of, notes FROM documents WHERE task_id = ? ORDER BY id ASC", (task[0],))
        documents = c.fetchall()
        
        doc_list = []
        for d in documents:
            doc_list.append({"id": d[0], "filename": d[1], "filepath": d[2], "revision_of": d[3], "notes": d[4]})
        task_dict['documents'] = doc_list
        task_list.append(task_dict)
    
    c.execute("SELECT sender_id, message, timestamp FROM chats WHERE project_id = ? ORDER BY timestamp ASC", (project_id,))
    chat_messages = c.fetchall()
    chat_list = [{"sender_id": m[0], "message": m[1], "timestamp": m[2]} for m in chat_messages]
    
    conn.close()
    
    if project:
        return {
            "id": project[0], "name": project[1], "description": project[2], "part_name": project[3],
            "part_number": project[4], "customer": project[5], "model": project[6],
            "creator_id": project[7], "tasks": task_list, "chatMessages": chat_list
        }
    return None

def get_direct_messages(user1_id, user2_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT sender_id, receiver_id, message, timestamp FROM direct_chats WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY timestamp ASC",
              (user1_id, user2_id, user2_id, user1_id))
    messages = c.fetchall()
    conn.close()
    return [{"sender_id": m[0], "receiver_id": m[1], "message": m[2], "timestamp": m[3]} for m in messages]

def get_user_notifications(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    notifications = []
    
    user_role = get_user(user_id)['role']
    if user_role in ['Manager', 'Supervisor']:
        c.execute("""SELECT t.title, u.fullname FROM tasks t JOIN users u ON t.pic_id = u.id 
                    WHERE t.status = 'Pending Approval' AND t.delegator_id = ?""", (user_id,))
        notifications = c.fetchall()
    
    conn.close()
    return notifications

def get_unread_direct_messages_count(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT sender_id, COUNT(*)
                 FROM direct_chats
                 WHERE receiver_id = ? AND is_read = 0
                 GROUP BY sender_id""", (user_id,))
    messages = c.fetchall()
    conn.close()
    return {sender_id: count for sender_id, count in messages}

def get_all_direct_chat_partners(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT DISTINCT sender_id AS partner_id FROM direct_chats WHERE receiver_id = ?
                 UNION
                 SELECT DISTINCT receiver_id AS partner_id FROM direct_chats WHERE sender_id = ?""", (user_id, user_id))
    partners = c.fetchall()
    conn.close()
    return [p[0] for p in partners]
    
def mark_direct_messages_as_read(sender_id, receiver_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""UPDATE direct_chats SET is_read = 1 WHERE sender_id = ? AND receiver_id = ?""", (sender_id, receiver_id))
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(user_id, password, fullname, departemen, seksi):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if c.fetchone():
            st.error("ID Karyawan sudah terdaftar.")
            return False
        hashed_password = hash_password(password)
        c.execute("INSERT INTO users (id, password, fullname, departemen, seksi, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, hashed_password, fullname, departemen, seksi, "Staff", "pending"))
        conn.commit()
        record_audit_trail(user_id, "User Register", f"Pengguna '{user_id}' mendaftar dengan peran 'Staff' dan status 'pending'.")
        st.success("Pendaftaran berhasil! Akun Anda menunggu persetujuan dari Admin atau Manager.")
        return True
    except sqlite3.Error as e:
        st.error(f"Error mendaftar pengguna: {e}")
        return False
    finally:
        conn.close()

def login_user(user_id, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT password, role, status FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        hashed_password = hash_password(password)
        if hashed_password == result[0]:
            if result[2] == "approved":
                st.session_state.logged_in = True
                st.session_state.current_user = {"id": user_id, "role": result[1], "fullname": get_user(user_id)['fullname']}
                record_audit_trail(user_id, "User Login", f"Pengguna '{user_id}' masuk.")
                st.rerun()
            else:
                st.error("Akun Anda sedang menunggu persetujuan dari Admin/Manager.")
        else:
            st.error("ID Karyawan atau kata sandi tidak valid.")
    else:
        st.error("ID Karyawan atau kata sandi tidak valid.")

def record_audit_trail(user_id, action, details):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audit_trail (timestamp, user_id, action, details) VALUES (?, ?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, action, details))
    conn.commit()
    conn.close()

def approve_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    record_audit_trail(st.session_state.current_user['id'], "Approve User", f"Pengguna '{user_id}' telah disetujui.")
    st.success(f"Pengguna '{user_id}' telah disetujui.")
    st.rerun()

def change_user_role(user_id, new_role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    record_audit_trail(st.session_state.current_user['id'], "Change User Role", f"Peran pengguna '{user_id}' diubah menjadi '{new_role}'.")
    st.success(f"Peran untuk pengguna '{user_id}' diubah menjadi '{new_role}'.")
    st.rerun()

def reset_user_password(user_id, new_password):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_password = hash_password(new_password)
    c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    conn.commit()
    conn.close()
    record_audit_trail(st.session_state.current_user['id'], "Reset Password", f"Kata sandi untuk pengguna '{user_id}' telah diatur ulang.")
    st.success(f"Kata sandi untuk pengguna '{user_id}' telah diatur ulang.")

def create_project(name, description, part_name, part_number, customer, model, members):
    conn = get_db_connection()
    c = conn.cursor()
    creator_id = st.session_state.current_user['id']
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO projects (name, description, part_name, part_number, customer, model, creator_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, description, part_name, part_number, customer, model, creator_id, current_time))
        project_id = c.lastrowid
        
        # Gunakan set untuk menghindari duplikasi member_id
        unique_members = list(set(members))
        for member_id in unique_members:
            c.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)", (project_id, member_id))
        
        conn.commit()
        record_audit_trail(creator_id, "Create Project", f"Proyek '{name}' (ID: {project_id}) dibuat.")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        st.error(f"Error membuat proyek: {e}")
        return False
    finally:
        conn.close()

def delete_project(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT creator_id FROM projects WHERE id = ?", (project_id,))
        result = c.fetchone()
        if not result:
            st.error("Proyek tidak ditemukan.")
            return False
            
        creator_id = result[0]
        if creator_id != st.session_state.current_user['id']:
            st.error("Anda tidak memiliki otorisasi untuk menghapus proyek ini.")
            return False

        # Hapus proyek - CASCADE akan otomatis menghapus project_members, tasks, chats
        c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Delete Project", f"Proyek dengan ID {project_id} telah dihapus.")
        st.success("Proyek berhasil dihapus.")
        st.rerun()
    except sqlite3.Error as e:
        conn.rollback()
        st.error(f"Error menghapus proyek: {e}")
        return False
    finally:
        conn.close()

def cleanup_orphan_data():
    """Membersihkan data orphan dari database."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Hapus project_members tanpa project
        c.execute("""DELETE FROM project_members 
                     WHERE project_id NOT IN (SELECT id FROM projects)""")
        orphan_members = c.rowcount
        
        # Hapus tasks tanpa project
        c.execute("""DELETE FROM tasks 
                     WHERE project_id NOT IN (SELECT id FROM projects)""")
        orphan_tasks = c.rowcount
        
        # Hapus chats tanpa project
        c.execute("""DELETE FROM chats 
                     WHERE project_id NOT IN (SELECT id FROM projects)""")
        orphan_chats = c.rowcount
        
        # Hapus documents tanpa task
        c.execute("""DELETE FROM documents 
                     WHERE task_id NOT IN (SELECT id FROM tasks)""")
        orphan_docs = c.rowcount
        
        conn.commit()
        
        total_cleaned = orphan_members + orphan_tasks + orphan_chats + orphan_docs
        if total_cleaned > 0:
            st.success(f"✅ Pembersihan selesai! {total_cleaned} data orphan dihapus.")
            st.info(f"Detail: {orphan_members} project members, {orphan_tasks} tasks, {orphan_chats} chats, {orphan_docs} documents")
        else:
            st.info("✨ Database sudah bersih, tidak ada data orphan.")
        
        return True
    except sqlite3.Error as e:
        conn.rollback()
        st.error(f"Error membersihkan database: {e}")
        return False
    finally:
        conn.close()

def edit_project(project_id, name, description, part_name, part_number, customer, model, members):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE projects SET name = ?, description = ?, part_name = ?, part_number = ?, customer = ?, model = ? WHERE id = ?",
                  (name, description, part_name, part_number, customer, model, project_id))
        
        c.execute("DELETE FROM project_members WHERE project_id = ?", (project_id,))
        
        # Gunakan set untuk menghindari duplikasi member_id
        unique_members = list(set(members))
        for member_id in unique_members:
            c.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)", (project_id, member_id))
            
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Edit Project", f"Proyek '{name}' (ID: {project_id}) berhasil diedit.")
        st.success("Proyek berhasil diperbarui!")
        st.rerun()
    except sqlite3.Error as e:
        conn.rollback()
        st.error(f"Error mengedit proyek: {e}")
    finally:
        conn.close()
        
def create_task(project_id, title, pic_id, delegator_id, due_date, notes):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO tasks (project_id, title, pic_id, delegator_id, due_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (project_id, title, pic_id, delegator_id, due_date, "Yet", current_time))
        task_id = c.lastrowid
        conn.commit()
        record_audit_trail(delegator_id, "Create Task", f"Tugas '{title}' (ID: {task_id}) didelegasikan ke '{pic_id}'. Catatan: '{notes}'")
        return True
    except sqlite3.Error as e:
        st.error(f"Error membuat tugas: {e}")
        return False
    finally:
        conn.close()

def edit_task(task_id, title, pic_id, due_date, notes):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE tasks SET title = ?, pic_id = ?, due_date = ? WHERE id = ?",
                  (title, pic_id, due_date, task_id))
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Edit Task", f"Tugas '{title}' (ID: {task_id}) berhasil diedit.")
        st.success("Tugas berhasil diperbarui!")
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Error mengedit tugas: {e}")
    finally:
        conn.close()

def upload_document(task_id, file, notes):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Save file to disk
        filename = file.name
        safe_filename = str(uuid.uuid4()) + "_" + filename
        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
        with open(filepath, "wb") as f:
            f.write(file.getbuffer())

        # Check for existing documents to determine revision
        c.execute("SELECT id FROM documents WHERE task_id = ? ORDER BY id DESC LIMIT 1", (task_id,))
        last_doc_id = c.fetchone()
        revision_of = last_doc_id[0] if last_doc_id else None

        c.execute("INSERT INTO documents (task_id, filename, filepath, revision_of, notes) VALUES (?, ?, ?, ?, ?)",
                  (task_id, filename, filepath, revision_of, notes))
        
        # Update task status to "Pending Approval" directly (auto request approval after upload)
        c.execute("UPDATE tasks SET status = ? WHERE id = ?", ("Pending Approval", task_id))
        
        conn.commit()
        
        record_audit_trail(st.session_state.current_user['id'], "Upload Document & Request Approval", f"Dokumen diunggah dan approval diminta untuk tugas '{task_id}'.")
        st.success("Dokumen berhasil diunggah. Status tugas diperbarui menjadi 'Pending Approval'.")
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Error mengunggah dokumen: {e}")
    finally:
        conn.close()

def request_task_approval(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE tasks SET status = ? WHERE id = ?", ("Pending Approval", task_id))
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Task Approval Request", f"Persetujuan diminta untuk tugas '{task_id}'.")
        st.success("Permintaan persetujuan telah dikirim ke pendelegasi.")
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Error meminta persetujuan: {e}")
    finally:
        conn.close()

def start_actual_work(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE tasks SET actual_start = ?, status = ? WHERE id = ? AND actual_start IS NULL", (current_time, "On Progress", task_id))
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Start Actual Work", f"Tugas '{task_id}' dimulai secara aktual.")
        st.success("Waktu mulai pengerjaan telah dicatat!")
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Error memulai pengerjaan: {e}")
    finally:
        conn.close()

def approve_task_completion(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?", ("Done", current_time, task_id))
        conn.commit()
        record_audit_trail(st.session_state.current_user['id'], "Task Approved", f"Tugas '{task_id}' disetujui sebagai 'Done'.")
        st.success("Tugas disetujui sebagai 'Done'.")
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Error menyetujui tugas: {e}")
    finally:
        conn.close()

def get_project_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    today = datetime.now()
    start_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - relativedelta(months=1))
    
    # Total Projects
    c.execute("SELECT COUNT(*) FROM projects")
    total_projects = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM projects WHERE created_at >= ?", (start_of_this_month,))
    this_month_projects = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM projects WHERE created_at >= ? AND created_at < ?", (start_of_last_month, start_of_this_month))
    last_month_projects = c.fetchone()[0]
    diff_projects = this_month_projects - last_month_projects

    # Total Tasks
    c.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_at >= ?", (start_of_this_month,))
    this_month_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_at >= ? AND created_at < ?", (start_of_last_month, start_of_this_month))
    last_month_tasks = c.fetchone()[0]
    diff_tasks = this_month_tasks - last_month_tasks

    # Done Tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Done'")
    done_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Done' AND created_at >= ?", (start_of_this_month,))
    this_month_done_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Done' AND created_at >= ? AND created_at < ?", (start_of_last_month, start_of_this_month))
    last_month_done_tasks = c.fetchone()[0]
    diff_done_tasks = this_month_done_tasks - last_month_done_tasks
    
    conn.close()
    
    return {
        'total_projects': total_projects, 'diff_projects': diff_projects,
        'total_tasks': total_tasks, 'diff_tasks': diff_tasks,
        'done_tasks': done_tasks, 'diff_done_tasks': diff_done_tasks
    }

def get_recent_audit_trail(limit=5):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, user_id, action, details FROM audit_trail ORDER BY timestamp DESC LIMIT ?", (limit,))
    recent_activities = c.fetchall()
    conn.close()
    return recent_activities

def get_all_audit_trail():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT timestamp, user_id, action, details FROM audit_trail ORDER BY timestamp DESC")
    all_activities = c.fetchall()
    conn.close()
    return all_activities

def send_project_message(project_id, sender_id, message):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chats (project_id, sender_id, message, timestamp) VALUES (?, ?, ?, ?)",
              (project_id, sender_id, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
def send_direct_message(sender_id, receiver_id, message):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO direct_chats (sender_id, receiver_id, message, timestamp, is_read) VALUES (?, ?, ?, ?, ?)",
              (sender_id, receiver_id, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0))
    conn.commit()
    conn.close()

def mark_project_messages_as_read(project_id, user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE chats SET is_read = 1 WHERE project_id = ? AND sender_id != ?", (project_id, user_id))
    conn.commit()
    conn.close()

# Panggil fungsi create_dummy_data setelah semua fungsi database didefinisikan
create_dummy_data()

# --- Fungsi Tampilan UI ---
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        try:
            st.image("gambarlogo.png", width = 100)
        except FileNotFoundError:
            st.error("File 'gambarlogo.png' tidak ditemukan. Pastikan file ada di folder yang sama.")

    st.subheader("Masuk")
    
    st.info(f"Untuk login gunakan ID Karyawan / nomor Register\n\n"
            f"- **Kata Sandi Default:** zzz")
    
    #st.info(f"Untuk login gunakan, gunakan akun default:\n\n"
           # f"- **Admin:** admin123\n"
           # f"- **Manager:** M123\n"
           # f"- **Supervisor:** S123\n"
           # f"- **Kata Sandi:** zzz")
    
    user_id = st.text_input("ID Karyawan")
    password = st.text_input("Kata Sandi", type="password")
    
    if st.button("Masuk"):
        login_user(user_id, password)
    
    st.markdown("---")
    if st.button("Daftar Akun Baru"):
        st.session_state.page = "register"
        st.rerun()

def show_register_page():
    st.title("Flux - Pendaftaran Akun Baru")
    st.write("Isi data berikut untuk mendaftar. Akun Anda akan berstatus 'Staff' dan memerlukan persetujuan dari Admin/Manager.")
    
    with st.form("register_form"):
        user_id = st.text_input("ID Karyawan", help="Isi dengan nomor induk karyawan Anda.")
        fullname = st.text_input("Nama Lengkap")
        password = st.text_input("Kata Sandi", type="password")
        departemen = st.selectbox("Departemen", DEPARTEMEN_OPTIONS)
        seksi = st.selectbox("Seksi", SEKSI_OPTIONS)
        
        submitted = st.form_submit_button("Daftar")
        if submitted:
            if user_id and fullname and password and departemen and seksi:
                register_user(user_id, password, fullname, departemen, seksi)
            else:
                st.error("Semua kolom harus diisi.")
                
    if st.button("Kembali ke Halaman Login"):
        st.session_state.page = "login"
        st.rerun()

def show_dashboard():
    user_fullname = st.session_state.current_user['fullname']
    user_role = st.session_state.current_user['role']
    st.title("Dashboard")
    st.markdown(f"Selamat datang, **{user_fullname}** ({user_role})")
    
    st.markdown("---")
    
    # Project Statistics
    st.subheader("Statistik Proyek")
    stats = get_project_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style="background-color: #007bff; padding: 15px; border-radius: 10px; color: white;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{get_svg_icon('project')}" width="24" height="24" style="filter: brightness(0) invert(1);">
                    <h5 style="margin: 0; color: white;">Total Projects</h5>
                </div>
                <h1 style="margin: 5px 0 0; font-size: 2.5em; color: white;">{stats['total_projects']}</h1>
                <p style="margin: 0; font-size: 0.9em; color: white;">{f'+{stats["diff_projects"]}' if stats['diff_projects'] >= 0 else str(stats['diff_projects'])} from last month</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="background-color: #28a745; padding: 15px; border-radius: 10px; color: white;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{get_svg_icon('task')}" width="24" height="24" style="filter: brightness(0) invert(1);">
                    <h5 style="margin: 0; color: white;">Total Tasks</h5>
                </div>
                <h1 style="margin: 5px 0 0; font-size: 2.5em; color: white;">{stats['total_tasks']}</h1>
                <p style="margin: 0; font-size: 0.9em; color: white;">{f'+{stats["diff_tasks"]}' if stats['diff_tasks'] >= 0 else str(stats['diff_tasks'])} from last month</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div style="background-color: #ffc107; padding: 15px; border-radius: 10px; color: white;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{get_svg_icon('done')}" width="24" height="24" style="filter: brightness(0) invert(1);">
                    <h5 style="margin: 0; color: white;">Done Tasks</h5>
                </div>
                <h1 style="margin: 5px 0 0; font-size: 2.5em; color: white;">{stats['done_tasks']}</h1>
                <p style="margin: 0; font-size: 0.9em; color: white;">{f'+{stats["diff_done_tasks"]}' if stats['diff_done_tasks'] >= 0 else str(stats['diff_done_tasks'])} from last month</p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Recent Activities & Notifications
    col_activity, col_notif = st.columns(2)
    
    with col_activity:
        st.subheader("Aktivitas Terbaru")
        recent_activities = get_recent_audit_trail()
        if recent_activities:
            df_activity = pd.DataFrame(recent_activities, columns=['Waktu', 'ID Pengguna', 'Aksi', 'Detail'])
            st.dataframe(df_activity, use_container_width=True)
        else:
            st.info("Tidak ada aktivitas baru.")
            
    with col_notif:
        st.subheader("Notifikasi")
        notifications = get_user_notifications(st.session_state.current_user['id'])
        if notifications:
            for title, pic_fullname in notifications:
                st.warning(f"Tugas '{title}' dari {pic_fullname} siap untuk persetujuan Anda!")
        else:
            st.info("Tidak ada notifikasi baru.")

def show_projects_page():
    st.title("Proyek")
    
    project_tabs = st.tabs(["Daftar Proyek", "Buat Proyek Baru"])
    
    with project_tabs[0]:
        st.subheader("Daftar Proyek")
        
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("Cari Proyek (Nama, Nama Part, Nomor Part)")
        with col_filter:
            all_users = get_all_users()
            creator_names = ["-- Semua --"] + [u['fullname'] for u in all_users]
            selected_creator_name = st.selectbox("Saring berdasarkan Pembuat", creator_names)
            selected_creator_id = None
            if selected_creator_name != "-- Semua --":
                selected_creator_id = [u['id'] for u in all_users if u['fullname'] == selected_creator_name][0]
                
        projects = get_projects(st.session_state.current_user['id'], search_query, selected_creator_id)
        
        if projects:
            for p in projects:
                unread_chat_count = p['unread_count']
                button_label = f"Lihat Detail {'(💬 ' + str(unread_chat_count) + ')' if unread_chat_count > 0 else ''}"
                
                with st.expander(f"**{p['name']}**"):
                    st.markdown(f"**Pembuat:** {p['creator_name']}")
                    st.markdown(f"**Nama Part:** {p['part_name']}")
                    st.markdown(f"**Nomor Part:** {p['part_number']}")
                    st.markdown(f"**Pelanggan:** {p['customer']}")
                    st.markdown(f"**Model:** {p['model']}")
                    
                    col_buttons = st.columns(3)
                    with col_buttons[0]:
                        if st.button(button_label, key=f"view_{p['id']}"):
                            st.session_state.selected_project_id = p['id']
                            mark_project_messages_as_read(p['id'], st.session_state.current_user['id'])
                            st.rerun()
                    with col_buttons[1]:
                         if st.button("Edit Proyek", key=f"edit_proj_{p['id']}"):
                            st.session_state.edit_project_id = p['id']
                            st.session_state.page = "edit_project"
                            st.rerun()
                    with col_buttons[2]:
                        if st.session_state.current_user['id'] == p['creator_id']:
                            if st.button("Hapus Proyek", key=f"delete_{p['id']}"):
                                delete_project(p['id'])
        else:
            st.info("Tidak ada proyek yang ditemukan.")
            
    with project_tabs[1]:
        st.subheader("Buat Proyek Baru")
        with st.form("new_project_form"):
            name = st.text_input("Nama Proyek")
            part_name = st.text_input("Nama Part")
            part_number = st.text_input("Nomor Part")
            customer = st.text_input("Pelanggan")
            model = st.text_input("Model")
            description = st.text_area("Deskripsi (Opsional)")
            
            all_approved_users = [u for u in get_all_users() if u['status'] == 'approved']
            user_options = {u['fullname']: u['id'] for u in all_approved_users}
            selected_members = st.multiselect("Pilih Anggota Proyek (Anda otomatis menjadi anggota):", list(user_options.keys()))
            
            # Gunakan set untuk menghindari duplikasi, creator otomatis menjadi anggota
            member_ids = list(set([user_options[name] for name in selected_members] + [st.session_state.current_user['id']]))

            submitted = st.form_submit_button("Buat Proyek")
            if submitted:
                if name and member_ids:
                    if create_project(name, description, part_name, part_number, customer, model, member_ids):
                        st.success("Proyek berhasil dibuat!")
                        st.session_state.page = "projects"
                        st.session_state.selected_project_id = None
                        st.rerun()
                else:
                    st.error("Nama Proyek dan Anggota Proyek harus diisi.")

def show_edit_project_page(project_id):
    project_details = get_project_details(project_id, st.session_state.current_user['id'])
    
    if project_details:
        st.title(f"Edit Proyek: {project_details['name']}")
        
        with st.form("edit_project_form"):
            name = st.text_input("Nama Proyek", value=project_details['name'])
            part_name = st.text_input("Nama Part", value=project_details['part_name'])
            part_number = st.text_input("Nomor Part", value=project_details['part_number'])
            customer = st.text_input("Pelanggan", value=project_details['customer'])
            model = st.text_input("Model", value=project_details['model'])
            description = st.text_area("Deskripsi (Opsional)", value=project_details['description'])
            
            current_members = get_project_members(project_id)
            current_member_ids = [m['id'] for m in current_members]
            
            all_approved_users = [u for u in get_all_users() if u['status'] == 'approved' and u['id'] != st.session_state.current_user['id']]
            user_options = {u['fullname']: u['id'] for u in all_approved_users}
            current_member_names = [m['fullname'] for m in current_members if m['id'] in user_options.values()]

            selected_members = st.multiselect("Pilih Anggota Proyek:", list(user_options.keys()), default=current_member_names)
            
            member_ids = [user_options[name] for name in selected_members]
            member_ids.append(st.session_state.current_user['id']) # Add creator as a member

            submitted = st.form_submit_button("Simpan Perubahan")
            if submitted:
                if name and member_ids:
                    edit_project(project_id, name, description, part_name, part_number, customer, model, member_ids)
                else:
                    st.error("Nama Proyek dan Anggota Proyek harus diisi.")

        if st.button("Batal"):
            st.session_state.page = "projects"
            st.session_state.edit_project_id = None
            st.rerun()

def show_project_details(project_id):
    project_details = get_project_details(project_id, st.session_state.current_user['id'])
    
    if project_details:
        st.title(f"📂 {project_details['name']}")
        
        # Tabs untuk navigasi - TAMBAH TAB APPROVAL
        info_tab, tasks_tab, approval_tab, docs_tab, chat_tab = st.tabs(["📋 Info Proyek", "✅ Tasks", "✔️ Approval", "📄 Documents", "💬 Chat"])
        
        project_members = get_project_members(project_id)
        tasks = project_details['tasks']
        
        # ==================== TAB 1: INFO PROYEK ====================
        with info_tab:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #2c3e50; font-weight: 600; margin: 0; font-size: 1.8em;">
                    🎯 Identitas Proyek
                </h2>
                <div style="width: 80px; height: 4px; background: linear-gradient(90deg, #f093fb, #4facfe); margin: 15px auto; border-radius: 2px;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2, gap="large")
            with col1:
                id_val = project_details['id']
                creator_name = get_user(project_details['creator_id'])['fullname']
                part_name = project_details['part_name']
                part_num = project_details['part_number']
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ff6b9d 0%, #c44569 100%); padding: 30px; border-radius: 18px; margin-bottom: 15px; box-shadow: 0 8px 25px rgba(255, 107, 157, 0.25); color: white; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="font-size: 1.5em; margin-right: 12px;">🆔</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">ID PROYEK</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.3em; font-weight: 700;">{id_val}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="font-size: 1.5em; margin-right: 12px;">👤</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">PEMBUAT</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.15em; font-weight: 600;">{creator_name}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="font-size: 1.5em; margin-right: 12px;">🔧</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">NAMA PART</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.15em; font-weight: 600;">{part_name}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5em; margin-right: 12px;">📦</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">NOMOR PART</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.15em; font-weight: 600;">{part_num}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                customer = project_details['customer']
                model = project_details['model']
                desc = project_details['description']
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00c6fb 100%); padding: 30px; border-radius: 18px; margin-bottom: 15px; box-shadow: 0 8px 25px rgba(79, 172, 254, 0.25); color: white; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="font-size: 1.5em; margin-right: 12px;">🏢</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">PELANGGAN</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.15em; font-weight: 600;">{customer}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                        <span style="font-size: 1.5em; margin-right: 12px;">🚗</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">MODEL</p>
                            <p style="margin: 5px 0 0 0; font-size: 1.15em; font-weight: 600;">{model}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start;">
                        <span style="font-size: 1.5em; margin-right: 12px;">📝</span>
                        <div style="flex: 1;">
                            <p style="margin: 0; font-size: 0.85em; opacity: 0.85; font-weight: 500; letter-spacing: 0.5px;">DESKRIPSI</p>
                            <p style="margin: 5px 0 0 0; font-size: 0.98em; line-height: 1.6; font-weight: 400;">{desc}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Layout 2 kolom untuk Anggota Proyek dan Overview Progress
            col_members, col_progress = st.columns([1, 1])
            
            # KOLOM 1: Anggota Proyek
            with col_members:
                st.subheader("👥 Anggota Proyek")
                
                # Warna untuk setiap role
                role_colors = {
                    'Admin': 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
                    'Manager': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    'Supervisor': 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)',
                    'Staff': 'linear-gradient(135deg, #ab47bc 0%, #8e24aa 100%)'
                }
                
                # Display members vertically in single column
                for member in project_members:
                    gradient = role_colors.get(member['role'], role_colors['Staff'])
                    member_name = member['fullname']
                    member_role = member['role']
                    st.markdown(f"""
                    <div style="background: {gradient}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                        <p style="margin: 0; font-weight: bold; color: white; font-size: 1em;">{member_name}</p>
                        <p style="margin: 5px 0 0 0; font-size: 0.85em; color: rgba(255,255,255,0.9); background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 12px; display: inline-block;">{member_role}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # KOLOM 2: Overview Progress
            with col_progress:
                st.subheader("📊 Overview Progress")
                
                total_tasks = len(tasks)
                done_tasks = len([t for t in tasks if t['status'] == 'Done'])
                on_progress = len([t for t in tasks if t['status'] == 'On Progress'])
                pending = len([t for t in tasks if t['status'] == 'Pending Approval'])
                yet_tasks = len([t for t in tasks if t['status'] == 'Yet'])
                percentage = int(done_tasks/total_tasks*100) if total_tasks > 0 else 0
                
                # Horizontal Layout - 4 kolom dalam 1 baris
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px 15px; border-radius: 15px; text-align: center; box-shadow: 0 6px 15px rgba(102, 126, 234, 0.3); margin-bottom: 10px; height: 140px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <p style="color: rgba(255,255,255,0.95); margin: 0 0 8px 0; font-size: 0.9em; font-weight: 500; letter-spacing: 0.5px;">Total Tasks</p>
                        <h1 style="color: white; margin: 0; font-weight: 700; font-size: 3em; line-height: 1;">{total_tasks}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 25px 15px; border-radius: 15px; text-align: center; box-shadow: 0 6px 15px rgba(56, 239, 125, 0.3); margin-bottom: 10px; height: 140px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <p style="color: rgba(255,255,255,0.95); margin: 0 0 8px 0; font-size: 0.9em; font-weight: 500; letter-spacing: 0.5px;">Done</p>
                        <h1 style="color: white; margin: 0; font-weight: 700; font-size: 3em; line-height: 1;">{done_tasks}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px 15px; border-radius: 15px; text-align: center; box-shadow: 0 6px 15px rgba(245, 87, 108, 0.3); margin-bottom: 10px; height: 140px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <p style="color: rgba(255,255,255,0.95); margin: 0 0 8px 0; font-size: 0.9em; font-weight: 500; letter-spacing: 0.5px;">On Progress</p>
                        <h1 style="color: white; margin: 0; font-weight: 700; font-size: 3em; line-height: 1;">{on_progress}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%); padding: 25px 15px; border-radius: 15px; text-align: center; box-shadow: 0 6px 15px rgba(255, 167, 38, 0.3); margin-bottom: 10px; height: 140px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <p style="color: rgba(255,255,255,0.95); margin: 0 0 8px 0; font-size: 0.9em; font-weight: 500; letter-spacing: 0.5px;">Yet to Start</p>
                        <h1 style="color: white; margin: 0; font-weight: 700; font-size: 3em; line-height: 1;">{yet_tasks}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Progress Bar
                if total_tasks > 0:
                    progress_percentage = done_tasks / total_tasks
                    st.progress(progress_percentage)
                    st.caption(f"Progress: {int(progress_percentage * 100)}% Complete")
            
            st.markdown("---")
            
            # Gantt Chart Gabungan Plan dan Aktual
            st.subheader("📅 Timeline Project")
            st.caption("🔵 Biru = Rencana (Plan) | � Merah = Aktual (Realisasi)")
            
            if tasks:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                # Prepare data untuk setiap task
                fig = go.Figure()
                
                task_names = []
                y_positions = []
                has_data = False
                legend_plan_added = False
                legend_actual_added = False
                
                for idx, task in enumerate(reversed(tasks)):  # Reversed agar task pertama di atas
                    created = task.get('created_at')
                    due = task.get('due_date')
                    actual_start = task.get('actual_start')
                    completed = task.get('completed_at')
                    status = task.get('status', '-')
                    task_title = task.get('title', '-')
                    
                    try:
                        pic = get_user(task['pic_id'])['fullname'] if task.get('pic_id') else '-'
                    except:
                        pic = '-'
                    
                    # Convert tanggal ke datetime untuk Plan
                    if created and due:
                        try:
                            start_plan = pd.to_datetime(created, format='mixed', errors='coerce')
                            end_plan = pd.to_datetime(due, format='mixed', errors='coerce')
                            
                            if pd.notna(start_plan) and pd.notna(end_plan):
                                # Tambahkan bar untuk Plan (Biru) menggunakan filled rectangle
                                fig.add_trace(go.Scatter(
                                    x=[start_plan, end_plan, end_plan, start_plan, start_plan],
                                    y=[idx, idx, idx+0.4, idx+0.4, idx],
                                    fill='toself',
                                    fillcolor='rgba(0, 123, 255, 0.7)',
                                    line=dict(color='rgba(0, 123, 255, 1)', width=1),
                                    mode='lines',
                                    name='Plan',
                                    legendgroup='plan',
                                    showlegend=not legend_plan_added,
                                    hovertemplate=f'<b>{task_title}</b><br>Type: Plan<br>PIC: {pic}<br>Start: {start_plan.strftime("%Y-%m-%d")}<br>End: {end_plan.strftime("%Y-%m-%d")}<br>Status: {status}<extra></extra>'
                                ))
                                legend_plan_added = True
                                has_data = True
                        except Exception as e:
                            pass
                    
                    # Convert tanggal ke datetime untuk Actual
                    if actual_start:
                        try:
                            start_actual = pd.to_datetime(actual_start, format='mixed', errors='coerce')
                            
                            if completed:
                                end_actual = pd.to_datetime(completed, format='mixed', errors='coerce')
                            else:
                                end_actual = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), format='mixed', errors='coerce')
                            
                            if pd.notna(start_actual) and pd.notna(end_actual):
                                # Tambahkan bar untuk Actual (Merah) menggunakan filled rectangle
                                fig.add_trace(go.Scatter(
                                    x=[start_actual, end_actual, end_actual, start_actual, start_actual],
                                    y=[idx+0.5, idx+0.5, idx+0.9, idx+0.9, idx+0.5],
                                    fill='toself',
                                    fillcolor='rgba(220, 53, 69, 0.7)',
                                    line=dict(color='rgba(220, 53, 69, 1)', width=1),
                                    mode='lines',
                                    name='Actual',
                                    legendgroup='actual',
                                    showlegend=not legend_actual_added,
                                    hovertemplate=f'<b>{task_title}</b><br>Type: Actual<br>PIC: {pic}<br>Start: {start_actual.strftime("%Y-%m-%d %H:%M:%S")}<br>End: {end_actual.strftime("%Y-%m-%d %H:%M:%S")}<br>Status: {status}<extra></extra>'
                                ))
                                legend_actual_added = True
                                has_data = True
                        except Exception as e:
                            pass
                
                if has_data:
                    # Buat y-axis labels
                    y_labels = [task.get('title', '-') for task in reversed(tasks)]
                    y_vals = list(range(len(y_labels)))
                    
                    # Update layout
                    fig.update_layout(
                        height=max(400, len(tasks) * 60),
                        xaxis=dict(
                            title='Timeline',
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='LightGray'
                        ),
                        yaxis=dict(
                            title='',
                            tickmode='array',
                            tickvals=[i+0.45 for i in y_vals],
                            ticktext=y_labels,
                            tickfont=dict(size=10),
                            range=[-0.5, len(tasks)]
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            bgcolor='rgba(255, 255, 255, 0.8)'
                        ),
                        margin=dict(l=150, r=50, t=60, b=50),
                        hovermode='closest',
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Tidak ada data timeline yang valid")
                
                # Keterangan
                st.markdown("---")
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.info("🔵 **Plan**: Jadwal rencana (dibuat → target selesai)")
                with col_info2:
                    st.error("� **Actual**: Waktu pengerjaan nyata (mulai aktual → selesai)")
                with col_info3:
                    total_tasks_display = len(tasks)
                    tasks_with_actual = len([t for t in tasks if t.get('actual_start')])
                    st.metric("Progress", f"{tasks_with_actual}/{total_tasks_display}", 
                             f"{int(tasks_with_actual/total_tasks_display*100) if total_tasks_display > 0 else 0}%")

            else:
                st.info("Belum ada tugas untuk proyek ini.")
        
        
        # ==================== TAB 2: TASKS ====================
        with tasks_tab:
            st.subheader("📋 Daftar Tugas")
            
            # Grafik Timeline di kolom atas
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**📊 Timeline Plan**")
                if tasks:
                    plan_data = []
                    for task in tasks:
                        start = task.get('created_at')
                        end = task.get('due_date')
                        if start and end:
                            plan_data.append({
                                'Task': task.get('title', '-')[:30],
                                'Start': start,
                                'End': end,
                                'Type': 'Plan'
                            })
                    
                    if plan_data:
                        df_plan = pd.DataFrame(plan_data)
                        # Gunakan format='mixed' untuk menangani berbagai format tanggal
                        df_plan['Start'] = pd.to_datetime(df_plan['Start'], format='mixed', errors='coerce')
                        df_plan['End'] = pd.to_datetime(df_plan['End'], format='mixed', errors='coerce')
                        df_plan = df_plan.dropna(subset=['Start', 'End'])
                        
                        if not df_plan.empty:
                            fig_plan = px.timeline(df_plan, x_start='Start', x_end='End', y='Task', 
                                                  title='Jadwal Rencana', height=300)
                            fig_plan.update_yaxes(autorange="reversed")
                            fig_plan.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
                            st.plotly_chart(fig_plan, use_container_width=True)
                        else:
                            st.info("Tidak ada data plan yang valid")
                    else:
                        st.info("Tidak ada data plan")
                else:
                    st.info("Belum ada tugas")
            
            with col_chart2:
                st.markdown("**📈 Timeline Aktual**")
                if tasks:
                    actual_data = []
                    for task in tasks:
                        start = task.get('actual_start') if task.get('actual_start') else task.get('created_at')
                        end = task.get('completed_at') if task.get('completed_at') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if start and end and task['status'] in ['On Progress', 'Done']:
                            actual_data.append({
                                'Task': task.get('title', '-')[:30],
                                'Start': start,
                                'End': end,
                                'Status': task['status']
                            })
                    
                    if actual_data:
                        df_actual = pd.DataFrame(actual_data)
                        # Gunakan format='mixed' untuk menangani berbagai format tanggal
                        df_actual['Start'] = pd.to_datetime(df_actual['Start'], format='mixed', errors='coerce')
                        df_actual['End'] = pd.to_datetime(df_actual['End'], format='mixed', errors='coerce')
                        df_actual = df_actual.dropna(subset=['Start', 'End'])
                        
                        if not df_actual.empty:
                            fig_actual = px.timeline(df_actual, x_start='Start', x_end='End', y='Task',
                                                    color='Status', title='Progress Aktual', height=300,
                                                    color_discrete_map={'On Progress': '#ffc107', 'Done': '#28a745'})
                            fig_actual.update_yaxes(autorange="reversed")
                            fig_actual.update_layout(xaxis_title="", yaxis_title="")
                            st.plotly_chart(fig_actual, use_container_width=True)
                        else:
                            st.info("Tidak ada data aktual yang valid")
                    else:
                        st.info("Belum ada progress aktual")
                else:
                    st.info("Belum ada tugas")
            
            st.markdown("---")
            
            # Form Buat Tugas Baru
            user_role = st.session_state.current_user['role']
            if user_role in ['Admin', 'Manager', 'Supervisor']:
                with st.expander("➕ Buat Tugas Baru"):
                    with st.form("new_task_form"):
                        task_title = st.text_input("Judul Tugas")
                        
                        member_options = {m['fullname']: m['id'] for m in project_members}
                        pic_name = st.selectbox("Tugaskan ke:", list(member_options.keys()))
                        pic_id = member_options.get(pic_name)
                        
                        due_date = st.date_input("Batas Waktu")
                        notes = st.text_area("Keterangan (Opsional)")
                        
                        delegator_id = st.session_state.current_user['id']
                        submitted = st.form_submit_button("Tugaskan")
                        
                        if submitted:
                            if task_title and pic_id and due_date:
                                create_task(project_id, task_title, pic_id, delegator_id, str(due_date), notes)
                                st.rerun()
                            else:
                                st.error("Judul Tugas, Penerima Tugas, dan Batas Waktu harus diisi.")
            
            # Daftar Tugas dalam Cards
            if tasks:
                for task in tasks:
                    task_pic = get_user(task['pic_id'])
                    task_delegator = get_user(task['delegator_id'])
                    
                    # Status color
                    status_colors = {
                        'Yet': '#6c757d',
                        'On Progress': '#ffc107',
                        'Pending Approval': '#17a2b8',
                        'Done': '#28a745'
                    }
                    status_color = status_colors.get(task['status'], '#6c757d')

                    with st.expander(f"**{task['title']}** - 🏷️ {task['status']}", expanded=False):
                        col_task1, col_task2 = st.columns([2, 1])
                        
                        with col_task1:
                            st.markdown(f"**👤 PIC:** {task_pic['fullname']} ({task_pic['role']})")
                            st.markdown(f"**📤 Delegator:** {task_delegator['fullname']}")
                            st.markdown(f"**📅 Deadline:** {task['due_date']}")
                        
                        with col_task2:
                            st.markdown(f"""
                            <div style="background-color: {status_color}; color: white; padding: 10px; 
                                        border-radius: 5px; text-align: center;">
                                <h4 style="margin: 0;">{task['status']}</h4>
                            </div>
                            """, unsafe_allow_html=True)

                        # Aksi untuk PIC
                        if st.session_state.current_user['id'] == task['pic_id'] and task['status'] != 'Done':
                            st.markdown("---")
                            
                            # Tombol Start Actual (hanya muncul jika belum dimulai)
                            if not task.get('actual_start') and task['status'] == 'Yet':
                                if st.button("🚀 Mulai Pengerjaan", key=f"start_actual_{task['id']}", type="primary"):
                                    start_actual_work(task['id'])
                            
                            # Tampilkan info jika sudah dimulai
                            if task.get('actual_start'):
                                st.info(f"⏱️ Dimulai: {task['actual_start']}")
                            
                            st.markdown("**📤 Upload Dokumen**")
                            with st.form(f"upload_form_{task['id']}"):
                                uploaded_file = st.file_uploader("Pilih file", key=f"uploader_{task['id']}")
                                notes_upload = st.text_area("Keterangan (Opsional)", key=f"notes_{task['id']}")
                                submit_upload = st.form_submit_button("Kirim & Minta Approval")
                                
                                if submit_upload:
                                    if uploaded_file:
                                        upload_document(task['id'], uploaded_file, notes_upload)
                                    else:
                                        st.error("Silakan pilih file untuk diunggah.")
                        
                        # Aksi untuk Delegator
                        if st.session_state.current_user['id'] == task['delegator_id'] and task['status'] == 'Pending Approval':
                            st.markdown("---")
                            if st.button("✅ Setujui Penyelesaian Tugas", key=f"approve_task_{task['id']}"):
                                approve_task_completion(task['id'])

                        # Aksi untuk Edit
                        if st.session_state.current_user['id'] == task['delegator_id'] and task['status'] != 'Done':
                            if st.button("✏️ Edit Tugas", key=f"edit_task_{task['id']}"):
                                st.session_state.edit_task_id = task['id']
                                st.session_state.page = "edit_task"
                                st.rerun()
            else:
                st.info("Tidak ada tugas untuk proyek ini.")
        
        # ==================== TAB 3: APPROVAL ====================
        with approval_tab:
            st.subheader("✔️ Persetujuan Tugas")
            st.caption("Kelola approval untuk tugas yang sudah selesai dikerjakan")
            
            # Filter tugas yang pending approval
            pending_tasks = [t for t in tasks if t['status'] == 'Pending Approval']
            
            # Cek apakah user adalah delegator dari project ini
            user_id = st.session_state.current_user['id']
            is_creator = project_details['creator_id'] == user_id
            user_role = st.session_state.current_user['role']
            
            if pending_tasks:
                st.info(f"📋 Ada **{len(pending_tasks)}** tugas menunggu persetujuan")
                
                for task in pending_tasks:
                    task_pic = get_user(task['pic_id'])
                    task_delegator = get_user(task['delegator_id'])
                    
                    # Cek apakah user berhak approve (delegator atau creator project atau admin/manager)
                    can_approve = (
                        user_id == task['delegator_id'] or 
                        is_creator or 
                        user_role in ['Admin', 'Manager']
                    )
                    
                    with st.expander(f"📝 **{task['title']}** - Pending Approval", expanded=True):
                        col_info1, col_info2 = st.columns([2, 1])
                        
                        with col_info1:
                            st.markdown(f"**👤 PIC:** {task_pic['fullname']}")
                            st.markdown(f"**📤 Delegator:** {task_delegator['fullname']}")
                            st.markdown(f"**📅 Deadline:** {task['due_date']}")
                            if task.get('actual_start'):
                                st.markdown(f"**⏱️ Dimulai:** {task['actual_start']}")
                        
                        with col_info2:
                            st.markdown("""
                            <div style="background-color: #17a2b8; color: white; padding: 15px; 
                                        border-radius: 5px; text-align: center;">
                                <h4 style="margin: 0;">⏳ Pending</h4>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown("**📄 Dokumen yang Diupload:**")
                        
                        # Tampilkan dokumen
                        if task['documents']:
                            for doc in task['documents']:
                                col_doc1, col_doc2 = st.columns([3, 1])
                                with col_doc1:
                                    st.markdown(f"📎 {doc['filename']}")
                                    if doc['notes']:
                                        st.caption(f"Catatan: {doc['notes']}")
                                with col_doc2:
                                    if os.path.exists(doc['filepath']):
                                        with open(doc['filepath'], "rb") as file:
                                            st.download_button(
                                                label="📥 Download",
                                                data=file,
                                                file_name=doc['filename'],
                                                key=f"download_approval_{doc['id']}"
                                            )
                        else:
                            st.info("Belum ada dokumen diupload")
                        
                        # Tombol Approve (hanya untuk yang berhak)
                        if can_approve:
                            st.markdown("---")
                            col_approve, col_reject = st.columns(2)
                            with col_approve:
                                if st.button("✅ Setujui & Tandai Selesai", key=f"approve_final_{task['id']}", type="primary", use_container_width=True):
                                    approve_task_completion(task['id'])
                            with col_reject:
                                st.caption("Fitur reject akan segera hadir")
                        else:
                            st.warning("⚠️ Anda tidak memiliki akses untuk approve tugas ini")
            else:
                st.success("✅ Tidak ada tugas yang menunggu persetujuan")
        
        # ==================== TAB 4: DOCUMENTS ====================
        with docs_tab:
            st.subheader("📄 Dokumen Proyek")
            
            # Upload Manual
            user_role = st.session_state.current_user['role']
            with st.expander("📤 Upload Dokumen Manual"):
                st.info("Upload dokumen yang tidak terkait dengan tugas spesifik")
                st.caption("Fitur ini untuk dokumen umum proyek. Untuk dokumen tugas, silakan upload di tab Tasks.")
            
            st.markdown("---")
            
            # Tampilkan semua dokumen dari tasks
            st.subheader("📚 Dokumen dari Tasks")
            
            all_documents = []
            for task in tasks:
                for doc in task['documents']:
                    all_documents.append({
                        'task_title': task['title'],
                        'task_id': task['id'],
                        'doc': doc,
                        'pic': get_user(task['pic_id'])['fullname']
                    })
            
            if all_documents:
                # Tampilkan dalam grid cards
                doc_cols = st.columns(3)
                for idx, doc_info in enumerate(all_documents):
                    with doc_cols[idx % 3]:
                        doc = doc_info['doc']
                        
                        # Tentukan icon berdasarkan ekstensi
                        ext = os.path.splitext(doc['filename'])[-1].lower()
                        icon_map = {
                            '.pdf': '📕', '.doc': '📘', '.docx': '📘',
                            '.xls': '📗', '.xlsx': '📗', '.txt': '📄',
                            '.zip': '📦', '.html': '🌐'
                        }
                        file_icon = icon_map.get(ext, '📎')
                        
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; 
                                    margin-bottom: 10px; border: 1px solid #dee2e6;">
                            <h4 style="margin: 0 0 10px 0;">{file_icon} {doc['filename'][:25]}...</h4>
                            <p style="margin: 5px 0; font-size: 0.85em;"><strong>Task:</strong> {doc_info['task_title'][:30]}</p>
                            <p style="margin: 5px 0; font-size: 0.85em;"><strong>Upload by:</strong> {doc_info['pic']}</p>
                            {f'<p style="margin: 5px 0; font-size: 0.85em;"><em>{doc["notes"]}</em></p>' if doc['notes'] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if os.path.exists(doc['filepath']):
                            try:
                                with open(doc['filepath'], "rb") as f:
                                    st.download_button(
                                        label=f"⬇️ Download",
                                        data=f.read(),
                                        file_name=doc['filename'],
                                        mime="application/octet-stream",
                                        key=f"doc_download_{doc['id']}",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        else:
                            st.error("File tidak ditemukan")
            else:
                st.info("Belum ada dokumen yang diupload dalam proyek ini.")
        
        # ==================== TAB 5: CHAT ====================
        with chat_tab:
            st.subheader("💬 Obrolan Proyek")
            st.caption("Diskusikan proyek dengan tim Anda di sini")
            
            mark_project_messages_as_read(project_id, st.session_state.current_user['id'])
            
            chat_container = st.container(height=400)
            with chat_container:
                for msg in project_details['chatMessages']:
                    sender_user = get_user(msg['sender_id'])
                    sender = sender_user['fullname']
                    sender_role = sender_user['role']
                    is_me = msg['sender_id'] == st.session_state.current_user['id']
                    
                    # Warna berdasarkan role untuk pesan orang lain
                    role_colors = {
                        'Admin': {'bg': '#FFE5E5', 'border': '#FF6B6B', 'name': '#C92A2A'},  # Merah muda
                        'Manager': {'bg': '#E3F2FD', 'border': '#2196F3', 'name': '#0D47A1'},  # Biru
                        'Supervisor': {'bg': '#FFF3E0', 'border': '#FF9800', 'name': '#E65100'},  # Orange
                        'Staff': {'bg': '#F3E5F5', 'border': '#9C27B0', 'name': '#4A148C'}  # Ungu
                    }
                    
                    if is_me:
                        align = 'flex-end'
                        bg_color = '#DCF8C6'  # Hijau muda untuk pesan sendiri
                        border_color = '#4CAF50'
                        name_color = '#2E7D32'
                        shadow = '2px 2px 5px rgba(0,0,0,0.15)'
                    else:
                        align = 'flex-start'
                        role_style = role_colors.get(sender_role, role_colors['Staff'])
                        bg_color = role_style['bg']
                        border_color = role_style['border']
                        name_color = role_style['name']
                        shadow = '2px 2px 5px rgba(0,0,0,0.1)'
                    
                    text_color = 'black'
                    
                    # Parse & render content
                    the_msg = msg['message']
                    msg_html = f"<strong style='color: {name_color};'>{sender}</strong> <span style='font-size: 0.75em; color: #666;'>({sender_role})</span><br>"
                    content_html = ""
                    
                    if '[IMAGE]' in the_msg:
                        before, image_path = the_msg.split('[IMAGE]', 1)
                        if before.strip():
                            content_html += f"<span>{before.strip()}</span><br>"
                        image_path = image_path.strip()
                        if os.path.exists(image_path):
                            try:
                                with open(image_path, "rb") as img_f:
                                    import base64
                                    img_b64 = base64.b64encode(img_f.read()).decode('utf-8')
                                ext = os.path.splitext(image_path)[-1][1:] or 'png'
                                filename = os.path.basename(image_path)
                                content_html += f'''<div style="margin: 8px 0;"><img src="data:image/{ext};base64,{img_b64}" style="max-width: 300px; max-height: 300px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; transition: transform 0.2s ease;" onclick="window.open(this.src, '_blank')" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'" title="Klik untuk memperbesar" /><br><a href="data:image/{ext};base64,{img_b64}" download="{filename}" style="display: inline-block; margin-top: 8px; padding: 6px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-size: 0.85em; font-weight: 500; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); transition: all 0.2s ease;">📥 Download</a></div>'''
                            except Exception as e:
                                content_html += f"<span style='color:#999;'>⚠ Error loading image</span>"
                        else:
                            content_html += f"<span style='color:#999;'>⚠ Gambar tidak ditemukan</span>"
                    elif '[FILE]' in the_msg:
                        before, file_field = the_msg.split('[FILE]', 1)
                        if before.strip():
                            content_html += f"<span>{before.strip()}</span><br>"
                        if '|' in file_field:
                            file_path, file_name = file_field.strip().split('|', 1)
                            file_path = file_path.strip()
                            file_name = file_name.strip()
                            if os.path.exists(file_path):
                                try:
                                    with open(file_path, "rb") as f:
                                        import base64
                                        file_b64 = base64.b64encode(f.read()).decode('utf-8')
                                    # Deteksi MIME type berdasarkan ekstensi
                                    ext = os.path.splitext(file_name)[-1].lower()
                                    mime_types = {
                                        '.pdf': 'application/pdf',
                                        '.doc': 'application/msword',
                                        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                        '.xls': 'application/vnd.ms-excel',
                                        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                        '.txt': 'text/plain',
                                        '.zip': 'application/zip',
                                        '.html': 'text/html',
                                    }
                                    mime_type = mime_types.get(ext, 'application/octet-stream')
                                    content_html += f'''<a href="data:{mime_type};base64,{file_b64}" download="{file_name}" 
                                        style="display:inline-block; color:#007bff; padding:4px 0; 
                                        text-decoration:underline; font-weight:500; margin:5px 0; cursor:pointer; 
                                        transition: all 0.2s ease;">
                                        📎 {file_name}
                                    </a>'''
                                except Exception as e:
                                    content_html += f"<span style='color:#999;'>⚠ Error loading file</span>"
                            else:
                                content_html += f"<span style='color:#999;'>⚠ File tidak ditemukan</span>"
                        else:
                            content_html += the_msg
                    else:
                        content_html += the_msg
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                            <div style="background-color: {bg_color}; padding: 12px 15px; border-radius: 15px; 
                                max-width: 80%; color: {text_color}; box-shadow: {shadow}; 
                                border-left: 4px solid {border_color};">
                                {msg_html}
                                <div style='margin:2px 0 0 0; word-break: break-word;'>{content_html}</div>
                                <small style="display: block; text-align: right; color: #888; font-size: 0.7em; margin-top: 5px;">{msg['timestamp']}</small>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Blok form yang sudah benar dengan clear_on_submit=True
            with st.form("project_chat_form", clear_on_submit=True):
                c1, c2 = st.columns([5,2])
                with c1:
                    message = st.text_input("Ketik pesan dan tekan Enter...", key="project_chat_input")
                with c2:
                    uploaded_file = st.file_uploader("", key="project_chat_file", label_visibility="collapsed")
                
                # Tombol submit
                send_chat = st.form_submit_button("Kirim", use_container_width=True)
                
                # Logika pengiriman pesan hanya dijalankan setelah tombol form ditekan
                if send_chat:
                    if message.strip() or uploaded_file:
                        # Simpan file yang diunggah jika ada
                        file_link = None
                        img_file = None
                        if uploaded_file:
                            import uuid
                            filename = f"chat_{uuid.uuid4().hex}_{uploaded_file.name}"
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            if uploaded_file.type.startswith("image/"):
                                img_file = filepath
                            else:
                                file_link = filepath
                        
                        # Buat pesan gabungan
                        mix_msg = message if message else ""
                        if img_file:
                            mix_msg += f" [IMAGE]{img_file}"
                        elif file_link:
                            mix_msg += f" [FILE]{file_link}|{uploaded_file.name}"
                        
                        # Panggil fungsi pengirim pesan
                        send_project_message(project_id, st.session_state.current_user['id'], mix_msg)
                        
                        # Rerun setelah pesan terkirim untuk memperbarui tampilan
                        st.rerun()
        
        # Tombol Kembali
        st.markdown("---")
        col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
        with col_back2:
            if st.button("⬅️ Kembali ke Daftar Proyek", use_container_width=True):
                st.session_state.page = "projects"
                st.session_state.selected_project_id = None
                st.rerun()

def show_edit_task_page(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT project_id, title, pic_id, due_date FROM tasks WHERE id = ?", (task_id,))
    task_details = c.fetchone()
    conn.close()
    
    if task_details:
        project_id, title, pic_id, due_date = task_details
        project_members = get_project_members(project_id)
        
        st.title(f"Edit Tugas: {title}")
        
        with st.form("edit_task_form"):
            new_title = st.text_input("Judul Tugas", value=title)
            
            member_options = {m['fullname']: m['id'] for m in project_members}
            pic_fullname = get_user(pic_id)['fullname']
            new_pic_name = st.selectbox("Tugaskan ke:", list(member_options.keys()), index=list(member_options.keys()).index(pic_fullname))
            new_pic_id = member_options.get(new_pic_name)
            
            new_due_date = st.date_input("Batas Waktu", value=datetime.strptime(due_date, "%Y-%m-%d").date())
            
            submitted = st.form_submit_button("Simpan Perubahan")
            
            if submitted:
                if new_title and new_pic_id and new_due_date:
                    edit_task(task_id, new_title, new_pic_id, str(new_due_date), "")
                    st.success("Tugas berhasil diperbarui!")
                    st.session_state.page = "project_details"
                    st.session_state.selected_project_id = project_id
                    st.session_state.edit_task_id = None
                    st.rerun()
                else:
                    st.error("Semua kolom harus diisi.")
        
        if st.button("Batal"):
            st.session_state.page = "project_details"
            st.session_state.selected_project_id = project_id
            st.session_state.edit_task_id = None
            st.rerun()


def show_user_management_page():
    st.title("Manajemen Pengguna")
    
    admin_tabs = st.tabs(["Persetujuan Pengguna", "Ubah Peran", "Atur Ulang Kata Sandi", "🔧 Database"])
    
    with admin_tabs[0]:
        st.subheader("Persetujuan Pengguna Baru")
        pending_users = [u['id'] for u in get_all_users() if u['status'] == 'pending']
        if pending_users:
            user_to_approve = st.selectbox("Pilih pengguna yang akan disetujui:", pending_users)
            if st.button("Setujui Pengguna"):
                approve_user(user_to_approve)
        else:
            st.info("Tidak ada pengguna baru yang perlu disetujui.")
            
    with admin_tabs[1]:
        st.subheader("Ubah Peran Pengguna")
        user_to_change_role = st.selectbox("Pilih pengguna:", [u['id'] for u in get_all_users()])
        new_role = st.selectbox("Pilih peran baru:", ["Admin", "Manager", "Supervisor", "Staff"])
        if st.button("Ubah Peran"):
            change_user_role(user_to_change_role, new_role)
            
    with admin_tabs[2]:
        st.subheader("Atur Ulang Kata Sandi")
        user_to_reset_pw = st.selectbox("Pilih pengguna untuk atur ulang kata sandi:", [u['id'] for u in get_all_users()])
        new_pw = st.text_input("Kata Sandi Baru", type="password")
        if st.button("Atur Ulang Kata Sandi"):
            if new_pw:
                reset_user_password(user_to_reset_pw, new_pw)
            else:
                st.error("Kata sandi baru tidak boleh kosong.")
    
    with admin_tabs[3]:
        st.subheader("🔧 Pemeliharaan Database")
        st.write("Bersihkan data orphan (data yang tidak memiliki referensi ke data induk)")
        
        st.warning("⚠️ **Gunakan fitur ini jika:**")
        st.markdown("""
        - Anda mengalami error UNIQUE constraint saat membuat proyek
        - Ada data yang tidak konsisten setelah menghapus proyek
        - Database terasa bermasalah
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Bersihkan Data Orphan", type="primary", use_container_width=True):
                cleanup_orphan_data()
        
        with col2:
            st.info("💡 Pembersihan aman dan tidak akan menghapus data yang valid")

def show_audit_trail_page():
    st.title("Jejak Audit Sistem")
    st.write("Semua aktivitas utama dalam aplikasi dicatat di sini.")
    
    all_activities = get_all_audit_trail()
    if all_activities:
        df_audit = pd.DataFrame(all_activities, columns=['Waktu', 'ID Pengguna', 'Aksi', 'Detail'])
        st.dataframe(df_audit, use_container_width=True)
    else:
        st.info("Tidak ada jejak audit yang ditemukan.")

def show_direct_chat_page():
    st.title("Obrolan Langsung")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Kontak")
        
        unread_counts = get_unread_direct_messages_count(st.session_state.current_user['id'])
        chat_partners = get_all_direct_chat_partners(st.session_state.current_user['id'])
        all_users = {u['id']: u['fullname'] for u in get_all_users()}
        
        # Sort partners with unread messages first
        partners_with_notif = [p for p in chat_partners if p in unread_counts]
        partners_without_notif = [p for p in chat_partners if p not in unread_counts]
        sorted_partners = partners_with_notif + partners_without_notif

        for partner_id in sorted_partners:
            partner_name = all_users.get(partner_id, "Pengguna Tidak Dikenal")
            unread_count = unread_counts.get(partner_id, 0)
            
            button_label = f"💬 {partner_name} ({unread_count})" if unread_count > 0 else f"👤 {partner_name}"
            
            if st.button(button_label, key=f"chat_{partner_id}", use_container_width=True):
                st.session_state.selected_chat_partner = partner_id
                st.rerun()

        st.markdown("---")
        if st.button("Mulai Obrolan Baru", key="new_chat_button", use_container_width=True):
            st.session_state.show_user_search = True
            st.session_state.selected_chat_partner = None

        if st.session_state.get('show_user_search', False):
            st.subheader("Cari Pengguna")
            search_term = st.text_input("Cari nama atau ID...", key="user_search")
            if search_term:
                search_results = [u for u in get_all_users() if search_term.lower() in u['fullname'].lower() or search_term.lower() in u['id'].lower()]
                for user in search_results:
                    if user['id'] != st.session_state.current_user['id'] and user['status'] == 'approved':
                        if st.button(f"👤 {user['fullname']} ({user['role']})", key=f"select_user_{user['id']}", use_container_width=True):
                            st.session_state.selected_chat_partner = user['id']
                            st.session_state.show_user_search = False
                            st.rerun()
    
    with col2:
        if st.session_state.get('selected_chat_partner'):
            receiver_id = st.session_state.selected_chat_partner
            receiver_name = get_user(receiver_id)['fullname']
            st.subheader(f"Obrolan dengan: {receiver_name}")
            
            mark_direct_messages_as_read(receiver_id, st.session_state.current_user['id'])

            chat_container = st.container(height=400)
            
            with chat_container:
                messages = get_direct_messages(st.session_state.current_user['id'], receiver_id)
                for msg in messages:
                    sender_user = get_user(msg['sender_id'])
                    sender = sender_user['fullname']
                    sender_role = sender_user['role']
                    is_me = msg['sender_id'] == st.session_state.current_user['id']

                    # Warna berdasarkan role untuk pesan orang lain
                    role_colors = {
                        'Admin': {'bg': '#FFE5E5', 'border': '#FF6B6B', 'name': '#C92A2A'},
                        'Manager': {'bg': '#E3F2FD', 'border': '#2196F3', 'name': '#0D47A1'},
                        'Supervisor': {'bg': '#FFF3E0', 'border': '#FF9800', 'name': '#E65100'},
                        'Staff': {'bg': '#F3E5F5', 'border': '#9C27B0', 'name': '#4A148C'}
                    }
                    
                    if is_me:
                        align = 'flex-end'
                        bg_color = '#DCF8C6'
                        border_color = '#4CAF50'
                        name_color = '#2E7D32'
                        shadow = '2px 2px 5px rgba(0,0,0,0.15)'
                    else:
                        align = 'flex-start'
                        role_style = role_colors.get(sender_role, role_colors['Staff'])
                        bg_color = role_style['bg']
                        border_color = role_style['border']
                        name_color = role_style['name']
                        shadow = '2px 2px 5px rgba(0,0,0,0.1)'
                    
                    text_color = 'black'

                    # Parse & render content
                    the_msg = msg['message']
                    msg_html = f"<strong style='color: {name_color};'>{sender}</strong> <span style='font-size: 0.75em; color: #666;'>({sender_role})</span><br>"
                    content_html = ""
                    
                    if '[IMAGE]' in the_msg:
                        before, image_path = the_msg.split('[IMAGE]', 1)
                        if before.strip():
                            content_html += f"<span>{before.strip()}</span><br>"
                        image_path = image_path.strip()
                        if os.path.exists(image_path):
                            try:
                                with open(image_path, "rb") as img_f:
                                    import base64
                                    img_b64 = base64.b64encode(img_f.read()).decode('utf-8')
                                ext = os.path.splitext(image_path)[-1][1:] or 'png'
                                filename = os.path.basename(image_path)
                                content_html += f'''<div style="margin: 8px 0;"><img src="data:image/{ext};base64,{img_b64}" style="max-width: 300px; max-height: 300px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; transition: transform 0.2s ease;" onclick="window.open(this.src, '_blank')" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'" title="Klik untuk memperbesar" /><br><a href="data:image/{ext};base64,{img_b64}" download="{filename}" style="display: inline-block; margin-top: 8px; padding: 6px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-size: 0.85em; font-weight: 500; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); transition: all 0.2s ease;">📥 Download</a></div>'''
                            except Exception as e:
                                content_html += f"<span style='color:#999;'>⚠ Error loading image</span>"
                        else:
                            content_html += f"<span style='color:#999;'>⚠ Gambar tidak ditemukan</span>"
                    elif '[FILE]' in the_msg:
                        before, file_field = the_msg.split('[FILE]', 1)
                        if before.strip():
                            content_html += f"<span>{before.strip()}</span><br>"
                        if '|' in file_field:
                            file_path, file_name = file_field.strip().split('|', 1)
                            file_path = file_path.strip()
                            file_name = file_name.strip()
                            if os.path.exists(file_path):
                                try:
                                    with open(file_path, "rb") as f:
                                        import base64
                                        file_b64 = base64.b64encode(f.read()).decode('utf-8')
                                    ext = os.path.splitext(file_name)[-1].lower()
                                    mime_types = {
                                        '.pdf': 'application/pdf',
                                        '.doc': 'application/msword',
                                        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                        '.xls': 'application/vnd.ms-excel',
                                        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                        '.txt': 'text/plain',
                                        '.zip': 'application/zip',
                                        '.html': 'text/html',
                                    }
                                    mime_type = mime_types.get(ext, 'application/octet-stream')
                                    content_html += f'''<a href="data:{mime_type};base64,{file_b64}" download="{file_name}" 
                                        style="display:inline-block; color:#007bff; padding:4px 0; 
                                        text-decoration:underline; font-weight:500; margin:5px 0; cursor:pointer; 
                                        transition: all 0.2s ease;">
                                        📎 {file_name}
                                    </a>'''
                                except Exception as e:
                                    content_html += f"<span style='color:#999;'>⚠ Error loading file</span>"
                            else:
                                content_html += f"<span style='color:#999;'>⚠ File tidak ditemukan</span>"
                        else:
                            content_html += the_msg
                    else:
                        content_html += the_msg
                        
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                            <div style="background-color: {bg_color}; padding: 12px 15px; border-radius: 15px; 
                                max-width: 80%; color: {text_color}; box-shadow: {shadow}; 
                                border-left: 4px solid {border_color};">
                                {msg_html}
                                <div style='margin:2px 0 0 0; word-break: break-word;'>{content_html}</div>
                                <small style='display: block; text-align: right; color: #888; font-size: 0.7em; margin-top: 5px;'>{msg['timestamp']}</small>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            with st.form("direct_chat_form", clear_on_submit=True):
                c1, c2 = st.columns([5,2])
                with c1:
                    message = st.text_input("Ketik pesan dan tekan Enter...", key="direct_chat_input")
                with c2:
                    uploaded_file = st.file_uploader("", key="direct_chat_file", label_visibility="collapsed")
                submit_button = st.form_submit_button("Kirim", use_container_width=True)
                if submit_button and (message or uploaded_file):
                    file_link = None
                    img_file = None
                    if uploaded_file:
                        import uuid
                        filename = f"chat_{uuid.uuid4().hex}_{uploaded_file.name}"
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        if uploaded_file.type.startswith("image/"):
                            img_file = filepath
                        else:
                            file_link = filepath
                    mix_msg = message if message else ""
                    if img_file:
                        mix_msg += f" [IMAGE]{img_file}"
                    elif file_link:
                        mix_msg += f" [FILE]{file_link}|{uploaded_file.name}"
                    send_direct_message(st.session_state.current_user['id'], receiver_id, mix_msg)
                    st.rerun()
        else:
            st.info("Pilih pengguna dari daftar kontak di samping untuk memulai obrolan.")

# --- Navigasi Sidebar ---
def nav_sidebar():
    st.sidebar.image("gambarlogo.png", width = 200)
    st.sidebar.header("Navigasi")
    
    if st.sidebar.button("Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.session_state.selected_project_id = None
        st.session_state.selected_chat_partner = None
        st.rerun()
        
    if st.sidebar.button("Proyek", use_container_width=True):
        st.session_state.page = "projects"
        st.session_state.selected_project_id = None
        st.session_state.selected_chat_partner = None
        st.rerun()
        
    user_role = st.session_state.current_user['role']
    if user_role in ['Admin', 'Manager']:
        if st.sidebar.button("Manajemen Pengguna", use_container_width=True):
            st.session_state.page = "user_management"
            st.session_state.selected_project_id = None
            st.session_state.selected_chat_partner = None
            st.rerun()

    unread_counts = get_unread_direct_messages_count(st.session_state.current_user['id'])
    total_unread = sum(unread_counts.values())
    chat_label = f"Obrolan Langsung {'(💬 ' + str(total_unread) + ')' if total_unread > 0 else ''}"
    if st.sidebar.button(chat_label, use_container_width=True):
        st.session_state.page = "direct_chat"
        st.session_state.selected_project_id = None
        st.rerun()
        
    if st.sidebar.button("Jejak Audit", use_container_width=True):
        st.session_state.page = "audit_trail"
        st.session_state.selected_project_id = None
        st.session_state.selected_chat_partner = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Keluar", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.page = "login"
        st.session_state.selected_project_id = None
        st.session_state.selected_chat_partner = None
        st.rerun()

# --- Main App ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = None
if 'edit_project_id' not in st.session_state:
    st.session_state.edit_project_id = None
if 'edit_task_id' not in st.session_state:
    st.session_state.edit_task_id = None
if 'selected_chat_partner' not in st.session_state:
    st.session_state.selected_chat_partner = None
if 'show_user_search' not in st.session_state:
    st.session_state.show_user_search = False

if not st.session_state.logged_in:
    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "register":
        show_register_page()
else:
    nav_sidebar()
    if st.session_state.edit_project_id:
        show_edit_project_page(st.session_state.edit_project_id)
    elif st.session_state.edit_task_id:
        show_edit_task_page(st.session_state.edit_task_id)
    elif st.session_state.selected_project_id:
        show_project_details(st.session_state.selected_project_id)
    else:
        if st.session_state.page == "dashboard":
            show_dashboard()
        elif st.session_state.page == "projects":
            show_projects_page()
        elif st.session_state.page == "user_management":
            show_user_management_page()
        elif st.session_state.page == "audit_trail":
            show_audit_trail_page()
        elif st.session_state.page == "direct_chat":
            show_direct_chat_page()
        else:
            show_dashboard()

# --- Tambahkan kode ini di bagian paling bawah file app.py Anda ---

# Footer
st.markdown("""
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f0f2f6; /* Warna latar belakang footer */
            color: #333; /* Warna teks */
            text-align: center;
            padding: 5px;
            font-size: 14px;
            border-top: 1px solid #ddd;
        }
        .footer p {
            margin-bottom: 2px; /* Mengurangi jarak di bawah setiap paragraf */
            line-height: 1.2;  /* Mengatur jarak antar baris teks */
        }
        .footer a {
            color: #4b89ff; /* Warna tautan */
            text-decoration: none;
            font-weight: bold;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
    <div class="footer">
        <p>Credit to <b>Galih Primananda</b></p>
        <p>
            <a href="https://instagram.com/glh_prima/" target="_blank">Instagram</a> |
            <a href="https://linkedin.com/in/galihprime/" target="_blank">LinkedIn</a> |
            <a href="https://github.com/PrimeFox59" target="_blank">GitHub</a> |
            <a href="https://drive.google.com/drive/folders/11ov7TpvOZ3m7k5GLRAbE2WZFbGVK2t7i?usp=sharing" target="_blank">Portfolio</a> |
            <a href="https://fastwork.id/user/glh_prima" target="_blank">Fastwork for Services & Collaboration</a>
        </p>
    </div>
""", unsafe_allow_html=True)