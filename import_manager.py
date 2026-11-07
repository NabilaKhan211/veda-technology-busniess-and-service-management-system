"""CSV IMPORT: add many customers, services or programs at once from a CSV file.

Required columns (any order, header names are not case-sensitive, extra columns such as id are ignored):
    customers : name, kind, email, phone, city
    services  : name, category, description, price, delivery_days
    programs  : name, type, description, duration_days, fee, seats, start_date
Every row goes through exactly the same validation and business rules as typing the record in the menu.
A bad row (invalid value, duplicate e-mail / name, ...) is skipped with a reason and the row number;
good rows are still imported. Importing a file twice is therefore safe: the second time every row is a duplicate.
CSV files written by export_manager.py can be imported again (the protective ' in front of =, @, +, - is removed).
"""
import csv
from dataclasses import dataclass, field

from models import BusinessError, ValidationError

MAX_ROWS = 1000
KINDS = {
    "customers": ("name", "kind", "email", "phone", "city"),
    "services": ("name", "category", "description", "price", "delivery_days"),
    "programs": ("name", "type", "description", "duration_days", "fee", "seats", "start_date"),
}


@dataclass
class ImportResult:
    kind: str
    added: list = field(default_factory=list)       # IDs of the new records
    skipped: list = field(default_factory=list)     # (row number, reason); row 1 is the header


class ImportManager:
    def __init__(self, customers, services, programs):
        self.managers = {"customers": customers, "services": services, "programs": programs}

    @staticmethod
    def clean(value):
        value = (value or "").strip()
        if len(value) > 1 and value[0] == "'" and value[1] in "=@+-":
            value = value[1:]                       # undo the protection added by the CSV export
        return value

    def read(self, kind, path):
        """Read and check the file. Returns (header map, rows)."""
        try:
            with open(path, newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValidationError("The file is empty.")
                headers = {name.strip().lower(): name for name in reader.fieldnames if name}
                missing = [c for c in KINDS[kind] if c not in headers]
                if missing:
                    raise ValidationError("The file is missing column(s): " + ", ".join(missing) + ". Required: " + ", ".join(KINDS[kind]))
                rows = []
                for row in reader:
                    rows.append(row)
                    if len(rows) > MAX_ROWS:
                        raise ValidationError(f"The file has more than {MAX_ROWS} rows. Split it into smaller files.")
        except FileNotFoundError:
            raise ValidationError(f"File not found: {path}")
        except (UnicodeDecodeError, csv.Error):
            raise ValidationError("This is not a valid UTF-8 CSV file.")
        except OSError as error:
            raise ValidationError(f"The file cannot be opened: {error.strerror or error}")
        return headers, rows

    def import_csv(self, kind, path):
        kind = (kind or "").strip().lower()
        if kind not in KINDS:
            raise ValidationError("Import is available for: " + ", ".join(KINDS) + ".")
        headers, rows = self.read(kind, path)
        result, manager = ImportResult(kind), self.managers[kind]
        for number, row in enumerate(rows, start=2):
            values = [self.clean(row.get(headers[column])) for column in KINDS[kind]]
            if not any(values):
                result.skipped.append((number, "empty row"))
                continue
            try:
                result.added.append(manager.add(*values).id)
            except (BusinessError, ValueError) as error:
                result.skipped.append((number, str(error)))
        return result