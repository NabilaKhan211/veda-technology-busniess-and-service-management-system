"""SEARCH & FILTERING: find customers, services, programs, inquiries and service requests.

Keyword search   : every word you type must appear somewhere in the record (or in the name of a
                   customer / service / program it refers to). Upper/lower case does not matter.
Filters          : exact filters such as status, category, priority. An empty value means "any".
All filter values are validated with the same rules as the rest of the system, so a typo such as
status "Opn" gives a clear message instead of silently returning nothing.
"""
from models import (CUSTOMER_KINDS, INQUIRY_STATUSES, INQUIRY_TOPICS, PRIORITIES, PROGRAM_STATUSES, PROGRAM_TYPES,
                    REQUEST_STATUSES, SERVICE_CATEGORIES, SERVICE_STATUSES, ValidationError, choice, money, record_id, today)


def _option(value, options, label):
    value = (value or "").strip()
    return choice(value, options, label) if value else ""


def _identifier(value, prefix, label):
    value = (value or "").strip()
    return record_id(value, prefix, label) if value else ""


class SearchManager:
    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    # ---------- keyword helper ----------
    def _related_names(self, record):
        """Names of the customers / services / programs a record refers to (so 'Aarav' finds his inquiries)."""
        names = []
        for field, collection in (("customer_id", "customers"), ("service_id", "services")):
            if hasattr(record, field) and self.store.exists(collection, getattr(record, field)):
                names.append(self.store.get(collection, getattr(record, field)).name)
        reference = getattr(record, "reference", "")
        if reference:
            collection = "services" if reference.startswith("SV-") else "programs"
            if self.store.exists(collection, reference):
                names.append(self.store.get(collection, reference).name)
        for customer_id in getattr(record, "enrolled", []):
            if self.store.exists("customers", customer_id):
                names.append(self.store.get("customers", customer_id).name)
        return names

    def _haystack(self, record):
        parts = []
        for value in record.to_dict().values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        parts.extend(str(v) for v in item.values())
                    else:
                        parts.append(str(item))
            else:
                parts.append(str(value))
        return " ".join(parts + self._related_names(record)).lower()

    def _find(self, collection, keyword, tests):
        words = (keyword or "").lower().split()
        found = []
        for record in self.store.all(collection):
            if all(test(record) for test in tests) and (not words or all(w in self._haystack(record) for w in words)):
                found.append(record)
        return found

    # ---------- searches ----------
    def customers(self, keyword="", kind="", city=""):
        kind, city = _option(kind, CUSTOMER_KINDS, "Customer type"), (city or "").strip().lower()
        return self._find("customers", keyword, [lambda r: not kind or r.kind == kind, lambda r: not city or r.city.lower() == city])

    def services(self, keyword="", category="", status="", min_price="", max_price=""):
        category, status = _option(category, SERVICE_CATEGORIES, "Category"), _option(status, SERVICE_STATUSES, "Status")
        low = money(min_price, "Minimum price") if (min_price or "").strip() else None
        high = money(max_price, "Maximum price") if (max_price or "").strip() else None
        if low is not None and high is not None and low > high:
            raise ValidationError("The minimum price cannot be more than the maximum price.")
        return self._find("services", keyword, [
            lambda r: not category or r.category == category, lambda r: not status or r.status == status,
            lambda r: low is None or r.price >= low, lambda r: high is None or r.price <= high])

    def programs(self, keyword="", type="", status="", available_only=False):
        type = _option(type, PROGRAM_TYPES, "Program type")
        status = _option(status, PROGRAM_STATUSES + ["Full"], "Status")        # "Full" = open but no seat left
        return self._find("programs", keyword, [
            lambda r: not type or r.type == type, lambda r: not status or r.effective_status() == status,
            lambda r: not available_only or (r.status == "Open" and r.seats_left() > 0)])

    def inquiries(self, keyword="", status="", priority="", topic="", customer_id=""):
        status, priority = _option(status, INQUIRY_STATUSES, "Status"), _option(priority, PRIORITIES, "Priority")
        topic, customer_id = _option(topic, INQUIRY_TOPICS, "Topic"), _identifier(customer_id, "CU", "Customer ID")
        return self._find("inquiries", keyword, [
            lambda r: not status or r.status == status, lambda r: not priority or r.priority == priority,
            lambda r: not topic or r.topic == topic, lambda r: not customer_id or r.customer_id == customer_id])

    def requests(self, keyword="", status="", customer_id="", service_id="", overdue_only=False):
        status = _option(status, REQUEST_STATUSES, "Status")
        customer_id, service_id = _identifier(customer_id, "CU", "Customer ID"), _identifier(service_id, "SV", "Service ID")
        today_text = self.clock().isoformat()
        return self._find("requests", keyword, [
            lambda r: not status or r.status == status, lambda r: not customer_id or r.customer_id == customer_id,
            lambda r: not service_id or r.service_id == service_id,
            lambda r: not overdue_only or (r.status not in ("Completed", "Cancelled") and r.due_date < today_text)])