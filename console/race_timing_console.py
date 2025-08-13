#!/usr/bin/env python3
"""
race_timing_console.py - TRTS Console Updated for TRMS Integration
Author: TJ Tryon
Date: August 12, 2025
Project: The Race Timing Solution for Cross Country and Road Races (TRTS)
Version: 1.1.0 - Enhanced TRMS Integration & Professional Race Management

🎉 MAJOR RELEASE: This version introduces intelligent environment detection that automatically 
configures for standalone or TRMS-integrated deployment, comprehensive admin authentication 
with bcrypt security, and enhanced file organization supporting primary CSV imports from 
TRDS/databases/imports/ with fallback locations. Features expanded race type support 
(Cross Country team scoring, Road Race age groups, Triathlon framework), professional-grade 
live timing engine with real-time status monitoring, and sophisticated results processing 
with championship-level algorithms. Includes automatic migration tools for seamless upgrades 
from previous TRTS installations while maintaining full backward compatibility. The modular 
architecture scales from local 5Ks to regional championships with enterprise-grade reliability.


Key updates for TRMS integration:
- Intelligent detection: standalone vs TRMS integrated
- Database configuration options (SQLite3/MariaDB)
- Enhanced race type selection (including Triathlon)
- Migration support for existing installations
- Maintains backward compatibility

🎽 This program helps you time cross country and road races! 🏃‍♀️🏃‍♂️
"""

# 📦 Import statements
import sqlite3
import os
import datetime
import csv
import bcrypt
import getpass
import time
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, Any, Tuple, List
import json

# Try to import mysql.connector for future MariaDB support
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# Try to import playsound for finish beep
try:
    from playsound import playsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# 🗺️ INTELLIGENT PATH DETECTION (Standalone vs TRMS Integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TRTSPathManager:
    """Intelligent path management - standalone TRTS vs TRMS integrated."""
    
    def __init__(self):
        self.is_trms_integrated = False
        self.trms_root = None
        self.data_dir = None
        self.config_db = None
        
        self._detect_environment()
        self._setup_paths()
    
    def _detect_environment(self):
        """Detect if we're running standalone or as part of TRMS."""
        # Start from current working directory
        current = Path.cwd()
        
        # Search up the directory tree for TRMS indicators
        for _ in range(10):  # Prevent infinite loops
            if self._is_trms_root(current):
                self.is_trms_integrated = True
                self.trms_root = current
                return
            
            if current.parent == current:  # Reached filesystem root
                break
            current = current.parent
        
        # No TRMS detected - running standalone
        self.is_trms_integrated = False
    
    def _is_trms_root(self, path):
        """Check if a path is a TRMS root directory."""
        # Must have TRDS directory to be considered TRMS integrated
        trds_dir = path / "TRDS: The Race Data Solution"
        if not trds_dir.exists():
            return False
        
        # Look for other TRMS components (at least one should exist)
        trms_components = [
            "TRTS: The Race Timing Solution",
            "TRRS: The Race Registration Solution", 
            "TRWS: The Race Web Solution"
        ]
        
        return any((path / component).exists() for component in trms_components)
    
    def _setup_paths(self):
        """Setup appropriate paths based on detected environment."""
        if self.is_trms_integrated:
            # Use TRMS integrated structure
            trds_dir = self.trms_root / "TRDS: The Race Data Solution"
            self.data_dir = trds_dir / "databases" / "sqlite3"
            self.config_db = trds_dir / "config" / "config.db"
            
            # Ensure TRMS directories exist
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.config_db.parent.mkdir(parents=True, exist_ok=True)
            
            # Create imports directory for CSV files
            imports_dir = trds_dir / "databases" / "imports"
            imports_dir.mkdir(parents=True, exist_ok=True)
            
        else:
            # Use standalone/original structure
            current_dir = Path.cwd()
            self.data_dir = current_dir / "data"
            self.config_db = self.data_dir / "config.db"
            
            # Ensure local directories exist
            self.data_dir.mkdir(exist_ok=True)
    
    def get_status_info(self):
        """Get status information for display."""
        return {
            'mode': 'TRMS Integrated' if self.is_trms_integrated else 'Standalone',
            'data_location': str(self.data_dir),
            'config_location': str(self.config_db),
            'trms_root': str(self.trms_root) if self.trms_root else 'N/A'
        }

# Initialize path manager
path_manager = TRTSPathManager()

# ═══════════════════════════════════════════════════════════════════════════════
# 🗄️ DATABASE CONFIGURATION ENUMS AND CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseType(Enum):
    """Database type enumeration."""
    SQLITE3 = "sqlite3"
    MARIADB = "mariadb"

class DatabaseLocation(Enum):
    """Database location enumeration."""
    LOCAL = "local"
    VIRTUAL_ENV = "virtual_environment"
    DOCKER = "docker"

class RaceType(Enum):
    """Race type enumeration with availability status."""
    CROSS_COUNTRY = ("cross_country", "Cross Country", True)
    ROAD_RACE = ("road_race", "Road Race", True) 
    TRIATHLON = ("triathlon", "Triathlon", False)  # Disabled for now
    
    def __new__(cls, value, display_name, enabled):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
        obj.enabled = enabled
        return obj

