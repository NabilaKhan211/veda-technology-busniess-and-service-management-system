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


def show_records(title, records):
    print(f"\n--- {title} ---")
    if not records:
        print("No records found.")
        return
    for record in records:
        fields = record.to_dict()
        print(" | ".join(f"{key}: {value}" for key, value in fields.items()))


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


def main():
    store = DataStore(DEFAULT_FILE)
    for warning in store.load():
        print("WARNING:", warning)

    customers = CustomerManager(store)
    services = ServiceManager(store)
    programs = ProgramManager(store)
    inquiries = InquiryManager(store)
    requests = RequestManager(store)

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

