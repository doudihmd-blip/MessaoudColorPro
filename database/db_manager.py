import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "messaoud_color_pro.db"

def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS color_systems (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, code_prefix TEXT, description TEXT, license_notes TEXT);
        CREATE TABLE IF NOT EXISTS colors (id INTEGER PRIMARY KEY AUTOINCREMENT, system_id INTEGER, code TEXT, name_ar TEXT, name_fr TEXT, rgb_r INT, rgb_g INT, rgb_b INT, hex_value TEXT, lab_l REAL, lab_a REAL, lab_b REAL, data_source TEXT, is_sample INT DEFAULT 0, verification_status TEXT DEFAULT 'unverified', UNIQUE(system_id, code));
        CREATE TABLE IF NOT EXISTS paint_products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, brand TEXT, category TEXT, finish_type TEXT);
        CREATE TABLE IF NOT EXISTS paint_bases (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, base_code TEXT, density_g_ml REAL DEFAULT 1.35, price_per_unit_dzd REAL, pricing_unit TEXT, packaging_cost_dzd REAL DEFAULT 0, preparation_cost_dzd REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS colorants (id INTEGER PRIMARY KEY AUTOINCREMENT, trade_name TEXT, manufacturer TEXT, code TEXT UNIQUE, approx_hex TEXT, price_dzd REAL, price_unit TEXT, density_g_ml REAL DEFAULT 1.15, pigment_concentration_pct REAL, colorant_type TEXT DEFAULT 'Water-Based', price_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS formulas (id INTEGER PRIMARY KEY AUTOINCREMENT, color_id INTEGER, base_id INTEGER, reference_volume_l REAL DEFAULT 1.0, min_valid_volume_l REAL DEFAULT 0.5, max_valid_volume_l REAL DEFAULT 25.0, formula_source TEXT, confidence_score INT DEFAULT 100, approval_status TEXT DEFAULT 'pending', notes TEXT);
        CREATE TABLE IF NOT EXISTS formula_items (id INTEGER PRIMARY KEY AUTOINCREMENT, formula_id INTEGER, colorant_id INTEGER, amount REAL, unit TEXT);
        CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, contact_info TEXT);
        CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT, item_id INTEGER, old_price_dzd REAL, new_price_dzd REAL, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, phone TEXT, city TEXT DEFAULT 'Hassi Messaoud');
        CREATE TABLE IF NOT EXISTS tinting_orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, formula_id INTEGER, target_volume_l REAL, total_cost_dzd REAL, selling_price_dzd REAL, profit_margin_dzd REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS formula_tests (id INTEGER PRIMARY KEY AUTOINCREMENT, formula_id INTEGER, delta_e_visual TEXT, coverage_rating INT, adjustment_notes TEXT, tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        """)
        for s in [("RAL Classic","RAL"),("RAL Design","RAL-D"),("NCS","NCS"),("Pantone","PMS"),("NOVA","NOVA")]:
            conn.execute("INSERT OR IGNORE INTO color_systems (name, code_prefix) VALUES (?,?)", s)
    conn.close()
    print("DB_OK: 13 Tables & 5 Color Systems Ready!")

if __name__ == "__main__":
    init_db()
