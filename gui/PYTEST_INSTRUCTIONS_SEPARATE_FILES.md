#### 1. **Database Structure Errors**
```
FAILED test_database_operations.py::TestDatabaseOperations::test_cross_country_database_creation
E   AssertionError: Column 'team' should exist in cross country runners table
```
**Cause**: Database table creation logic is incorrect  
**Impact**: GUI cannot store runner data properly  
**Fix**: Check `create_database_structure()` method in main application

#### 2. **Time Formatting Issues**
```
FAILED test_time_formatting.py::TestTimeFormatting::test_format_time_precision
E   AssertionError: 123.1235 seconds should format as 02:03.124
E   assert '02:03.123' == '02:03.124'
```
**Cause**: Rounding logic in `format_time()` is incorrect  
**Impact**: Race times displayed incorrectly  
**Fix**: Check decimal formatting and rounding in time formatting method

#### 3. **Scoring Algorithm Errors**
```
FAILED test_race_scoring.py::TestCrossCountryScoring::test_cross_country_team_scoring# 🧪 RUN_UNIT_TESTS.md

## Running Unit Tests for The Race Timing Solution GUI

This document provides comprehensive instructions for running the pytest unit tests for the Race Timing Solution GUI application.

---

## 📋 Prerequisites

### Required Software
- **Python 3.7+** installed on your system
- **pytest** testing framework
- **bcrypt** for password hashing compatibility

### Installation Commands
```bash
# Install pytest and required dependencies
pip install pytest pytest-cov bcrypt

# Optional: Install additional pytest plugins for enhanced functionality
pip install pytest-xdist pytest-html pytest-mock
```

### Verify Installation
```bash
# Check pytest version
pytest --version

# Should output something like: pytest 7.4.0
```

---

## 📁 File Structure

Ensure your project directory contains:
```
project/
├── gui/
│   └── race_timing_gui.py          # Main GUI application
├── test_race_timing_gui.py         # Unit tests (this file)
├── RUN_UNIT_TESTS.md              # This instruction file
└── data/                          # Auto-created during tests
```

---

## 🚀 Running the Tests

### Basic Test Execution

#### Run All Tests
```bash
# Run all tests with verbose output
pytest test_*.py -v

# Run all tests with simple output
pytest test_*.py
```

#### Run Specific Test Files
```bash
# Run only database operation tests
pytest test_database_operations.py -v

# Run only time formatting tests
pytest test_time_formatting.py -v

# Run only race scoring tests
pytest test_race_scoring.py -v
```

#### Run Specific Test Groups
```bash
# Run specific test class from database tests
pytest test_database_operations.py::TestDatabaseOperations -v

# Run specific test class from time formatting tests
pytest test_time_formatting.py::TestTimeFormatting -v

# Run specific test class from scoring tests
pytest test_race_scoring.py::TestCrossCountryScoring -v
```

#### Run Individual Tests
```bash
# Run specific test by name
pytest test_database_operations.py::test_cross_country_database_creation -v

# Run tests matching a pattern across all files
pytest test_*.py -k "format_time" -v

# Run tests matching multiple patterns
pytest test_*.py -k "database or scoring" -v
```

### Advanced Test Options

#### Coverage Reports
```bash
# Run tests with coverage report
pytest test_*.py --cov=race_timing_gui

# Generate HTML coverage report
pytest test_*.py --cov=race_timing_gui --cov-report=html

# View coverage report (opens in browser)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Test Execution Control
```bash
# Stop on first failure
pytest test_*.py -x

# Stop after 3 failures
pytest test_*.py --maxfail=3

# Run tests in parallel (faster execution)
pytest test_*.py -n auto

# Show local variables in tracebacks
pytest test_*.py -l
```

#### Output Formatting
```bash
# Short traceback format
pytest test_*.py --tb=short

# One line per failure
pytest test_*.py --tb=line

# No traceback
pytest test_*.py --tb=no

# Generate HTML test report
pytest test_*.py --html=report.html --self-contained-html
```

---

## 🎯 What We Are Testing

### 1. **Database Operations** (`test_database_operations.py`)
**Purpose**: Verify that the GUI can create and manage race databases correctly

**Test Classes**:
- `TestDatabaseOperations` - Core database functionality

**Tests Include**:
- ✅ Cross country database creation with correct table structure
- ✅ Road race database creation with different table structure  
- ✅ Race type auto-detection from existing databases
- ✅ Graceful handling of missing database connections
- ✅ Multiple database structure handling
- ✅ Corrupted database recovery
- ✅ Table existence validation

**Critical Functionality**: Ensures the GUI can store runner data and race results in the correct format for each race type.

