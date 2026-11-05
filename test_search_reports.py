"""Automatic tests for search/filtering and reports.  Run:  python -m unittest -v"""
import unittest
from datetime import date
from decimal import Decimal

from customer_manager import CustomerManager
from inquiry_manager import InquiryManager, RequestManager
from models import ValidationError
from program_manager import ProgramManager
from report_manager import ReportManager
from search_manager import SearchManager
from service_manager import ServiceManager
from storage import DataStore

DAY = lambda: date(2026, 11, 10)


class Base(unittest.TestCase):
    def setUp(self):
        self.store = DataStore(None)                     # in memory: nothing is written to disk
        self.customers, self.services = CustomerManager(self.store, DAY), ServiceManager(self.store, DAY)
        self.programs, self.inquiries = ProgramManager(self.store, DAY), InquiryManager(self.store, DAY)
        self.requests = RequestManager(self.store, DAY)
        self.search, self.reports = SearchManager(self.store, DAY), ReportManager(self.store, DAY)
        self.c1 = self.customers.add("Aarav Sharma", "Individual", "aarav@example.com", "+91 98765 10001", "Indore")
        self.c2 = self.customers.add("Bright Academy", "Business", "info@bright.example", "+91 98765 10002", "Bhopal")
        self.s1 = self.services.add("Website Development", "Development", "Business website", "15000", "15")
        self.s2 = self.services.add("UI UX Design", "Design", "App design", "8000", "7")
        self.p1 = self.programs.add("Python Training", "Training", "Python basics", "30", "2500", "1", "2026-11-15")
        self.programs.enrol(self.p1.id, self.c1.id)       # fills the only seat -> "Full"


class SearchTests(Base):
    def test_keyword_is_case_insensitive_and_all_words_must_match(self):
        self.assertEqual([r.id for r in self.search.services("website DEVELOPMENT")], [self.s1.id])
        self.assertEqual(self.search.services("website design"), [])

    def test_filters(self):
        self.assertEqual([r.id for r in self.search.customers(kind="business")], [self.c2.id])
        self.assertEqual([r.id for r in self.search.customers(city="INDORE")], [self.c1.id])
        self.assertEqual([r.id for r in self.search.services(min_price="10000")], [self.s1.id])
        self.assertEqual([r.id for r in self.search.services(max_price="8000")], [self.s2.id])

    def test_full_program_status_and_availability(self):
        self.assertEqual(len(self.search.programs(status="Full")), 1)
        self.assertEqual(self.search.programs(available_only=True), [])

    def test_keyword_finds_records_through_customer_name(self):
        self.inquiries.create(self.c1.id, "General", "", "What are your hours?")
        self.assertEqual(len(self.search.inquiries("aarav")), 1)

    def test_overdue_requests(self):
        late = RequestManager(self.store, lambda: date(2026, 11, 1)).create(self.c1.id, self.s1.id, "Site", None, "2026-11-09")
        self.assertEqual([r.id for r in self.search.requests(overdue_only=True)], [late.id])
        self.requests.set_status(late.id, "Cancelled")
        self.assertEqual(self.search.requests(overdue_only=True), [])

    def test_bad_filters_are_rejected(self):
        for call in (lambda: self.search.services(status="Opn"), lambda: self.search.services(min_price="abc"),
                     lambda: self.search.services(min_price="500", max_price="100"), lambda: self.search.inquiries(customer_id="X1")):
            with self.assertRaises(ValidationError):
                call()


class ReportTests(Base):
    def test_money_totals(self):
        done = self.requests.create(self.c1.id, self.s2.id, "Design", "7999.50")
        for status in ("Approved", "In Progress", "Completed"):
            self.requests.set_status(done.id, status)
        self.requests.create(self.c2.id, self.s1.id, "Site")
        text = self.reports.build()
        self.assertIn("INR 7,999.50", text)                      # completed value
        self.assertIn("INR 15,000.00", text)                     # pipeline value
        self.assertIn("Overdue requests          : 0", text)

    def test_customer_value_is_services_plus_fees(self):
        done = self.requests.create(self.c1.id, self.s2.id, "Design")
        for status in ("Approved", "In Progress", "Completed"):
            self.requests.set_status(done.id, status)
        self.assertEqual(self.customers.history(self.c1.id)["total_value"], Decimal("10500.00"))   # 8000 + 2500 fee
        self.assertIn("INR 10,500.00", "".join(self.reports.top_customers()))

    def test_empty_store_does_not_crash(self):
        text = ReportManager(DataStore(None), DAY).build()
        self.assertIn("End of report", text)

    def test_export_writes_file(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as folder:
            path = self.reports.export(folder)
            self.assertTrue(os.path.basename(path) == "business_report_2026-11-10.txt")
            self.assertIn("BUSINESS OVERVIEW", open(path, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()