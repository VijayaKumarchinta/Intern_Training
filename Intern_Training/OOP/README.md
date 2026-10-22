# OOP Concepts — Intern Training

**Source:** `OOP/README.md`, `OOP/*.py` (Single, Multiple, MultiLevel, Hierarchical, Hybrid inheritance + Encapsulation)

> Six small Python files — one for each topic the training asked for on day one: five inheritance types plus encapsulation.

| File | What it shows |
|---|---|
| `Single_inheritance.py` | `Son` inherits from `Father` and reuses `fun1()` |
| `Multiple_inheritance.py` | `Son(Mother, Father)` — two parents, one child |
| `MultiLevel_inheritance.py` | GrandFather → Father → Son, three levels deep |
| `Hierarchical_inheritance.py` | Two children sharing one `Father` |
| `Hybrid_inheritance.py` | A mix: multiple + multilevel in one tree |
| `Encapsulation.py` | Public, protected (`_Code`), and private (`__battery_health`) members |

---

## 1. Why everything is wrapped in try/except

The instruction was "use an exception in every example", so each file ends with something like:

```python
try:
    obj.fun1()
    obj.fun2()
except AttributeError as e:
    print("Error:", e)
```

In these examples the calls normally succeed — the try/except is there to show how to guard attribute access. To actually see it fire, call a method that does not exist (e.g., `obj.fun3()` in `Single_inheritance.py`) and watch the `AttributeError` get caught instead of crashing the script.

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

## 2. One thing worth remembering

In `Encapsulation.py` the private attribute `__battery_health` gets **name-mangled** to `_Smartphone__battery_health`. It is not truly invisible — it just can't be reached by its original name from outside.

Python's "private" is a **convention, not a wall**, and it took a while to accept that.

**Pros:**
- Restricts accidental access from outside.
- Name-mangling prevents accidental name clashes in subclasses.

**Cons/drawbacks:**
- Name-mangling is **not true privacy** — `_Smartphone__battery_health` is reachable.

**Errors encountered & causes:**
- Assuming `__private` is invisible → it is reachable via `_ClassName__private`.

**Use cases:**
- Teaching access control in Python.
- Signalling internal APIs with `_`.

**Usage:**
- Use `_` for "internal / protected by convention".
- Do **not** rely on name-mangling for security; it's only name-clash prevention.

---

## 3. Quick reference — all OOP files

| File | What it shows |
|---|---|
| Single_inheritance.py | One parent → one child |
| Multiple_inheritance.py | `Son(Mother, Father)` |
| MultiLevel_inheritance.py | GrandFather → Father → Son |
| Hierarchical_inheritance.py | One `Father`, two children |
| Hybrid_inheritance.py | Mix of multiple + multilevel |
| Encapsulation.py | Public, `_protected`, `__private` name-mangling |

**Status:** 6 runnable files, one per topic. Run each with `python <file>.py`.
