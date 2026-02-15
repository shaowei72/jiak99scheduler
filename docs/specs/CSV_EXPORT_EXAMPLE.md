# CSV Export Format - Visual Example

**File**: `schedule_2026-02-15.csv`

## How It Looks in Excel

When the manager opens the exported CSV in Excel, they see a grid that matches the Schedule Manager UI:

```
┌─────────────────────┬───────────────────────────┬───────────────────────────┬───────────────────────────┬───────────────────────────┐
│ Time Slot           │ John Doe (FT)             │ Jane Smith (PTM)          │ Bob Wilson (PTA)          │ Alice Brown (FT)          │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 08:30 AM - 10:30 AM │ FT                        │                           │ N/A                       │                           │
│                     │ 25                        │                           │                           │                           │
│                     │ Local                     │                           │                           │                           │
│                     │ Online                    │                           │                           │                           │
│                     │                           │                           │                           │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 09:00 AM - 11:00 AM │ FT                        │ PTM                       │ N/A                       │                           │
│                     │ 30                        │ 20                        │                           │                           │
│                     │ International             │ Local                     │                           │                           │
│                     │ Direct                    │ Walk-in                   │                           │                           │
│                     │                           │                           │                           │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 09:30 AM - 11:30 AM │                           │ PTM                       │ N/A                       │ FT                        │
│                     │                           │ 15                        │                           │ 40                        │
│                     │                           │ Local                     │                           │ International             │
│                     │                           │ Online                    │                           │ Direct                    │
│                     │                           │                           │                           │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 10:00 AM - 12:00 PM │                           │ PTM                       │ N/A                       │                           │
│                     │                           │ 25                        │                           │                           │
│                     │                           │ Local                     │                           │                           │
│                     │                           │ Walk-in                   │                           │                           │
│                     │                           │ Group booking             │                           │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 10:30 AM - 12:30 PM │                           │                           │ N/A                       │ FT                        │
│                     │                           │                           │                           │ 35                        │
│                     │                           │                           │                           │ Local                     │
│                     │                           │                           │                           │ Online                    │
│                     │                           │                           │                           │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ 11:00 AM - 01:00 PM │                           │                           │ N/A                       │                           │
├─────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┼───────────────────────────┤
│ ...                 │ ...                       │ ...                       │ ...                       │ ...                       │
└─────────────────────┴───────────────────────────┴───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

## Raw CSV File Content

The actual CSV file looks like this:

```csv
Time Slot,John Doe (FT),Jane Smith (PTM),Bob Wilson (PTA),Alice Brown (FT)
08:30 AM - 10:30 AM,"FT;
25;
Local;
Online;
","","N/A",""
09:00 AM - 11:00 AM,"FT;
30;
International;
Direct;
","PTM;
20;
Local;
Walk-in;
","N/A",""
09:30 AM - 11:30 AM,"","PTM;
15;
Local;
Online;
","N/A","FT;
40;
International;
Direct;
"
10:00 AM - 12:00 PM,"","PTM;
25;
Local;
Walk-in;
Group booking","N/A",""
10:30 AM - 12:30 PM,"","","N/A","FT;
35;
Local;
Online;
"
11:00 AM - 01:00 PM,"","","N/A",""
11:30 AM - 01:30 PM,"","","N/A",""
12:00 PM - 02:00 PM,"","","N/A",""
12:30 PM - 02:30 PM,"","","N/A",""
01:00 PM - 03:00 PM,"","N/A","PTA;
30;
International;
Online;
",""
01:30 PM - 03:30 PM,"","N/A","PTA;
25;
Local;
Direct;
","FT;
45;
International;
Walk-in;
"
...
```

## Cell Content Format

Each non-empty cell contains **5 lines separated by semicolons**:

```
[Line 1]: Guide Type (FT, PTM, or PTA)
[Line 2]: Visitor Count (number or empty)
[Line 3]: Visitor Type (Local, International, or empty)
[Line 4]: Booking Channel (Online, Walk-in, Direct, or empty)
[Line 5]: Notes (any text or empty)
```

**Example cell:**
```
FT;
25;
Local;
Online;

