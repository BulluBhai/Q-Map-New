# Q-MAP — Owner's User Guide
**Version:** 1.0  
**Prepared:** 14 November 2026  
**Applies to:** `main` branch, commit `001e03a5ee1a03527b595876b2d4f0beaee92e9c`  
**Audience:** Project Owner; Windows user running Python through IDLE

---

## 1. Welcome — what Q-MAP does

Q-MAP is a local market-data system. It has two main jobs:

1. **Keep your market data organised and checked.** The Data Manager imports your files, stores the data, records where it came from and flags data-quality matters for your attention.
2. **Analyse the stored data.** The first analytical tool currently available is the EMA Trend Alignment scanner. It reads data from the Q-MAP database and creates an Excel report and a JSON file.

There is also a separate **Universe Inventory** tool. It examines a folder of stock files and creates an Excel workbook describing what is present and what needs attention. It does not import anything into the Q-MAP database.

| Program | What it is for | Does it change the database? |
|---|---|---|
| Q-MAP Data Manager | Import, update, check and maintain the central data store | Yes |
| Q-MAP Universe Inventory | Inspect a stock-data folder and prepare an inventory workbook | No — read-only |
| Q-MAP EMA Scanner | Analyse daily stock data already stored in Q-MAP | No — reads data and writes reports |
| Q-MAP M2 Example | Demonstrate data retrieval and timeframe aggregation | No — read-only demonstration |

The database folder is the common source of data. The scanner does not independently open your market-data files.

**Important:** Q-MAP is an analysis platform, not an automatic trading or order-placement program. It does not connect to your broker.

## 2. Before you start

### 2.1 Download the latest Q-MAP files

Use the repository's `main` branch:

