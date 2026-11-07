"""Automatic tests for CSV import and the command-line options.  Run:  python -m unittest -v"""
import contextlib
import glob
import io
import os
import tempfile
import unittest
from datetime import date

import main as app
from customer_manager import CustomerManager
from export_manager import ExportManager
from import_manager import MAX_ROWS, ImportManager
from models import ValidationError
from program_manager import ProgramManager
from service_manager import ServiceManager
from storage import DataStore

DAY = lambda: date(2026, 11, 7)


def write(path, text, encoding="utf-8"):
    with open(path, "w", encoding=encoding, newline="") as file:
        file.write(text)


def build(store):
    return CustomerManager(store, DAY), ServiceManager(store, DAY), ProgramManager(store, DAY)


class ImportBase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = DataStore(None)
        self.customers, self.services, self.programs = build(self.store)
        self.importer = ImportManager(self.customers, self.services, self.programs)

    def file(self, name, text, **kw):
        path = os.path.join(self.folder.name, name)
        write(path, text, **kw)
        return path


class ImportTests(ImportBase):
    CUSTOMERS = "name,kind,email,phone,city\nNeha Joshi,Individual,neha@example.com,+91 98765 10013,Indore\nOrbit Labs,Business,team@orbit.example,+91 98765 10015,Pune\n"

    def test_good_rows_are_imported(self):
        result = self.importer.import_csv("customers", self.file("c.csv", self.CUSTOMERS))
        self.assertEqual(result.added, ["CU-001", "CU-002"])
        self.assertEqual(result.skipped, [])
        self.assertEqual(self.customers.get("CU-002").kind, "Business")

    def test_bad_rows_are_skipped_with_row_numbers_and_good_rows_still_import(self):
        text = ("name,kind,email,phone,city\n"
                "Good Person,Individual,good@example.com,+91 98765 10001,Indore\n"      # row 2 ok
                "Copy Cat,Individual,GOOD@example.com,+91 98765 10002,Indore\n"         # row 3 duplicate e-mail
                "Bad Mail,Individual,nope,+91 98765 10003,Indore\n"                     # row 4 bad e-mail
                "Wrong Type,Company,type@example.com,+91 98765 10004,Pune\n"            # row 5 bad type
                ",,,,\n"                                                                # row 6 empty
                "Short Phone,Individual,short@example.com,123,Pune\n")                  # row 7 bad phone
        result = self.importer.import_csv("customers", self.file("c.csv", text))
        self.assertEqual(result.added, ["CU-001"])
        self.assertEqual([row for row, _ in result.skipped], [3, 4, 5, 6, 7])
        self.assertEqual(dict(result.skipped)[6], "empty row")
        self.assertEqual(len(self.customers.all()), 1)

    def test_importing_twice_is_safe(self):
        path = self.file("c.csv", self.CUSTOMERS)
        self.importer.import_csv("customers", path)
        again = self.importer.import_csv("customers", path)
        self.assertEqual(again.added, [])
        self.assertEqual(len(again.skipped), 2)
        self.assertEqual(len(self.customers.all()), 2)

    def test_headers_are_not_case_sensitive_extra_columns_and_bom_are_ok(self):
        text = "id,NAME, Kind ,Email,PHONE,City,created\nCU-099,Neha Joshi,Individual,neha@example.com,+91 98765 10013,Indore,2020-01-01\n"
        result = self.importer.import_csv("customers", self.file("c.csv", text, encoding="utf-8-sig"))
        self.assertEqual(result.added, ["CU-001"])                       # a new ID is given, the id column is ignored
        self.assertNotEqual(self.customers.get("CU-001").created, "2020-01-01")

    def test_services_and_programs(self):
        services = self.importer.import_csv("services", self.file("s.csv", "name,category,description,price,delivery_days\nChatbot,Development,Support chatbot,25000,20\n"))
        programs = self.importer.import_csv("programs", self.file("p.csv", "name,type,description,duration_days,fee,seats,start_date\nGit Workshop,Training,Version control basics,5,500,30,2026-12-15\n"))
        self.assertEqual((services.added, programs.added), (["SV-001"], ["PR-001"]))
        self.assertEqual(self.programs.get("PR-001").seats, 30)

    def test_problems_with_the_file_itself(self):
        cases = {
            "missing columns": self.file("a.csv", "name,email\nA,a@example.com\n"),
            "empty file": self.file("b.csv", ""),
            "not a text file": self.file("c.bin", "", encoding="utf-8"),
        }
        with open(cases["not a text file"], "wb") as file:
            file.write(b"\xff\xfe\x00\x81\x82")
        for label, path in cases.items():
            with self.subTest(label), self.assertRaises(ValidationError):
                self.importer.import_csv("customers", path)
        with self.assertRaises(ValidationError):
            self.importer.import_csv("customers", os.path.join(self.folder.name, "nope.csv"))
        with self.assertRaises(ValidationError):
            self.importer.import_csv("inquiries", cases["missing columns"])
        with self.assertRaises(ValidationError):
            self.importer.import_csv("customers", self.folder.name)              # a folder, not a file

    def test_row_limit(self):
        rows = "".join(f"P{i},Individual,p{i}@example.com,+91 98765 {10000 + i},Indore\n" for i in range(MAX_ROWS + 1))
        with self.assertRaises(ValidationError):
            self.importer.import_csv("customers", self.file("big.csv", "name,kind,email,phone,city\n" + rows))
        self.assertEqual(self.customers.all(), [])                               # nothing was imported

    def test_export_protection_is_removed_on_import(self):
        self.assertEqual(ImportManager.clean("'=A1"), "=A1")
        self.assertEqual(ImportManager.clean("'hello"), "'hello")
        self.assertEqual(ImportManager.clean("  x  "), "x")
        self.assertEqual(ImportManager.clean(None), "")

    def test_exported_files_can_be_imported_into_an_empty_system(self):
        self.customers.add("Aarav Sharma", "Individual", "aarav@example.com", "+91 98765 10001", "Indore")
        self.services.add("Website Development", "Development", "Business website", "15000", "15")
        self.programs.add("Python Training", "Training", "Python basics", "30", "2500", "20", "2026-12-01")
        folder, _ = ExportManager(self.store, DAY).export_csv(os.path.join(self.folder.name, "out"))
        other = DataStore(None)
        importer = ImportManager(*build(other))
        for kind in ("customers", "services", "programs"):
            self.assertEqual(len(importer.import_csv(kind, os.path.join(folder, f"{kind}.csv")).added), 1, kind)
        self.assertEqual(other.all("services")[0].price, self.store.all("services")[0].price)
        self.assertEqual(other.all("programs")[0].fee, self.store.all("programs")[0].fee)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "data.json")
        store = DataStore(self.path)
        CustomerManager(store, DAY).add("Aarav Sharma", "Individual", "aarav@example.com", "+91 98765 10001", "Indore")

    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            app.main(["--data", self.path, *args])
        return out.getvalue()

    def test_report(self):
        text = self.run_main("--report")
        self.assertIn("BUSINESS OVERVIEW", text)
        self.assertIn("Customers        : 1", text)

    def test_export_and_backup(self):
        text = self.run_main("--export", "--backup")
        self.assertIn("customers: 1", text)
        self.assertEqual(len(glob.glob(os.path.join(self.folder.name, "exports", "*", "customers.csv"))), 1)
        self.assertEqual(len(glob.glob(os.path.join(self.folder.name, "backups", "business_data_*.json"))), 1)

    def test_missing_data_file_and_bad_option(self):
        with self.assertRaises(SystemExit):
            app.main(["--data", os.path.join(self.folder.name, "nope.json"), "--report"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            app.main(["--unknown"])


if __name__ == "__main__":
    unittest.main()