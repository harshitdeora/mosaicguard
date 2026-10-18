# Hackathon demo data: anonymous training feedback

These files contain fictional people and events. They are safe to use in a public hackathon recording.

## The story

An organisation wants to share `anonymous_training_feedback.csv` with its HR analytics team. The file has no employee names or IDs, so it appears anonymous. HR already possesses `training_attendance_roster.csv`, which connects each training code to the employees who attended.

MosaicGuard tests whether the shared `course_code` can form a graph path from a feedback row to a small set of employees in the roster.

## Files

- `anonymous_training_feedback.csv` — the **candidate to share**, with eight anonymous responses.
- `training_attendance_roster.csv` — the **authorised reference**, with eight fictional employees.

## Expected baseline result

Confirm one exact mapping:

`anonymous_training_feedback.course_code` → `training_attendance_roster.course_code`

| Course | Feedback rows | Roster candidates per feedback row |
| --- | ---: | ---: |
| SAFE-101 | 2 | 2 |
| LEAD-202 | 1 | 1 |
| DATA-303 | 3 | 3 |
| DESIGN-404 | 2 | 2 |

The full eight-row candidate dataset should be assessed. The `LEAD-202` response has one roster candidate, while the other responses retain two or three candidates. This is scoped linkage evidence, not proof that the named employee wrote the response.

## Expected repair result

Test a branch that removes `course_code` from the candidate file. The confirmed course-code path is then blocked, so the branch should have no single-candidate result from that rule. MosaicGuard keeps the original unchanged and shows the loss of assessment coverage separately.

The complete recording walkthrough is in [`docs/HACKATHON_DEMO_VIDEO.md`](../../docs/HACKATHON_DEMO_VIDEO.md).
