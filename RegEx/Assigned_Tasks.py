import re

def Validate_Emp_Id(emp_id):
    return bool(re.fullmatch(r"EMP\d{4}", emp_id))

def Extract_phone_numbers(text):
    pattern = r"(?P<phone>(?<![A-Za-z0-9])\d{10}(?![A-Za-z0-9]))"
    return [m.group("phone") for m in re.finditer(pattern, text)]

def extract_machine_info(text):
    pattern = r"Machine\s+(M\d+)\s+temperature\s+(\d+(?:\.\d+)?)"
    return re.findall(pattern, text)

def extract_machine_info_1(text):
    pattern = (
        r"Machine\s+(?P<machine_id>M\d+)\s+"
        r"temperature\s+(?P<temperature>\d+(?:\.\d+)?)\s+"
        r"status\s+(?P<status>\w+)"
    )
    match = re.search(pattern, text)
    return match.groupdict() if match else None

def Validate_Machine_Id(machine_id):
    return bool(re.fullmatch(r"M\d{3}", machine_id))

def Extract_from_logs(log_text):
    pattern = (
        r"Machine:\s*(?P<machine_id>M\d+)\s*\|\s*"
        r"Temperature:\s*(?P<temperature>\d+(?:\.\d+)?)\s*C\s*\|\s*"
        r"Status:\s*(?P<status>\w+)"
    )
    match = re.search(pattern, log_text)
    return match.groupdict() if match else None

def replace_special_characters_with_underscore(text):
    return re.sub(r"[^a-zA-Z0-9]", "_", text)

def Split_using_Multiple_seperators(text):
    return re.split(r"[,;|:]+", text)

def Validate_Email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.fullmatch(pattern, email))

def Extract_Dates(text):
    pattern = r"(?P<date>\b\d{2}[-/]\d{2}[-/]\d{4}\b)"
    return [m.group("date") for m in re.finditer(pattern, text)]

def find_errors_in_a_log(log_text):
    pattern = (
        r"ERROR\s+Machine\s+"
        r"(?P<machine_id>M\d+)\s+"
        r"(?P<error_message>.+)"
    )
    return [
        (m.group("machine_id"), m.group("error_message"))
        for m in re.finditer(pattern, log_text)
    ]

def main():
    print("Validate an Employee IDs:---")
    emp_ids = ["EMP1234", "EMP0001", "EMP123", "EMP12345", "emp1234", "EMP12A4"]
    for emp_id in emp_ids:
        print(f"{emp_id} | {Validate_Emp_Id(emp_id)}")
    print("\n")

    print("Extracting Phone numbers:---")
    texts = [
        "Contact numbers are 9876543210, 9123456780 and 9988776655.",
        "9876543210", "12345", "987654321", "98765432101", "AB9876543210"
    ]
    for text in texts:
        print(f"{text} | {Extract_phone_numbers(text)}")
    print("\n")

    print("Extract Machine Information:---")
    machine_texts = [
        "Machine M123 temperature 78.5",
        "Machine M245 temperature 82.3",
        "Machine M007 temperature 65.8"
    ]
    for text in machine_texts:
        info = extract_machine_info(text)
        if info:
            machine_id, temperature = info[0]
            print(f"{machine_id} -> {temperature}")
    print("\n")

    print("Extract the machine, temperature and status separately:---")
    status_texts = [
        "Machine M123 temperature 78.5 status OK",
        "Machine M245 temperature 82.3 status FAIL",
        "Machine M007 temperature 65.8 status OK"
    ]
    for text in status_texts:
        info = extract_machine_info_1(text)
        if info:
            print(
                f"{info['machine_id']} | "
                f"{info['temperature']} | "
                f"{info['status']}"
            )
    print("\n")

    print("Validate a Machine IDs:---")
    machine_ids = ["M001", "M123", "M999", "M12", "M1234", "A123", "MABC", "M 123"]
    for machine_id in machine_ids:
        print(f"{machine_id} | {Validate_Machine_Id(machine_id)}")
    print("\n")

    print("Extracting clean log line:---")
    log_texts = [
        "Machine: M123 | Temperature: 78.5 C| Status: OK",
        "Machine: M245 | Temperature: 82.3 C| Status: FAIL",
        "Machine: M007 | Temperature: 65.8 C| Status: OK",
        "Machine: M999 | Temperature: 90.1 C| Status: CRITICAL"
    ]
    for text in log_texts:
        info = Extract_from_logs(text)
        if info:
            print(f"Machine = {info['machine_id']}")
            print(f"Temperature = {info['temperature']}")
            print(f"Status = {info['status']}")
            print()
            
    print("Replace Unwanted Characters:---")
    special_texts = [
        "Hello@World#2026!Python$",
        "ITC@Trichy#GMIIoT$Backend!",
        "Python@3.9#Regex$Module!",
        "Special@Characters#Here$!"
    ]
    for text in special_texts:
        print(f"{text} | {replace_special_characters_with_underscore(text)}")
    print("\n")

    print("Split Data Using Multiple Separators:---")
    separator_texts = [
        "Python,SQL;HTML|CSS:JavaScript",
        "Data,Science;Machine|Learning:AI",
        "Regex,Pattern;Matching|Text:Processing",
        "Split,Using;Multiple|Separators:InText"
    ]
    for text in separator_texts:
        print("\n".join(Split_using_Multiple_seperators(text)))
        print()

    print("Validate a simple email:---")
    emails = [
        "john@gmail.com", "test.user@yahoo.com", "abc123@company.in",
        "john@gmail", "@gmail.com", "john@", "john gmail.com"
    ]
    for email in emails:
        print(f"{email} | {Validate_Email(email)}")
    print("\n")

    print("Extract Dates:---")
    dates = [
        "Production started on 01-10-2026.",
        "Next maintenance is 15-10-2026.",
        "Previous maintenance was 28-09-2026.",
        "Production started on 01/10/2026.",
        "Next maintenance is 15/10/2026.",
        "Previous maintenance was 28/09/2026."
    ]
    for date in dates:
        print(*Extract_Dates(date), sep="\n")
    print("\n")

    print("Finding Errors in a Log:----")
    logs = [
        "2026-10-05 10:01:23 INFO Machine M123 started",
        "2026-10-05 10:02:11 ERROR Machine M124 connection failed",
        "2026-10-05 10:03:45 INFO Machine M125 started",
        "2026-10-05 10:04:17 ERROR Machine M126 timeout"
    ]
    machine_ids = []
    error_messages = []
    for log in logs:
        for machine_id, error_message in find_errors_in_a_log(log):
            machine_ids.append(machine_id)
            error_messages.append(error_message)
    print("Extracted Machine IDs:")
    print(*machine_ids, sep="\n")
    print("Extracted Error Messages:")
    print(*error_messages, sep="\n")

if __name__ == "__main__":
    main()