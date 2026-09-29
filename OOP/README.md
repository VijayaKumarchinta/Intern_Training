# OOP Practice

Six small Python files — one for each topic that was asked for on day one of
training: single, multiple, multilevel, hierarchical and hybrid inheritance,
plus encapsulation.

Every file runs on its own: `python Single_inheritance.py` and so on.

## The files

| File | What it shows |
|---|---|
| [Single_inheritance.py](Single_inheritance.py) | `Son` inherits from `Father` and reuses `fun1()` |
| [Multiple_inheritance.py](Multiple_inheritance.py) | `Son(Mother, Father)` — two parents, one child |
| [MultiLevel_inheritance.py](MultiLevel_inheritance.py) | GrandFather → Father → Son, three levels deep |
| [Hierarchical_inheritance.py](Hierarchical_inheritance.py) | Two children sharing one `Father` |
| [Hybrid_inheritance.py](Hybrid_inheritance.py) | A mix: multiple + multilevel in one tree |
| [Encapsulation.py](Encapsulation.py) | Public, protected (`_Code`) and private (`__battery_health`) members |

## Why everything is wrapped in try/except

The instruction was "use an exception in every example", so each file ends with
something like this:

```python
try:
    obj.fun1()
    obj.fun2()
except AttributeError as e:
    print("Error:", e)
```

In these examples the calls normally succeed — the try/except is there to show
how to guard attribute access. To actually see it fire, call a method that does
not exist (try `obj.fun3()` in Single_inheritance.py) and watch the
`AttributeError` get caught instead of crashing the script.

## One thing worth remembering

In `Encapsulation.py` the private attribute `__battery_health` gets
name-mangled to `_Smartphone__battery_health`. It is not truly invisible — it
just can't be reached by its original name from outside. Python's "private" is
a convention, not a wall, and it took a while to accept that.

---
Back to the [repository guide](../README.md).
