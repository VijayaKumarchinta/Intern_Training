# Linux and Unix Basics Concepts — Intern Training

**Source:** `Linux/README.md`, `Linux/Learning_linux.md`

---

## 1. What was practiced

Commands covered:

```text
pwd   ls     cd     mkdir   touch
cp    mv     rm     cat     less
head  tail   grep   find    wc
sort  uniq   explorer.exe .
```

**Concepts learned:**
- Navigation
- Create / copy / move
- Read files
- Search text/files
- Inspect command-line output

**Why this matters for application-side IIoT:**
- Linux is common for servers, gateways, containers, and edge systems.
- The goal is not to master system administration yet, but to be comfortable moving around the file system, reading logs/files, finding files, and running commands.

**Pros:**
- A universal skill for servers, gateways, containers, and edge systems.
- One consistent way to inspect logs, find files, and process data.

**Cons/drawbacks:**
- Only a foundation; deep system administration needs more study.
- Windows equivalents exist but differ in semantics (cmd vs PowerShell).

**Errors encountered & causes:**
- N/A here (practiced skills, not project code).

**Use cases:**
- Day-to-day sysadmin, troubleshooting, log inspection, running IIoT daemons on Linux.

**Usage:**
- Learn the `navigation → create/copy/move → read → search → inspect` flow; use `grep` for content, `find` for files, `wc` for counts, `sort`/`uniq` for analysis.

---

## 2. Commands of Linux

| Command | What it does |
|---|---|
| `pwd` | shows the directory we are in |
| `ls` | list of files in directory |
| `cd` | change directory |
| `mkdir` | create directories |
| `touch` | create a new file |
| `cp` | copy the file |
| `mv` | move files |
| `rm` | delete the file |
| `cat` | display the file |
| `less` | read the file |
| `head` | display first lines |
| `tail` | display last lines |
| `grep` | search text |
| `find` | find files |
| `wc` | count lines/words |
| `sort` | sort data |
| `uniq` | remove duplicates |
| `explorer.exe .` | open the file location in explorer |

**Pros:**
- Daily productivity for terminal work.

**Cons/drawbacks:**
- Each has subtle flags; `grep`/`find` need practice.

**Errors encountered & causes:**
- N/A here (practiced commands).

**Use cases:**
- Inspect logs, find files, count lines, sort/uniq data.

**Usage:**
- `grep "ERROR" log.txt`, `find . -name "*.log"`, `tail -f log.txt`, `wc -l log.txt`.

---

## 3. `explorer.exe .`

**What:** Helps to open the file location in explorer.

**Pros:**
- Quickly visualises files from the terminal.

**Cons/drawbacks:**
- Windows-only; not available on Linux.

**Use cases:**
- Quick file preview on Windows.

**Usage:**
- Run `explorer.exe .` from a Windows terminal.

---

## 4. Dealing with the computer through a terminal

**What:** How to communicate with your computer through a command line.

- **Command prompt** — built-in tool to communicate with our computer.
- **PowerShell** — more advanced cmd-line tool for automation and scripting.
- **Windows** — open cmd prompt, PowerShell within a single window.

We use them for troubleshooting, performing tasks quickly, and accessing advanced tools/system recovery. Activate cmd prompt via the **run** dialog box. For changes, open the terminal in **admin mode**.

- `powercfg/batteryreport` — check battery health.
- `sfc/scannow` — scan Windows and find errors.
- `DISM/RestoreHealth` — repairs Windows system image.

**Pros:**
- Fast troubleshooting and advanced tooling.

**Cons/drawbacks:**
- Requires admin mode for system changes.
- Admin usage carries risk; only run trusted commands.

**Errors encountered & causes:**
- N/A here (learning notes).

**Use cases:**
- System recovery, battery reports, security scans.

**Usage:**
- `powercfg /batteryreport`, `sfc /scannow`, `DISM /Online /Cleanup-Image /RestoreHealth`.

---

## 5. Unix — the bigger picture

**What:** A multi-user OS where it allows multiple users to work on the same machine and run different programs at once.

**Pros:**
- Multi-user, multi-programming; the foundation of all servers and cloud infrastructure.

**Cons/drawbacks:**
- Different tooling conventions from Windows.

**Errors encountered & causes:**
- N/A here (conceptual).

**Use cases:**
- Servers, gateways, containers, edge systems — the runtime of IIoT.

**Usage:**
- Write scripts that are portable across Unix-like systems.

---

**Quick reference — all Linux files**
| File | Role |
|---|---|
| README.md | Command-line learning notes |
| Learning_linux.md | Additional Linux learning notes |

**Status:** Command-line notes + practical skills, runnable standalone.
