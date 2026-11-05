"""BASIC BUSINESS REPORTS: a plain-text summary of the whole business, printable and saveable.

Sections: overview, services, programs, inquiries, service requests, top customers.
Money is calculated with Decimal (never float) so totals are exact.
"""
import os
from collections import Counter
from datetime import date
from decimal import Decimal

from customer_manager import CustomerManager
from models import CUSTOMER_KINDS, INQUIRY_STATUSES, PRIORITIES, PROGRAM_STATUSES, REQUEST_STATUSES, SERVICE_STATUSES, today

ZERO = Decimal("0.00")


def inr(amount):
    return f"INR {amount:,.2f}"


def table(headers, rows):
    """Left-aligned text table; returns a list of lines."""
    rows = [[str(c) for c in row] for row in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = lambda cells: "  " + "  ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()
    return [line(headers), "  " + "  ".join("-" * w for w in widths)] + [line(r) for r in rows]


class ReportManager:
    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    @staticmethod
    def counts(records, field, order):
        found = Counter(getattr(r, field) for r in records)
        return [(item, found.get(item, 0)) for item in order]

    @staticmethod
    def summary(pairs):
        return ", ".join(f"{name}: {count}" for name, count in pairs)

    # ---------- sections ----------
    def overview(self):
        s = self.store
        return ["BUSINESS OVERVIEW",
                f"  Customers        : {len(s.all('customers'))}  ({self.summary(self.counts(s.all('customers'), 'kind', CUSTOMER_KINDS))})",
                f"  Services         : {len(s.all('services'))}",
                f"  Programs         : {len(s.all('programs'))}",
                f"  Inquiries        : {len(s.all('inquiries'))}",
                f"  Service requests : {len(s.all('requests'))}"]

    def services(self):
        services, requests = self.store.all("services"), self.store.all("requests")
        lines = ["SERVICES", "  By status  : " + self.summary(self.counts(services, "status", SERVICE_STATUSES))]
        by_category = Counter(sv.category for sv in services)
        lines.append("  By category: " + (self.summary(sorted(by_category.items())) or "none"))
        if services:
            lines.append("  Average price: " + inr(sum((sv.price for sv in services), ZERO) / len(services)))
        rows = []
        for sv in services:
            mine = [r for r in requests if r.service_id == sv.id]
            done = sum((r.quote for r in mine if r.status == "Completed"), ZERO)
            rows.append((sv.id, sv.name, sv.status, len(mine), inr(done)))
        rows.sort(key=lambda r: (-r[3], r[0]))
        return lines + ["", "  Demand per service (most requested first):"] + table(["ID", "Service", "Status", "Requests", "Completed value"], rows)

    def programs(self):
        programs = self.store.all("programs")
        lines = ["PROGRAMS", "  By status: " + self.summary(self.counts(programs, "status", PROGRAM_STATUSES))]
        seats, taken = sum(p.seats for p in programs), sum(len(p.enrolled) for p in programs)
        rows = [(p.id, p.name, p.type, f"{len(p.enrolled)}/{p.seats}", f"{len(p.enrolled) / p.seats * 100:.0f}%",
                 p.effective_status(), inr(p.fee * len(p.enrolled))) for p in programs]
        if seats:
            lines.append(f"  Seat utilisation: {taken}/{seats} seats taken ({taken / seats * 100:.1f}%)")
        lines.append("  Expected fee income: " + inr(sum((p.fee * len(p.enrolled) for p in programs), ZERO)))
        return lines + [""] + table(["ID", "Program", "Type", "Enrolled", "Filled", "Status", "Fee income"], rows)

    def inquiries(self):
        inquiries = self.store.all("inquiries")
        lines = ["CUSTOMER INQUIRIES", "  By status  : " + self.summary(self.counts(inquiries, "status", INQUIRY_STATUSES)),
                 "  By priority: " + self.summary(self.counts(inquiries, "priority", PRIORITIES))]
        open_ones = [i for i in inquiries if i.status in ("New", "In Progress")]
        days = [(date.fromisoformat(i.resolved_on) - date.fromisoformat(i.created)).days for i in inquiries if i.resolved_on]
        lines.append(f"  Still open : {len(open_ones)}")
        lines.append("  Average days to resolve: " + (f"{sum(days) / len(days):.1f}" if days else "n/a"))
        if open_ones:
            rank = {p: n for n, p in enumerate(reversed(PRIORITIES))}
            open_ones.sort(key=lambda i: (rank[i.priority], i.created))
            lines += ["", "  Open inquiries (highest priority first):"] + table(
                ["ID", "Customer", "Priority", "Status", "Since"], [(i.id, i.customer_id, i.priority, i.status, i.created) for i in open_ones])
        return lines

    def requests(self):
        requests = self.store.all("requests")
        lines = ["SERVICE REQUESTS", "  By status: " + self.summary(self.counts(requests, "status", REQUEST_STATUSES))]
        pipeline = sum((r.quote for r in requests if r.status in ("Submitted", "Approved", "In Progress")), ZERO)
        completed = sum((r.quote for r in requests if r.status == "Completed"), ZERO)
        lines += [f"  Completed value (earned)  : {inr(completed)}", f"  Pipeline value (not done) : {inr(pipeline)}"]
        overdue = [r for r in requests if r.status not in ("Completed", "Cancelled") and r.due_date < self.clock().isoformat()]
        lines.append(f"  Overdue requests          : {len(overdue)}")
        if overdue:
            lines += table(["ID", "Customer", "Service", "Due date", "Status"], [(r.id, r.customer_id, r.service_id, r.due_date, r.status) for r in overdue])
        return lines

    def top_customers(self, limit=5):
        manager, rows = CustomerManager(self.store, self.clock), []
        for customer in self.store.all("customers"):
            h = manager.history(customer.id)
            rows.append((customer.id, customer.name, len(h["requests"]), len(h["programs"]), h["total_value"]))
        rows.sort(key=lambda r: (-r[4], r[0]))
        return ["TOP CUSTOMERS BY VALUE (completed services + program fees)"] + table(
            ["ID", "Customer", "Requests", "Programs", "Total value"], [(a, b, c, d, inr(e)) for a, b, c, d, e in rows[:limit]])

    # ---------- whole report ----------
    SECTIONS = {"overview": overview, "services": services, "programs": programs, "inquiries": inquiries,
                "requests": requests, "customers": top_customers}

    def build(self, sections=None):
        header = ["=" * 66, " BUSINESS & SERVICE MANAGEMENT REPORT", f" Generated on {self.clock().isoformat()}", "=" * 66]
        body = []
        for name in sections or self.SECTIONS:
            body += [""] + self.SECTIONS[name](self)
        return "\n".join(header + body + ["", "=" * 66, " End of report", "=" * 66]) + "\n"

    def export(self, folder=None):
        folder = folder or os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, f"business_report_{self.clock().isoformat()}.txt")
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.build())
        return path