# ═══════════════════════════════════════════════════════════════════════════════
# 🔐 ADMIN AUTHENTICATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_config_db():
    """Enhanced admin setup with path detection."""
    config_db_path = path_manager.config_db
    
    if not config_db_path.exists():
        status = path_manager.get_status_info()
        
        print("\n" + "="*70)
        print("🔐 TRTS Admin Setup - First Time Configuration")
        print("="*70)
        print(f"Environment: {status['mode']}")
        print(f"Data Location: {status['data_location']}")
        if path_manager.is_trms_integrated:
            print(f"TRMS Root: {status['trms_root']}")
        print("")
        print("Creating admin credentials for race management...")
        print("")
        
        conn = sqlite3.connect(str(config_db_path))
        c = conn.cursor()
        
        c.execute('''CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash BLOB NOT NULL,
                        created_at TEXT NOT NULL)''')
        
        # Get admin credentials
        while True:
            username = input("Enter admin username: ").strip()
            if username:
                break
            print("Username cannot be empty.")
        
        while True:
            password = getpass.getpass("Enter admin password: ").strip()
            if len(password) >= 6:
                confirm = getpass.getpass("Confirm admin password: ").strip()
                if password == confirm:
                    break
                else:
                    print("Passwords do not match. Please try again.")
            else:
                print("Password must be at least 6 characters long.")
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.datetime.now().isoformat()
        
        c.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)', 
                  (username, password_hash, created_at))
        conn.commit()
        conn.close()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"🗂️ Configuration saved to: {config_db_path}")
        print("")

def verify_admin():
    """Verify admin credentials."""
    config_db_path = path_manager.config_db
    
    if not config_db_path.exists():
        print("❌ No admin configuration found. Setting up now...")
        initialize_config_db()
        return True
    
    print("\n🔐 Admin Authentication Required")
    print("="*40)
    
    for attempt in range(3):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        conn = sqlite3.connect(str(config_db_path))
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
            print("✅ Authentication successful!")
            return True
        
        print(f"❌ Invalid credentials. {2-attempt} attempts remaining.")
    
    print("❌ Authentication failed. Exiting.")
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# 🌍 GLOBAL VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

DB_FILENAME = ""
race_started = False
race_stopped = False
race_start_time = None
RACE_TYPE = ""

# Database configuration
DB_TYPE = "sqlite3"  # sqlite3 or mariadb
DB_LOCATION = "local"  # local, virtual_environment, docker
MARIADB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'username': 'root',
    'password': '',
    'database': 'trts_races'
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🖥️ ENHANCED CONSOLE APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def show_startup_banner():
    """Display enhanced startup banner with environment detection."""
    status = path_manager.get_status_info()
    
    print("\n" + "="*80)
    print("⏱️  TRTS: The Race Timing Solution")
    print("👤 Author: TJ Tryon")
    print("📅 Created: 2025")
    print("🏷️  Version: 2.0.0")
    print("="*80)
    print("")
    print("📊 CURRENT STATUS:")
    print(f"   🔧 Environment: {status['mode']}")
    print(f"   📁 Data Location: {status['data_location']}")
    if path_manager.is_trms_integrated:
        print(f"   🏗️  TRMS Root: {status['trms_root']}")
    print(f"   🗄️  Database Type: {DB_TYPE.upper()}")
    print(f"   📍 Database Location: {DB_LOCATION.title()}")
    print(f"   📂 Current Race DB: {Path(DB_FILENAME).name if DB_FILENAME else '[None Loaded]'}")
    print(f"   🏃 Race Type: {RACE_TYPE.replace('_', ' ').title() if RACE_TYPE else '[None]'}")
    print("")

def configure_database():
    """Interactive database configuration with enhanced options."""
    global DB_TYPE, DB_LOCATION, MARIADB_CONFIG
    
    print("\n" + "="*60)
    print("🗄️  Database Configuration")
    print("="*60)
    
    # Database Type Selection
    print("\nSelect Database Type:")
    print("1) SQLite3 (Local file-based database)")
    print("2) MariaDB/MySQL (Server-based database) [COMING SOON]")
    
    while True:
        choice = input("\nDatabase Type [1]: ").strip() or "1"
        if choice == "1":
            DB_TYPE = "sqlite3"
            break
        elif choice == "2":
            print("⚠️  MariaDB/MySQL integration is coming soon in TRMS v2.1!")
            print("Using SQLite3 for now...")
            DB_TYPE = "sqlite3"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")
    
    # Database Location Selection
    print(f"\nSelected: {DB_TYPE.upper()}")
    print("\nSelect Database Location:")
    print("1) Local (Current system)")
    print("2) Virtual Environment [COMING SOON]")
    print("3) Docker Container [COMING SOON]")
    
    while True:
        choice = input("\nDatabase Location [1]: ").strip() or "1"
        if choice == "1":
            DB_LOCATION = "local"
            break
        elif choice in ["2", "3"]:
            loc_name = "Virtual Environment" if choice == "2" else "Docker Container"
            print(f"⚠️  {loc_name} support is coming soon!")
            print("Using Local for now...")
            DB_LOCATION = "local"
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    # Future MariaDB configuration
    if DB_TYPE == "mariadb" and DB_LOCATION != "local":
        print(f"\nMariaDB Configuration for {DB_LOCATION}:")
        MARIADB_CONFIG['host'] = input("Enter MariaDB Host/IP [localhost]: ").strip() or "localhost"
        
        port_str = input("Enter MariaDB Port [3306]: ").strip() or "3306"
        try:
            MARIADB_CONFIG['port'] = int(port_str)
        except ValueError:
            MARIADB_CONFIG['port'] = 3306
            
        MARIADB_CONFIG['username'] = input("Enter MariaDB Username [root]: ").strip() or "root"
        MARIADB_CONFIG['password'] = getpass.getpass("Enter MariaDB Password: ").strip()
        MARIADB_CONFIG['database'] = input("Enter Database Name [trts_races]: ").strip() or "trts_races"
    
    # Test connection
    test_database_connection()
    
    print("\n✅ Database configuration completed!")
    input("Press Enter to continue...")

