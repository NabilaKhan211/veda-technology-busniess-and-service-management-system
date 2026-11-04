"""MODELS: the five record types, their allowed values, and all validation.

Record types (each is a class):
    Customer, Service, Program, Inquiry, ServiceRequest

Every field of every record has a validator. The SAME validators check what a user
types AND what is read back from the data file, so bad data cannot get in either way.

Errors: BusinessError is the base class; every message is short, plain, and safe to
show to the user (ValidationError, NotFoundError, RuleError).
"""
import re
from datetime import date, datetime
from decimal import Decimal

CENT = Decimal("0.01")


class BusinessError(Exception):
    """Base class: the message is always safe to show to the user."""


class ValidationError(BusinessError):
    """A value is not acceptable (wrong format, out of range ...)."""


class NotFoundError(BusinessError):
    """A record with that ID does not exist."""


class RuleError(BusinessError):
    """The action is valid in form but breaks a business rule (duplicate, wrong status, record in use ...)."""


def today():
    return date.today()


# ---------- Allowed values and status flows ----------
SERVICE_CATEGORIES = ["Development", "Design", "Cloud", "Data", "Security", "Consulting", "Marketing"]
SERVICE_STATUSES = ["Active", "Paused", "Retired"]
PROGRAM_TYPES = ["Training", "Internship"]
PROGRAM_STATUSES = ["Open", "Closed", "Completed"]
CUSTOMER_KINDS = ["Individual", "Business"]
INQUIRY_TOPICS = ["Service", "Program", "General"]
INQUIRY_STATUSES = ["New", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High"]
REQUEST_STATUSES = ["Submitted", "Approved", "In Progress", "Completed", "Cancelled"]

# status -> statuses it may move to. An empty list means the status is final.
SERVICE_FLOW = {"Active": ["Paused", "Retired"], "Paused": ["Active", "Retired"], "Retired": []}
PROGRAM_FLOW = {"Open": ["Closed", "Completed"], "Closed": ["Open", "Completed"], "Completed": []}
INQUIRY_FLOW = {"New": ["In Progress", "Closed"], "In Progress": ["Resolved", "Closed"], "Resolved": ["In Progress", "Closed"], "Closed": []}
REQUEST_FLOW = {"Submitted": ["Approved", "Cancelled"], "Approved": ["In Progress", "Cancelled"],
                "In Progress": ["Completed", "Cancelled"], "Completed": [], "Cancelled": []}


def check_transition(flow, current, new, label):
    """Raise RuleError unless `current` may move to `new`."""
    if new == current:
        raise RuleError(f"The {label} is already '{current}'.")
    if new not in flow[current]:
        allowed = ", ".join(flow[current]) or "nothing (this status is final)"
        raise RuleError(f"A {label} cannot move from '{current}' to '{new}'. It can move to: {allowed}.")


# ---------- Validators: each returns the cleaned value or raises ValidationError ----------
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
MONEY = re.compile(r"^[0-9]{1,8}(\.[0-9]{1,2})?$")
WHOLE = re.compile(r"^[0-9]{1,6}$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
EMAIL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def clean_text(value, label, min_len, max_len):
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    text = " ".join(value.split())
    if CONTROL.search(text):
        raise ValidationError(f"{label} contains invalid characters.")
    if len(text) < min_len or len(text) > max_len:
        raise ValidationError(f"{label} must be {min_len} to {max_len} characters long." if min_len else f"{label} can be at most {max_len} characters long.")
    return text


def name(value, label="Name", min_len=2, max_len=60):
    """Letters, digits, spaces and . , ' & ( ) / + - only; must start with a letter or digit
    (so a spreadsheet can never read a name as a formula such as =CMD())."""
    text = clean_text(value, label, min_len, max_len)
    if not text[0].isalnum() or not all(c.isalnum() or c in " .,'&()/+-" for c in text):
        raise ValidationError(f"{label} may use letters, digits, spaces and . , ' & ( ) / + - only, and must start with a letter or digit.")
    return text


def message(value, label="Text", max_len=500):
    return clean_text(value, label, 1, max_len)


def optional_message(value, label="Text", max_len=200):
    return clean_text(value, label, 0, max_len)


def money(value, label="Amount", minimum=Decimal("0"), maximum=Decimal("10000000")):
    text = value.strip() if isinstance(value, str) else (str(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else "")
    if not MONEY.match(text):
        raise ValidationError(f"{label} must be a number such as 4999 or 1999.50 (digits only, at most 2 decimals, no minus sign).")
    amount = Decimal(text).quantize(CENT)
    if amount < minimum:
        raise ValidationError(f"{label} must be at least {minimum}.")
    if amount > maximum:
        raise ValidationError(f"{label} cannot be more than {maximum}.")
    return amount


def whole(value, label, low, high):
    text = value.strip() if isinstance(value, str) else (str(value) if isinstance(value, int) and not isinstance(value, bool) else "")
    if not WHOLE.match(text) or not low <= int(text) <= high:
        raise ValidationError(f"{label} must be a whole number from {low} to {high}.")
    return int(text)


def iso_date(value, label="Date"):
    text = value.strip() if isinstance(value, str) else ""
    try:
        if not DATE.match(text):
            raise ValueError
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
        if not 2000 <= parsed.year <= 2100:
            raise ValueError
    except ValueError:
        raise ValidationError(f"{label} must be a real date from 2000 to 2100 in the form YYYY-MM-DD (for example 2026-11-04).") from None
    return parsed.isoformat()


def optional_date(value, label="Date"):
    return "" if isinstance(value, str) and not value.strip() else iso_date(value, label)


def email(value, label="Email"):
    text = clean_text(value, label, 5, 100).lower()
    if not EMAIL.match(text):
        raise ValidationError(f"{label} must look like name@example.com.")
    return text


def phone(value, label="Phone"):
    text = clean_text(value, label, 7, 20)
    digits = sum(c.isdigit() for c in text)
    if not (text[0] == "+" or text[0].isdigit()) or not all(c.isdigit() or c in "+ -()" for c in text) or "+" in text[1:] or not 7 <= digits <= 15:
        raise ValidationError(f"{label} must have 7 to 15 digits and may use spaces, hyphens, parentheses, and a leading + (for example +91 00000 00101).")
    return text


def choice(value, options, label):
    text = value.strip().lower() if isinstance(value, str) else ""
    for option in options:
        if option.lower() == text:
            return option
    raise ValidationError(f"{label} must be one of: {', '.join(options)}.")


def record_id(value, prefix, label="ID"):
    text = value.strip().upper() if isinstance(value, str) else ""
    if not re.match(rf"^{prefix}-[0-9]{{3,6}}$", text):
        raise ValidationError(f"{label} must look like {prefix}-001.")
    return text


def optional_reference(value):
    text = value.strip().upper() if isinstance(value, str) else None
    if text is None or (text and not re.match(r"^(SV|PR)-[0-9]{3,6}$", text)):
        raise ValidationError("Reference must be empty or a service or program ID such as SV-001 or PR-001.")
    return text


def id_list(value, prefix, label):
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list.")
    cleaned = [record_id(item, prefix, label) for item in value]
    if len(set(cleaned)) != len(cleaned):
        raise ValidationError(f"{label} contains the same ID twice.")
    return cleaned


def notes(value):
    if not isinstance(value, list):
        raise ValidationError("Notes must be a list.")
    cleaned = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"date", "text"}:
            raise ValidationError("Each note must have a date and a text.")
        cleaned.append({"date": iso_date(item["date"], "Note date"), "text": message(item["text"], "Note", 300)})
    return cleaned


# ---------- Record base class ----------
class Record:
    """A stored record. Subclasses list their FIELDS: {field name: validator}."""
    COLLECTION = PREFIX = LABEL = ""
    FIELDS = {}
    UNIQUE = ()                 # fields whose values must be unique (compared ignoring upper/lower case)

    def __init__(self, **data):
        self.__dict__.update(data)

    @classmethod
    def build(cls, raw):
        """Validate a dictionary and create the record, or raise ValidationError."""
        if not isinstance(raw, dict):
            raise ValidationError(f"A {cls.LABEL.lower()} record must be an object.")
        missing = [k for k in cls.FIELDS if k not in raw]
        extra = [k for k in raw if k not in cls.FIELDS]
        if missing or extra:
            raise ValidationError(("missing field(s): " + ", ".join(missing) + ". " if missing else "") + ("unknown field(s): " + ", ".join(extra) + "." if extra else ""))
        record = cls(**{key: check(raw[key]) for key, check in cls.FIELDS.items()})
        record.check_rules()
        return record

    def check_rules(self):
        """Rules that involve several fields at once. Subclasses override."""

    def to_dict(self):
        out = {}
        for key in self.FIELDS:
            value = getattr(self, key)
            out[key] = f"{value:.2f}" if isinstance(value, Decimal) else ([dict(x) if isinstance(x, dict) else x for x in value] if isinstance(value, list) else value)
        return out

    def apply(self, changes):
        """Validate every change first, then apply them all (all or nothing)."""
        cleaned = {}
        for key, value in changes.items():
            if key not in self.FIELDS or key == "id":
                raise ValidationError(f"'{key}' cannot be changed.")
            cleaned[key] = self.FIELDS[key](value)
        backup = dict(self.__dict__)
        self.__dict__.update(cleaned)
        try:
            self.check_rules()
        except ValidationError:
            self.__dict__.clear(); self.__dict__.update(backup)
            raise

    def __eq__(self, other):
        return type(self) is type(other) and self.to_dict() == other.to_dict()

    def __repr__(self):
        return f"<{self.LABEL} {self.id}>"

    __hash__ = None


class Customer(Record):
    COLLECTION, PREFIX, LABEL, UNIQUE = "customers", "CU", "Customer", ("email",)
    FIELDS = {"id": lambda v: record_id(v, "CU", "Customer ID"), "name": lambda v: name(v, "Customer name"),
              "kind": lambda v: choice(v, CUSTOMER_KINDS, "Customer type"), "email": email, "phone": phone,
              "city": lambda v: name(v, "City", 2, 40), "created": lambda v: iso_date(v, "Created date")}


class Service(Record):
    COLLECTION, PREFIX, LABEL, UNIQUE = "services", "SV", "Service", ("name",)
    FIELDS = {"id": lambda v: record_id(v, "SV", "Service ID"), "name": lambda v: name(v, "Service name"),
              "category": lambda v: choice(v, SERVICE_CATEGORIES, "Category"), "description": lambda v: optional_message(v, "Description"),
              "price": lambda v: money(v, "Price", Decimal("1")), "delivery_days": lambda v: whole(v, "Delivery time in days", 1, 365),
              "status": lambda v: choice(v, SERVICE_STATUSES, "Status"), "created": lambda v: iso_date(v, "Created date")}


class Program(Record):
    COLLECTION, PREFIX, LABEL, UNIQUE = "programs", "PR", "Program", ("name",)
    FIELDS = {"id": lambda v: record_id(v, "PR", "Program ID"), "name": lambda v: name(v, "Program name"),
              "type": lambda v: choice(v, PROGRAM_TYPES, "Program type"), "description": lambda v: optional_message(v, "Description"),
              "duration_days": lambda v: whole(v, "Duration in days", 1, 365), "fee": lambda v: money(v, "Fee"),
              "seats": lambda v: whole(v, "Number of seats", 1, 500), "start_date": lambda v: iso_date(v, "Start date"),
              "status": lambda v: choice(v, PROGRAM_STATUSES, "Status"), "enrolled": lambda v: id_list(v, "CU", "Enrolled customers")}

    def check_rules(self):
        if len(self.enrolled) > self.seats:
            raise ValidationError(f"{len(self.enrolled)} people are enrolled but there are only {self.seats} seats.")

    def effective_status(self):
        """'Full' when an open program has no seats left."""
        return "Full" if self.status == "Open" and len(self.enrolled) >= self.seats else self.status

    def seats_left(self):
        return self.seats - len(self.enrolled)


class Inquiry(Record):
    COLLECTION, PREFIX, LABEL = "inquiries", "IQ", "Inquiry"
    FIELDS = {"id": lambda v: record_id(v, "IQ", "Inquiry ID"), "customer_id": lambda v: record_id(v, "CU", "Customer ID"),
              "topic": lambda v: choice(v, INQUIRY_TOPICS, "Topic"), "reference": optional_reference,
              "message": lambda v: message(v, "Message"), "priority": lambda v: choice(v, PRIORITIES, "Priority"),
              "status": lambda v: choice(v, INQUIRY_STATUSES, "Status"), "created": lambda v: iso_date(v, "Created date"),
              "updated": lambda v: iso_date(v, "Updated date"), "resolved_on": lambda v: optional_date(v, "Resolved date"), "notes": notes}

    def check_rules(self):
        if self.updated < self.created:
            raise ValidationError("The updated date cannot be before the created date.")
        if (self.status in ("Resolved", "Closed")) != bool(self.resolved_on):
            raise ValidationError("A resolved or closed inquiry needs a resolved date, and an open one must not have one.")
        if self.topic == "General" and self.reference:
            raise ValidationError("A general inquiry cannot refer to a service or program.")
        if self.topic == "Service" and not self.reference.startswith("SV-") or self.topic == "Program" and not self.reference.startswith("PR-"):
            raise ValidationError(f"A {self.topic.lower()} inquiry must refer to a {self.topic.lower()} ID.")


class ServiceRequest(Record):
    COLLECTION, PREFIX, LABEL = "requests", "RQ", "Service request"
    FIELDS = {"id": lambda v: record_id(v, "RQ", "Request ID"), "customer_id": lambda v: record_id(v, "CU", "Customer ID"),
              "service_id": lambda v: record_id(v, "SV", "Service ID"), "details": lambda v: message(v, "Details", 300),
              "quote": lambda v: money(v, "Quote"), "status": lambda v: choice(v, REQUEST_STATUSES, "Status"),
              "requested_on": lambda v: iso_date(v, "Request date"), "due_date": lambda v: iso_date(v, "Due date"),
              "updated": lambda v: iso_date(v, "Updated date"), "completed_on": lambda v: optional_date(v, "Completed date")}

    def check_rules(self):
        if self.due_date < self.requested_on:
            raise ValidationError("The due date cannot be before the request date.")
        if self.updated < self.requested_on:
            raise ValidationError("The updated date cannot be before the request date.")
        if (self.status == "Completed") != bool(self.completed_on):
            raise ValidationError("Only a completed request has a completed date, and every completed request needs one.")


CLASSES = {cls.COLLECTION: cls for cls in (Customer, Service, Program, Inquiry, ServiceRequest)}