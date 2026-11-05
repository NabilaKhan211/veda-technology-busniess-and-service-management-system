# Business & Service Management System

**Veda Technology – Python Programming Project**

## Project Overview

The Business & Service Management System is a console-based application developed using Python. It helps businesses manage customers, services, training programs, inquiries, and service requests in one place.

The application uses JSON file storage to save records permanently, so the data remains available even after closing the program.

## Features

- **Customer Management:** Add, view, update, and delete customer records.
- **Service Management:** Manage service details, categories, prices, and delivery time.
- **Program Management:** Manage training and internship programs, seats, and enrolments.
- **Inquiry Management:** Store customer inquiries and track their status.
- **Service Requests:** Create and manage customer service requests.
- **Search & Filtering:** Keyword search plus filters by type, category, status, priority, price range, free seats and overdue requests.
- **Business Reports:** Summary of customers, services, programs, inquiries, requests and money (earned vs. pipeline), printable and exportable to a text file.
- **Record Management:** Edit, change status of and delete records from the menu (with the same business rules).
- **Data Storage:** Save all records in a JSON file.
- **Data Validation:** Validate user inputs and prevent invalid operations.
- **Unique IDs:** Generate unique IDs for different records.

## Technologies Used

- Python 3
- JSON
- Object-Oriented Programming (OOP)
- File Handling
- Visual Studio Code

## Project Structure

```text
Business-Service-Management-System/
│
├── main.py
├── models.py
├── storage.py
├── customer_manager.py
├── service_manager.py
├── program_manager.py
├── inquiry_manager.py
├── search_manager.py
├── report_manager.py
├── test_search_reports.py
├── business_data.json
├── business_report_2026-11-05.txt   (sample generated report)
└── README.md
```

## Installation and Setup

**Step 1: Install Python**

Install Python 3 on your computer.

**Step 2: Open Project**

Open the project folder in Visual Studio Code.

**Step 3: Open Terminal**

Open the integrated terminal in VS Code.

**Step 4: Run the Application**

```bash
python main.py
```

## Application Modules

| Module | Description |
|---|---|
| main.py | Main application and menu |
| models.py | Data models and validation |
| storage.py | JSON data storage |
| customer_manager.py | Customer operations |
| service_manager.py | Service operations |
| program_manager.py | Program and enrolment operations |
| inquiry_manager.py | Inquiry and request operations |
| search_manager.py | Search and filtering for every record type |
| report_manager.py | Business reports and text-file export |
| test_search_reports.py | Automatic tests (`python -m unittest`) |

## Main Menu

```text
1. Add Customer                  9. Create Service Request
2. View Customers               10. View Service Requests
3. Add Service                  11. Enrol Customer in Program
4. View Services                12. Update Inquiry Status
5. Add Program                  13. Update Service Request Status
6. View Programs                14. Search & Filter
7. Add Inquiry                  15. Business Reports
8. View Inquiries               16. Manage Records (edit / delete)
                                 0. Exit
```

## Search & Filtering (menu option 14)

Choose what to search, type an optional keyword, then pick optional filters (press `0` or Enter for "any").

| Search in | Filters |
|---|---|
| Customers | type (Individual / Business), city |
| Services | category, status, minimum and maximum price |
| Programs | type, status (including **Full**), only programs with free seats |
| Inquiries | status, priority, topic, customer ID |
| Service requests | status, customer ID, service ID, only overdue requests |

The keyword is not case-sensitive and every word must match. It also looks at related names, so searching `aarav` finds Aarav's inquiries and requests, not only his customer record. Invalid filter values (for example status `Opn`) show a clear error message.

## Business Reports (menu option 15)

The report can be viewed as a whole or section by section, and saved as `business_report_<date>.txt`.

| Section | What it shows |
|---|---|
| Overview | Number of customers, services, programs, inquiries and requests |
| Services | Count by status and category, average price, demand and completed value per service |
| Programs | Seat utilisation, enrolled/seats per program, expected fee income |
| Inquiries | Count by status and priority, open inquiries (highest priority first), average days to resolve |
| Service requests | Count by status, completed value (earned), pipeline value, overdue requests |
| Top customers | Customers ranked by completed services plus program fees |

Money is calculated with `Decimal`, so totals are exact. See `business_report_2026-11-05.txt` for a sample.

## Running Tests

```bash
python -m unittest -v
```

The tests use an in-memory store, so they never change `business_data.json`.

## Data Storage

The application uses `business_data.json` to store:

- Customer records
- Service records
- Program records
- Inquiry records
- Service request records
- ID counters

All changes are saved through the storage module.

## Business Rules

- Customer and service information must pass validation.
- Service and program names must be unique.
- Customers cannot be enrolled twice in the same program.
- Programs cannot accept enrolments when full or closed.
- Completed programs cannot be edited.
- Retired services cannot be edited.
- Records linked to other records cannot be deleted when deletion would break existing relationships.
- Only Active services can be requested; status changes must follow the allowed flow (for example a Completed request cannot be reopened).
- Search filters are validated, so a mistyped filter value is reported instead of returning an empty list.

## How It Works

1. Run the application using `python main.py`.
2. Select an option from the main menu.
3. Enter the required information.
4. The application validates the entered data.
5. Records are saved in the JSON database.
6. View or manage saved records through the menu.
7. Use **Search & Filter** to find records and **Business Reports** to review the business.

## Learning Outcomes

This project demonstrates practical implementation of:

- Python programming
- Classes and objects
- Modular programming
- Functions and exception handling
- Input validation
- JSON file handling
- Data management
- Business logic implementation
- Search, filtering and report generation
- Automated testing with `unittest`

## Conclusion

The Business & Service Management System provides a simple way to organize and manage business-related information using Python. Its modular structure makes the application easier to understand, maintain, and extend.

**Developed as part of the Veda Technology Python Programming Internship.**