def test_database_connection():
    """Test database connection with detailed feedback."""
    print(f"\n🔄 Testing {DB_TYPE.upper()} connection...")
    
    if DB_TYPE == "sqlite3":
        try:
            # Test SQLite connectivity
            test_db = path_manager.data_dir / "connection_test.db"
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            if test_db.exists():
                test_db.unlink()  # Clean up
            
            print("✅ SQLite3 connection successful!")
            print(f"📁 Database directory: {path_manager.data_dir}")
            return True
        except Exception as e:
            print(f"❌ SQLite3 connection failed: {e}")
            return False
    
    elif DB_TYPE == "mariadb" and MYSQL_AVAILABLE:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=MARIADB_CONFIG['host'],
                port=MARIADB_CONFIG['port'],
                user=MARIADB_CONFIG['username'],
                password=MARIADB_CONFIG['password'],
                connection_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            print(f"✅ MariaDB connection successful!")
            print(f"🌐 Connected to: {MARIADB_CONFIG['host']}:{MARIADB_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ MariaDB connection failed: {e}")
            return False
    
    return False

def create_new_database():
    """Enhanced database creation with triathlon support."""
    global DB_FILENAME, RACE_TYPE
    
    print("\n" + "="*60)
    print("🆕 Create New Race Database")
    print("="*60)
    
    print("Select Race Type:")
    for i, race_type in enumerate(RaceType, 1):
        status = "" if race_type.enabled else " [COMING SOON]"
        print(f"{i}) {race_type.display_name}{status}")
    
    while True:
        choice = input(f"\nRace Type [1]: ").strip() or "1"
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(RaceType):
                selected_race = list(RaceType)[choice_num - 1]
                if selected_race.enabled:
                    RACE_TYPE = selected_race.value
                    break
                else:
                    print(f"⚠️  {selected_race.display_name} support is coming soon!")
                    print("Please choose Cross Country or Road Race for now.")
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    # Get race details with enhanced prompting
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    if RACE_TYPE == "triathlon":
        # For triathlon, use "race number" terminology (same as others)
        while True:
            number = input("Enter race number (e.g., 1): ").strip().zfill(2)
            if number.isdigit() and number != "00":
                break
            print("❌ Please enter a valid race number.")
        
        # For triathlon, get properly formatted race name
        race_name_input = input("Enter race name (e.g., 'Iron Man Triathlon'): ").strip()
        if not race_name_input:
            print("❌ Race name cannot be empty.")
            return
        
        # Convert to underscore format for filename
        race_name_formatted = race_name_input.replace(" ", "_")
        
        # Triathlon filename format: YYYYMMDD-##-tri-Proper_Race_Name.db
        db_filename = f"{today}-{number}-tri-{race_name_formatted}.db"
        
    else:
        # For cross country and road race, use "race number" terminology
        while True:
            number = input("Enter race number (e.g., 1): ").strip().zfill(2)
            if number.isdigit() and number != "00":
                break
            print("❌ Please enter a valid race number.")
        
        # For CC/RR, convert to underscore format (existing behavior)
        name = input("Enter race name: ").strip().replace(" ", "_")
        suffix = {"cross_country": "cc", "road_race": "rr"}[RACE_TYPE]
        db_filename = f"{today}-{number}-{suffix}-{name}.db"
    
    DB_FILENAME = str(path_manager.data_dir / db_filename)
    
    # Show preview with correct terminology
    print(f"\n📋 Database Preview:")
    print(f"   📄 Filename: {db_filename}")
    print(f"   📍 Location: {path_manager.data_dir}")
    print(f"   🏃 Race Type: {RACE_TYPE.replace('_', ' ').title()}")
    
    if RACE_TYPE == "triathlon":
        print(f"   🏊‍♀️🚴‍♂️🏃‍♂️ Race Number: {number}")
        print(f"   🏁 Race Name: {race_name_input}")
        print(f"   📄 Filename: {race_name_formatted}")
        print("   📊 Format: YYYYMMDD-##-tri-Proper_Race_Name.db")
    else:
        print(f"   🔢 Race Number: {number}")
        print("   📊 Format: YYYYMMDD-##-{cc|rr}-race_name.db")
    
    confirm = input("\nCreate this database? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("❌ Database creation cancelled.")
        return
    
    # Create database structure
    init_db(new_db=True)
    
    print(f"\n✅ Database created successfully!")
    print(f"📂 Path: {DB_FILENAME}")
    input("Press Enter to continue...")

def load_existing_database():
    """Load existing database with migration support."""
    global DB_FILENAME, RACE_TYPE
    
    print("\n" + "="*60)
    print("📂 Load Existing Race Database")
    print("="*60)
    
    # Look for databases in current structure
    db_files = list(path_manager.data_dir.glob("*.db"))
    
    # Check for old data that needs migration (only if TRMS integrated)
    if path_manager.is_trms_integrated:
        old_data_dir = Path("data")
        if old_data_dir.exists():
            old_db_files = [f for f in old_data_dir.glob("*.db") if f.name != "config.db"]
            if old_db_files:
                print("📋 Found databases in old location that can be migrated:")
                for db_file in old_db_files:
                    print(f"   📁 {db_file.name}")
                
                migrate = input("\nMigrate old databases to TRMS structure? [y/N]: ").strip().lower()
                if migrate == 'y':
                    migrate_old_databases(old_db_files)
                    db_files = list(path_manager.data_dir.glob("*.db"))
    
    if not db_files:
        print("❌ No race databases found.")
        print(f"📍 Looking in: {path_manager.data_dir}")
        input("Press Enter to continue...")
        return
    
    print("📋 Available Race Databases:")
    for i, db_file in enumerate(db_files, 1):
        print(f"{i}) {db_file.name}")
    
    while True:
        try:
            choice = int(input(f"\nSelect database [1]: ") or "1")
            if 1 <= choice <= len(db_files):
                DB_FILENAME = str(db_files[choice - 1])
                break
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    # Load race type
    load_race_type()
    
    print(f"✅ Loaded: {Path(DB_FILENAME).name}")
    print(f"🏃 Race Type: {RACE_TYPE.replace('_', ' ').title() if RACE_TYPE else 'Unknown'}")
    input("Press Enter to continue...")

def migrate_old_databases(old_db_files):
    """Migrate databases from old structure to TRMS."""
    print("\n🔄 Migrating databases to TRMS structure...")
    
    for old_db in old_db_files:
        new_path = path_manager.data_dir / old_db.name
        if not new_path.exists():
            old_db.rename(new_path)
            print(f"   ✅ Migrated: {old_db.name}")
    
    print("🎉 Migration completed!")

def show_instructions():
    """Display comprehensive instructions."""
    status = path_manager.get_status_info()
    
    print("\n" + "="*80)
    print("📚 TRTS: The Race Timing Solution - Instructions")
    print("="*80)
    print(f"""
🏁 GETTING STARTED:
   1. Configure your database connection (Option 1 in main menu)
   2. Create a new race database or load an existing one
   3. Import runner data from CSV files  
   4. Start timing your race!

🗄️ DATABASE SETUP:
   • SQLite3: Local file-based storage (recommended for most users)
   • MariaDB: Server-based storage (coming soon for large deployments)
   • Race databases: {status['data_location']}""")

    if path_manager.is_trms_integrated:
        imports_dir = path_manager.trms_root / "TRDS: The Race Data Solution" / "databases" / "imports"
        print(f"   • CSV imports: {imports_dir}")
    
    print(f"""
🏃 RACE TYPES:
   • Cross Country: Team-based scoring with 5 scorers + 2 displacers
   • Road Race: Age group divisions based on runner age
   • Triathlon: Multi-sport timing (coming soon in v2.1)

📊 CSV FILE FORMATS:
   Cross Country: bib, name, team, age, grade, rfid
   Road Race: bib, name, dob, rfid
   Triathlon: bib, name, age_group, rfid (coming soon)
   Example: 101, John Smith, Lincoln High, 16, 11th, RFID123

📁 CSV FILE LOCATIONS:""")
    
    if path_manager.is_trms_integrated:
        imports_dir = path_manager.trms_root / "TRDS: The Race Data Solution" / "databases" / "imports"
        print(f"   • Primary: {imports_dir}")
        print(f"   • Secondary: {status['data_location']}")
        print("   • Convenience: Current directory")
    else:
        print(f"   • Primary: {status['data_location']}")
        print("   • Convenience: Current directory")
    
    print(f"""
📝 DATABASE NAMING CONVENTIONS:
   Cross Country: YYYYMMDD-##-cc-Race_Name.db
   Road Race: YYYYMMDD-##-rr-Race_Name.db  
   Triathlon: YYYYMMDD-##-tri-Proper_Race_Name.db
   Where ## is the race number for the day

⏱️ RACE TIMING:
   • Select "Start Race Timing" from main menu
   • Enter bib numbers as runners finish
   • Type 'exit' to stop timing
   • All times automatically calculated and stored

📈 VIEWING RESULTS:
   • Individual Results: Overall finish order
   • Team Results: Cross country team scoring (low score wins)
   • Age Group Results: Road race divisions by age

🔧 CONFIGURATION:
   • Environment: {status['mode']}
   • Admin database: {status['config_location']}
   • Race databases: {status['data_location']}
   • Settings saved automatically""")

    if path_manager.is_trms_integrated:
        print(f"""
🔗 TRMS INTEGRATION:
   • Part of The Race Management Solution ecosystem
   • Unified data storage with other TRMS components
   • Enhanced migration tools for existing data
   • Centralized configuration management
   • TRMS Root: {status['trms_root']}""")
    
    print(f"""
❓ NEED HELP?
   • All data is automatically backed up
   • Database files can be shared between computers
   • Contact TJ Tryon for technical support
""")
    
    input("Press Enter to return to main menu...")

def main_menu():
    """Enhanced main menu with status display."""
    while True:
        show_startup_banner()
        
        print("MAIN MENU:")
        print("1) 🗄️  Configure Database Connection")
        print("2) 🆕 Create New Race Database")
        print("3) 📂 Load Existing Race Database")
        print("4) 📊 Load Runners from CSV")
        print("5) 👥 View All Runners")
        print("6) 🏁 Start Race Timing")
        print("7) 🏆 Show Individual Results")
        
        if RACE_TYPE == "cross_country":
            print("8) 🏫 Show Team Results")
        elif RACE_TYPE == "road_race":
            print("8) 🎂 Show Age Group Results")
        else:
            print("8) 📊 Show Results [Load race database first]")
        
        print("9) 📚 Instructions")
        print("0) 🚪 Exit")
        
        choice = input("\n🎯 Choose option [0-9]: ").strip()
        
        if choice == '1':
            configure_database()
        elif choice == '2':
            create_new_database()
        elif choice == '3':
            load_existing_database()
        elif choice == '4':
            load_runners_from_csv()
        elif choice == '5':
            show_all_runners()
        elif choice == '6':
            start_race()
        elif choice == '7':
            show_individual_results()
        elif choice == '8':
            if RACE_TYPE == "cross_country":
                show_team_results()
            elif RACE_TYPE == "road_race":
                show_age_group_results()
            else:
                print("❌ Please load a race database first.")
                input("Press Enter to continue...")
        elif choice == '9':
            show_instructions()
        elif choice == '0':
            print("\n👋 Thank you for using TRTS!")
            break
        else:
            print("❌ Invalid choice. Please enter 0-9.")
            input("Press Enter to continue...")

# ═══════════════════════════════════════════════════════════════════════════════
# 🗃️ DATABASE FUNCTIONS (Updated for new structure)
# ═══════════════════════════════════════════════════════════════════════════════

def init_db(new_db=True):
    """Initialize database with new path structure."""
    global DB_FILENAME, RACE_TYPE
    
    if new_db and not DB_FILENAME:
        print("❌ No database filename set.")
        return
    
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()

    if new_db:
        c.execute("CREATE TABLE race_type (type TEXT)")
        c.execute("INSERT INTO race_type (type) VALUES (?)", (RACE_TYPE,))

    # Create race-specific tables
    if RACE_TYPE == "cross_country":
        c.execute('''CREATE TABLE IF NOT EXISTS runners (
                        bib INTEGER PRIMARY KEY,
                        name TEXT,
                        team TEXT,
                        age INTEGER,
                        grade TEXT,
                        rfid TEXT)''')
    elif RACE_TYPE == "road_race":
        c.execute('''CREATE TABLE IF NOT EXISTS runners (
                        bib INTEGER PRIMARY KEY,
                        name TEXT,
                        dob TEXT,
                        age INTEGER,
                        rfid TEXT)''')
    elif RACE_TYPE == "triathlon":
        # Triathlon table structure (for future implementation)
        c.execute('''CREATE TABLE IF NOT EXISTS runners (
                        bib INTEGER PRIMARY KEY,
                        name TEXT,
                        age_group TEXT,
                        swim_time REAL,
                        bike_time REAL,
                        run_time REAL,
                        total_time REAL,
                        rfid TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bib INTEGER,
                    finish_time REAL,
                    race_date TEXT)''')
    
    conn.commit()
    conn.close()

def load_race_type():
    """Load race type from database."""
    global RACE_TYPE
    try:
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        c.execute("SELECT type FROM race_type")
        result = c.fetchone()
        RACE_TYPE = result[0] if result else "unknown"
        conn.close()
    except Exception:
        RACE_TYPE = "unknown"

def load_runners_from_csv():
    """Load runners from CSV with enhanced path support."""
    global DB_FILENAME, RACE_TYPE
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    # Look for CSV files in multiple locations
    csv_files = []
    search_locations = []
    
    # Primary location: TRDS imports directory (if TRMS integrated)
    if path_manager.is_trms_integrated:
        imports_dir = path_manager.trms_root / "TRDS: The Race Data Solution" / "databases" / "imports"
        if imports_dir.exists():
            imports_csv = list(imports_dir.glob("*.csv"))
            csv_files.extend(imports_csv)
            search_locations.append(("TRDS imports/", imports_dir, len(imports_csv)))
    
    # Secondary location: data directory
    data_csv = list(path_manager.data_dir.glob("*.csv"))
    csv_files.extend(data_csv)
    search_locations.append(("data/", path_manager.data_dir, len(data_csv)))
    
    # Tertiary location: current directory for convenience
    current_csv = list(Path(".").glob("*.csv"))
    csv_files.extend(current_csv)
    search_locations.append(("current/", Path("."), len(current_csv)))
    
    if not csv_files:
        print("❌ No CSV files found.")
        print("\n📍 CSV files can be placed in:")
        if path_manager.is_trms_integrated:
            print(f"   • TRDS imports: {path_manager.trms_root / 'TRDS: The Race Data Solution' / 'databases' / 'imports'}")
        print(f"   • Data directory: {path_manager.data_dir}")
        print("   • Current directory (for convenience)")
        input("Press Enter to continue...")
        return
    
    print("📋 Available CSV files:")
    print(f"\n🔍 Searched {len(search_locations)} locations:")
    for location_name, location_path, file_count in search_locations:
        if file_count > 0:
            print(f"   ✅ {location_name} - {file_count} file(s) found")
        else:
            print(f"   📁 {location_name} - empty")
    
    print(f"\n📄 Found {len(csv_files)} CSV files total:")
    for i, csv_file in enumerate(csv_files, 1):
        # Determine which location this file is from
        if path_manager.is_trms_integrated:
            imports_dir = path_manager.trms_root / "TRDS: The Race Data Solution" / "databases" / "imports"
            if str(csv_file).startswith(str(imports_dir)):
                location = "TRDS imports/"
            elif str(csv_file).startswith(str(path_manager.data_dir)):
                location = "data/"
            else:
                location = "current/"
        else:
            if str(csv_file).startswith(str(path_manager.data_dir)):
                location = "data/"
            else:
                location = "current/"
        
        print(f"{i}) {csv_file.name} ({location})")
    
    try:
        choice = int(input(f"\nSelect CSV file [1]: ") or "1")
        if 1 <= choice <= len(csv_files):
            csv_file = csv_files[choice - 1]
            process_csv_file(csv_file)
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Please enter a valid number.")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")

