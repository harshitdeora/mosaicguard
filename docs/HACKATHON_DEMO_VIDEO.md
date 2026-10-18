# Hackathon demo video: exact recording walkthrough

This walkthrough is designed for a three-to-four-minute Graph Hacks submission. It uses only fictional data and demonstrates a real FalkorDB-backed audit, a graph-derived finding, and a measured repair.

## Before recording

1. Download or open these two files:
   - [`anonymous_training_feedback.csv`](../examples/hackathon_demo/anonymous_training_feedback.csv)
   - [`training_attendance_roster.csv`](../examples/hackathon_demo/training_attendance_roster.csv)
2. Open the live app: <https://mosaicguard-production.up.railway.app/>
3. Sign in and close unrelated browser tabs and notifications.
4. Use a clean browser window at 100% zoom. Keep this guide on another device if possible.
5. Do one rehearsal before recording so background audits have time to finish.

## What you are demonstrating

An organisation wants to share anonymous employee training feedback with HR. The candidate CSV contains no name or employee ID. HR already has an attendance roster. A shared `course_code` creates this graph path:

`Feedback row` → `course_code` → `Attendance record` → `employee_id`

For `LEAD-202`, only one employee appears in the roster. MosaicGuard therefore reports one single-candidate path record under the stated assumptions. It does not claim that the person definitely wrote the response.

## Click-by-click recording plan

### Scene 1 — State the problem (0:00–0:25)

**On screen:** Show the two CSVs briefly, with the headers and a few rows visible.

**Say:**

> “This is MosaicGuard. I want to share an anonymous employee training survey with HR. The survey has no names or employee IDs, but HR already has the attendance roster. I will use a graph audit to test whether the two files can still be linked.”

Point out `course_code` in both files. In the roster, point out that `LEAD-202` has only one attendee.

### Scene 2 — Create a workspace (0:25–0:40)

1. Sign in to MosaicGuard.
2. On the home page, under **Use my CSVs**, click **Create a workspace**.
3. In **Workspace name**, enter `Graph Hacks training demo`.
4. Click **Create workspace**.

**Say:**

> “I start with a private workspace. The source versions are immutable, so later repairs cannot overwrite the original evidence.”

### Scene 3 — Import the anonymous survey (0:40–1:05)

1. Click **Import a CSV** or open **Datasets** in the left navigation.
2. Click **Choose a file**.
3. Select `anonymous_training_feedback.csv`.
4. Leave **Encoding** as `UTF-8 / BOM`, **Delimiter** as `Comma`, and **First record is a header** checked.
5. Click **Reveal local sample values** so viewers can see the fictional rows.
6. Under **Describe the columns**:
   - Keep `course_code`, `department`, `office`, and `feedback_topic` as **Text / identifier**.
   - Set `rating` to **Numeric** if it is not already suggested.
   - Check **Sensitive** for `rating` and `feedback_topic`.
   - Do not check **Identifier** for any candidate column.
7. Set **Dataset role** to **Candidate to share**.
8. Set **One row represents** to **person**.
9. Click **Confirm and import**.

**Say:**

> “This is the candidate file we plan to share. I mark the survey answer fields as sensitive, and I do not pretend that the course code is a unique person identifier.”

### Scene 4 — Import the attendance roster (1:05–1:30)

1. Click **Choose a file** again.
2. Select `training_attendance_roster.csv`.
3. Leave the CSV parsing settings unchanged and click **Reveal local sample values**.
4. Under **Describe the columns**:
   - Keep every column as **Text / identifier**.
   - Check **Identifier** for `employee_id` and `employee_name`.
5. Set **Dataset role** to **Authorised reference**.
6. Set **One row represents** to **person**.
7. Click **Confirm and import**.

**Say:**

> “This second file represents information the intended audience already has. The graph will use tokenised values rather than placing plaintext names in FalkorDB.”

### Scene 5 — Define the audience and graph rule (1:30–2:20)

1. Open **Release scenarios**.
2. In **1. Describe the release**, enter:
   - **Scenario name:** `Anonymous training feedback review`
   - **Intended audience:** `HR analytics team`
   - **Purpose:** `Share training feedback trends without exposing individual respondents`
3. Under **Candidate versions to share**, check `anonymous_training_feedback.csv`.
4. Under **Information available to this audience**, check `training_attendance_roster.csv`.
5. In **Reference coverage and limitations**, enter `Complete fictional attendance roster for the four October 2026 training sessions.`
6. In **2. Confirm meaningful relationships**:
   - Set **Source version** to `anonymous_training_feedback.csv`.
   - Set **Destination version** to `training_attendance_roster.csv`.
   - Under **Source components**, check only `course_code`.
   - Under **Destination components**, check only `course_code`.
   - Verify the line reads `course_code → course_code`.
   - **Intended meaning:** `Both values refer to the same employee training session`
   - **Subject unit:** `person`
   - **Time / cohort context:** `Same October 2026 employee training programme`
   - **Predicate:** `Exact / composite exact`
