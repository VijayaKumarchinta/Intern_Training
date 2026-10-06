Regular Expression - a sequence of characters that defines a specific search pattern
  - Used for
    - Search
    - match
    - validate
    - extract
    - replace the text based on defined pattern
- RegEx is commonly used for
  - Input validation - while matching the i/p aganist a pattern
  - To Extract the information - by using groups we can able to pull specific parts of unstructured data
  - log Processing - parse Structured/semi-structuredlog lines into fieldsusing named groups
  - API input validation - same as i/p validation but on req body brfore processing
  - Data cleaning - Use re.sub() to replace the unwanted patterns with a clean version

- RegEx Pattern: the sequence of chracters that defines what we want to find, match, validate, extract or replace
  
- RegEx Engine: more like a component where it interprets a regex pattern an apply to the input text
  
- Literal chracters - chracters which represent themselved in a regex pattern
  
- Metchracters - in which we got a special meaning in regex pattern as follows:
  - "\" : Escape character
  - "[]": Character class
  - "^" : Start of the string
  - "$" : End of the string
  - "." : Any character execept newline
  - "?" : zero/one occurance
  - "*" : zero/more occurance
  - "+" : one/more occurance
  - "{}": Specifies the exact range
  - "()": Divided into groups and match to that particular string
  

M.chine - can match with any chracter
    - Ex: Machine, M1chine, M_chine

Machine | Sensor - means either machine or sensor

\d+ - one or more digits can match the pattern

\d{3} - can validate exaclty three digits

^abc != [^abc] - in first case it is an anchor and in second case it is a negation


Anchors - which specifies a position in the text rather than matching an actual character

  - "^" - matches the beginning of the string
  - "$" - Matches the end of the string
  - Together we mainly used for validation purpose
  - \A - Absolute start of the string
  - \Z / \z - Absolute end of the string

- Special sequences - regex provides predefined sequence for matching purpose
  - \d - specifis digit
        - Matches digits
  - \D - specifies non-digit
        - Matches any character that is not a digit
  - \w - specifies word character
        - Maches a word character
  - \W - specifies Non-word character
  - \s - specifies whitespace
        - mtches whitespaces such as : tab,space,newline
  - \S - specifies non-whitespace
  - \b - Word boundary
        - Represents a word boundary
  - \B - Non-word boundary


Some common regex functions which are useful:
  - re.search() - find the first match of anywhere
  - re.match() - match only from the beginning
  - re.fullmatch() - matches the entire string
  - re.findall() - find all the matches
  - re.sub() - Replace the text accordingly
  - re.split() - split it based on patteren



### import re - helps to import all the methods related to RegEx so that we can search,validate the given sequence
- re.search() - searching for exactly what we need to find
  
- re.fullmatch() - check the match throughout the entered string
  
- re.findall() - this will check and return the letters and digits which are present in the string
  - .join helps us to combine all the list values and return as single list.
  
- match_five_digit() - pattern is - "(?<!\d)\d{5}(?!\d)"" - to match the exact 5 digits 
  
- match_only_lowercase() - pattern is - "[a-z]" - to match with the lowercases
  
- match_only_uppercase() - pattern is - "[A-Z]" - to match with the uppercase
  
- match_letters_and_numbers() - pattern is - "([a-zA-Z]+)(\d+)" with the respective letters and numbers by forming grouping
  
- match_a_string_starts_with_A() - pattern is "\bA\w*" - so that it will match with the string which starts with "A"
  
- match_a_string_ends_with_Z() - pattern is "\w*Z\b" - so it will match with the string that ends with "Z"

- match_a_string_contains_only_digits() - pattern is "\d+" - so it will check for the numbers itself

- match_a_string_contains_no_digits() - pattern is "\D+" - so it will check for non-numbers