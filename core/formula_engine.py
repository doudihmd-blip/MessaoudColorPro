from database.db_manager import get_connection

UNAPPROVED_MSG_AR = "لا توجد تركيبة معتمدة لهذا اللون ضمن نظام الدهان والقاعدة المختارين."

class FormulaEngine:
    def __init__(self, db_path=None):
        self.db_path = db_path

    @staticmethod
    def convert_units(amount, from_u, to_u, density):
        if from_u.lower() == to_u.lower(): return round(amount, 4)
        if density <= 0: raise ValueError("Density must be > 0")
        return round(amount * density, 4) if from_u.lower() == "ml" else round(amount / density, 4)

    @staticmethod
    def unit_cost(price_dzd, price_unit, density, target_unit):
        pu, tu = price_unit.upper(), target_unit.lower()
        if pu == "L": c_ml = price_dzd / 1000.0; c_g = c_ml / density
        elif pu == "ML": c_ml = price_dzd; c_g = c_ml / density
        elif pu == "KG": c_g = price_dzd / 1000.0; c_ml = c_g * density
        else: c_g = price_dzd; c_ml = c_g * density
        return c_ml if tu == "ml" else c_g

    def compute_tinting_formula(self, color_id, base_id, target_volume_l, profit_margin_pct=25.0):
        conn = get_connection(self.db_path)
        try:
            f = conn.execute("""
                SELECT f.*, c.code as color_code, c.name_ar, b.base_code, b.density_g_ml as base_density,
                       b.price_per_unit_dzd as base_price, b.pricing_unit, b.packaging_cost_dzd, b.preparation_cost_dzd
                FROM formulas f JOIN colors c ON f.color_id=c.id JOIN paint_bases b ON f.base_id=b.id
                WHERE f.color_id=? AND f.base_id=? AND f.approval_status='approved' LIMIT 1
            """, (color_id, base_id)).fetchone()
            if not f: return {"success": False, "message": UNAPPROVED_MSG_AR}
            if not (f["min_valid_volume_l"] <= target_volume_l <= f["max_valid_volume_l"]):
                return {"success": False, "message": "الحجم خارج مجال التناسب الخطي المعتمد."}
            items = conn.execute("""
                SELECT fi.*, col.trade_name, col.code as c_code, col.price_dzd, col.price_unit, col.density_g_ml
                FROM formula_items fi JOIN colorants col ON fi.colorant_id=col.id WHERE fi.formula_id=?
            """, (f["id"],)).fetchall()
            if not items: return {"success": False, "message": UNAPPROVED_MSG_AR}
            scale = target_volume_l / f["reference_volume_l"]
            out_items, col_cost = [], 0.0
            for it in items:
                amt = round(it["amount"] * scale, 3)
                u, d = it["unit"], it["density_g_ml"]
                ml = amt if u == "ml" else self.convert_units(amt, "g", "ml", d)
                g = amt if u == "g" else self.convert_units(amt, "ml", "g", d)
                cost = round(amt * self.unit_cost(it["price_dzd"], it["price_unit"], d, u), 2)
                col_cost += cost
                out_items.append({"colorant_code": it["c_code"], "trade_name": it["trade_name"], "amount_ml": ml, "amount_g": g, "cost_dzd": cost})
            b_cost = round(target_volume_l * f["base_price"], 2) if f["pricing_unit"].upper() == "L" else round(target_volume_l * f["base_density"] * f["base_price"], 2)
            tot_cost = round(b_cost + col_cost + f["packaging_cost_dzd"] + f["preparation_cost_dzd"], 2)
            sell = round(tot_cost * (1 + profit_margin_pct / 100.0), 2)
            return {
                "success": True, "color_code": f["color_code"], "color_name_ar": f["name_ar"], "base_code": f["base_code"],
                "target_volume_l": target_volume_l, "colorants": out_items,
                "cost_breakdown": {"base_cost_dzd": b_cost, "colorants_cost_dzd": round(col_cost, 2), "packaging_cost_dzd": f["packaging_cost_dzd"], "preparation_cost_dzd": f["preparation_cost_dzd"], "total_cost_dzd": tot_cost, "selling_price_dzd": sell, "profit_margin_dzd": round(sell - tot_cost, 2)}
            }
        finally:
            conn.close()
print("ENGINE_OK: Formula & Costing Engine Ready!")