7. Click **Profile fan-out** and briefly show the possible match count.
8. Check **I confirm the subject, component meanings, and time/cohort assumptions for this rule.**
9. Click **Add confirmed rule**.

**Say:**

> “Equal column names alone are not evidence. I explicitly confirm what the relationship means, whose context it concerns, and the time period. This confirmed rule becomes a graph-query tool for the audit.”

### Scene 6 — Preserve useful analysis and save (2:20–2:45)

1. In **3. Define diagnostics and analytical requirements**, leave the within-file quasi-identifier boxes clear for this focused demo.
2. Under **Protected columns**, check `department`.
3. Set **Analytical goal** to **Counts by category**.
4. Set **Group / date column** to `department`.
5. Set **Maximum relative drift** to `0`.
6. Click **Add analytical requirement**.
7. Leave **Minimum retained-row proportion** as `1` and **Candidate review threshold** as `5`.
8. Expand **Optional: confirmed identity anchor**.
9. Set **Anchor reference version** to `training_attendance_roster.csv`.
10. Under **Entity-key components**, check `employee_id`.
11. Enter `Each employee_id is unique in this complete fictional attendance roster.`
12. Click **Save scenario snapshot**.

**Say:**

> “I also tell MosaicGuard what utility must survive the repair: department-level counts. The employee ID is a defensible synthetic identity anchor for counting distinct roster candidates.”

### Scene 7 — Run and explain the graph audit (2:45–3:20)

1. Open **Audits & findings**.
2. Find `Anonymous training feedback review` and click **Run audit**.
3. Wait for the background activity to finish.
4. Show the four result cards. The expected baseline is:
   - **Candidate records:** `8`
   - **Single-candidate path records:** `1`
   - **Assessed path records:** `8`
   - **Unassessed path records:** `0`
5. Under **Findings and evidence**, expand the linkage finding.
6. Point to the `LEAD-202` evidence path and its one candidate. Then contrast it with `SAFE-101`, `DATA-303`, or `DESIGN-404`, which have multiple candidates.

**Say:**

> “The graph assessed all eight feedback rows. Seven rows still map to two or three possible employees. The LEAD-202 response maps to one roster record because only one person attended that session. This is a reason to review the release; it is not proof that the employee wrote the response.”

### Scene 8 — Test a repair (3:20–3:50)

1. Open **Repair comparison**.
2. In **Branch name**, enter `Remove training code before sharing`.
3. Choose candidate `anonymous_training_feedback.csv` if the page asks for it.
4. Set **Column** to `course_code`.
5. Set **Transformation** to **Remove column**.
6. Click **Add to recipe**.
7. Click **Evaluate full repair**.
8. Wait for the full re-audit and show the resulting branch card.
9. Point out that the baseline had `1` single-candidate path record, while this rule no longer produces a single-candidate path. Also show the retained rows and the department-count utility status.

**Say:**

> “MosaicGuard creates a separate immutable branch, removes the course code, and runs the complete graph audit again. The original remains available for comparison. The reviewed linkage path is blocked, all rows are retained, and the department-count requirement remains measurable. The reduced assessment coverage is still shown rather than being called proof of safety.”

### Scene 9 — Close with the product value (3:50–4:05)

1. Click **Review export options**.
2. Show the selected branch, residual findings, coverage, and package contents.
3. Do not click **Record as released** during the hackathon demo unless you want to demonstrate local release history.

**Say:**

> “MosaicGuard turns connected-data risk into an explainable release decision: explicit audience assumptions, deterministic FalkorDB queries, inspectable evidence, measured repairs, and a verified package. That is why the project fits Track 01: Agents That Act on Connected Data.”

## If a background job takes longer during recording

Pause silently for a few seconds or cut the wait from the final video. Do not reload while an audit or repair is running. The result appears when the background activity completes.

## What not to say

- Do not say MosaicGuard proves an employee wrote a response.
- Do not call a zero-result repair “guaranteed anonymous” or “safe.”
- Do not say an AI model decides the finding. The recorded result comes from deterministic graph queries under the confirmed scenario.
- Do not upload real employee information in a public demonstration.

## Final submission checklist

- The live URL opens before recording.
- Both CSVs import with the roles above.
- The scenario contains one confirmed `course_code` rule and the `employee_id` anchor.
- The baseline audit shows eight candidate records and one single-candidate path record.
- The repair branch is visible beside the baseline result.
- The final frame shows the live project name, the evidence, and the Track 01 fit.
