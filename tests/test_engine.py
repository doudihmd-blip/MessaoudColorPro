import unittest, tempfile
from pathlib import Path
from database.db_manager import init_db, get_connection
from core.formula_engine import FormulaEngine, UNAPPROVED_MSG_AR

class TestMCP(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        init_db(self.db)
        self.eng = FormulaEngine(self.db)
        conn = get_connection(self.db)
        with conn:
            conn.execute("INSERT INTO colors (id,system_id,code,name_ar,data_source,is_sample,verification_status) VALUES (1,1,'RAL 1015','عاجي تجريبي','TEST_LAB',1,'verified'),(2,1,'RAL 5012','أزرق مرئي فقط','VISUAL',1,'unverified')")
            conn.execute("INSERT INTO paint_products (id,name,brand,category) VALUES (1,'Satin Pro','Messaoud','Satin')")
            conn.execute("INSERT INTO paint_bases (id,product_id,base_code,density_g_ml,price_per_unit_dzd,pricing_unit,packaging_cost_dzd,preparation_cost_dzd) VALUES (1,1,'Base P',1.40,350.0,'KG',120.0,80.0)")
            conn.execute("INSERT INTO colorants (id,trade_name,manufacturer,code,price_dzd,price_unit,density_g_ml) VALUES (1,'Yellow Oxide','Chroma','YO1',4500.0,'L',1.25)")
            conn.execute("INSERT INTO formulas (id,color_id,base_id,reference_volume_l,min_valid_volume_l,max_valid_volume_l,formula_source,approval_status) VALUES (1,1,1,1.0,0.5,20.0,'Lab #1','approved')")
            conn.execute("INSERT INTO formula_items (formula_id,colorant_id,amount,unit) VALUES (1,1,10.0,'ml')")
        conn.close()

    def tearDown(self): self.tmp.cleanup()

    def test_unit_conversion(self):
        self.assertEqual(self.eng.convert_units(10.0, "ml", "g", 1.25), 12.5)
        self.assertEqual(self.eng.convert_units(12.5, "g", "ml", 1.25), 10.0)

    def test_approved_formula_and_dzd_cost(self):
        r = self.eng.compute_tinting_formula(1, 1, 4.0, 25.0)
        self.assertTrue(r["success"])
        self.assertEqual(r["colorants"][0]["amount_ml"], 40.0)
        self.assertEqual(r["colorants"][0]["amount_g"], 50.0)
        self.assertEqual(r["cost_breakdown"]["base_cost_dzd"], 1960.0)
        self.assertEqual(r["cost_breakdown"]["colorants_cost_dzd"], 180.0)

    def test_reject_unapproved_color(self):
        r = self.eng.compute_tinting_formula(2, 1, 1.0)
        self.assertFalse(r["success"])
        self.assertEqual(r["message"], UNAPPROVED_MSG_AR)

if __name__ == "__main__":
    unittest.main(verbosity=2)
