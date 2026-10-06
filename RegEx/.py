import re

def match_five_digit(result1):
    match = re.search(r"(?<!\d)\d{5}(?!\d)", result1)
    return match.group() if match else None

def match_only_lowercase(result2):
    match = re.findall(r"[a-z]", result2)
    return match if match else None

def match_only_uppercase(result3):
    match = re.findall(r"[A-Z]", result3)
    return match if match else None

def match_letter_and_numbers(result4):
    letters = re.findall(r"[A-Za-z]", result4)
    numbers = re.findall(r"\d+", result4)

    if not letters and not numbers:
        return None

    return {
        "letters": letters,
        "numbers": ",".join(numbers)
    }

def match_a_string_starts_with_A(result5):
    match = re.findall(r"\bA\w*", result5)
    return match if match else None

def match_a_string_ends_with_Z(result6):
    match = re.findall(r"\w*Z\b", result6)
    return match if match else None

def match_a_string_contains_only_digits(result7):
    match = re.findall(r"\d+", result7)
    return match if match else None

def match_a_string_contains_no_digits(result8):
    match = re.findall(r"\D+", result8)
    return match if match else None

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

    result4 = match_letter_and_numbers(input("Enter a pattern containing letters and digits: "))

    if result4:
        print(
            f"Letters found: {result4['letters']}, "
            f"Numbers found: {result4['numbers']}"
        )
    else:
        print("No letters or numbers found.")

    result5 = match_a_string_starts_with_A(input("Enter a pattern starting with 'A': "))
    if result5:
        print(f"Strings starts with 'A': {result5}")
    else:
        print("Strings does not start with 'A'.")

    result6 = match_a_string_ends_with_Z(input("Enter a pattern ending with 'Z': "))
    if result6:
        print(f"Strings ends with 'Z': {result6}")
    else:
        print("Strings does not end with 'Z'.")

    result7 = match_a_string_contains_only_digits(input("Enter a pattern containing digits: "))
    if result7:
        print(f"Strings contains the following digits: {result7}")
    else:
        print("Strings does not contain any digits.")

    result8 = match_a_string_contains_no_digits(input("Enter a pattern containing digits and letters : "))
    if result8:
        print(f"Strings contains no digits: {result8}")
    else:
        print("Strings contains digits.")

if __name__ == "__main__":
    main()