### 2. **Time Formatting** (`test_time_formatting.py`)
**Purpose**: Verify accurate time display for race results

**Test Classes**:
- `TestTimeFormatting` - Basic time formatting (MM:SS.mmm)
- `TestExtendedTimeFormatting` - Extended formatting (HH:MM:SS.mmm)
- `TestRaceTimingScenarios` - Real-world race scenarios

**Tests Include**:
- ✅ Basic time conversion (seconds → MM:SS.mmm format)
- ✅ Extended time formatting for longer races (HH:MM:SS.mmm)
- ✅ Edge cases (None values, very small/large times)
- ✅ Millisecond precision and rounding
- ✅ Time parsing (string → seconds conversion)
- ✅ Round-trip conversion testing
- ✅ Sprint, distance, and marathon race scenarios
- ✅ Close finish precision testing

**Critical Functionality**: Ensures race times are displayed accurately for official results and timing displays.

### 3. **Race Scoring Logic** (`test_race_scoring.py`)
**Purpose**: Verify complex scoring algorithms for both race types

**Test Classes**:
- `TestCrossCountryScoring` - Team scoring algorithms
- `TestRoadRaceScoring` - Age group classification
- `TestAdditionalScoringFeatures` - Individual awards and tie detection
- `TestScoringIntegration` - Integration and edge cases

**Tests Include**:
- ✅ Cross country team scoring (top 5 runners, displacers for tiebreaking)
- ✅ Teams with insufficient runners (< 5) don't score
- ✅ Road race age group classification (13 age divisions)
- ✅ Age group boundary conditions (exact age cutoffs)
- ✅ Individual award calculations (1st, 2nd, 3rd place)
- ✅ Tie detection in team scoring
- ✅ Complete meet scenarios with multiple teams
- ✅ Edge cases (single runners, extreme ages)

**Critical Functionality**: Ensures accurate competition results following official USATF rules.

---

## ✅ Expected Results When Tests PASS

### Successful Test Output
```
========================= test session starts =========================
platform linux -- Python 3.9.7, pytest-7.4.0, pluggy-1.0.0
collected 45 items

test_database_operations.py::TestDatabaseOperations::test_cross_country_database_creation PASSED [ 2%]
test_database_operations.py::TestDatabaseOperations::test_road_race_database_creation PASSED [ 4%]
test_database_operations.py::TestDatabaseOperations::test_race_type_detection_with_no_database PASSED [ 7%]
test_database_operations.py::TestDatabaseOperations::test_database_creation_without_connection PASSED [ 9%]
test_database_operations.py::TestDatabaseOperations::test_race_type_table_creation PASSED [11%]
test_database_operations.py::TestDatabaseOperations::test_multiple_database_structures PASSED [13%]
test_database_operations.py::TestDatabaseOperations::test_corrupted_race_type_detection PASSED [15%]
test_database_operations.py::TestDatabaseOperations::test_table_existence_checks PASSED [18%]

test_time_formatting.py::TestTimeFormatting::test_format_time_basic_cases[60.0-01:00.000] PASSED [20%]
test_time_formatting.py::TestTimeFormatting::test_format_time_basic_cases[123.456-02:03.456] PASSED [22%]
test_time_formatting.py::TestTimeFormatting::test_format_time_basic_cases[45.789-00:45.789] PASSED [24%]
test_time_formatting.py::TestTimeFormatting::test_format_time_basic_cases[0.0-00:00.000] PASSED [27%]
test_time_formatting.py::TestTimeFormatting::test_format_time_edge_cases[None-00:00.000] PASSED [29%]
test_time_formatting.py::TestTimeFormatting::test_format_time_edge_cases[0.001-00:00.001] PASSED [31%]
test_time_formatting.py::TestTimeFormatting::test_format_time_edge_cases[665.123-11:05.123] PASSED [33%]
test_time_formatting.py::TestExtendedTimeFormatting::test_format_time_hours[3661.5-01:01:01.500] PASSED [36%]
test_time_formatting.py::TestExtendedTimeFormatting::test_parse_time_input_valid[02:03.456-123.456] PASSED [38%]
test_time_formatting.py::TestRaceTimingScenarios::test_sprint_race_times PASSED [40%]
test_time_formatting.py::TestRaceTimingScenarios::test_marathon_times_with_hours PASSED [42%]

test_race_scoring.py::TestCrossCountryScoring::test_cross_country_team_scoring PASSED [44%]
test_race_scoring.py::TestCrossCountryScoring::test_team_scoring_insufficient_runners PASSED [47%]
test_race_scoring.py::TestCrossCountryScoring::test_team_scoring_tiebreaker_scenarios PASSED [49%]
test_race_scoring.py::TestRoadRaceScoring::test_road_race_age_grouping PASSED [51%]
test_race_scoring.py::TestRoadRaceScoring::test_age_group_boundaries[15-1-15] PASSED [53%]
test_race_scoring.py::TestRoadRaceScoring::test_age_group_boundaries[71-71+] PASSED [56%]
test_race_scoring.py::TestAdditionalScoringFeatures::test_individual_awards_calculation PASSED [58%]
test_race_scoring.py::TestAdditionalScoringFeatures::test_scoring_tie_detection PASSED [60%]
test_race_scoring.py::TestScoringIntegration::test_complete_cross_country_meet_scoring PASSED [62%]
test_race_scoring.py::TestScoringIntegration::test_large_road_race_age_groups PASSED [64%]
test_race_scoring.py::TestScoringIntegration::test_scoring_system_consistency PASSED [67%]

========================= 45 passed in 0.28s =========================
```

