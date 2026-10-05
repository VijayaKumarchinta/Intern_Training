import re

def match_five_digit(result1):
    match = re.search(r"(?<!\d)\d{5}(?!\d)", result1)
    return match.group() if match else None

def match_only_lowercase(result2):
    match = re.search(r"[a-z]+", result2)
    return match.group() if match else None

def match_only_uppercase(result3):
    match = re.search(r"[A-Z]+", result3)
    return match.group() if match else None

def match_letter_and_digit(result4):
    letters = re.findall(r"[A-Za-z]", result4)
    digits = re.findall(r"\d", result4)

    if not letters and not digits:
        return None

    return {
        "letters": "".join(letters),
        "digits": "".join(digits)
    }

def match_a_string_starts_with_A(result5):
    match = re.match(r"^A", result5)
    return result5 if match else None

def match_a_string_ends_with_Z(result6):
    match = re.search(r"Z$", result6)
    return result6 if match else None

def match_a_string_contains_only_numbers(result7):
    match = re.search(r"\d+", result7)
    return match.group() if match else None

def match_a_string_contains_no_digits(result8):
    match = re.search(r"\D+", result8)
    return match.group() if match else None

def main():
    result1 = match_five_digit(input("Enter a pattern containing a five-digit number in it: "))
    if result1:
        print(f"Five-digit number found: {result1}")
    else:
        print("No five-digit number found.")

    result2 = match_only_lowercase(input("Enter a pattern containing lowercase letters in it: "))
    if result2:
        print(f"Lowercase letters found: {result2}")
    else:
        print("No lowercase letters found.")

    result3 = match_only_uppercase(input("Enter a pattern containing uppercase letters in it: "))
    if result3:
        print(f"Uppercase letters found: {result3}")
    else:
        print("No uppercase letters found.")

    result4 = match_letter_and_digit(input("Enter a pattern containing letters and digits: "))

    if result4:
        print(
            f"Letters found: {result4['letters']}, "
            f"Digits found: {result4['digits']}"
        )
    else:
        print("No letters or digits found.")

    result5 = match_a_string_starts_with_A(input("Enter a pattern starting with 'A': "))
    if result5:
        print(f"String starts with 'A': {result5}")
    else:
        print("String does not start with 'A'.")

    result6 = match_a_string_ends_with_Z(input("Enter a pattern ending with 'Z': "))
    if result6:
        print(f"String ends with 'Z': {result6}")
    else:
        print("String does not end with 'Z'.")

    result7 = match_a_string_contains_only_numbers(input("Enter a pattern containing only numbers: "))
    if result7:
        print(f"String contains only numbers: {result7}")
    else:
        print("String does not contain only numbers.")

    result8 = match_a_string_contains_no_digits(input("Enter a pattern containing no digits: "))
    if result8:
        print(f"String contains no digits: {result8}")
    else:
        print("String contains digits.")

if __name__ == "__main__":
    main()