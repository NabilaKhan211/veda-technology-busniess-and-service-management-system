"""Console entry point for the Business & Service Management System."""

from storage import DataStore, DEFAULT_FILE
from models import (
    BusinessError, CUSTOMER_KINDS, SERVICE_CATEGORIES, PROGRAM_TYPES,
    INQUIRY_TOPICS, PRIORITIES, SERVICE_STATUSES, PROGRAM_STATUSES,
    INQUIRY_STATUSES, REQUEST_STATUSES,
)
from customer_manager import CustomerManager
from service_manager import ServiceManager
from program_manager import ProgramManager
from inquiry_manager import InquiryManager, RequestManager
from search_manager import SearchManager
from report_manager import ReportManager

# Which columns to show for each kind of record
COLUMNS = {
    "customers": ["id", "name", "kind", "email", "phone", "city"],
    "services": ["id", "name", "category", "price", "delivery_days", "status"],
    "programs": ["id", "name", "type", "fee", "start_date", "seats", "status"],
    "inquiries": ["id", "customer_id", "topic", "reference", "priority", "status", "message"],
    "requests": ["id", "customer_id", "service_id", "quote", "status", "due_date"],
}


def ask(label):
    return input(label).strip()


def choose(label, options):
    print(label + ":")
    for index, option in enumerate(options, 1):
        print(f"  {index}. {option}")
    while True:
        value = ask("Choose number: ")
        if value.isdigit() and 1 <= int(value) <= len(options):
            return options[int(value) - 1]
        print("Please enter a valid option number.")

        
def choose_any(label, options):
    """Like choose(), but 0 means 'any' (used by search filters). Returns '' for any."""
    print(label + ":")
    print("  0. Any")
    for index, option in enumerate(options, 1):
        print(f"  {index}. {option}")
    while True:
        value = ask("Choose number: ")
        if value == "0":
            return ""
        if value.isdigit() and 1 <= int(value) <= len(options):
            return options[int(value) - 1]
        print("Please enter a valid option number.")
 
 
def row_values(record, collection):
    data = record.to_dict()
    if collection == "programs":
        data["seats"] = f"{len(record.enrolled)}/{record.seats}"
        data["status"] = record.effective_status()
    if collection == "inquiries" and len(data["message"]) > 35:
        data["message"] = data["message"][:32] + "..."
    return [str(data[column]) for column in COLUMNS[collection]]
 
 
def show_records(title, records, collection):
    print(f"\n--- {title} ({len(records)}) ---")
    if not records:
        print("No records found.")
        return
    headers = [c.replace("_", " ").title() for c in COLUMNS[collection]]
    rows = [row_values(record, collection) for record in records]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
 

def add_customer(customers):
    print("\nADD CUSTOMER")
    record = customers.add(
        ask("Customer name: "),
        choose("Customer type", CUSTOMER_KINDS),
        ask("Email: "),
        ask("Phone: "),
        ask("City: "),
    )
    print(f"Customer added successfully. ID: {record.id}")


def add_service(services):
    print("\nADD SERVICE")
    record = services.add(
        ask("Service name: "),
        choose("Category", SERVICE_CATEGORIES),
        ask("Description: "),
        ask("Price: "),
        ask("Delivery time (days): "),
    )
    print(f"Service added successfully. ID: {record.id}")


def add_program(programs):
    print("\nADD PROGRAM")
    record = programs.add(
        ask("Program name: "),
        choose("Program type", PROGRAM_TYPES),
        ask("Description: "),
        ask("Duration (days): "),
        ask("Fee: "),
        ask("Number of seats: "),
        ask("Start date (YYYY-MM-DD): "),
    )
    print(f"Program added successfully. ID: {record.id}")


def add_inquiry(inquiries):
    print("\nADD INQUIRY")
    customer_id = ask("Customer ID (e.g. CU-001): ")
    topic = choose("Inquiry topic", INQUIRY_TOPICS)
    reference = ""
    if topic == "Service":
        reference = ask("Service ID (e.g. SV-001): ")
    elif topic == "Program":
        reference = ask("Program ID (e.g. PR-001): ")
    message = ask("Inquiry message: ")
    priority = choose("Priority", PRIORITIES)
    record = inquiries.create(customer_id, topic, reference, message, priority)
    print(f"Inquiry created successfully. ID: {record.id}")


