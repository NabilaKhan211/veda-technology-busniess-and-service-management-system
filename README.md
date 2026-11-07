# Business & Service Management System

**Veda Technology – Python Programming Internship Project (final version)**

## Project Overview

The Business & Service Management System is a console-based application written in Python. It represents the operations of a technology and digital-services company and manages customers, services, training and internship programs, customer inquiries and service requests in one place.

All records are saved in a JSON file, so the data stays available after the program is closed. The project uses only the Python standard library and **only synthetic data** (no private Veda Technology production data).

## Features

| Area | What it does |
|---|---|
| **Customers** | Add, view, edit, delete; unique e-mail; history and value per customer |
| **Services** | Add, view, edit, delete; categories, price, delivery days; Active / Paused / Retired |
| **Programs** | Training and internship programs with seats, fee, start date; enrol and withdraw customers; Open / Closed / Completed (shown as **Full** when no seat is left) |
| **Inquiries** | Customer questions about a service, a program or anything else; priority, notes and status flow New → In Progress → Resolved → Closed |
| **Service requests** | Customers order a service; quote, due date and status flow Submitted → Approved → In Progress → Completed (or Cancelled) |
| **Search & filtering** | Keyword search plus filters for every record type |
| **Business reports** | Overview, services, programs, inquiries, requests and top customers; print or save as a text file |
| **Export & backup** | All data to CSV files (Excel / Google Sheets) and dated backups of the JSON file |
| **CSV import** | Add many customers, services or programs at once; bad rows are skipped with a reason |
| **Command line** | `--report`, `--export`, `--backup` and `--data FILE` options |
| **Validation & business rules** | Every input is checked; invalid operations are refused with a clear message |
| **Safe storage** | Atomic saves, damaged files kept as `.corrupt`, broken records skipped, IDs never reused |
| **Automatic tests** | 44 unit tests |

## Technologies Used

- Python 3 (standard library only)
- JSON and CSV
- Object-Oriented Programming (OOP)
- File handling
- Git and GitHub
- Visual Studio Code

## Project Structure

```text
Business-Service-Management-System/
├── main.py                  # menu and command-line options
├── models.py                # data classes, status flows, validators
├── storage.py               # JSON storage
├── customer_manager.py      # customers
├── service_manager.py       # services
├── program_manager.py       # programs and enrolments
├── inquiry_manager.py       # inquiries and service requests
├── search_manager.py        # search and filtering
├── report_manager.py        # business reports
├── export_manager.py        # CSV export and JSON backup
├── import_manager.py        # CSV import
├── test_core_rules.py       # tests: business rules, storage, export, backup
├── test_search_reports.py   # tests: search, filters, reports
├── test_import_cli.py       # tests: CSV import, command-line options
├── business_data.json       # data file (synthetic sample data)
├── sample_import/           # example CSV files for the import
├── exports/2026-11-07/      # sample CSV export
├── business_report_2026-11-07.txt   # sample report
├── project_report.pdf / .txt        # project report
├── linkedin_post.txt
├── .gitignore
└── README.md
```

## Installation and Setup

1. Install Python 3.8 or newer (python.org, tick **Add Python to PATH**).
2. Download or clone the project and open the folder in Visual Studio Code.
3. Open the terminal (`Ctrl + backtick`) in that folder.
4. Run the application:

```bash
python main.py
```

No extra libraries are needed.

## Main Menu

```text
 1. Add Customer                 10. View Service Requests
 2. View Customers               11. Enrol Customer in Program
 3. Add Service                  12. Update Inquiry Status
 4. View Services                13. Update Service Request Status
 5. Add Program                  14. Search & Filter
 6. View Programs                15. Business Reports
 7. Add Inquiry                  16. Manage Records (edit / delete)
 8. View Inquiries               17. Export & Backup (CSV / JSON)
 9. Create Service Request       18. Import Data from CSV
                                  0. Exit
```

## Command-Line Options

```bash
python main.py --report              # print the full business report and exit
python main.py --export              # export all data to CSV files and exit
python main.py --backup              # back up the JSON data file and exit
python main.py --data other.json --report   # use another data file
python main.py --help
```

## Search & Filtering (menu option 14)

Choose what to search, type an optional keyword, then pick optional filters (`0` or Enter means "any").

| Search in | Filters |
|---|---|
| Customers | type (Individual / Business), city |
| Services | category, status, minimum and maximum price |
| Programs | type, status (including **Full**), only programs with free seats |
| Inquiries | status, priority, topic, customer ID |
| Service requests | status, customer ID, service ID, only overdue requests |

The keyword is not case-sensitive and every word must match. It also checks related names, so searching `aarav` finds Aarav's inquiries and requests too. A mistyped filter value (for example status `Opn`) gives a clear error message.

## Business Reports (menu option 15)

| Section | What it shows |
|---|---|
| Overview | Number of customers, services, programs, inquiries and requests |
| Services | Count by status and category, average price, demand and completed value per service |
| Programs | Seat utilisation, enrolled / seats per program, expected fee income |
| Inquiries | Count by status and priority, open inquiries (highest priority first), average days to resolve |
| Service requests | Count by status, completed value (earned), pipeline value, overdue requests |
| Top customers | Customers ranked by completed services plus program fees |

