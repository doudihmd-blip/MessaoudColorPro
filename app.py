import http.server, socketserver, json, urllib.parse
from pathlib import Path
from database.db_manager import init_db, get_connection
from core.formula_engine import FormulaEngine
from core.data_exchange import DataExchangeManager

PORT = 8080

def seed_demo():
    init_db()
    conn = get_connection()
    with conn:
        conn.execute("INSERT OR IGNORE INTO colors (id,system_id,code,name_ar,name_fr,hex_value,data_source,is_sample,verification_status) VALUES (1,1,'RAL 1015','عاجي فاتح (عينة اختبارية)','Ivoire clair (Échantillon)','#E6D690','WORKSHOP_SAMPLE',1,'verified'),(2,3,'NCS S 1050-Y90R','أحمر طوبي (مرئي فقط بدون وصفة)','Rouge brique (Visuel)','#9E3A26','NCS_DEMO',1,'unverified')")
        conn.execute("INSERT OR IGNORE INTO paint_products (id,name,brand,category,finish_type) VALUES (1,'Satin Pro Interior','Messaoud Colors','Water-Based','Satin')")
        conn.execute("INSERT OR IGNORE INTO paint_bases (id,product_id,base_code,density_g_ml,price_per_unit_dzd,pricing_unit,packaging_cost_dzd,preparation_cost_dzd) VALUES (1,1,'Base P (Pastel)',1.38,380.0,'KG',150.0,100.0),(2,1,'Base TR (Transparent)',1.25,420.0,'L',150.0,100.0)")
        conn.execute("INSERT OR IGNORE INTO colorants (id,trade_name,manufacturer,code,approx_hex,price_dzd,price_unit,density_g_ml) VALUES (1,'Ocre Jaune WB','ChromaLab','OJ-10','#D4AF37',4800.0,'L',1.22),(2,'Oxyde Rouge WB','ChromaLab','OR-20','#A52A2A',5200.0,'KG',1.35)")
        conn.execute("INSERT OR IGNORE INTO formulas (id,color_id,base_id,reference_volume_l,min_valid_volume_l,max_valid_volume_l,formula_source,approval_status) VALUES (1,1,1,1.0,0.5,25.0,'تعيير ورشة مسعود #01','approved')")
        conn.execute("INSERT OR IGNORE INTO formula_items (id,formula_id,colorant_id,amount,unit) VALUES (1,1,1,8.5,'ml')")
    conn.close()

class Handler(http.server.SimpleHTTPRequestHandler):
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(Path("ui/index.html").read_bytes())
        elif p.path == "/api/data":
            conn = get_connection()
            data = {
                "systems": [dict(r) for r in conn.execute("SELECT * FROM color_systems").fetchall()],
                "colors": [dict(r) for r in conn.execute("SELECT c.*, s.name as sys_name FROM colors c JOIN color_systems s ON c.system_id=s.id").fetchall()],
                "bases": [dict(r) for r in conn.execute("SELECT * FROM paint_bases").fetchall()],
                "colorants": [dict(r) for r in conn.execute("SELECT * FROM colorants").fetchall()],
                "orders": [dict(r) for r in conn.execute("SELECT * FROM tinting_orders ORDER BY id DESC LIMIT 20").fetchall()]
            }
            conn.close()
            self.send_json(data)
        elif p.path == "/api/calc":
            q = urllib.parse.parse_qs(p.query)
            res = FormulaEngine().compute_tinting_formula(int(q["cid"][0]), int(q["bid"][0]), float(q["vol"][0]), float(q.get("margin",[25])[0]))
            if res.get("success") and q.get("save",[0])[0] == "1":
                cb = res["cost_breakdown"]
                conn = get_connection()
                with conn:
                    conn.execute("INSERT INTO tinting_orders (formula_id,target_volume_l,total_cost_dzd,selling_price_dzd,profit_margin_dzd) VALUES (?,?,?,?,?)", (1, float(q["vol"][0]), cb["total_cost_dzd"], cb["selling_price_dzd"], cb["profit_margin_dzd"]))
                conn.close()
            self.send_json(res)
        elif p.path == "/api/backup":
            b = DataExchangeManager().backup()
            self.send_json({"success": True, "path": b})
        else:
            self.send_error(404)

if __name__ == "__main__":
    seed_demo()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as s:
        print(f"SERVER_READY: http://127.0.0.1:{PORT}")
        s.serve_forever()
