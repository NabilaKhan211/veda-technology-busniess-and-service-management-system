"""STORAGE: keeps every record in memory and saves them all to ONE JSON file.

Safety:
    * saving writes a temporary file first and then swaps it in (a crash cannot leave a half-written file)
    * a damaged file is kept as <name>.corrupt and the program starts empty
    * invalid, duplicate, or dangling records are skipped with a reason, and the original file is first
      copied to <name>.bak, so nothing is lost by the next save
    * ID counters are saved too, so an ID is never reused after a record is deleted
"""
import json
import os
import shutil

from models import CLASSES, Customer, NotFoundError, Program, RuleError, Service, ValidationError

ORDER = ("customers", "services", "programs", "inquiries", "requests")      # a record can only refer to earlier ones
DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_data.json")


def number(record_id):
    return int(record_id.split("-")[1])


class DataStore:
    def __init__(self, path=None):
        self.path = path                                    # None = keep everything in memory only (used by tests)
        self.data = {name: {} for name in ORDER}
        self.counters = {cls.PREFIX: 0 for cls in CLASSES.values()}

    # ---------- access ----------
    def all(self, collection):
        return sorted(self.data[collection].values(), key=lambda r: number(r.id))

    def get(self, collection, record_id):
        record = self.data[collection].get(str(record_id).strip().upper())
        if record is None:
            raise NotFoundError(f"No {CLASSES[collection].LABEL.lower()} found with ID {str(record_id).strip().upper()}.")
        return record

    def exists(self, collection, record_id):
        return str(record_id).strip().upper() in self.data[collection]

    def new_id(self, cls):
        self.counters[cls.PREFIX] += 1
        return f"{cls.PREFIX}-{self.counters[cls.PREFIX]:03d}"

    def add(self, record):
        self.data[record.COLLECTION][record.id] = record

    def remove(self, record):
        del self.data[record.COLLECTION][record.id]

    # ---------- rules that need to see other records ----------
    def ensure_unique(self, cls, values, ignore_id=None):
        for field in cls.UNIQUE:
            if field in values:
                for other in self.all(cls.COLLECTION):
                    if other.id != ignore_id and getattr(other, field).lower() == values[field].lower():
                        raise RuleError(f"A {cls.LABEL.lower()} with that {field} already exists ({other.id}: {getattr(other, field)}).")

    def check_references(self, record):
        """Every ID a record mentions must exist."""
        if hasattr(record, "customer_id") and not self.exists("customers", record.customer_id):
            raise ValidationError(f"customer {record.customer_id} does not exist")
        if hasattr(record, "service_id") and not self.exists("services", record.service_id):
            raise ValidationError(f"service {record.service_id} does not exist")
        if record.COLLECTION == "inquiries" and record.reference:
            if not self.exists("services" if record.reference.startswith("SV-") else "programs", record.reference):
                raise ValidationError(f"{record.reference} does not exist")
        if record.COLLECTION == "programs":
            for customer_id in record.enrolled:
                if not self.exists("customers", customer_id):
                    raise ValidationError(f"enrolled customer {customer_id} does not exist")

    # ---------- files ----------
    def load(self):
        """Read the data file. Returns a list of messages about anything unusual."""
        if self.path is None or not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8-sig") as file:
                raw = json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return [self._set_aside("The data file was damaged.")]
        if not isinstance(raw, dict) or any(not isinstance(raw.get(name, []), list) for name in ORDER):
            return [self._set_aside("The data file had the wrong structure.")]

        messages = []
        for name in ORDER:
            cls = CLASSES[name]
            for index, item in enumerate(raw.get(name, []), start=1):
                label = item.get("id", f"#{index}") if isinstance(item, dict) else f"#{index}"
                try:
                    record = cls.build(item)
                    if record.id in self.data[name]:
                        raise ValidationError("duplicate ID")
                    self.ensure_unique(cls, record.__dict__)
                    self.check_references(record)
                except (ValidationError, RuleError) as error:
                    messages.append(f"Skipped {cls.LABEL.lower()} {label}: {error}")
                    continue
                self.add(record)
        saved = raw.get("counters", {})
        for cls in CLASSES.values():
            highest = max((number(r.id) for r in self.data[cls.COLLECTION].values()), default=0)
            value = saved.get(cls.PREFIX) if isinstance(saved, dict) else None
            self.counters[cls.PREFIX] = max(highest, value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0)
        if messages:
            shutil.copyfile(self.path, self.path + ".bak")
            messages.append(f"A copy of the original file was saved as {os.path.basename(self.path)}.bak so nothing is lost.")
        return messages

    def _set_aside(self, reason):
        os.replace(self.path, self.path + ".corrupt")
        return f"{reason} It was kept as {os.path.basename(self.path)}.corrupt and a new empty file will be used."

    def save(self):
        """Write everything to the data file (does nothing for an in-memory store)."""
        if self.path is None:
            return
        payload = {"version": 1, "counters": self.counters}
        payload.update({name: [r.to_dict() for r in self.all(name)] for name in ORDER})
        temp = self.path + ".tmp"
        with open(temp, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
        os.replace(temp, self.path)