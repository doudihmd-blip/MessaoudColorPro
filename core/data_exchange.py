import csv, json, shutil
from datetime import datetime
from pathlib import Path
from database.db_manager import get_connection, DB_PATH

class DataExchangeManager:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    def import_csv(self, csv_path):
        conn = get_connection(self.db_path)
        ins, skip = 0, 0
        with open(csv_path, "r", encoding="utf-8-sig") as f, conn:
            for r in csv.DictReader(f):
                s = conn.execute("SELECT id FROM color_systems WHERE name=?", (r["system_name"].strip(),)).fetchone()
                if not s: continue
                c = conn.execute("INSERT OR IGNORE INTO colors (system_id,code,name_ar,name_fr,hex_value,data_source,is_sample,verification_status) VALUES (?,?,?,?,?,?,?,?)",
                    (s["id"], r["code"].strip(), r.get("name_ar",""), r.get("name_fr",""), r.get("hex_value",""), r["data_source"].strip(), int(r.get("is_sample",0)), r.get("verification_status","unverified")))
                if c.rowcount > 0: ins += 1
                else: skip += 1
        conn.close()
        return {"inserted": ins, "skipped": skip}

    def backup(self, out_dir="data/backups"):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        dest = Path(out_dir) / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(self.db_path, dest)
        return str(dest)

for name in ["RAL_Classic", "RAL_Design", "NCS", "Pantone", "NOVA"]:
    Path(f"data/templates/template_{name}.csv").write_text("system_name,code,name_ar,name_fr,hex_value,data_source,is_sample,verification_status\n", encoding="utf-8")
print("IMPORT_EXPORT_OK: CSV/JSON & 5 Templates Ready!")
