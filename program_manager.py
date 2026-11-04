"""PROGRAM MANAGEMENT MODULE: training and internship programs, seats, and enrolments.

Rules: program names are unique; seats can never drop below the number enrolled; only an
Open program with a free seat accepts a new enrolment, and nobody can be enrolled twice;
a Completed program is frozen; a program with enrolled customers cannot be deleted.
Status changes follow PROGRAM_FLOW. A program that is Open with no free seat shows as "Full".
"""
from models import PROGRAM_FLOW, PROGRAM_STATUSES, Program, RuleError, ValidationError, check_transition, choice, today


class ProgramManager:
    EDITABLE = ("name", "type", "description", "duration_days", "fee", "seats", "start_date")

    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def all(self):
        return self.store.all("programs")

    def get(self, program_id):
        return self.store.get("programs", program_id)

    def add(self, name, type, description, duration_days, fee, seats, start_date):
        record = Program.build({"id": "PR-000", "name": name, "type": type, "description": description, "duration_days": duration_days,
                                "fee": fee, "seats": seats, "start_date": start_date, "status": "Open", "enrolled": []})
        self.store.ensure_unique(Program, record.__dict__)
        record.id = self.store.new_id(Program)
        self.store.add(record)
        self.store.save()
        return record

    def update(self, program_id, **changes):
        record = self.get(program_id)
        if record.status == "Completed":
            raise RuleError(f"{record.name} is completed and cannot be edited.")
        unknown = [key for key in changes if key not in self.EDITABLE]
        if unknown:
            raise ValidationError("These fields cannot be changed here: " + ", ".join(unknown))
        if "name" in changes:
            self.store.ensure_unique(Program, {"name": Program.FIELDS["name"](changes["name"])}, ignore_id=record.id)
        record.apply(changes)                       # also refuses fewer seats than people enrolled
        self.store.save()
        return record

    def set_status(self, program_id, status):
        record = self.get(program_id)
        status = choice(status, PROGRAM_STATUSES, "Status")
        check_transition(PROGRAM_FLOW, record.status, status, "program")
        record.status = status
        self.store.save()
        return record

    def enrol(self, program_id, customer_id):
        record = self.get(program_id)
        customer = self.store.get("customers", customer_id)
        if record.status != "Open":
            raise RuleError(f"{record.name} is {record.status.lower()} and cannot take new enrolments.")
        if customer.id in record.enrolled:
            raise RuleError(f"{customer.name} ({customer.id}) is already enrolled in {record.name}.")
        if record.seats_left() <= 0:
            raise RuleError(f"{record.name} is full ({record.seats} of {record.seats} seats taken).")
        record.enrolled.append(customer.id)
        self.store.save()
        return record

    def withdraw(self, program_id, customer_id):
        record = self.get(program_id)
        customer = self.store.get("customers", customer_id)
        if record.status == "Completed":
            raise RuleError(f"{record.name} is completed, so its enrolments can no longer change.")
        if customer.id not in record.enrolled:
            raise RuleError(f"{customer.name} ({customer.id}) is not enrolled in {record.name}.")
        record.enrolled.remove(customer.id)
        self.store.save()
        return record

    def enrolled_customers(self, program_id):
        return [self.store.get("customers", cid) for cid in self.get(program_id).enrolled]

    def delete(self, program_id):
        record = self.get(program_id)
        inquiries = sum(1 for i in self.store.all("inquiries") if i.reference == record.id)
        if record.enrolled or inquiries:
            raise RuleError(f"{record.name} has {len(record.enrolled)} enrolled customer(s) and {inquiries} inquiry(ies) and cannot be deleted. Close it instead.")
        self.store.remove(record)
        self.store.save()
        return record