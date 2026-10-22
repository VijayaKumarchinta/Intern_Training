# Regular Expressions (Concepts) — Intern Training

**Source:** `RegEx/regex_readme.md`

> Regular Expression — a sequence of characters that defines a specific search pattern. Used for search, match, validate, extract, replace text based on defined pattern.

---

## 1. Pattern elements

**What:** The building blocks of a regex.

- **RegEx Pattern** — the sequence of characters that defines what we want to find/match/validate/extract/replace.
- **RegEx Engine** — interprets a regex pattern and applies it to input text.
- **Literal characters** — represent themselves.
- **Meta characters**:
  - `\` — escape character
  - `[]` — character class
  - `^` — start of string
  - `$` — end of string
  - `.` — any character except newline
  - `?` — zero/one occurrence
  - `*` — zero/more occurrence
  - `+` — one/more occurrence
  - `{}` — specifies exact range
  - `()` — groups

**Pros:**
- Compact, readable patterns for common matching tasks.

**Cons/drawbacks:**
- Easy to get a single character wrong (`^` anchor vs `[^` negation).

**Errors encountered & causes:**
- `^abc` misinterpreted as negation instead of "starts with abc" → anchor vs negation confusion.

**Use cases:**
- Input validation, log parsing, search-and-replace, data cleaning.

**Usage:**
- Learn meta characters first; test patterns with a regex tester before embedding in code.

---

## 2. Anchors

**What:** Specify a **position** in the text rather than matching an actual character.

| Anchor | What it matches |
|---|---|
| `^` | beginning of string |
| `$` | end of string |
| `\A` | absolute start of string |
| `\Z` / `\z` | absolute end of string |

**Concepts learned:**
- Anchors are positions, not characters.
- `^` is NOT the same as `[^` (negation) — one character, opposite meaning.

**Pros:**
- `^` and `$` let you match "whole line" patterns.

**Cons/drawbacks:**
- `^` can also mean "not" inside a character class — a frequent source of bugs.

**Errors encountered & causes:**
- `^abc` (anchor) vs `[^abc]` (negation) — one character, opposite meanings.

**Use cases:**
- Matching start/end of lines, passwords, whole-string validation.

**Usage:**
- `^abc` → starts with abc
- `abc$` → ends with abc
- `^abc$` → exactly abc

---

## 3. Special sequences

| Sequence | What it matches |
|---|---|
| `\d` | digit |
| `\D` | non-digit |
| `\w` | word character |
| `\W` | non-word character |
| `\s` | whitespace (tab, space, newline) |
| `\S` | non-whitespace |
| `\b` | word boundary |
| `\B` | non-word boundary |

**Pros:**
- Shorthand for common character classes.
- Shorter, more readable patterns.

**Cons/drawbacks:**
- `\w` and `\b` depend on the "word" definition — easy to misuse with non-ASCII text.

**Errors encountered & causes:**
- N/A (used correctly in practice).

**Use cases:**
- `^\d{5}$` for 5-digit codes; `\bword\b` for whole-word matches; `\d+` for numbers.

**Usage:**
- `\d{5}` for exactly five digits; `\b[A-Z]` for uppercase words; `\w+@\w+\.\w+` for simple emails.

---

## 4. Common regex functions

| Function | What it does |
|---|---|
| `re.search()` | find first match anywhere |
| `re.match()` | match only from the beginning |
| `re.fullmatch()` | matches the entire string |
| `re.findall()` | find all matches |
| `re.sub()` | replace text |
| `re.split()` | split based on a pattern |

**Concepts learned:**
- Know which function to use for each scenario:
  - `search` → find first match anywhere
  - `match` → from beginning
  - `fullmatch` → entire string
  - `findall` → extract all
  - `sub` → replace
  - `split` → split by pattern

**Pros:**
- Python exposes the full regex toolkit in one module.

**Cons/drawbacks:**
- Using the wrong function gives subtly wrong results (e.g., `match` vs `search`).

**Errors encountered & causes:**
- `^abc` vs `[^abc]` confusion (anchor vs negation) — a function-level bug too.

**Use cases:**
- Input validation (`fullmatch`), data extraction (`findall`), cleaning (`sub`), splitting (`split`).

**Usage:**
```python
import re
m = re.fullmatch(r"\d{5}", "12345")   # exact 5 digits
m = re.search(r"\d+", "abc 123")     # first number
```

---

## 5. Matcher functions — the eight exercises

**What:** Eight matcher functions driven by an interactive `main()`.

| Function | Pattern | Purpose |
|---|---|---|
| `match_five_digit()` | `(?<!\d)\d{5}(?!\d)` | exact 5 digits |
| `match_only_lowercase()` | `[a-z]` | lowercase-only scan |
| `match_only_uppercase()` | `[A-Z]` | uppercase-only scan |
| `match_letters_and_numbers()` | `([a-zA-Z]+)(\d+)` with grouping | grouped letters + numbers extraction |
| `match_a_string_starts_with_A()` | `\bA\w*` | starts with A |
| `match_a_string_ends_with_Z()` | `\w*Z\b` | ends with Z |
| `match_a_string_contains_only_digits()` | `\d+` | digits-only |
| `match_a_string_contains_no_digits()` | `\D+` | no-digits scan |

**Note:** `match_letter_and_numbers()` in the implementation uses **two separate `findall` calls**:
```python
def match_letter_and_numbers(result4):
    letters = re.findall(r"[A-Za-z]", result4)
    numbers = re.findall(r"\d+", result4)
    if not letters and not numbers:
        return None
    return {"letters": letters, "numbers": ",".join(numbers)}
```

**Concepts learned:**
- **Lookarounds** (`(?<!\d)…(?!…)`) match a **position**, not a character — the clean way to say "exactly five digits, not part of a longer number".
- `^abc` (anchor) ≠ `[^abc]` (negation).

**Pros:**
- Lookarounds give precise position-based matching without consuming characters.
- `findall` with two patterns cleanly separates letters and numbers.

**Cons/drawbacks:**
- Regex is not a general-purpose parser for nested/structured data.
- Readmes can drift from code (legacy issue noted in the Oct 8 review).

**Errors encountered & causes:**
- Readme documented a grouping pattern the implementation no longer used → corrected; code is the source of truth.

**Use cases:**
- Input validation, log parsing with named groups, `re.sub()` data cleaning.

**Usage:**
- Use `fullmatch` for whole-string validation; use `findall` with `[]` and `\d` for extraction; use lookarounds for exact-length, non-part-of-longer-number matching.

---

## 6. Important notes

- `^abc != [^abc]` — first is an anchor (starts with abc), second is negation (not a, b, or c).
- Know which use cases to apply for `search/match/fullmatch/findall/sub/split`.
- Regex is mainly used for **validation** in day-to-day scenarios — not as a puzzle toy.

---

**Quick reference — all RegEx files**
| File | Role |
|---|---|
| regex_readme.md | Eight matcher functions + full notes |
| Assigned_Tasks.py | Practice exercises |
| `.py` | (concept file literally named `.py` — hidden from most tooling until renamed) |

**Status:** 8 matcher functions + notes, runnable standalone.
