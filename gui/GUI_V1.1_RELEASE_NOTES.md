# 🎉 TRTS GUI — Version 1.1 Release Notes
**Date:** August 12, 2025

## 🚀 Major Release: Themed UI, TRMS Awareness, and Production Polish
TRTS **GUI v1.1** brings a fully themed, libadwaita‑style interface that matches the **TRMS Launcher** and a smarter runtime that auto‑detects whether you’re running **Standalone** or **Integrated With TRMS**. This release focuses on **visual parity**, **tight dialog sizing**, **safer actions**, and **clear environment signaling**—all while maintaining full backwards compatibility with existing TRTS databases.

> These notes complement the Console v1.1 release (environment detection, directory conventions, and security model). fileciteturn8file0

---

## 🧠 Integration & Environment Intelligence
- **Automatic mode detection**: Shows **“Running Standalone”** or **“Integrated With TRMS”** in the header, right‑aligned above the current database line.
- **TRMS‑aware paths (Integrated)**  
  - `TRDS/config/config.db` — bcrypt admin credentials  
  - `TRDS/databases/imports/` — primary CSV import location  
  - `TRDS/databases/sqlite3/` — SQLite race databases  
  - `TRDS/databases/mysql/` — reserved for future MariaDB integration  
- **Standalone paths** fall back to local `./data/` (auto‑created on first run).

**Directory maps**

```text
TRMS: The Race Management Solution/
├── TRTS: The Race Timing Solution/
│   └── gui/race_timing_gui.py
└── TRDS: The Race Data Solution/
    ├── config/
    │   └── config.db
    └── databases/
        ├── imports/     # CSV intake
        ├── sqlite3/     # *.db output
        └── mysql/       # future
```

```text
Standalone/
├── gui/race_timing_gui.py
└── data/
    ├── config.db
    ├── *.csv
    └── *.db
```

---

## 🖥️ UI & Theming
- **Pixel‑parity with TRMS Launcher**: colors, spacing, typography (GTK4 + libadwaita).  
- **Header**: two right‑aligned status lines (no separators):  
  1) **Running Standalone / Integrated With TRMS**  
  2) **Database name / No database loaded**
- **Stopwatch iconography** applied across the app branding (where supported by the icon theme / search path).
- **Unified menu**: *About → Environment…* shows GTK/libadwaita versions, session type (Wayland/X11), and detected paths.

---

## 📋 Dialogs & Layout (Tightened)
- All task dialogs are **content‑sized** (no excess vertical whitespace):  
  - **Select Race Type** (Cross Country / Road Race — Triathlon listed but disabled)  
  - **Create New Database** (race number + race name)  
  - **Load Runners from CSV** (themed file picker)  
  - **Load Existing Database** (themed file picker)  
  - **CSV Import Success** (compact message window)  
- The app ensures windows open **only as big as necessary** for the controls shown.

---

## 🗃️ Databases & Types
- **Active backend**: **SQLite3** (unchanged).  
- **MariaDB option present but disabled** in the GUI (logic reserved for future TRDS‑backed release).  
- **File naming** (unchanged, now enforced consistently in GUI flows):  
  ```
  YYYYMMDD-<race#>-<type>-<Race_Name>.db
  # type = cc (Cross Country), rr (Road Race), tri (Triathlon framework)
  # race# = 2 digits (01, 02, …)
  ```

---

## 🏁 Timing & Results UX
- **Start the Race**: big live clock, bib entry, incremental recording.
- **Dynamic Results** button auto‑adapts:  
  - **Cross Country** → Team Results  
  - **Road Race** → Age‑Group Results
- **Individual Results** button is **auto‑disabled** until the database actually has recorded results.
- **Copy to Clipboard** is available in the console pane and results/information windows.

---

## 🔒 First‑Run Admin Setup (GUI Flow)
- If `config.db` is missing, the **Admin Setup** dialog appears **before** the main window.  
- **bcrypt** is required for password hashing (same security model as the Console).

---

## 🧱 Stability & Compatibility
- Hardened **GApplication** startup chain; explicit base class chaining prevents libadwaita/GTK init issues.
- Wayland‑first; **X11 compatible**. **GTK‑only fallback** is available via `TRTS_FORCE_GTK=1`.
- Fully **backwards compatible** with existing TRTS databases; GUI creates/updates tables as needed.

---

## 🧑‍💻 Developer Notes
- Themed widgets prefer **libadwaita**; when not available, the app falls back cleanly to GTK‑only with consistent visuals.
- The icon theme search path includes common `icons/` locations under the TRMS tree for the stopwatch asset.
- File pickers use modern GTK widgets with filters for `*.db` and `*.csv` and open in Integrated/Standalone default directories automatically.

---

## ⚠️ Known Limits
- **Triathlon** listed in the UI but intentionally **disabled** (framework only; multi‑split logic arrives in a later release).  
- **MariaDB** is **visible but disabled**; SQLite3 remains the active backend.

---

## 🧪 Quick Start
```bash
# Normal launch
python3 "TRTS: The Race Timing Solution/gui/race_timing_gui.py"

# If libadwaita misbehaves on your distro build:
TRTS_FORCE_GTK=1 python3 "TRTS: The Race Timing Solution/gui/race_timing_gui.py"
```

---

## 📣 Summary
v1.1 delivers a **production‑polished**, **TRMS‑aware** GUI with a refined theme, compact dialogs, safer defaults, and clear environment signaling—ready for timing meets from local 5Ks to district championships.