The report can be shown completely or section by section, and saved as `business_report_<date>.txt`. Money is calculated with `Decimal`, so totals are exact. See `business_report_2026-11-07.txt` for a sample.

## Export & Backup (menu option 17)

| Action | Result |
|---|---|
| Export all data to CSV files | `exports/<date>/customers.csv`, `services.csv`, `programs.csv`, `inquiries.csv`, `requests.csv` |
| Backup data file (JSON) | `backups/business_data_<date>_<time>.json` |

Lists are flattened (for example `CU-001;CU-002`), and text starting with `=` or `@` is protected so a spreadsheet cannot run it as a formula. The `backups/` folder is ignored by Git.

## Import from CSV (menu option 18)

Add many records at once. The file needs these columns (any order, header names are not case-sensitive, extra columns are ignored):

| Import | Required columns |
|---|---|
| Customers | `name, kind, email, phone, city` |
| Services | `name, category, description, price, delivery_days` |
| Programs | `name, type, description, duration_days, fee, seats, start_date` |

Every row goes through the same validation and business rules as the menu. A bad row is skipped with its row number and reason, and the good rows are still imported:

```text
Imported 1 customer: CU-013.
Skipped 5 row(s):
  row 3: A customer with that email already exists (CU-001: aarav.sharma@example.com).
  row 4: Email must look like name@example.com.
  row 5: Customer type must be one of: Individual, Business.
  row 6: empty row
  row 7: Phone must be 7 to 20 characters long.
```

Importing the same file twice is safe because the second time every row is a duplicate. Files written by the export can be imported again. Try the examples in `sample_import/` (`new_customers.csv`, `new_services.csv`, `new_programs.csv`, and `customers_with_errors.csv` to see the error report).

## Running Tests

```bash
python -m unittest -v
```

44 tests cover customers, services, programs, inquiries, requests, search, reports, storage safety (damaged file, broken references), CSV export, backup, CSV import and the command-line options. Tests use an in-memory store or temporary folders, so they never change `business_data.json`.

## Application Modules

| Module | Description |
|---|---|
| main.py | Menu, input handling and command-line options |
| models.py | Data models, status flows and validation |
| storage.py | JSON data storage |
| customer_manager.py | Customer operations |
| service_manager.py | Service operations |
| program_manager.py | Program and enrolment operations |
| inquiry_manager.py | Inquiry and request operations |
| search_manager.py | Search and filtering |
| report_manager.py | Business reports |
| export_manager.py | CSV export and JSON backup |
| import_manager.py | CSV import |

## Data Storage

`business_data.json` stores customers, services, programs, inquiries, service requests and the ID counters. Saving writes a temporary file first and then swaps it in, so a crash cannot leave a half-written file. A damaged file is kept as `business_data.json.corrupt`; invalid or dangling records are skipped with a message and the original file is copied to `.bak` first.

## Business Rules

- Customer e-mails, service names and program names must be unique (not case-sensitive).
- A customer cannot be enrolled twice in a program; a full, closed or completed program accepts no new enrolments.
- Seats cannot be reduced below the number of enrolled customers; a completed program cannot be edited.
- Status changes follow fixed flows (for example a Completed request cannot be reopened); a retired service cannot be edited.
- Only Active services can be requested; a due date cannot be earlier than the request date.
- Records that are in use (a service with requests, a customer with history, a program with enrolments) cannot be deleted.
- IDs are never reused after a record is deleted.

## How It Works

1. Run `python main.py` and pick an option from the menu.
2. Enter the requested information; the application validates it.
3. Valid records are saved in the JSON file.
4. Use **Search & Filter** to find records, **Business Reports** to review the business, and **Export / Import** to work with CSV files.

## Project Progress

| Day | Work done |
|---|---|
| Day 2 | Core system: customers, services, programs, inquiries, service requests, validation, business rules, JSON storage |
| Day 3 | Search & filtering, business reports, record management menu, CSV export and JSON backup, complete sample data, 32 tests, fix for the default service-request quote |
| Day 4 | CSV import with row-by-row error report, command-line options, sample import files, final documentation and report, 44 tests |

## Learning Outcomes

- Python programming, classes and objects, inheritance
- Modular programming and separation of concerns
- Functions, exception handling and input validation
- JSON and CSV file handling
- Business logic implementation
- Search, filtering and report generation
- Command-line programs with `argparse`
- Automated testing with `unittest`
- Git and GitHub workflow

## Future Improvements

- User login with roles
- Charts in the reports
- Web interface (Flask or Streamlit) on top of the same manager classes

## Conclusion

The Business & Service Management System shows how a small business can organise its customers, services, programs, inquiries and requests with Python. The modular structure, strict validation, safe storage and automatic tests make the application reliable and easy to extend.

**Developed as part of the Veda Technology Python Programming Internship.**