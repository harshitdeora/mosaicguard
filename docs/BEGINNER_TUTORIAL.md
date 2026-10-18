# Beginner walkthrough

This walkthrough uses two tiny fictional CSV files. It takes about five minutes and does not require any real personal data.

## 1. Start the app

From the repository folder, run:

```powershell
docker compose up -d
```

Open `http://127.0.0.1:8027`. On the first visit, create the local owner account. Keep the generated `.env` file backed up securely because it contains the key needed to read imported data.

## 2. Load the simple example

On the home screen, choose **Explore example** under **Explore a simple example**. MosaicGuard creates a workspace and imports:

- `anonymous_feedback.csv`: six fictional responses intended for sharing.
- `workshop_registration.csv`: seven fictional registrations the audience already possesses.

You can also create a normal workspace and upload the same files from `examples/simple/` yourself.

## 3. Describe the release scenario

Open **Release scenarios** and enter:

- Scenario name: `Workshop feedback review`
- Intended audience: `Workshop sponsor`
- Purpose: `Share feedback for programme improvement`
- Candidate versions: `anonymous_feedback.csv`
- Information available to this audience: `workshop_registration.csv`
- Reference coverage: `Complete fictional registration list for these four workshops`

Add one mapping rule:

- Source: `anonymous_feedback.csv`
- Source component: `event_code`
- Target: `workshop_registration.csv`
- Target component: `event_code`
- Meaning: `Same fictional workshop event`
- Subject unit: `event`
- Cohort/time context: `Same October 2026 workshop programme`
- Predicate: `exact`
- Confirm the mapping after reviewing it.

For a defensible fictional endpoint count, choose `workshop_registration.csv` as the anchor reference, select `member_id`, and enter: `Each fictional member_id is unique in this complete registration list.`

Optionally select `city` and `age_group` as within-file diagnostic columns. Mark `feedback_topic` as sensitive during import review if you uploaded the files manually. Add a utility count grouped by `city` if you want a simple measurement to preserve during repairs.

Save the scenario snapshot.

## 4. Run and read the audit

Open **Audits & findings** and run the saved scenario. Expand the linkage finding.

The full six-row denominator should be assessed. Responses from `EVT-200` and `EVT-400` each narrow to one registered-member candidate. Responses from `EVT-100` have two candidates, and responses from `EVT-300` have three.

The result does not prove who wrote a response. It shows what the selected audience could infer under the exact data and mapping assumptions you supplied. A missing match would also not prove safety.

## 5. Compare a repair

Open **Repair comparison**, select `anonymous_feedback.csv`, choose `event_code`, and test **Drop column** with a name such as `Remove event code`.

MosaicGuard creates a new immutable branch and reruns the audit. The original remains unchanged. Review both the blocked linkage path and the utility results: removing a join field changes what can be linked, while the city-based count remains available.

You can also try suppressing rare values or removing a different column. Each recipe is evaluated independently; MosaicGuard does not silently pick a “safe” version.

## 6. Review and export

Choose the original or repaired audit in **Release history**. Read the residual-exposure and coverage notes, acknowledge them, and build the ZIP package. Downloading prepares an artifact locally; it does not send data to the audience.

Use **Record as released** only after you have actually shared that package. This records the audience and date so future reviews include historical exposure.

## What the example teaches

The candidate file looks anonymous because it contains no names. The audience's registration file changes the question: an event attended by only one registered member can make a response much easier to associate with someone. MosaicGuard makes that reasoning explicit, measures how many candidate records remain, tests practical changes, and preserves evidence for the release decision.