def add_request(requests):
    print("\nCREATE SERVICE REQUEST")
    customer_id = ask("Customer ID (e.g. CU-001): ")
    service_id = ask("Service ID (e.g. SV-001): ")
    details = ask("Request details: ")
    quote = ask("Quote (press Enter to use service price): ")
    due_date = ask("Due date YYYY-MM-DD (press Enter for automatic date): ")
    record = requests.create(customer_id, service_id, details, quote or None, due_date or None)
    print(f"Service request created successfully. ID: {record.id}")

# ---------- search & filtering ----------
def search_menu(search):
    print("\nSEARCH & FILTER")
    kind = choose("Search in", ["Customers", "Services", "Programs", "Inquiries", "Service requests"])
    keyword = ask("Keyword (press Enter to skip): ")
    if kind == "Customers":
        found = search.customers(keyword, choose_any("Customer type", CUSTOMER_KINDS), ask("City (Enter = any): "))
        show_records("CUSTOMER RESULTS", found, "customers")
    elif kind == "Services":
        found = search.services(keyword, choose_any("Category", SERVICE_CATEGORIES), choose_any("Status", SERVICE_STATUSES),
                                ask("Minimum price (Enter = any): "), ask("Maximum price (Enter = any): "))
        show_records("SERVICE RESULTS", found, "services")
    elif kind == "Programs":
        found = search.programs(keyword, choose_any("Program type", PROGRAM_TYPES), choose_any("Status", PROGRAM_STATUSES + ["Full"]),
                                ask("Only programs with free seats? (y/n): ").lower() == "y")
        show_records("PROGRAM RESULTS", found, "programs")
    elif kind == "Inquiries":
        found = search.inquiries(keyword, choose_any("Status", INQUIRY_STATUSES), choose_any("Priority", PRIORITIES),
                                 choose_any("Topic", INQUIRY_TOPICS), ask("Customer ID (Enter = any): "))
        show_records("INQUIRY RESULTS", found, "inquiries")
    else:
        found = search.requests(keyword, choose_any("Status", REQUEST_STATUSES), ask("Customer ID (Enter = any): "),
                                ask("Service ID (Enter = any): "), ask("Only overdue requests? (y/n): ").lower() == "y")
        show_records("SERVICE REQUEST RESULTS", found, "requests")
 
 
# ---------- reports ----------
def report_menu(reports):
    print("\nBUSINESS REPORTS")
    names = list(reports.SECTIONS)
    pick = choose("Report", ["Full report"] + [name.title() for name in names] + ["Save full report to a text file"])
    if pick == "Full report":
        print(reports.build())
    elif pick.startswith("Save"):
        print("Report saved to:", reports.export())
    else:
        print(reports.build([pick.lower()]))
 
 
# ---------- update / delete ----------
CHOICE_FIELDS = {"kind": CUSTOMER_KINDS, "category": SERVICE_CATEGORIES, "type": PROGRAM_TYPES}
 
 
def edit_record(manager, label):
    record_id = ask(f"{label} ID: ")
    field = choose("Field to change", list(manager.EDITABLE))
    value = choose("New value", CHOICE_FIELDS[field]) if field in CHOICE_FIELDS else ask("New value: ")
    record = manager.update(record_id, **{field: value})
    print(f"{label} {record.id} updated.")
 
 
