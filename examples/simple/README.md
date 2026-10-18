# Beginner example: workshop feedback

These two files contain only fictional people and events.

- `anonymous_feedback.csv` is the candidate dataset an organisation plans to share. It has no name or member ID.
- `workshop_registration.csv` is information the intended audience already has. It links each event code to registered members.

The example asks a simple question: **can an audience combine the event code in an anonymous response with its registration list and narrow the response to one member?**

Expected result after confirming `anonymous_feedback.event_code` → `workshop_registration.event_code`:

| Event | Responses | Registered-member candidates per response |
| --- | ---: | ---: |
| EVT-100 | 2 | 2 |
| EVT-200 | 1 | 1 |
| EVT-300 | 2 | 3 |
| EVT-400 | 1 | 1 |

Two of the six responses therefore have one candidate under these assumptions. This is a reason to inspect the release, not proof that the named member wrote the response.

For the exact click-by-click flow, see [the beginner walkthrough](../../docs/BEGINNER_TUTORIAL.md).
