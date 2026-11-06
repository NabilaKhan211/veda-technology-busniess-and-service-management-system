"""DATA EXPORT & BACKUP: CSV files for Excel / Google Sheets, and dated copies of the JSON data file.

CSV export : one file per record type (customers.csv, services.csv, ...), saved in exports/<date>/.
             Lists are flattened (enrolled customers become "CU-001;CU-002", notes become one text cell).
             Cells that could be run as spreadsheet formulas (start with = or @) are made safe with a leading '.
Backup     : copies business_data.json to backups/business_data_<date>_<time>.json.
"""
import csv
import os
import shutil
from datetime import datetime

from models import RuleError, today
from storage import ORDER


def flatten(value):
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            return " | ".join(f"{item.get('date', '')}: {item.get('text', '')}" for item in value)
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def safe_cell(field, text):
    """Stop spreadsheet programs from running user text as a formula."""
    if text.startswith(("=", "@")) or (text.startswith(("+", "-")) and field != "phone"):
        return "'" + text
    return text


class ExportManager:
    def __init__(self, store, clock=today):
        self.store, self.clock = store, clock

    def _base_folder(self):
        return os.path.dirname(os.path.abspath(self.store.path)) if self.store.path else os.getcwd()

    def export_csv(self, folder=None):
        """Write one CSV per collection. Returns (folder, {collection: number of rows})."""
        folder = folder or os.path.join(self._base_folder(), "exports", self.clock().isoformat())
        os.makedirs(folder, exist_ok=True)
        counts = {}
        for name in ORDER:
            records = [record.to_dict() for record in self.store.all(name)]
            columns = list(records[0].keys()) if records else list(self._columns(name))
            with open(os.path.join(folder, f"{name}.csv"), "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                for row in records:
                    writer.writerow([safe_cell(c, flatten(row[c])) for c in columns])
            counts[name] = len(records)
        return folder, counts

    def _columns(self, name):
        """Column names for an empty collection (taken from a blank record of that type)."""
        from models import CLASSES
        return [field for field in CLASSES[name].FIELDS]

    def backup(self, folder=None):
        """Save the current data, then copy the data file. Returns the backup path."""
        if self.store.path is None:
            raise RuleError("This store is kept in memory only, so there is no data file to back up.")
        self.store.save()
        folder = folder or os.path.join(self._base_folder(), "backups")
        os.makedirs(folder, exist_ok=True)
        stamp = f"{self.clock().strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}"
        path = os.path.join(folder, f"business_data_{stamp}.json")
        shutil.copy2(self.store.path, path)
        return path