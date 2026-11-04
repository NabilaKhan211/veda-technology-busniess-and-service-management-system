"""CUSTOMER MANAGEMENT: the people and businesses we work with.

Rules: email addresses are unique; a customer who has inquiries, service requests, or
program enrolments cannot be deleted (their history must not disappear).
"""
from decimal import Decimal

from models import Customer, RuleError, ValidationError, today


class CustomerManager:
    EDITABLE = ("name", "kind", "email", "phone", "city")

    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def all(self):
        return self.store.all("customers")

    def get(self, customer_id):
        return self.store.get("customers", customer_id)

    def add(self, name, kind, email, phone, city):
        record = Customer.build({"id": "CU-000", "name": name, "kind": kind, "email": email, "phone": phone, "city": city,
                                 "created": self.clock().isoformat()})
        self.store.ensure_unique(Customer, record.__dict__)
        record.id = self.store.new_id(Customer)
        self.store.add(record)
        self.store.save()
        return record

    def update(self, customer_id, **changes):
        record = self.get(customer_id)
        unknown = [key for key in changes if key not in self.EDITABLE]
        if unknown:
            raise ValidationError("These fields cannot be changed here: " + ", ".join(unknown))
        if "email" in changes:
            self.store.ensure_unique(Customer, {"email": Customer.FIELDS["email"](changes["email"])}, ignore_id=record.id)
        record.apply(changes)
        self.store.save()
        return record

    def history(self, customer_id):
        """Everything linked to a customer."""
        record = self.get(customer_id)
        inquiries = [i for i in self.store.all("inquiries") if i.customer_id == record.id]
        requests = [r for r in self.store.all("requests") if r.customer_id == record.id]
        programs = [p for p in self.store.all("programs") if record.id in p.enrolled]
        service_value = sum((r.quote for r in requests if r.status == "Completed"), Decimal("0.00"))
        program_fees = sum((p.fee for p in programs), Decimal("0.00"))
        return {"customer": record, "inquiries": inquiries, "requests": requests, "programs": programs,
                "service_value": service_value, "program_fees": program_fees, "total_value": service_value + program_fees}

    def delete(self, customer_id):
        h = self.history(customer_id)
        if h["inquiries"] or h["requests"] or h["programs"]:
            raise RuleError(f"{h['customer'].name} has {len(h['inquiries'])} inquiry(ies), {len(h['requests'])} request(s) and "
                            f"{len(h['programs'])} program enrolment(s) and cannot be deleted.")
        self.store.remove(h["customer"])
        self.store.save()
        return h["customer"]