def process_csv_file(csv_file):
    """Process CSV file and load runners into database."""
    global DB_FILENAME, RACE_TYPE
    
    if not DB_FILENAME or not RACE_TYPE:
        print("❌ No database loaded or race type not set.")
        return
    
    print(f"\n📊 Processing CSV file: {csv_file.name}")
    print(f"🏃 Race Type: {RACE_TYPE.replace('_', ' ').title()}")
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            
            # Skip header if present
            first_row = next(csv_reader, None)
            if first_row and not first_row[0].isdigit():
                print("📋 Skipping header row")
            else:
                # Put the row back if it's data
                csv_reader = csv.reader(f)
                f.seek(0)
        
        runners_added = 0
        errors = []
        
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            
            # Skip header if present
            first_row = next(csv_reader, None)
            if first_row and not first_row[0].isdigit():
                pass  # Skip header
            else:
                # Process first row as data
                if first_row:
                    try:
                        process_runner_row(c, first_row, RACE_TYPE)
                        runners_added += 1
                    except Exception as e:
                        errors.append(f"Row 1: {e}")
            
            # Process remaining rows
            for row_num, row in enumerate(csv_reader, start=2):
                if not row or all(cell.strip() == '' for cell in row):
                    continue  # Skip empty rows
                
                try:
                    process_runner_row(c, row, RACE_TYPE)
                    runners_added += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Successfully loaded {runners_added} runners!")
        
        if errors:
            print(f"⚠️  {len(errors)} errors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(errors) > 5:
                print(f"   • ... and {len(errors) - 5} more errors")
    
    except Exception as e:
        print(f"❌ Error processing CSV file: {e}")
    
    input("Press Enter to continue...")

def process_runner_row(cursor, row, race_type):
    """Process a single runner row from CSV."""
    if race_type == "cross_country":
        # Expected format: bib, name, team, age, grade, rfid
        if len(row) < 5:
            raise ValueError(f"Insufficient columns (need at least 5): {row}")
        
        bib = int(row[0].strip())
        name = row[1].strip()
        team = row[2].strip()
        age = int(row[3].strip()) if row[3].strip() else None
        grade = row[4].strip()
        rfid = row[5].strip() if len(row) > 5 else ""
        
        cursor.execute('''INSERT OR REPLACE INTO runners 
                         (bib, name, team, age, grade, rfid) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (bib, name, team, age, grade, rfid))
    
    elif race_type == "road_race":
        # Expected format: bib, name, dob, rfid
        if len(row) < 3:
            raise ValueError(f"Insufficient columns (need at least 3): {row}")
        
        bib = int(row[0].strip())
        name = row[1].strip()
        dob = row[2].strip()
        rfid = row[3].strip() if len(row) > 3 else ""
        
        # Calculate age from date of birth
        age = calculate_age_from_dob(dob) if dob else None
        
        cursor.execute('''INSERT OR REPLACE INTO runners 
                         (bib, name, dob, age, rfid) 
                         VALUES (?, ?, ?, ?, ?)''',
                      (bib, name, dob, age, rfid))
    
    elif race_type == "triathlon":
        # Expected format: bib, name, age_group, rfid
        if len(row) < 3:
            raise ValueError(f"Insufficient columns (need at least 3): {row}")
        
        bib = int(row[0].strip())
        name = row[1].strip()
        age_group = row[2].strip()
        rfid = row[3].strip() if len(row) > 3 else ""
        
        cursor.execute('''INSERT OR REPLACE INTO runners 
                         (bib, name, age_group, rfid) 
                         VALUES (?, ?, ?, ?)''',
                      (bib, name, age_group, rfid))

def calculate_age_from_dob(dob_str):
    """Calculate age from date of birth string."""
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']:
            try:
                birth_date = datetime.datetime.strptime(dob_str, fmt).date()
                today = datetime.date.today()
                age = today.year - birth_date.year
                if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                    age -= 1
                return age
            except ValueError:
                continue
        
        # If no format worked, return None
        return None
    except:
        return None

def show_all_runners():
    """Display all runners in the database."""
    global DB_FILENAME, RACE_TYPE
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    
    c.execute("SELECT * FROM runners ORDER BY bib")
    runners = c.fetchall()
    conn.close()
    
    if not runners:
        print("\n❌ No runners found in database.")
        input("Press Enter to continue...")
        return
    
    print(f"\n📋 ALL RUNNERS ({len(runners)} total)")
    print("="*80)
    
    if RACE_TYPE == "cross_country":
        print(f"{'BIB':<5} {'NAME':<25} {'TEAM':<20} {'AGE':<5} {'GRADE':<8} {'RFID':<10}")
        print("-"*80)
        for runner in runners:
            bib, name, team, age, grade, rfid = runner
            print(f"{bib:<5} {name[:24]:<25} {team[:19]:<20} {age or 'N/A':<5} {grade[:7]:<8} {rfid[:9]:<10}")
    
    elif RACE_TYPE == "road_race":
        print(f"{'BIB':<5} {'NAME':<30} {'DOB':<12} {'AGE':<5} {'RFID':<10}")
        print("-"*70)
        for runner in runners:
            bib, name, dob, age, rfid = runner
            print(f"{bib:<5} {name[:29]:<30} {dob[:11]:<12} {age or 'N/A':<5} {rfid[:9]:<10}")
    
    elif RACE_TYPE == "triathlon":
        print(f"{'BIB':<5} {'NAME':<30} {'AGE GROUP':<12} {'RFID':<10}")
        print("-"*65)
        for runner in runners:
            bib, name, age_group, _, _, _, _, rfid = runner  # Triathlon has more columns
            print(f"{bib:<5} {name[:29]:<30} {age_group[:11]:<12} {rfid[:9]:<10}")
    
    print(f"\nTotal runners: {len(runners)}")
    input("Press Enter to continue...")

def start_race():
    """Start race timing with enhanced features."""
    global race_started, race_stopped, race_start_time, DB_FILENAME
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    # Check if runners are loaded
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM runners")
    runner_count = c.fetchone()[0]
    conn.close()
    
    if runner_count == 0:
        print("❌ No runners loaded. Please load runners from CSV first.")
        input("Press Enter to continue...")
        return
    
    print(f"\n🏁 RACE TIMING STARTED")
    print("="*60)
    print(f"📊 Runners loaded: {runner_count}")
    print(f"🏃 Race Type: {RACE_TYPE.replace('_', ' ').title()}")
    print("")
    print("⏱️  Race timing is now active!")
    print("📝 Enter bib numbers as runners finish")
    print("💡 Type 'exit' to stop timing")
    print("💡 Type 'status' to see race status")
    print("")
    
    race_started = True
    race_stopped = False
    race_start_time = time.time()
    
    finish_count = 0
    
    while not race_stopped:
        try:
            user_input = input("🏃 Bib number: ").strip().lower()
            
            if user_input == 'exit':
                race_stopped = True
                break
            elif user_input == 'status':
                show_race_status(finish_count)
                continue
            elif user_input == '':
                continue
            
            # Try to convert to bib number
            try:
                bib = int(user_input)
            except ValueError:
                print("❌ Invalid bib number. Enter a number or 'exit'.")
                continue
            
            # Record finish time
            finish_time = time.time() - race_start_time
            current_time = datetime.datetime.now().isoformat()
            
            # Verify runner exists
            conn = sqlite3.connect(DB_FILENAME)
            c = conn.cursor()
            c.execute("SELECT name FROM runners WHERE bib = ?", (bib,))
            runner = c.fetchone()
            
            if not runner:
                print(f"⚠️  Warning: Bib {bib} not found in database!")
                confirm = input("Record anyway? [y/N]: ").strip().lower()
                if confirm != 'y':
                    conn.close()
                    continue
                runner_name = "Unknown Runner"
            else:
                runner_name = runner[0]
            
            # Check if already finished
            c.execute("SELECT id FROM results WHERE bib = ?", (bib,))
            if c.fetchone():
                print(f"⚠️  Bib {bib} ({runner_name}) already finished!")
                confirm = input("Update time? [y/N]: ").strip().lower()
                if confirm != 'y':
                    conn.close()
                    continue
                
                # Update existing result
                c.execute("UPDATE results SET finish_time = ?, race_date = ? WHERE bib = ?",
                         (finish_time, current_time, bib))
                action = "Updated"
            else:
                # Insert new result
                c.execute("INSERT INTO results (bib, finish_time, race_date) VALUES (?, ?, ?)",
                         (bib, finish_time, current_time))
                finish_count += 1
                action = "Recorded"
            
            conn.commit()
            conn.close()
            
            # Format time display
            minutes = int(finish_time // 60)
            seconds = int(finish_time % 60)
            milliseconds = int((finish_time % 1) * 1000)
            
            print(f"✅ {action}: Bib {bib} ({runner_name}) - {minutes:02d}:{seconds:02d}.{milliseconds:03d}")
            
            # Play sound if available
            if SOUND_AVAILABLE:
                try:
                    # You can add a beep sound file here
                    pass
                except:
                    pass
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Race timing interrupted!")
            confirm = input("Stop timing? [y/N]: ").strip().lower()
            if confirm == 'y':
                race_stopped = True
            else:
                print("Continuing race timing...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🏁 RACE TIMING STOPPED")
    print(f"📊 Total finishers recorded: {finish_count}")
    print(f"⏱️  Race duration: {format_time(time.time() - race_start_time)}")
    
    race_started = False
    input("Press Enter to continue...")

def show_race_status(finish_count):
    """Show current race status."""
    elapsed = time.time() - race_start_time if race_start_time else 0
    print(f"\n📊 RACE STATUS:")
    print(f"   ⏱️  Elapsed Time: {format_time(elapsed)}")
    print(f"   🏃 Finishers: {finish_count}")
    print(f"   📊 Race Type: {RACE_TYPE.replace('_', ' ').title()}")
    print("")

def format_time(seconds):
    """Format seconds into MM:SS.mmm format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

def show_individual_results():
    """Show individual race results."""
    global DB_FILENAME, RACE_TYPE
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    
    # Get results with runner info
    if RACE_TYPE == "cross_country":
        query = '''SELECT r.bib, ru.name, ru.team, r.finish_time, r.race_date
                   FROM results r
                   JOIN runners ru ON r.bib = ru.bib
                   ORDER BY r.finish_time'''
    elif RACE_TYPE == "road_race":
        query = '''SELECT r.bib, ru.name, ru.age, r.finish_time, r.race_date
                   FROM results r
                   JOIN runners ru ON r.bib = ru.bib
                   ORDER BY r.finish_time'''
    else:
        query = '''SELECT r.bib, r.finish_time, r.race_date
                   FROM results r
                   ORDER BY r.finish_time'''
    
    c.execute(query)
    results = c.fetchall()
    conn.close()
    
    if not results:
        print("\n❌ No race results found.")
        input("Press Enter to continue...")
        return
    
    print(f"\n🏆 INDIVIDUAL RESULTS ({len(results)} finishers)")
    print("="*80)
    
    if RACE_TYPE == "cross_country":
        print(f"{'PLACE':<6} {'BIB':<5} {'NAME':<25} {'TEAM':<20} {'TIME':<12}")
        print("-"*80)
        for i, (bib, name, team, finish_time, _) in enumerate(results, 1):
            time_str = format_time(finish_time)
            print(f"{i:<6} {bib:<5} {name[:24]:<25} {team[:19]:<20} {time_str:<12}")
    
    elif RACE_TYPE == "road_race":
        print(f"{'PLACE':<6} {'BIB':<5} {'NAME':<30} {'AGE':<5} {'TIME':<12}")
        print("-"*70)
        for i, (bib, name, age, finish_time, _) in enumerate(results, 1):
            time_str = format_time(finish_time)
            print(f"{i:<6} {bib:<5} {name[:29]:<30} {age or 'N/A':<5} {time_str:<12}")
    
    else:
        print(f"{'PLACE':<6} {'BIB':<5} {'TIME':<12}")
        print("-"*30)
        for i, (bib, finish_time, _) in enumerate(results, 1):
            time_str = format_time(finish_time)
            print(f"{i:<6} {bib:<5} {time_str:<12}")
    
    print(f"\nTotal finishers: {len(results)}")
    input("Press Enter to continue...")

def show_team_results():
    """Show cross country team results."""
    global DB_FILENAME
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    
    # Get team results (cross country scoring)
    query = '''SELECT ru.team, r.bib, ru.name, r.finish_time,
                      ROW_NUMBER() OVER (ORDER BY r.finish_time) as place
               FROM results r
               JOIN runners ru ON r.bib = ru.bib
               ORDER BY r.finish_time'''
    
    c.execute(query)
    results = c.fetchall()
    conn.close()
    
    if not results:
        print("\n❌ No race results found.")
        input("Press Enter to continue...")
        return
    
    # Calculate team scores
    team_scores = {}
    for team, bib, name, finish_time, place in results:
        if team not in team_scores:
            team_scores[team] = []
        team_scores[team].append((place, bib, name, finish_time))
    
    # Calculate final team scores (sum of top 5 runners)
    final_scores = []
    for team, runners in team_scores.items():
        if len(runners) >= 5:  # Need at least 5 runners to score
            scorers = runners[:5]  # Top 5 runners
            total_score = sum(place for place, _, _, _ in scorers)
            final_scores.append((total_score, team, scorers, runners[5:]))
    
    final_scores.sort(key=lambda x: x[0])  # Sort by total score
    
    print(f"\n🏫 TEAM RESULTS")
    print("="*80)
    
    if not final_scores:
        print("❌ No complete teams found (need 5+ runners per team).")
        input("Press Enter to continue...")
        return
    
    for i, (total_score, team, scorers, displacers) in enumerate(final_scores, 1):
        print(f"\n{i}. {team} - Score: {total_score}")
        print("   Scorers:")
        for place, bib, name, finish_time in scorers:
            time_str = format_time(finish_time)
            print(f"      {place:2d}. Bib {bib} - {name} ({time_str})")
        
        if displacers:
            print("   Displacers:")
            for place, bib, name, finish_time in displacers[:2]:  # Show up to 2 displacers
                time_str = format_time(finish_time)
                print(f"      {place:2d}. Bib {bib} - {name} ({time_str})")
    
    input("Press Enter to continue...")

def show_age_group_results():
    """Show road race age group results."""
    global DB_FILENAME
    
    if not DB_FILENAME:
        print("❌ No database loaded.")
        input("Press Enter to continue...")
        return
    
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    
    # Get results with age groups
    query = '''SELECT r.bib, ru.name, ru.age, r.finish_time
               FROM results r
               JOIN runners ru ON r.bib = ru.bib
               WHERE ru.age IS NOT NULL
               ORDER BY r.finish_time'''
    
    c.execute(query)
    results = c.fetchall()
    conn.close()
    
    if not results:
        print("\n❌ No race results found.")
        input("Press Enter to continue...")
        return
    
    # Group by age groups
    age_groups = {}
    for bib, name, age, finish_time in results:
        # Determine age group
        if age < 20:
            group = "Under 20"
        elif age < 30:
            group = "20-29"
        elif age < 40:
            group = "30-39"
        elif age < 50:
            group = "40-49"
        elif age < 60:
            group = "50-59"
        elif age < 70:
            group = "60-69"
        else:
            group = "70+"
        
        if group not in age_groups:
            age_groups[group] = []
        age_groups[group].append((bib, name, age, finish_time))
    
    print(f"\n🎂 AGE GROUP RESULTS")
    print("="*80)
    
    # Sort age groups
    group_order = ["Under 20", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"]
    
    for group in group_order:
        if group in age_groups:
            print(f"\n{group}:")
            print(f"{'PLACE':<6} {'BIB':<5} {'NAME':<25} {'AGE':<5} {'TIME':<12}")
            print("-"*60)
            
            for i, (bib, name, age, finish_time) in enumerate(age_groups[group], 1):
                time_str = format_time(finish_time)
                print(f"{i:<6} {bib:<5} {name[:24]:<25} {age:<5} {time_str:<12}")
    
    input("Press Enter to continue...")

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        # Verify admin credentials
        if verify_admin():
            main_menu()
        else:
            print("❌ Authentication required to run TRTS.")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this error to TJ Tryon.")