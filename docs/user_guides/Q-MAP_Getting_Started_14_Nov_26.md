# Q-MAP — Getting Started (Windows, Python 3.12.10, IDLE)

This page takes you from nothing to your first EMA scanner result. You do not need to type any commands. For more detail on any screen, see the [Owner's User Guide](Q-MAP_Owners_User_Guide_v1.0_14_Nov_26.md).

**Every program is started the same way:** open IDLE (Start menu → "IDLE (Python 3.12)"), choose **File → Open...**, select the `.py` file named below, then press **F5**. The program's window opens; messages also appear in the IDLE Shell.

---

## 1. What you need (once)

1. **Python 3.12.10** from python.org, installed with its normal options (IDLE and Tkinter are included).
2. **The Q-MAP files.** On https://github.com/BulluBhai/Q-Map-New check that the branch shows **main**, click **Code → Download ZIP**, and extract it, for example to `D:\Q-MAP\`. You get the folder `D:\Q-MAP\Q-Map-New-main\`.
3. **The packages.** Open `tools\QMAP_Install_Requirements.py` and press F5. Wait for **Done**.
4. **The check.** Open `tests\t_env_01_environment_check.py` and press F5. The last line must read `all_environment_checks_match: TRUE`. If anything says FALSE, stop and send me the IDLE Shell text.

## 2. Create a folder for Q-MAP's database

Make a new, empty folder **outside** the Q-MAP folder, for example `D:\QMAP_TEST_DATA`. This is the **data root**: Q-MAP keeps its database, reports, backups and logs there. Use a test folder for your first session, not your long-term database.

## 3. First data load

1. Open `apps\QMAP_Data_Manager.py` and press F5.
2. **Section 2:** click **Browse...** and choose your data-root folder.
3. **Section 1:** click **Add files...** and choose two or three source files, for example your CONCOR and INFY daily files.
4. Click **Run initial load**. Watch **Progress / Status** and the **Live log**.
5. When it says **Finished**, click **Check integrity**. It should say **Integrity check PASSED**.

**Which files can be loaded now?** Only these instruments are registered at present: **NIFTY** and **BANKNIFTY** (1-minute files), **CONCOR** and **INFY** (daily stock files) and **NIFTYIT** (daily index). Q-MAP recognises them by file name, for example `CONCOR.txt` or `INFY_daily ....parquet`. Any other file is reported as **NOT IMPORTED - ... not a registered instrument**, and nothing is changed for it. Other stocks are added in the pilot stage, after you approve the pilot list.

**Start small.** Do not load your full historical archive yet.

## 4. Look at the result

- **Live log:** each file shows how many rows were imported and how many were quarantined (rejected rows kept aside, never silently corrected).
- **Validation report:** the log prints its location: an Excel file in the data root's `reports` folder.
- **Export data summary...:** writes Excel-readable files (issues, quarantined rows, record counts) to a folder you choose outside the data root.
- **Awaiting your decision:** this list shows items only you can decide, such as large ±15% price moves (G-03). Leave them alone for now; the full guide explains them.

## 5. Run the EMA scanner

1. Open `apps\QMAP_EMA_Scanner.py` and press F5. It finds your data root and lists the loaded stocks by itself.
2. Click one stock (for example INFY). The count beside **Select all** should say **1 selected**.
3. **Section 2:** click **Browse...** and choose a folder for the reports (not inside the data root).
4. **Analysis date(s):** keep the date shown (the latest date in your data) or type one, for example `06-Nov-26`.
5. Keep the **reference check** ticked only if both CONCOR and INFY are loaded; otherwise untick it.
6. Click **Run EMA scanner**. It ends with **Finished. Files saved.**

## 6. Where the results are

In the report folder you chose there are two new files:

- `Q-MAP_Run_Report_<date_time>.xlsx` — open this one. Its **Scanner_Results** sheet has one row per stock and date: the **status**, the **score** (0–100) and the **state** (BULLISH, NEUTRAL, BEARISH ...).
- `Q-MAP_Run_<date_time>.json` — the complete, full-precision record of the same run.

How to read the status:

| Status | Meaning |
|---|---|
| OK | A score was calculated. |
| INVALID_DATA | An unverified ±15% move lies in the last 800 trading days, so no score is given until you verify that move (G-03). |
| INSUFFICIENT_DATA | Fewer than 800 trading days, or the data ends before the requested date. |
| NOT_APPLICABLE | The stock has no loaded data in this data root. |

All results are labelled **provisional** until you decide the two open rules D-EMA-11 and D-EMA-12. The score describes trend alignment; it is not a buy/sell recommendation.

## 7. Close and reopen

Close any Q-MAP window with its normal **X** button once it is not working on something. Your data stays in the data root. Next time, open the program again (IDLE → File → Open → F5): the Data Manager and the EMA Scanner remember the data root you last used for a load or update, and the stored data is still there. No reload is needed.

## 8. If something goes wrong

1. Do not retry repeatedly and do not delete or edit files in the data root.
2. Note what you clicked and the exact message on the screen.
3. Send me:
   - the complete IDLE Shell text (select all, copy);
   - the program's **Live log** text;
   - the newest file in the data root's `logs` folder;
   - the `EV12_environment_....txt` file from the `tests` folder.
4. Never send or upload your whole data folder or market-data archive.