def manage_menu(customers, services, programs, inquiries, requests):
    print("\nMANAGE RECORDS (edit / delete)")
    pick = choose("Action", [
        "Edit customer", "Delete customer", "Edit service", "Change service status", "Delete service",
        "Edit program", "Change program status", "Withdraw customer from program", "Delete program",
        "Add inquiry note", "Change inquiry priority", "Update request quote"])
    if pick == "Edit customer":
        edit_record(customers, "Customer")
    elif pick == "Delete customer":
        print(f"Deleted customer {customers.delete(ask('Customer ID: ')).name}.")
    elif pick == "Edit service":
        edit_record(services, "Service")
    elif pick == "Change service status":
        record = services.set_status(ask("Service ID: "), choose("New status", SERVICE_STATUSES))
        print(f"Service {record.id} is now {record.status}.")
    elif pick == "Delete service":
        print(f"Deleted service {services.delete(ask('Service ID: ')).name}.")
    elif pick == "Edit program":
        edit_record(programs, "Program")
    elif pick == "Change program status":
        record = programs.set_status(ask("Program ID: "), choose("New status", PROGRAM_STATUSES))
        print(f"Program {record.id} is now {record.status}.")
    elif pick == "Withdraw customer from program":
        record = programs.withdraw(ask("Program ID: "), ask("Customer ID: "))
        print(f"Withdrawn. Seats left: {record.seats_left()}")
    elif pick == "Delete program":
        print(f"Deleted program {programs.delete(ask('Program ID: ')).name}.")
    elif pick == "Add inquiry note":
        record = inquiries.add_note(ask("Inquiry ID: "), ask("Note: "))
        print(f"Note added to {record.id}.")
    elif pick == "Change inquiry priority":
        record = inquiries.set_priority(ask("Inquiry ID: "), choose("New priority", PRIORITIES))
        print(f"Inquiry {record.id} priority is now {record.priority}.")
    else:
        record = requests.update_quote(ask("Request ID: "), ask("New quote: "))
        print(f"Request {record.id} quote is now {record.quote}.")
 

def main():
    store = DataStore(DEFAULT_FILE)
    for warning in store.load():
        print("WARNING:", warning)

    customers = CustomerManager(store)
    services = ServiceManager(store)
    programs = ProgramManager(store)
    inquiries = InquiryManager(store)
    requests = RequestManager(store)
    search = SearchManager(store)
    reports = ReportManager(store)

    actions = {
        "1": lambda: add_customer(customers),
        "2": lambda: show_records("CUSTOMERS", customers.all()),
        "3": lambda: add_service(services),
        "4": lambda: show_records("SERVICES", services.all()),
        "5": lambda: add_program(programs),
        "6": lambda: show_records("PROGRAMS", programs.all()),
        "7": lambda: add_inquiry(inquiries),
        "8": lambda: show_records("INQUIRIES", inquiries.all()),
        "9": lambda: add_request(requests),
        "10": lambda: show_records("SERVICE REQUESTS", requests.all()),
        "14": lambda: search_menu(search),
        "15": lambda: report_menu(reports),
        "16": lambda: manage_menu(customers, services, programs, inquiries, requests),
    }

    while True:
        print("\n" + "=" * 48)
        print(" BUSINESS & SERVICE MANAGEMENT SYSTEM")
        print("=" * 48)
        print("1. Add Customer")
        print("2. View Customers")
        print("3. Add Service")
        print("4. View Services")
        print("5. Add Program")
        print("6. View Programs")
        print("7. Add Inquiry")
        print("8. View Inquiries")
        print("9. Create Service Request")
        print("10. View Service Requests")
        print("11. Enrol Customer in Program")
        print("12. Update Inquiry Status")
        print("13. Update Service Request Status")
        print("14. Search & Filter")
        print("15. Business Reports")
        print("16. Manage Records (edit / delete)")
        print("0. Exit")

        choice = ask("\nEnter your choice: ")
        try:
            if choice in actions:
                actions[choice]()
            elif choice == "11":
                program_id = ask("Program ID: ")
                customer_id = ask("Customer ID: ")
                record = programs.enrol(program_id, customer_id)
                print(f"Enrolment successful. Seats left: {record.seats_left()}")
            elif choice == "12":
                inquiry_id = ask("Inquiry ID: ")
                status = choose("New inquiry status", INQUIRY_STATUSES)
                record = inquiries.set_status(inquiry_id, status)
                print(f"Inquiry {record.id} status updated to {record.status}.")
            elif choice == "13":
                request_id = ask("Request ID: ")
                status = choose("New request status", REQUEST_STATUSES)
                record = requests.set_status(request_id, status)
                print(f"Request {record.id} status updated to {record.status}.")
            elif choice == "0":
                store.save()
                print("Data saved. Thank you for using the system!")
                break
            else:
                print("Invalid choice. Please select a number from the menu.")
        except (BusinessError, ValueError) as error:
            print("Error:", error)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Data has been saved.")
            store.save()
            break


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nApplication closed.")