```

## Special Cell Values

| Value | Meaning | When to Use |
|-------|---------|-------------|
| `""` (empty) | Unassigned slot | Guide not assigned to this time slot |
| `"N/A"` | Incompatible | Guide type cannot work this time slot (e.g., PTM in afternoon) |
| Multi-line | Assigned | Guide is working this slot with booking details |

## What Managers Can Do in Excel

### 1. **View Schedule**
   - See the full day at a glance
   - Grid layout matches the Schedule Manager UI
   - Easy to spot unassigned slots (empty cells)

### 2. **Analyze Data**
   - Sum visitor counts: `=SUM(B2:B25)` for John Doe's total visitors
   - Count tours: `=COUNTA(B2:B25)` for number of assigned tours
   - Filter by visitor type: Use Excel's filter to show only "International"

### 3. **Format for Printing**
   - Add borders and colors
   - Adjust column widths
   - Print landscape for full-day view
   - Distribute to staff

### 4. **Create Reports**
   - Copy to PowerPoint presentations
   - Paste into emails
   - Share with stakeholders

### 5. **Cross-Reference**
   - Open alongside Schedule Manager
   - Verify assignments
   - Spot patterns and issues

## Excel Tips for Managers

### Viewing Multi-line Cells
- **Single-click**: See first line
- **Double-click**: Enter edit mode, see all lines
- **Wrap Text**: Enable in Excel (Home → Alignment → Wrap Text) to see all lines at once

### Adjusting Row Height
- Select all rows
- Right-click → Row Height → Set to ~75 (or Auto-fit)

### Formatting
- Apply borders: Select all → Borders → All Borders
- Highlight unassigned: Conditional Formatting → Highlight Cells Rules → Equal to ""
- Freeze panes: Select cell B2 → View → Freeze Panes (keeps headers visible)

### Analysis Examples

**Total visitors for John Doe:**
```excel
=SUMPRODUCT(--(ISNUMBER(SEARCH("Local",B2:B25))),
            VALUE(MID(B2:B25,FIND(";",B2:B25)+2,FIND(";",B2:B25,FIND(";",B2:B25)+1)-FIND(";",B2:B25)-2)))
```
(This extracts visitor count from multi-line cells)

**Simpler approach:**
Use Excel's "Text to Columns" feature:
1. Copy a guide's column
2. Data → Text to Columns → Delimited → Semicolon
3. Now visitor counts are in separate column for easy summing

## File Size Estimate

**For typical day:**
- 24 time slots (rows)
- 10 guides (columns)
- ~240 cells
- Average cell: ~50 characters
- **Total file size: ~15-20 KB** (very lightweight)

## Compatibility

**Tested and works with:**
- ✅ Microsoft Excel 2016+
- ✅ Google Sheets
- ✅ LibreOffice Calc
- ✅ Apple Numbers
- ✅ Any text editor (Notepad, VS Code)

**Note:** Multi-line cells display best in Excel. Google Sheets shows line breaks as well, but may require manual adjustment of row height.

## Example Use Cases

### Use Case 1: Weekly Reporting
1. Export Monday-Friday schedules
2. Open all 5 CSVs in Excel
3. Copy relevant data to master report
4. Generate charts (visitors per day, channel breakdown)
5. Present to management

### Use Case 2: Shift Distribution Analysis
1. Export schedule
2. Count tours per guide (use COUNTA)
3. Check workload balance
4. Identify over/under-utilized guides

### Use Case 3: Visitor Forecasting
1. Export historical schedules (past month)
2. Sum visitor counts by day/week
3. Calculate averages
4. Predict future demand

### Use Case 4: Channel Performance
1. Export schedule
2. Use Excel filter to show only "Online" bookings
3. Count tours and sum visitors
4. Compare with "Walk-in" and "Direct"
5. Identify most effective channels

### Use Case 5: Printing for Distribution
1. Export schedule
2. Format in Excel (colors, borders, fonts)
3. Add company header/footer
4. Print landscape on A3 paper
5. Post in staff room or distribute to guides

---

## Comparison: Grid vs. Flat List Format

**Grid Format (APPROVED):**
- ✅ Matches Schedule Manager UI visually
- ✅ Easy to see guide workload at a glance
- ✅ Shows time slot distribution across guides
- ✅ Better for printing as daily reference
- ❌ Harder to query/filter in Excel
- ❌ Multi-line cells require special handling for formulas

**Flat List Format (Alternative, not used):**
- ✅ Easy to sort, filter, and analyze
- ✅ Standard database format
- ✅ Simple formulas (no multi-line parsing)
- ✅ Better for data import/export
- ❌ Loses visual grid structure
- ❌ Harder to see daily overview
- ❌ More rows (one per assignment, not per time slot)

**Decision Rationale:**
The grid format was chosen because it:
1. Provides immediate visual reference matching the UI
2. Supports the manager's primary use case: viewing/printing daily schedules
3. Maintains the mental model of "time slots × guides"
4. Is more human-readable for quick reviews
5. Can still be analyzed in Excel with some formula work

---

**For advanced analytics, consider future enhancement: Separate "Flat Export" option for data analysis.**

---

## Technical Notes for Developers

### CSV Generation Considerations

**Quoting:**
- Always quote cells with newlines: `"FT;\n25;\n..."`
- Use RFC 4180 compliant CSV writer (Python's `csv` module handles this)

**Line Endings:**
- Within cells: Use `\n` (LF) for line breaks
- Between rows: Use `\r\n` (CRLF) for Windows compatibility

**Character Encoding:**
- UTF-8 with BOM (`\ufeff`) for Excel compatibility
- Ensures special characters display correctly

**Empty vs. N/A:**
- Empty: `""` (double quotes with nothing inside)
- N/A: `"N/A"` (quoted string)
- Consistent handling prevents Excel auto-formatting issues

**Testing:**
- Test with special characters in notes (commas, quotes, newlines)
- Test with empty schedules (all unassigned)
- Test with partial schedules (some assigned, some not)
- Test with maximum visitor counts (large numbers)
- Verify Excel opens without prompts or warnings
