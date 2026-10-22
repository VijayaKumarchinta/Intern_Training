# 7 Common Programming Principles — Intern Training (Review)

**Source:** `7_Common_programming_Principles.md` (pre-existing)

> A reference document on the core programming principles that apply to every concept above.

---

## 1. Abstraction

**What:** Hiding the complex implementation details and showing only the essential features of an object.

**Concepts learned:**
- Reduces complexity by hiding how something works.
- Makes systems easier to understand and use.

**Pros:**
- Simpler interfaces.
- Easier to change the implementation without affecting users.

**Cons/drawbacks:**
- Misused abstraction can become a maze of indirection.
- Over-abstracting adds layers that obscure flow.

**Errors encountered & causes:**
- N/A here (conceptual).

**Use cases:**
- Any API, library, or service boundary where the user doesn't need the internal details.

**Usage:**
- Hide implementation behind interfaces, factory functions, and layered architectures.

---

## 2. Encapsulation

**What:** Wrapping data and methods into a single unit (a class) and restricting direct access to some of its components.

**Concepts learned:**
- Public members (`name`) are freely usable.
- Protected-by-convention (`_Code`) signals internal use.
- Private (`__battery_health`) uses name-mangling to `_Smartphone__battery_health`.
- Python's "private" is a convention, not a wall.

**Pros:**
- Prevents accidental modification of internal state.
- Organises code into logical units.

**Cons/drawbacks:**
- Name-mangling is **not true privacy**.
- Over-zealous encapsulation makes debugging harder.

**Errors encountered & causes:**
- Assuming `__private` is invisible → reachable via `_ClassName__private`.

**Use cases:**
- Class-based models where internal state must be protected or grouped.

**Usage:**
- Use `_` for "internal / protected by convention"; don't rely on name-mangling for security.

---

## 3. Inheritance

**What:** A mechanism where a class (child) acquires the properties and methods of another class (parent).

**Concepts learned:**
- Code reuse between related classes.
- **MRO (Method Resolution Order):** with `Son(Mother, Father)`, Python searches parents left to right.
- Multi-level chains (GrandFather → Father → Son) and hybrids are just these patterns composed.

**Pros:**
- Reuses code; models "is-a" relationships.

**Cons/drawbacks:**
- Multiple inheritance + MRO can surprise (diamond problems).
- Deep hierarchies become hard to read.

**Errors encountered & causes:**
- MRO surprise in `Son(Mother, Father)` → decide parent order deliberately.
- AttributeError on invalid method access → guarded.

**Use cases:**
- `Single`, `Multiple`, `MultiLevel`, `Hierarchical`, `Hybrid` inheritance.

**Usage:**
- Use single/multilevel for clean hierarchies; prefer composition over multiple inheritance in production.

---

## 4. Polymorphism

**What:** The ability of different objects to respond to the same method call in their own way.

**Concepts learned:**
- Different classes can implement the same method with different behaviour.
- `Son` overriding or extending a parent's method.

**Pros:**
- Flexible, extensible code; a common interface can drive many implementations.

**Cons/drawbacks:**
- Hard to trace which implementation a call will resolve to (MRO).

**Errors encountered & causes:**
- MRO confusion in multiple inheritance → that's where polymorphism's dispatch happens.

**Use cases:**
- Plugins, strategy patterns, any codebase with interchangeable implementations.

**Usage:**
- Define a common interface; let each subclass implement it.

---

## 5. Composition over Inheritance

**What:** Prefer composing objects with other objects rather than inheriting from them to reuse behaviour.

**Concepts learned:**
- Inheritance is "is-a"; composition is "has-a".
- Composition is more flexible and easier to change.

**Pros:**
- More flexible; avoids deep inheritance trees and MRO problems.
- Behaviour can be swapped at runtime.

**Cons/drawbacks:**
- Can lead to more classes and verbose wiring.

**Errors encountered & causes:**
- N/A here (conceptual).

**Use cases:**
- When an "is-a" relationship is weak or when behaviour needs to combine from multiple sources.

**Usage:**
- Compose objects; prefer aggregation and dependency injection over multi-level inheritance.

---

## 6. DRY (Don't Repeat Yourself)

**What:** Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.

**Concepts learned:**
- Shared validators and shared filter builders in the capstone.
- One-edit guarantee: change once, update everywhere.

**Pros:**
- Less duplication; easier to maintain and update.

**Cons/drawbacks:**
- Premature abstraction creates a tangled web.

**Errors encountered & causes:**
- Copy-pasted validation/filter logic in three places → found in design review → moved to one shared module + one shared filter builder.

**Use cases:**
- Validation logic, SQL filter builders, config, logging configuration.

**Usage:**
- Extract duplicated logic into a single shared module with a single owner.

---

## 7. Separation of Concerns

**What:** Dividing a program into distinct sections, where each section addresses a separate concern.

**Concepts learned:**
- Routes → Services → Database layering.
- `app.py` (HTTP/factory) stays separate from `services/` (SQL) and `database/` (pool).
- Validation lives in `utils/validation.py`, not in routes.

**Pros:**
- Each layer can be changed without affecting others.
- Testable in isolation.

**Cons/drawbacks:**
- Adds indirection; wrong boundaries create friction.

**Errors encountered & causes:**
- Validation inside a single view class → moved into `utils/validation.py` (one shared door).
- `WHERE 1 = 1` string surgery → moved to a shared `_build_reading_filters()`.

**Use cases:**
- Every API: routes, services, database, config, logging, validation.

**Usage:**
- Keep HTTP handling in routes, SQL in services, connection management in database; validate in one shared module.

---

## Quick reference — all principles

| Principle | Core idea | Best use case |
|---|---|---|
| Abstraction | Hide complexity, show essentials | APIs, libraries |
| Encapsulation | Bundle data + methods, restrict access | Classes, models |
| Inheritance | Reuse via "is-a" | Clear hierarchies |
| Polymorphism | Different objects respond to the same call | Plugins, strategies |
| Composition over Inheritance | "has-a" instead of "is-a" | Flexible/complex systems |
| DRY | Single source of truth per piece of knowledge | Shared logic, config |
| Separation of Concerns | Distinct sections for distinct concerns | Large applications |

---

**Source:** `7_Common_programming_Principles.md`
