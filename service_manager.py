"""SERVICE MANAGEMENT MODULE: the digital services the company sells.

Rules: service names are unique; a Retired service is frozen; a service that has
requests or inquiries cannot be deleted (retire it instead); status changes follow
SERVICE_FLOW (Active <-> Paused, either -> Retired).
"""
from models import SERVICE_FLOW, RuleError, Service, ValidationError, check_transition, choice, SERVICE_STATUSES, today


class ServiceManager:
    EDITABLE = ("name", "category", "description", "price", "delivery_days")

    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def all(self):
        return self.store.all("services")

    def get(self, service_id):
        return self.store.get("services", service_id)

    def add(self, name, category, description, price, delivery_days):
        record = Service.build({"id": "SV-000", "name": name, "category": category, "description": description, "price": price,
                                "delivery_days": delivery_days, "status": "Active", "created": self.clock().isoformat()})
        self.store.ensure_unique(Service, record.__dict__)
        record.id = self.store.new_id(Service)          # an ID is only used up when everything else has passed
        self.store.add(record)
        self.store.save()
        return record

    def update(self, service_id, **changes):
        record = self.get(service_id)
        if record.status == "Retired":
            raise RuleError(f"{record.name} is retired and cannot be edited.")
        unknown = [key for key in changes if key not in self.EDITABLE]
        if unknown:
            raise ValidationError("These fields cannot be changed here: " + ", ".join(unknown))
        if "name" in changes:
            self.store.ensure_unique(Service, {"name": Service.FIELDS["name"](changes["name"])}, ignore_id=record.id)
        record.apply(changes)
        self.store.save()
        return record

    def set_status(self, service_id, status):
        record = self.get(service_id)
        status = choice(status, SERVICE_STATUSES, "Status")
        check_transition(SERVICE_FLOW, record.status, status, "service")
        record.status = status
        self.store.save()
        return record

    def usage(self, service_id):
        """(number of requests, number of inquiries) that mention this service."""
        return (sum(1 for r in self.store.all("requests") if r.service_id == service_id),
                sum(1 for i in self.store.all("inquiries") if i.reference == service_id))

    def delete(self, service_id):
        record = self.get(service_id)
        requests, inquiries = self.usage(record.id)
        if requests or inquiries:
            raise RuleError(f"{record.name} is used by {requests} request(s) and {inquiries} inquiry(ies) and cannot be deleted. Retire it instead.")
        self.store.remove(record)
        self.store.save()
        return record