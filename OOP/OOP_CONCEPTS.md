# OOP Concepts — Intern Training

**Source:** `OOP/README.md`, `OOP/*.py` (Single, Multiple, MultiLevel, Hierarchical, Hybrid inheritance + Encapsulation)

---

## 1. Inheritance — general concept

**What:** A mechanism where a class (child/subclass) acquires the properties and methods of another class (parent/superclass).

**Concepts learned:**
- Inheritance is the foundation of the five inheritance types.
- MRO (Method Resolution Order): with `Son(Mother, Father)`, Python searches parents **left to right**.
- Hybrid trees are just these patterns composed together.

**Pros:**
- Code reuse between related classes.
- Organises a class hierarchy logically.
- Enables polymorphism.

**Cons/drawbacks:**
- Multiple inheritance + MRO can surprise (diamond problems in hybrid trees).
- Deep hierarchies become hard to read.

**Errors encountered & causes:**
- AttributeError on invalid method access → expected; guarded with `try/except` because the instruction demanded it.

**Use cases:**
- Any inheritance-type demonstration, and as a starting point for larger class design.
- Teaching OOP fundamentals.

**Usage:**
- Use `class Child(Parent):` and call `super()` carefully.
- Prefer composition over multiple inheritance in production.

---

## 2. Single Inheritance

**What:** One child class inherits from exactly one parent class.

**Example concept:** `Son` inherits from `Father` and reuses `fun1()`.

**Pros:**
- Simple, clear, easy to reason about.
- No MRO ambiguity.

**Cons/drawbacks:**
- Limited to one parent — cannot share from two classes.

**Errors encountered & causes:**
- AttributeError on calling a non-existent method → guarded with `try/except`.

**Use cases:**
- Straightforward "is-a" relationships (e.g., `Employee` → `Person`).

**Usage:**
```python
class Father:
    def fun1(self):
        print("Father's method")

class Son(Father):
    pass
```

---

## 3. Multiple Inheritance

**What:** A child class inherits from **two or more** parent classes.

**Example concept:** `Son(Mother, Father)` — two parents, one child.

**Pros:**
- A class can gather capabilities from several parents.
- Models real-world mixed roles.

**Cons/drawbacks:**
- MRO order matters: `Son(Mother, Father)` searches Mother **first**; wrong order can silently pick the wrong parent's method.
- Diamond problems in complex trees.

**Errors encountered & causes:**
- Confusing MRO → ensure the correct parent order in the class definition.
- AttributeError on invalid access → guarded.

**Use cases:**
- Mixing behaviours (e.g., `Flyable` + `Swimmable` roles).

**Usage:**
```python
class Mother:
    pass

class Father:
    pass

class Son(Mother, Father):
    pass
# Python searches Mother first, then Father
```

---

## 4. MultiLevel Inheritance

**What:** Inheritance across **three or more levels**: GrandFather → Father → Son.

**Example concept:** GrandFather → Father → Son, three levels deep.

**Pros:**
- Deep "is-a" chains model multi-generational hierarchies.
- Reuses methods at every level.

**Cons/drawbacks:**
- Deep chains obscure which parent a method comes from.
- Harder to test and maintain.

**Errors encountered & causes:**
- AttributeError when calling a method not defined at the exact level → guarded with `try/except`.

**Use cases:**
- Modelling inheritance of roles/traits across generations.
- Teaching multi-level hierarchy.

**Usage:**
```python
class GrandFather:
    def trait(self):
        return "GrandFather trait"

class Father(GrandFather):
    pass

class Son(Father):
    pass
```

---

## 5. Hierarchical Inheritance

**What:** **One parent** with **two or more children** sharing it.

**Example concept:** Two children sharing one `Father`.

**Pros:**
- Shared behaviour for a group of related children.
- Reduces duplication.

**Cons/drawbacks:**
- Adding a new child may require changing many parents.
- A child cannot share from two unrelated parents.

**Errors encountered & causes:**
- AttributeError when a child is asked for a parent's method → guarded.

**Use cases:**
- Multiple report types / data loaders sharing a base class.

**Usage:**
```python
class Father:
    def fun1(self):
        return "shared"

class Son(Father):
    pass

class Daughter(Father):
    pass
```

---

## 6. Hybrid Inheritance

**What:** A **mix** of multiple + multilevel in one tree.

**Example concept:** A hybrid tree combining multiple and multilevel inheritance.

**Pros:**
- Most flexible "is-a" modelling available.
- Can represent very complex real-world relationships.

**Cons/drawbacks:**
- Highest risk of MRO confusion and diamond problems.
- Hardest to read and maintain.

**Errors encountered & causes:**
- MRO surprises → decide parent order deliberately.
- AttributeError on invalid access → guarded.

**Use cases:**
- Complex domain models where multiple hierarchies intersect.

**Usage:**
- Use only when a clean "is-a" relationship truly requires mixing; otherwise use composition.

---

## 7. Encapsulation

**What:** Restricting direct access to an object's internal state. Three levels:

- **Public** — `name` — accessible from anywhere.
- **Protected (by convention)** — `_Code` — intended for internal use; not enforced.
- **Private (name-mangling)** — `__battery_health` — not truly hidden.

**Concepts learned:**
- `Encapsulation.py` shows a class with public, protected, and private members.
- `__battery_health` gets name-mangled to `_Smartphone__battery_health`.
- Python's "private" is a **convention, not a wall**.

**Pros:**
- Public members are freely usable.
- `_` conventions signal "internal".
- Name-mangling prevents accidental name clashes.

**Cons/drawbacks:**
- Name-mangling is **not true privacy** — `_Smartphone__battery_health` is reachable.
- Overengineering "private" in Python adds little security.
- Protected members can be accessed by subclasses.

**Errors encountered & causes:**
- Believing `__private` is invisible → it is reachable via `_ClassName__private`.
- Trying to call a private method from outside → `AttributeError` → shows it's a convention, not a wall.

**Use cases:**
- Teaching access control in Python.
- Signalling internal APIs with `_`.

**Usage:**
- Use `_` for "internal / protected by convention".
- Do **not** rely on `__name-mangling` for security; it's only name-clash prevention.
- Keep truly sensitive logic in module-level functions, not inside a class.

---

## 8. Exception-in-every-example (the stated instruction)

**What:** Each OOP file wraps demo calls in `try/except AttributeError`.

**Concepts learned:**
- Exceptions belong around *plausible* failure points.
- The OOP exercises used `try/except AttributeError` as guards for invalid attribute access — exactly where `AttributeError` actually comes from.

**Pros:**
- Prevents a single bad attribute access from crashing the demo script.

**Cons/drawbacks:**
- Guard calls that cannot fail add noise.
- In production, exceptions should be raised at the source, not swallowed in demos.

**Errors encountered & causes:**
- AttributeError firing on invalid method access → the reason the `try/except` exists.

**Use cases:**
- Learning demonstrations, not production code.

**Usage:**
- For real code: raise typed exceptions; let callers handle them. For demos: `try/except AttributeError` is fine.

--- 

**Quick reference — all OOP files**
| File | What it shows |
|---|---|
| Single_inheritance.py | One parent → one child |
| Multiple_inheritance.py | `Son(Mother, Father)` |
| MultiLevel_inheritance.py | GrandFather → Father → Son |
| Hierarchical_inheritance.py | One `Father`, two children |
| Hybrid_inheritance.py | Mix of multiple + multilevel |
| Encapsulation.py | Public, `_protected`, `__private` name-mangling |

**Status:** 6 runnable files, one per topic.
