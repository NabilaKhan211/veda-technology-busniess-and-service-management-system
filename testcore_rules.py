"""Automatic tests for the core business rules, storage safety and export/backup.  Run:  python -m unittest -v"""
import csv
import json
import os
import tempfile
import unittest
from datetime import date

from customer_manager import CustomerManager
from export_manager import ExportManager
from inquiry_manager import InquiryManager, RequestManager
from models import BusinessError, NotFoundError, RuleError, ValidationError
from program_manager import ProgramManager
from service_manager import ServiceManager
from storage import DataStore

DAY = lambda: date(2026, 11, 6)


def read(path, encoding="utf-8-sig"):
    with open(path, encoding=encoding) as file:
        return file.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


class Base(unittest.TestCase):
    def setUp(self):
        self.store = DataStore(None)
        self.customers, self.services = CustomerManager(self.store, DAY), ServiceManager(self.store, DAY)
        self.programs, self.inquiries = ProgramManager(self.store, DAY), InquiryManager(self.store, DAY)
        self.requests = RequestManager(self.store, DAY)
        self.c1 = self.customers.add("Aarav Sharma", "Individual", "aarav@example.com", "+91 98765 10001", "Indore")
        self.c2 = self.customers.add("Bright Academy", "Business", "info@bright.example", "+91 98765 10002", "Bhopal")
        self.sv = self.services.add("Website Development", "Development", "Business website", "15000", "15")
        self.pr = self.programs.add("Python Training", "Training", "Python basics", "30", "2500", "2", "2026-12-01")


class CustomerTests(Base):
    def test_email_must_be_valid_and_unique(self):
        with self.assertRaises(ValidationError):
            self.customers.add("Bad Mail", "Individual", "not-an-email", "+91 98765 10003", "Indore")
        with self.assertRaises(RuleError):
            self.customers.add("Copy Cat", "Individual", "AARAV@example.com", "+91 98765 10003", "Indore")

    def test_ids_are_never_reused(self):
        self.customers.delete(self.c2.id)
        self.assertEqual(self.customers.add("New Person", "Individual", "new@example.com", "+91 98765 10009", "Delhi").id, "CU-003")

    def test_customer_with_history_cannot_be_deleted(self):
        self.inquiries.create(self.c1.id, "General", "", "Working hours?")
        with self.assertRaises(RuleError):
            self.customers.delete(self.c1.id)
        self.assertEqual(self.customers.delete(self.c2.id).id, self.c2.id)

    def test_unknown_field_and_missing_record(self):
        with self.assertRaises(ValidationError):
            self.customers.update(self.c1.id, id="CU-999")
        with self.assertRaises(NotFoundError):
            self.customers.get("CU-404")


class ServiceTests(Base):
    def test_unique_name_and_validation(self):
        with self.assertRaises(RuleError):
            self.services.add("website development", "Design", "Copy", "100", "3")
        with self.assertRaises(ValidationError):
            self.services.add("Bad Price", "Design", "x", "-5", "3")

    def test_status_flow_and_retired_is_frozen(self):
        self.services.set_status(self.sv.id, "Paused")
        self.services.set_status(self.sv.id, "Retired")
        with self.assertRaises(BusinessError):
            self.services.set_status(self.sv.id, "Active")
        with self.assertRaises(RuleError):
            self.services.update(self.sv.id, price="1")

    def test_service_in_use_cannot_be_deleted(self):
        self.requests.create(self.c1.id, self.sv.id, "Site")
        with self.assertRaises(RuleError):
            self.services.delete(self.sv.id)


class ProgramTests(Base):
    def test_enrol_rules(self):
        self.programs.enrol(self.pr.id, self.c1.id)
        with self.assertRaises(RuleError):                       # twice
            self.programs.enrol(self.pr.id, self.c1.id)
        self.programs.enrol(self.pr.id, self.c2.id)
        self.assertEqual(self.programs.get(self.pr.id).effective_status(), "Full")
        extra = self.customers.add("Third Person", "Individual", "third@example.com", "+91 98765 10003", "Delhi")
        with self.assertRaises(RuleError):                       # full
            self.programs.enrol(self.pr.id, extra.id)

    def test_closed_program_takes_no_enrolments_and_withdraw_frees_seat(self):
        self.programs.enrol(self.pr.id, self.c1.id)
        self.programs.withdraw(self.pr.id, self.c1.id)
        self.assertEqual(self.programs.get(self.pr.id).seats_left(), 2)
        self.programs.set_status(self.pr.id, "Closed")
        with self.assertRaises(RuleError):
            self.programs.enrol(self.pr.id, self.c1.id)

    def test_seats_cannot_drop_below_enrolled_and_completed_is_frozen(self):
        self.programs.enrol(self.pr.id, self.c1.id)
        self.programs.enrol(self.pr.id, self.c2.id)
        with self.assertRaises(BusinessError):
            self.programs.update(self.pr.id, seats="1")
        self.programs.set_status(self.pr.id, "Completed")
        with self.assertRaises(RuleError):
            self.programs.update(self.pr.id, fee="1")
        with self.assertRaises(RuleError):
            self.programs.withdraw(self.pr.id, self.c1.id)

    def test_program_with_enrolments_cannot_be_deleted(self):
        self.programs.enrol(self.pr.id, self.c1.id)
        with self.assertRaises(RuleError):
            self.programs.delete(self.pr.id)


