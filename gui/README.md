# 🖥️ TRTS: The Race Timing Solution — GUI (v1.1)

**Professional Race Timing and Results · A TRMS: The Race Management Solution Suite Component**

The TRTS GUI is a polished, libadwaita-themed GTK4 app for timing **Cross Country** and **Road Races** with the same databases and authentication used by the console edition. It auto-detects whether you’re running **Standalone** or **Integrated With TRMS**, and adjusts paths accordingly.

---

## 🚀 What’s New in v1.1

- **TRMS parity & theme:** UI matches the TRMS Launcher look/spacing/typography.
- **Right‑aligned dual‑line header:**  
  Line 1: “Running Standalone” or “Integrated With TRMS”  
  Line 2: current database (or “No database loaded”).
- **First‑run admin setup:** bcrypt‑secured credential dialog appears **before** the main window if `config.db` is missing.
- **Content‑sized dialogs:** Race type picker, new‑DB details, file pickers, and the CSV import success dialog are tightly sized (no extra vertical space).
- **Safer buttons:** **Individual Results** stays disabled until results exist; **Dynamic Results** adapts to race type.
- **Smart integration paths:** Uses TRDS directories automatically when integrated; uses local `data/` otherwise.
- **Sturdy startup:** Clear DEBUG breadcrumbs; Wayland‑first but **X11 compatible**, with a GTK‑only fallback (`TRTS_FORCE_GTK=1`).

---

## 🗺️ Modes & Directories

### Integrated With TRMS (auto‑detected)
```
TRMS: The Race Management Solution/
└── TRDS: The Race Data Solution/
    ├── config/config.db            # bcrypt admin
    └── databases/
        ├── imports/               # primary CSV location
        ├── sqlite3/               # *.db race databases
        └── mysql/                 # future MariaDB integration
```

### Standalone
```
TRTS-Directory/
├── gui/race_timing_gui.py
└── data/
    ├── config.db
    ├── *.csv
    └── *.db
```

---

## 🗃️ Database Naming

```
YYYYMMDD-<race#>-<type>-<Race_Name>.db
# Examples:
20251007-01-cc-County_Championship.db
20251007-02-rr-City_5K.db
20251007-03-tri-Lakes_Tri.db     # triathlon framework (UI shown, logic later)
```
- `<type>` is `cc` (cross country), `rr` (road race), or `tri` (triathlon).
- Race **number** is 2‑digit (01, 02, …).

---

## 📦 Requirements

- **Python** 3.10+  
- **GTK4** + PyGObject (`python3-gi`, `gir1.2-gtk-4.0`)  
- **libadwaita** recommended (falls back to GTK automatically)  
- **bcrypt** (`pip install bcrypt`) for admin setup

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
pip install bcrypt
```

---

## ▶️ Run

```bash
python3 "TRTS: The Race Timing Solution/gui/race_timing_gui.py"
# If libadwaita misbehaves, force GTK fallback:
TRTS_FORCE_GTK=1 python3 "TRTS: The Race Timing Solution/gui/race_timing_gui.py"
```
First run shows the **Admin Setup** window (bcrypt). After saving, the main window opens.

---

## 🖱️ Typical Workflow

1. **Create New Database**
   - Choose **Cross Country** or **Road Race** (Triathlon is shown but disabled for now).
   - Enter **Race Number** (e.g., `01`) and **Race Name** (e.g., `County_Meet`).
   - DB saved to `TRDS/databases/sqlite3/` (integrated) or `data/` (standalone).
2. **Load Runners from CSV**
   - CSV formats:
     - Cross Country: `bib,name,team,age,grade,rfid`
     - Road Race:     `bib,name,dob,rfid` (age auto‑calculated)
   - The CSV picker starts at `TRDS/databases/imports/` when integrated.
3. **Start the Race**
   - Big live clock; enter bib + `Enter` to record a finish; `exit` to stop.
4. **Results**
   - **Dynamic Results**: Team results (XC) or Age‑group results (Road).
   - **Individual Results**: Enabled automatically after first finisher.
   - Results open in themed text windows with **Copy** to clipboard.

---

## 🧰 Troubleshooting

- **No window / blank:** run with `PYTHONUNBUFFERED=1` to see DEBUG lines.  
- **GI import errors:** ensure `python3-gi` and GTK4 packages are installed.  
- **Wayland quirks:** try `TRTS_FORCE_GTK=1` for the GTK fallback.  
- **CSV import:** verify exact columns and UTF‑8 encoding.

---

## 📄 License
MIT

---

## 🙋 Support
Use the in‑app **Instructions** and **Environment…** (menu) for quick checks, or open an issue with your platform details and startup DEBUG logs.
