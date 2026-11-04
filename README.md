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
├── business_data.json
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

## How It Works

1. Run the application using `python main.py`.
2. Select an option from the main menu.
3. Enter the required information.
4. The application validates the entered data.
5. Records are saved in the JSON database.
6. View or manage saved records through the menu.

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

## Conclusion

The Business & Service Management System provides a simple way to organize and manage business-related information using Python. Its modular structure makes the application easier to understand, maintain, and extend.

**Developed as part of the Veda Technology Python Programming Internship.**