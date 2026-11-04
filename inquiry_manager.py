"""CUSTOMER / SERVICE INQUIRY MANAGEMENT: inquiries and service requests.

Inquiry   : a customer's question about a service, a program, or anything else.
            Flow: New -> In Progress -> Resolved -> Closed (Resolved can be reopened).
Request   : a customer ordering a service.
            Flow: Submitted -> Approved -> In Progress -> Completed (or Cancelled before it is completed).

Rules: both need an existing customer; a request needs an ACTIVE service; dates are never
allowed to go backwards; statuses only move along their flow (see models.py).
"""
from datetime import timedelta

from models import (INQUIRY_FLOW, INQUIRY_STATUSES, INQUIRY_TOPICS, PRIORITIES, REQUEST_FLOW, REQUEST_STATUSES, Inquiry, RuleError,
                    ServiceRequest, ValidationError, check_transition, choice, message, money, today)


class InquiryManager:
    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def all(self):
        return self.store.all("inquiries")

    def get(self, inquiry_id):
        return self.store.get("inquiries", inquiry_id)

    def _today(self, record):
        return max(self.clock().isoformat(), record.created)       # never earlier than the creation date

    def create(self, customer_id, topic, reference, text, priority="Medium"):
        customer = self.store.get("customers", customer_id)
        topic = choice(topic, INQUIRY_TOPICS, "Topic")
        reference = "" if topic == "General" else reference
        if topic == "Service":
            reference = self.store.get("services", reference).id
        elif topic == "Program":
            reference = self.store.get("programs", reference).id
        now = self.clock().isoformat()
        record = Inquiry.build({"id": "IQ-000", "customer_id": customer.id, "topic": topic, "reference": reference, "message": text,
                                "priority": priority, "status": "New", "created": now, "updated": now, "resolved_on": "", "notes": []})
        record.id = self.store.new_id(Inquiry)
        self.store.add(record)
        self.store.save()
        return record

    def set_status(self, inquiry_id, status):
        record = self.get(inquiry_id)
        status = choice(status, INQUIRY_STATUSES, "Status")
        check_transition(INQUIRY_FLOW, record.status, status, "inquiry")
        record.status, record.updated = status, self._today(record)
        if status in ("Resolved", "Closed") and not record.resolved_on:
            record.resolved_on = record.updated                    # the first date it was resolved or closed
        elif status == "In Progress":
            record.resolved_on = ""                                # reopened
        self.store.save()
        return record

    def set_priority(self, inquiry_id, priority):
        record = self.get(inquiry_id)
        if record.status == "Closed":
            raise RuleError("A closed inquiry cannot be changed.")
        record.apply({"priority": priority})
        record.updated = self._today(record)
        self.store.save()
        return record

    def add_note(self, inquiry_id, text):
        record = self.get(inquiry_id)
        if record.status == "Closed":
            raise RuleError("A closed inquiry cannot be changed.")
        record.updated = self._today(record)
        record.notes.append({"date": record.updated, "text": message(text, "Note", 300)})
        self.store.save()
        return record


class RequestManager:
    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def all(self):
        return self.store.all("requests")

    def get(self, request_id):
        return self.store.get("requests", request_id)

    def _today(self, record):
        return max(self.clock().isoformat(), record.requested_on)

    def create(self, customer_id, service_id, details, quote=None, due_date=None):
        customer = self.store.get("customers", customer_id)
        service = self.store.get("services", service_id)
        if service.status != "Active":
            raise RuleError(f"{service.name} is {service.status.lower()} and cannot be requested right now.")
        now = self.clock()
        record = ServiceRequest.build({
            "id": "RQ-000", "customer_id": customer.id, "service_id": service.id, "details": details,
            "quote": service.price if quote in (None, "") else quote, "status": "Submitted", "requested_on": now.isoformat(),
            "due_date": due_date or (now + timedelta(days=service.delivery_days)).isoformat(), "updated": now.isoformat(), "completed_on": ""})
        record.id = self.store.new_id(ServiceRequest)
        self.store.add(record)
        self.store.save()
        return record

    def set_status(self, request_id, status):
        record = self.get(request_id)
        status = choice(status, REQUEST_STATUSES, "Status")
        check_transition(REQUEST_FLOW, record.status, status, "service request")
        record.status, record.updated = status, self._today(record)
        if status == "Completed":
            record.completed_on = record.updated
        self.store.save()
        return record

    def update_quote(self, request_id, quote):
        record = self.get(request_id)
        if record.status not in ("Submitted", "Approved"):
            raise RuleError(f"The quote can only be changed while a request is Submitted or Approved (this one is {record.status}).")
        record.apply({"quote": quote})
        record.updated = self._today(record)
        self.store.save()
        return record