### What Passing Tests Mean
- **✅ Database Integrity**: GUI can create proper race databases compatible with console version
- **✅ Timing Accuracy**: Race times display correctly to millisecond precision
- **✅ Scoring Reliability**: Competition results calculated correctly per USATF rules
- **✅ System Integration**: All components work together seamlessly
- **✅ Production Ready**: Core functionality is stable and tested

---

## ❌ Expected Results When Tests FAIL

### Example Failure Output
```
========================= FAILURES =========================
_______ TestTimeFormatting.test_format_time_basic_cases[123.456-02:03.456] _______

app = <test_race_timing_gui.TestableRaceTimingApp object at 0x7f8b8c0d5f40>
input_time = 123.456, expected = '02:03.456'

    @pytest.mark.parametrize("input_time,expected", [
        (60.0, "01:00.000"),
        (123.456, "02:03.456"),
        (45.789, "00:45.789"),
        (0.0, "00:00.000"),
    ])
    def test_format_time_basic_cases(self, app, input_time, expected):
        result = app.format_time(input_time)
>       assert result == expected, f"{input_time} seconds should format as {expected}"
E       AssertionError: 123.456 seconds should format as 02:03.456
E       assert '02:03.457' == '02:03.456'
E         - 02:03.456
E         + 02:03.457

test_race_timing_gui.py:245: AssertionError
========================= short test summary info =========================
FAILED test_race_timing_gui.py::TestTimeFormatting::test_format_time_basic_cases[123.456-02:03.456] - AssertionError: 123.456 seconds should format as 02:03.456
========================= 1 failed, 15 passed in 0.18s =========================
```

### Common Failure Scenarios

#### 1. **Database Structure Errors**
```
FAILED test_race_timing_gui.py::TestDatabaseOperations::test_cross_country_database_creation
E   AssertionError: Column 'team' should exist in cross country runners table
```
**Cause**: Database table creation logic is incorrect
**Impact**: GUI cannot store runner data properly
**Fix**: Check `create_database_structure()` method

#### 2. **Time Formatting Issues**
```
FAILED test_race_timing_gui.py::TestTimeFormatting::test_format_time_precision
E   AssertionError: 123.1235 seconds should format as 02:03.124
E   assert '02:03.123' == '02:03.124'
```
**Cause**: Rounding logic in `format_time()` is incorrect
**Impact**: Race times displayed incorrectly
**Fix**: Check decimal formatting and rounding

#### 3. **Scoring Algorithm Errors**
```
FAILED test_race_scoring.py::TestCrossCountryScoring::test_cross_country_team_scoring
E   AssertionError: Team A score should be 21
E   assert 25 == 21
```
**Cause**: Team scoring calculation is wrong  
**Impact**: Incorrect race results and team standings  
**Fix**: Check `calculate_team_scores()` logic in scoring system

#### 4. **Age Group Classification Issues**
```
FAILED test_race_scoring.py::TestRoadRaceScoring::test_road_race_age_grouping
E   AssertionError: Should have 2 runners in 21-25 group
E   assert 1 == 2
```
**Cause**: Age grouping logic is incorrect  
**Impact**: Road race results in wrong age divisions  
**Fix**: Check `group_by_age()` method in scoring system

#### 5. **Extended Time Formatting Failures**
```
FAILED test_time_formatting.py::TestExtendedTimeFormatting::test_parse_time_input_valid
E   AssertionError: '02:03.456' should parse to 123.456 seconds
E   assert 183.456 == 123.456
```
**Cause**: Time parsing logic has calculation error  
**Impact**: Manual time entry and corrections will be wrong  
**Fix**: Check time string parsing mathematics