class InquiryTests(Base):
    def test_reference_must_exist_and_topic_decides_reference(self):
        with self.assertRaises(NotFoundError):
            self.inquiries.create(self.c1.id, "Service", "SV-404", "Hello")
        self.assertEqual(self.inquiries.create(self.c1.id, "General", "SV-001", "Hello").reference, "")

    def test_status_flow_and_resolved_date(self):
        iq = self.inquiries.create(self.c1.id, "Service", self.sv.id, "Timeline?")
        with self.assertRaises(BusinessError):                   # New -> Resolved is not allowed
            self.inquiries.set_status(iq.id, "Resolved")
        self.inquiries.set_status(iq.id, "In Progress")
        self.assertEqual(self.inquiries.set_status(iq.id, "Resolved").resolved_on, "2026-11-06")
        self.assertEqual(self.inquiries.set_status(iq.id, "In Progress").resolved_on, "")        # reopened
        self.inquiries.set_status(iq.id, "Closed")
        with self.assertRaises(RuleError):
            self.inquiries.add_note(iq.id, "too late")


class RequestTests(Base):
    def test_default_quote_and_due_date(self):
        rq = self.requests.create(self.c1.id, self.sv.id, "Five pages")
        self.assertEqual(str(rq.quote), "15000.00")
        self.assertEqual(rq.due_date, "2026-11-21")              # 6 Nov + 15 delivery days

    def test_only_active_service_can_be_requested(self):
        self.services.set_status(self.sv.id, "Paused")
        with self.assertRaises(RuleError):
            self.requests.create(self.c1.id, self.sv.id, "Site")

    def test_due_date_cannot_be_before_request_date(self):
        with self.assertRaises(ValidationError):
            self.requests.create(self.c1.id, self.sv.id, "Site", None, "2026-11-01")

    def test_status_flow_quote_rule_and_completed_date(self):
        rq = self.requests.create(self.c1.id, self.sv.id, "Site")
        self.requests.update_quote(rq.id, "14000")
        for status in ("Approved", "In Progress", "Completed"):
            self.requests.set_status(rq.id, status)
        self.assertEqual(self.requests.get(rq.id).completed_on, "2026-11-06")
        with self.assertRaises(BusinessError):
            self.requests.set_status(rq.id, "In Progress")
        with self.assertRaises(RuleError):
            self.requests.update_quote(rq.id, "1")


class StorageTests(Base):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            store = DataStore(path)
            ServiceManager(store, DAY).add("Cloud Setup", "Cloud", "Hosting", "6000", "5")
            self.assertFalse(os.path.exists(path + ".tmp"))
            again = DataStore(path)
            self.assertEqual(again.load(), [])
            self.assertEqual(again.all("services")[0].name, "Cloud Setup")

    def test_damaged_file_is_kept_aside(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            write(path, "{ this is not json")
            messages = DataStore(path).load()
            self.assertEqual(len(messages), 1)
            self.assertTrue(os.path.exists(path + ".corrupt"))

    def test_dangling_reference_is_skipped_with_a_message(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            bad = {"version": 1, "counters": {}, "inquiries": [{
                "id": "IQ-001", "customer_id": "CU-404", "topic": "General", "reference": "", "message": "Hi",
                "priority": "Low", "status": "New", "created": "2026-11-01", "updated": "2026-11-01", "resolved_on": "", "notes": []}]}
            write(path, json.dumps(bad))
            store = DataStore(path)
            messages = store.load()
            self.assertTrue(any("IQ-001" in m for m in messages))
            self.assertEqual(store.all("inquiries"), [])
            self.assertTrue(os.path.exists(path + ".bak"))


class ExportTests(Base):
    def test_csv_export(self):
        self.programs.enrol(self.pr.id, self.c1.id)
        self.inquiries.create(self.c1.id, "General", "", "=HYPERLINK(\"http://x\")")
        with tempfile.TemporaryDirectory() as folder:
            _, counts = ExportManager(self.store, DAY).export_csv(folder)
            self.assertEqual(counts, {"customers": 2, "services": 1, "programs": 1, "inquiries": 1, "requests": 0})
            rows = list(csv.reader(read(os.path.join(folder, "customers.csv")).splitlines()))
            self.assertEqual(len(rows), 3)                       # header + 2 customers
            self.assertEqual(rows[1][rows[0].index("phone")], "+91 98765 10001")   # phones are not changed
            self.assertIn("CU-001", read(os.path.join(folder, "programs.csv")))
            self.assertIn("'=HYPERLINK", read(os.path.join(folder, "inquiries.csv")))
            self.assertTrue(os.path.exists(os.path.join(folder, "requests.csv")))   # empty file still has a header

    def test_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            store = DataStore(os.path.join(folder, "data.json"))
            ServiceManager(store, DAY).add("Cloud Setup", "Cloud", "Hosting", "6000", "5")
            path = ExportManager(store, DAY).backup(os.path.join(folder, "backups"))
            self.assertIn("business_data_20261106_", path)
            self.assertEqual(json.loads(read(path))["services"][0]["name"], "Cloud Setup")
        with self.assertRaises(RuleError):
            ExportManager(DataStore(None), DAY).backup()


if __name__ == "__main__":
    unittest.main()