[Open Q-MAP on GitHub](https://github.com/BulluBhai/Q-Map-New)

For a fresh copy, open the repository page, make sure the branch selector shows **main**, select **Code**, then **Download ZIP**. The ZIP contains one folder named `Q-Map-New-main`. Extract it to a normal folder on your PC, for example:

`D:\Q-MAP\Q-Map-New-main\`

Do not extract it inside your live market-data folder.

When a new version is issued, download and extract that latest version separately. Do not mix files from different ZIP versions.

### 2.2 Keep your market data outside the code folder

Choose a separate folder for Q-MAP's working database, for example:

`D:\QMAP_DATA\`

This is called the **Q-MAP data root**. It is where Q-MAP stores the catalogue, imported market data, quarantined rows, backups, reports and logs.

Keep it outside the repository folder. Do not save your live database, full market-data archive or backups inside the GitHub code folder.

Your original market-data files should also remain in their own source folder. Q-MAP reads those files during import; the Data Manager does not use the repository's sample fixtures as your live database.

### 2.3 Required Python version and packages

Q-MAP is built for **Python 3.12.10**.

The repository currently pins these four packages:

| Package | Required version |
|---|---:|
| duckdb | 1.5.6 |
| pandas | 2.3.3 |
| pyarrow | 26.0.1 |
| openpyxl | 3.1.5 |

Tkinter is also required for the Windows screens. It normally comes with the standard Windows installation of Python from python.org.

### 2.4 Install the packages using IDLE

You do not need to type installation commands into a command window.

1. Open the extracted Q-MAP folder.
2. Open the `tools` folder.
3. Right-click `QMAP_Install_Requirements.py` and choose **Edit with IDLE** (on Windows 11 it may be under **Show more options**). If that option is not shown, open IDLE first and use **File → Open...** to select the file.
4. In the IDLE editor window, press **F5** (or choose **Run → Run Module**).
5. Look at the IDLE Shell. The installer prints the installation messages.
6. Wait until it says **Done**. If it reports an error or a non-zero exit code, stop and keep the complete Shell output for review.

The installer checks that it is running under Python 3.12.10. If it prints a **WARNING** that Q-MAP requires Python 3.12.10, it installs nothing: open the file with the IDLE that belongs to Python 3.12.10 and run it again. It uses the same Python installation as the IDLE window that opened it.

### 2.5 Check your Python environment

Before opening the applications, run the environment check:

1. In IDLE, choose **File → Open...**.
2. Open `tests\t_env_01_environment_check.py` from the Q-MAP folder.
3. Press **F5**.
4. Read the IDLE Shell output.

You should see `python_match: TRUE`, a `_match: TRUE` line for each of the four packages, a `tkinter_installed:` line showing a version number (for example `8.6`), and finally:

`all_environment_checks_match: TRUE`

The script creates a file named like:

`EV12_environment_14_Nov_26_153000.txt`

It saves that file in the `tests` folder. Keep it: it records the environment information from your PC.

**Stop here if the check says FALSE or shows a version mismatch.** Do not continue with a database import or scanner run until the environment has been reviewed. The Linux test results do not replace this check on your Windows PC.

## 3. First-time testing — recommended order

Use this order for your first session:

1. Run the environment check in section 2.5.
2. Open the Data Manager and use a **separate, new test data-root folder** (not your intended long-term database) with a small set of files you deliberately choose. This keeps the first experiment isolated from any existing Q-MAP data.
3. Review the import log and data-quality issues. Do not automatically accept warnings or large price moves.
4. Run **Check integrity**.
5. Run the M2 Example to confirm the stored data can be read at different supported timeframes.
6. Run the Universe Inventory separately against a small stock-data folder and inspect its Excel workbook.
7. Run the EMA Scanner against one or two stocks and one analysis date. Inspect its output before expanding the selection.

Do not start with your entire historical archive. The first run is intended to confirm that the software starts correctly, can read your files and puts its outputs in the expected places. Once that is satisfactory, you can plan the larger import.

## 4. Q-MAP Data Manager

### 4.1 What it does

Open:

`apps\QMAP_Data_Manager.py`

In IDLE, open the file and press **F5**.

The window title is **Q-MAP Data Manager**. It is the only application that writes to the Q-MAP database.

The window is arranged in sections. It may be taller than your screen; use the vertical scroll bar to reach the lower sections.

### 4.2 Section 1 — Input: source data files

This is where you tell Q-MAP which original market-data files to import.

- **Add files...** opens a file picker. Select the files you want to import. The supported file types shown are Parquet, CSV and TXT.
- **Remove selected** removes highlighted entries from the selection list. It does not delete the original files from your computer.
- **Clear** clears the selection list.

The application shows the number of selected files.

For an initial test, choose only a small number of files you understand. Select the exact files you intend to load; do not select an entire drive or an unrelated folder.

### 4.3 Section 2 — Output: Q-MAP data root folder

This is the location where Q-MAP creates and maintains its database.

Click **Browse...** and choose your separate data-root folder, for example `D:\QMAP_DATA\`.

The folder must be outside the extracted GitHub repository.

The data root is remembered once you run **Run initial load** or **Run update** with it. It is saved in `config\settings.json` inside the program folder, and the M2 Example and the EMA Scanner use the same saved value. A freshly extracted ZIP starts with no saved data root. Always check that the folder shown is the intended one before running an operation.

### 4.4 Section 3 — Options

The current optional setting is:

**Official NSE calendar file (optional):**

Use **Browse...** to select the calendar file only when you have the appropriate official calendar file and intend to provide it.

Importing a calendar does not automatically make it official. It remains unconfirmed until the required source and confirmation steps are completed. Do not select an arbitrary holiday list just to fill this field.

### 4.5 Run initial load

Click **Run initial load** after you have checked the selected source files and the data-root folder.

This creates or uses the selected data root, prepares the catalogue and imports the selected files. It also validates the data and records the results.

During the run:

- **Progress / Status** shows the current activity and status.
- **Live log** shows the detailed messages.

Let the run finish. Do not close the window while it is working.

The original source files are not a working database. Q-MAP stores its own managed copy under the data root. Keep your original files unchanged.

### 4.6 Understanding the import result

A file can contain valid records as well as rows that fail validation. Q-MAP records the results and keeps quarantined rows separately for inspection. A quarantined row is not silently corrected and inserted as if it were valid.

Pay attention to messages about invalid or unreadable files, invalid OHLC prices or volume values, large price moves that may affect continuity, duplicate or conflicting sources, and incomplete or uncertain session information.

A warning is not automatically proof that the source is wrong. It is a request to inspect the available evidence.

### 4.7 Section 4 — Maintenance (M1b)

This section is for later updates and database maintenance.

**Add update folder...**

Choose a folder containing changed or newly received source files. You can add more than one folder.

**Clear folders**

Empties the whole update-folder list (not just the highlighted entries). It does not delete those folders or their files.

**Run update**

Use this after the initial load when you receive new or changed market-data files.

Q-MAP checks the files against what it already knows:
- files it has already imported unchanged can be skipped;
- new data can be appended;
- changes to previously stored history are held for your review rather than automatically replacing the history.

Do not assume that a revised historical file has been accepted just because it was selected for an update.

**Check integrity**

Use this to check that the active stored data files still exist and match the fingerprints and row counts recorded by Q-MAP.

A clean integrity result is expected. If it reports a problem, keep the complete log and do not delete or rename database files in an attempt to fix it manually.

**Restore catalogue backup...**

Use this only when a catalogue restore is genuinely required and you know which backup you intend to restore.

The application asks you to choose a catalogue backup file, normally from the data-root folder under `backups\catalogue\`. It asks for confirmation before restoring.

Close every **other** Q-MAP program before a restore; leave the Data Manager open because it is the program performing the restore. After restoring, it runs an integrity check.

A restore is not an everyday update operation. Do not use it simply because you are unsure what a warning means.

**Export data summary...**

This creates CSV files in a folder you choose. The export includes source fingerprints, record counts, issues and quarantined rows so that you can inspect them in Excel.

Choose an export folder outside the Q-MAP data root. The export is for review; it does not modify the database.

### 4.8 Awaiting your decision — sessions, held revisions and continuity issues

This section lists four kinds of items that require your decision: CAS-rule candidates, unrecognised trading days, G-03 continuity issues and held historical revisions. Click **Refresh list** to reload the items. Select one item before using an action.

**Confirm selected... — CAS rule**

For a listed CAS candidate, the program asks you to state the basis for confirming the CAS rule for that instrument from **03 Aug 26** (for example, the relevant NSE circular). Enter the actual source you checked. The program then records the confirmation and re-validates the data. Do not confirm a CAS pattern merely because the file looks unusual.

**Confirm selected... — unrecognised trading day**

The list may show a date with only a partial set of records and ask whether it was a special session or truncated data. The prompt requires this exact format:

- `SPECIAL 13:45 14:45`
- `SPECIAL_CAS 13:45 14:45`

The two times are the session open and close in `HH:MM` format. If the close is genuinely unknown, it may be left blank, for example `SPECIAL 13:45`. Use `SPECIAL` or `SPECIAL_CAS` only when you have reliable evidence for that session. Do not label incomplete source data as a special session just to clear the item.

**Confirm selected... — G-03 continuity issue**

For a G-03 continuity issue, the program asks for a written basis before marking that particular occurrence **VERIFIED_OK**. Only verify a move after checking the original data and the reason for the move. The program takes a catalogue backup, then records your decision and your explanation as evidence. The stored prices are not changed. Verifying one occurrence does not automatically verify every other large move in the same stock, and a later update of the same unchanged history does not re-open it.

The CAS and special-session confirmations re-validate the affected intraday data. A G-03 verification does not re-validate anything; it simply stops that one occurrence blocking calculations such as the EMA Scanner. If you are unsure, leave the item awaiting your decision.

**Approve held revision**

Use this only when you have reviewed the changed historical source and explicitly decide that the new history should replace the active version. Q-MAP rebuilds and revalidates the data; it does not simply overwrite the old rows without checks.

**Reject held revision**

Use this when you decide that the proposed historical revision should not be applied. The program asks for a reason, which is kept as evidence. The held data is retained, the active data is unchanged, and the same source file is not offered to you again.

Do not approve or reject a revision just to clear the list. If you are uncertain, leave it awaiting your decision.

## 5. M2 Example — check that data can be read

Open:

`apps\QMAP_M2_Example.py`

Run it from IDLE using **F5**.

It has no window of its own: the results are printed in the IDLE Shell. If a data root has been saved by the Data Manager (section 4.3), it uses that folder and prints "Using the saved data root: ..."; otherwise it asks you to choose the data root.

It prints fixed examples built around the sample data:
1. the list of instruments in the database;
2. NIFTY 5-minute bars for 17 Aug 26;
3. BANKNIFTY 5-minute bars for 19 Aug 26, including an incomplete 13:25 bar;
4. CONCOR's latest five daily closes;
5. a deliberate unsupported-timeframe error and its message;
6. the same data at every supported timeframe, from 1 minute to monthly: NIFTY on 18 Aug 26, NIFTY for Aug–Oct 26, and CONCOR for Sep–Oct 26.

Each example runs separately. If your database does not contain that instrument or those dates, that example prints "Not shown - ..." with the reason and the next example continues. The program only reads: it does not change the database. It is a demonstration, not a data importer or scanner.

If it reports that no data root was selected, choose the correct folder and run it again.

## 6. Q-MAP Universe Inventory — inspect your stock folder

### 6.1 What it does — and what it does not do

Open:

`tools\QMAP_Universe_Inventory.py`

Run it from IDLE using **F5**.

The window title is **Q-MAP Universe Inventory (read-only)**.

This tool reads the files in the stock-data folder you choose, including files in its subfolders. It prepares an Excel workbook describing the available files, symbols, dates, formats and potential data-quality matters.

**It does not import data into Q-MAP. It does not change your source files. It does not choose your final pilot stocks.** It reports possible duplicates, conflicts, large moves and eligibility flags for you to review.

### 6.2 Section 1 — Input: stock-data folder

Click **Browse...** and choose the folder containing the stock files you want to inspect.

The small count beside the input shows how many files were found. The program includes files in subfolders too, so choose the top-level folder you actually intend to examine.

Before running it on your complete stock collection, try a small folder first and check that the workbook looks sensible.

### 6.3 Section 2 — Output: Excel workbook

Click **Save As...** and choose the name and location for the Excel workbook.

The suggested filename looks like:

`Q-MAP_Universe_Inventory_14_Nov_26_153000.xlsx`

Save it outside the source-data folder (the program refuses a location inside the folder being inspected) and outside the Q-MAP program folder.

### 6.4 Section 3 — Options

The thresholds are fixed by the inventory design. The current screen explains them as:
- ±15% open or close moves versus the previous close;
- 20 identical consecutive volume values;
- 800-row and 2,500-row history checks;
- a 0.05 price tick grid, **reported only** (the inventory does not decide that an unverified tick rule is valid).

There are no user-adjustable threshold controls in this screen.

### 6.5 Run inventory

Click **Run inventory**.

Watch **Progress / Status**, the file counter and **Live log**. When it finishes, the status should say **Finished. Workbook saved.**

If it fails, the window says to see the log. Save the full error information for review.

### 6.6 Understanding the workbook

The workbook contains 12 sheets:

| Sheet | What you will find there |
|---|---|
| Summary | Overall counts, formats, large moves, coverage and other headline checks |
| Files | One row for each successfully inspected file |
| Symbols | Files grouped by symbol, including duplicate/conflict status |
| Format_Variants | File formats found |
| Problems | Unsupported, unreadable, empty or otherwise problematic files |
| Universe_Calendar | Dates and how many files have data on each date |
| Large_Moves | Large open or close moves for review |
| Moves_By_Date | For each date with a large move, how many files show one (many files on one date suggests a market-wide event) |
| Absences_For_Review | Periods where a stock has no file data, for review |
| Coverage | Coverage and naming checks |
| Pilot_Eligibility | Eligibility flags for later review |
| Notes | Important explanations and limitations |

Read **Summary** first, then **Problems**, **Symbols**, **Large_Moves**, **Absences_For_Review** and **Pilot_Eligibility**.

Important interpretations:
- Files with identical content (same SHA-256 fingerprint) are reported as identical duplicates.
- Files that differ are a conflict for your review. The tool does not choose one or merge them.
- Large moves are reported for G-03 review. The tool does not verify or unblock them.
- Missing dates are shown for review; they are not automatically declared errors.
- Pilot eligibility contains flags only. It is not an approved final stock list.
- At the end, the tool checks the fingerprints of a sample of source files again (not every file). The workbook reports whether any file in that sample changed during the scan.
- Every discovered file is recorded in either **Files** or **Problems**; an unsupported file type is listed under **Problems**.

Do not delete source files or resolve conflicts solely on the basis of an inventory flag. Inspect the original files and decide what action is justified.

## 7. Q-MAP EMA Trend Alignment Scanner

### 7.1 What it does

Open:

`apps\QMAP_EMA_Scanner.py`

Run it from IDLE using **F5**.

The window title is:

**Q-MAP EMA Scanner (provisional: D-EMA-11/12 pending)**

This scanner analyses daily NSE stock data already imported into Q-MAP. It does not scan arbitrary files in a folder. First load the required daily stock data using the Data Manager.

It creates two files for each run:
- a JSON file containing the structured results and an integrity SHA-256;
- an Excel workbook for easier reading.

### 7.2 Section 1 — Input: Q-MAP data root and stocks

Choose the same Q-MAP data root that you used in the Data Manager.

Click **Load stock list**. The scanner lists the daily stock instruments registered in that database. If a data root has been saved by the Data Manager, the list loads automatically when the window opens.

CONCOR and INFY are registered in every new database, so they appear in the list even if you have not imported their files. A stock without imported data gives the status **NOT_APPLICABLE** with the message "... has no loaded data yet. Run the Data Manager's Initial load first."

When the list loads, the application automatically selects **all** listed stocks. The count shows how many are selected. The **Select all** button selects them all again.

For your first test, do not accidentally run the full universe. Click the one stock you want to test; use Ctrl-click to add or remove individual stocks from the selection. Check the selected count before running.

### 7.3 Section 2 — Output: folder for the run files

Click **Browse...** and select an output folder.

Use a separate folder for scanner reports. A folder inside the Q-MAP data root is refused. Do not choose the Q-MAP program folder either.

### 7.4 Section 3 — Options

**Analysis date(s), comma-separated**

Enter one or more dates, separated by commas. The accepted formats include:
- `06-Nov-26`
- `2026-11-06`

For example:

`06-Nov-26, 03-Feb-26`

Each date is a separate analysis date. The scanner also checks whether the stored data supports that date. If a stock's data ends before the requested date, the result may be insufficient under the currently applied provisional rule.

When the stock list is loaded, the application fills the date field with the latest date found in the available daily stock data if you have not already entered a date. Always review the date before running.

**Add the reference check (documented CONCOR/INFY cases, doc 10 B9.3 / doc 13)**

This is selected by default. It always runs the 11 documented CONCOR and INFY cases (whatever stocks you selected) and adds a **Reference_Check** sheet comparing them with the documented results.

Leave it selected only when CONCOR and INFY daily history has been imported into this data root. If either is missing, its rows show NOT_APPLICABLE and the verdict **DIFFERENT**; that is expected and is not a scanner fault. **MATCH** is expected when the imported CONCOR and INFY files contain the same history as the documented reference files (data to 06-Nov-26). While the CONCOR large moves are unverified, several CONCOR cases are expected to be INVALID_DATA, and that counts as a MATCH.

**Add the 800-row EMA table per result (for Excel verification, doc 10 B9.2)**

This is also selected by default. It adds a detailed table for each result showing the daily close and EMA values through the 800-row analysis window.

The scanner's current defaults are:
- short EMA: 20;
- medium EMA: 50;
- long EMA: 200;
- EMA slope lookback: 10 bars;
- calculation window: 800 bars;
- tie band: 0.

These are fixed defaults in the current application. There are no screen controls to change these parameters.

### 7.5 Run EMA scanner

Click **Run EMA scanner**.

The application shows progress and writes messages to **Live log**. When finished, it says **Finished. Files saved.**

If the run fails, the status says **The run failed - see the log.** Keep the full log and do not interpret a partial run as a completed scan.

### 7.6 The two output files

The files look like:

`Q-MAP_Run_14_Nov_26_153000.json`

`Q-MAP_Run_Report_14_Nov_26_153000.xlsx`

The Excel workbook contains these main sheets:
- **Summary** — number of runs and results, status counts, and explicit notes about provisional rules and combined scoring.
- **Scanner_Results** — one row per stock/date, including status, score, state, the six comparison signals, EMA values and messages. When the reference check is selected, the reference cases also appear here as rows.
- **Reference_Check** — appears when the reference-check option is selected.
- **Data_Warnings** — data warnings and issues connected to the results.
- **Run_Settings** — the settings and dates used in the run.
- **EMA_...** sheets — detailed 800-row tables, when the detail option is selected.

The JSON file stores full-precision values and includes a SHA-256 integrity value for the core result sections. The Excel workbook formats the values for reading; it is not the authoritative full-precision data file.

### 7.7 Understanding the scanner's score and status

The score is on a 0–100 scale and is built from six trend-alignment comparisons:
- close above EMA 20;
- close above EMA 50;
- close above EMA 200;
- EMA 20 above EMA 50;
- EMA 50 above EMA 200;
- EMA 50 rising compared with its value 10 bars earlier.

Each of the six comparisons can contribute **+1** when bullish, **-1** when bearish or **0** when tied. Q-MAP adds those six values to get a net score from -6 to +6, then converts that net figure to the 0–100 scale using `50 + (50 × net ÷ 6)`. For example, net +6 gives 100, net 0 gives 50, and net -6 gives 0. A score near 100 therefore means the comparisons are strongly aligned bullish; a score near 0 means they are strongly aligned bearish. A score around 50 means the directional signals balance out.

This is not simply a count of how many comparisons are positive: bearish comparisons subtract from the net and ties contribute zero.

The state is shown as one of:
- **BULLISH** — net score +4, +5 or +6;
- **NEUTRAL_LEANING_BULLISH** — net score +3;
- **NEUTRAL** — net score from -2 to +2;
- **NEUTRAL_LEANING_BEARISH** — net score -3;
- **BEARISH** — net score -4, -5 or -6.

These labels describe the balance of the six EMA comparisons. They are not separate predictions.

The score is not a probability of profit, a buy/sell instruction or a guarantee of future movement. It is a rule-based summary of the six checks.

### 7.8 Important — provisional rules D-EMA-11 and D-EMA-12

The scanner's core methodology D-EMA-01 to D-EMA-10 is approved. Two additional rules are still proposals awaiting your decision:

- **D-EMA-11:** how to treat data that ends before the requested analysis date.
- **D-EMA-12:** how to round values before comparisons and store the score.

The current code applies these two rules provisionally so that their practical effect can be inspected. Results are labelled **Provisional result** and the output records the provisional rules. The scanner version remains 0.9.0 rather than the final 1.0.0.

Treat the output as provisional until you have reviewed and decided on D-EMA-11 and D-EMA-12. Do not remove the provisional warning or treat those rules as approved simply because the program has produced a score.

### 7.9 Combined scoring is not available yet

The workbook states that combined scoring has not been produced because it belongs to M5 and requires the Owner's approved scoring profile and weights (G-10).

Do not expect a combined score from the current EMA scanner. A second scanner and combined scoring are separate future work, not current screen options.

## 8. Common situations and what to do

| What you see | What it means / what to do |
|---|---|
| Python version is not 3.12.10 | Stop. Open IDLE belonging to Python 3.12.10 and repeat the environment check. |
| A package is missing or its version differs | Run the installer from the correct IDLE. Repeat the environment check. If it still differs, preserve the output and stop. |
| Data Manager says to choose a data root | Click **Browse...** in section 2 and select the correct Q-MAP data root. |
| Data Manager says to add at least one source file | Click **Add files...** and select the files you intend to import. |
| A stock's status is NOT_APPLICABLE ("has no loaded data yet") | That stock is registered but its data has not been imported into this data root. Import it with the Data Manager first. |
| Scanner says to choose an output folder | Use **Browse...** and select an existing folder for the reports. |
| Scanner says to choose at least one stock and one analysis date | Select one or more stocks and enter a date. |
| Scanner reports INVALID_DATA | A continuity-blocking G-03 issue overlaps the 800-bar analysis window. Read the issue details and resolve it only through the Owner verification process; do not bypass it. |
| Scanner reports INSUFFICIENT_DATA | There are not enough usable bars or the requested date is not supported under the current provisional rule. Read the message for the reason. |
| An inventory file appears on Problems | The file could not be inspected normally. Check the exact problem in the Problems sheet and the original file. |
| An inventory symbol has differing files | Treat it as a source conflict. The inventory tool deliberately does not select or merge the files. |
| A program fails or closes unexpectedly | Do not keep retrying on the live database. Save the full IDLE Shell output and the application's Live log, note the steps you took, and report them. |

## 9. Important safety rules

1. Keep the Q-MAP data root outside the repository.
2. Keep your original source files unchanged.
3. Do not manually edit Parquet files, DuckDB files, catalogue tables or quarantine files.
4. Do not delete a data-quality issue just because it is inconvenient.
5. Do not verify a G-03 continuity issue unless you have checked that exact occurrence and can state your basis.
6. Do not approve a historical revision until you have compared and accepted it.
7. Do not treat an inventory eligibility flag as a final pilot-stock decision.
8. Do not treat EMA provisional results as final approval of D-EMA-11/12.
9. Keep backups and exported evidence safe. Do not put live databases, market-data archives, logs or reports into the public GitHub repository.

## 10. What is not yet part of the current application

The current merged code provides the Data Manager, the M2 retrieval example, the read-only Universe Inventory and the EMA Trend Alignment scanner.

The following should not be expected as available user features at this stage:
- a second analytical scanner;
- combined scoring;
- ORB strategy backtesting;
- broker connectivity or automatic trading;
- cloud data synchronisation;
- AI-generated market interpretations.

Those items are not enabled by the screens described in this guide.

## 11. How to report a problem

When something does not work, please record:

1. Which program you were using (Data Manager, Inventory, M2 Example or EMA Scanner).
2. What you clicked or entered immediately before the problem.
3. The exact message shown on the screen.
4. The complete IDLE Shell output, copied as text if possible.
5. The Live log text, if the application has one.
6. Your Python version and whether the environment check showed TRUE.
7. Whether the problem happened with one file or multiple files.

Do not send passwords, access tokens or private account information. Do not email or upload your full live database or market-data archive into the public repository.

---

## 12. Current baseline and testing status

This guide describes the application code on GitHub `main` at commit:

`001e03a5ee1a03527b595876b2d4f0beaee92e9c`

The guide itself was added by PR #11, which changed no application code.

Merged changes:
- PR #8 — Data Manager G-03 verification, data-summary export and IDLE installer.
- PR #10 — EMA Trend Alignment scanner.
- PR #9 — read-only Universe Inventory and its inventory calculation tests.

The reported full test suite on the updated PR #9 branch was 181 tests, with 0 failures, 0 errors and 0 skipped, using Python 3.12.10 and the exact pinned packages in a Linux development environment.

**Windows testing has not yet been completed.** The Owner's first Windows run is the next practical validation step. The first run should begin with the environment check and a small, controlled data sample.

---

*This guide explains how to use the current merged applications. The approved blueprints and design documents remain the authority for system requirements and decisions. Where this guide is unclear or appears inconsistent with the current application, follow the actual screen and stop to request clarification rather than guessing.*