#### 6. **Integration Test Failures**
```
FAILED test_race_scoring.py::TestScoringIntegration::test_complete_cross_country_meet_scoring
E   AssertionError: Should have 3 complete teams
E   assert 2 == 3
```
**Cause**: Team completeness validation is incorrect  
**Impact**: Teams may be scored when they shouldn't be  
**Fix**: Check minimum runner requirements in team scoring

### What Failing Tests Mean
- **⚠️ Data Integrity Risk**: Database operations may corrupt race data
- **⚠️ Timing Inaccuracy**: Race times may be displayed incorrectly
- **⚠️ Scoring Errors**: Competition results may be wrong
- **⚠️ System Instability**: Components not working together properly
- **⚠️ Not Production Ready**: Core issues need fixing before use

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: `ModuleNotFoundError: No module named 'pytest'`
```bash
# Solution: Install pytest
pip install pytest
```

#### Issue: `ModuleNotFoundError: No module named 'bcrypt'`
```bash
# Solution: Install bcrypt
pip install bcrypt
```

#### Issue: Tests fail with database permission errors
```bash
# Solution: Ensure write permissions in test directory
chmod 755 .
mkdir -p data
chmod 755 data
```

#### Issue: GTK4 import errors during testing
**Expected Behavior**: Tests should run without GTK4 installed  
**Solution**: The tests mock GTK4 dependencies - this is normal

#### Issue: All tests skip or no tests collected
```bash
# Check test file locations
ls -la test_*.py

# Run with test discovery
pytest --collect-only

# Specify files explicitly
pytest test_database_operations.py test_time_formatting.py test_race_scoring.py -v
```

#### Issue: Some tests pass, others fail randomly
```bash
# Check for race conditions or shared state
pytest test_*.py --forked

# Run tests individually to isolate issues
pytest test_database_operations.py -v
pytest test_time_formatting.py -v  
pytest test_race_scoring.py -v
```

---

## 📊 Understanding Test Coverage

### Running Coverage Analysis
```bash
# Generate coverage report for all test files
pytest test_*.py --cov=race_timing_gui --cov-report=term-missing

# Expected coverage areas:
# - Database operations: 100%
# - Time formatting: 100%  
# - Scoring algorithms: 100%
# - Error handling: 85%+
```

### Coverage Report Example
```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
race_timing_gui.py               250     45    82%   125-130, 145-150, 200-205
test_database_operations.py     180      0   100%
test_time_formatting.py         220      0   100%
test_race_scoring.py             300      0   100%
------------------------------------------------------------
TOTAL                            950     45    95%
```

---

## 🎯 Best Practices

### Running Tests During Development
```bash
# Quick test of specific functionality during coding
pytest test_database_operations.py -v  # Test database code
pytest test_time_formatting.py -v      # Test time formatting
pytest test_race_scoring.py -v         # Test scoring logic

# Full test suite before committing
pytest test_*.py --cov=race_timing_gui

# Test specific functionality with pattern matching
pytest test_*.py -k "cross_country" -v     # All cross country tests
pytest test_*.py -k "time_format" -v       # All time formatting tests
pytest test_*.py -k "age_group" -v         # All age group tests

# Continuous testing (watch for file changes - requires pytest-watch)
pytest-watch test_*.py
```

### Integration with IDEs
- **VSCode**: Install Python Test Explorer extension
- **PyCharm**: Built-in pytest integration  
- **Vim/Neovim**: Use pytest plugins

### Pre-commit Testing
```bash
# Add to your workflow
pytest test_*.py -x --tb=short
if [ $? -eq 0 ]; then
    echo "✅ All tests passed - ready to commit"
else
    echo "❌ Tests failed - fix issues before committing"
    exit 1
fi
```

---

## 📞 Getting Help

### When Tests Fail
1. **Read the error message carefully** - pytest provides detailed failure information
2. **Check the specific assertion that failed** - tells you exactly what went wrong
3. **Run individual failing tests** - isolate the problem
4. **Check the test data and expected results** - verify your understanding
5. **Review the corresponding application code** - look for logic errors

### Debug Mode
```bash
# Run with Python debugger on failure
pytest test_*.py --pdb

# Run specific failing test with debugger
pytest test_race_scoring.py::test_cross_country_team_scoring --pdb

# Run with extra verbose output
pytest test_*.py -vvv

# Show local variables in failures
pytest test_*.py -l --tb=long

# Run single test file in debug mode
pytest test_time_formatting.py --pdb -v
```

---

## 🏁 Conclusion

These unit tests ensure the Race Timing Solution GUI maintains the same reliability and accuracy as the console version while providing a user-friendly graphical interface. Regular testing helps catch issues early and ensures race directors can trust the system for official competitions.

**Remember**: Tests passing means your core race timing functionality is working correctly and ready for production use! 🏃‍♀️🏃‍♂️🏆