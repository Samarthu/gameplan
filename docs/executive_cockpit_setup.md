# Executive Cockpit setup (Gameplan)

The CEO Executive Cockpit lives at `/g/executive` and aggregates team execution health from Gameplan (tasks, projects, goals, sprints). It complements Dieture 2.2 KPI dashboards (Weekly Scorecard, Control Dashboard) via optional links in **GP Settings**.

## Management view (what the CEO sees)

1. **Summary tiles** — teams in red, leads at risk, teams without a lead, people behind, overdue total, completions this week.
2. **CEO insights** — auto bullets (e.g. missing lead, lead accountable for red team, top overdue person).
3. **Team lead accountability** — troubled teams with lead name, health, and plain-English insight.
4. **Who is not performing** — people ranked by overdue tasks (critical vs struggling).
5. Team health, initiatives, escalations.

Assign **Team Lead** on each GP Team Overview. Without it, the cockpit shows “Not assigned” and leadership accountability is unclear.

## Access

Users who can open the cockpit:

- **Administrator** or **System Manager**
- **Gameplan Admin**
- Users listed under **GP Settings → Executive Dashboard Users**

## GP Settings

Open **GP Settings** in Desk (Gameplan module) and configure:

| Field | Purpose |
|-------|---------|
| Enable Executive Dashboard | Master switch |
| Executive Dashboard Users | CEO and other executives without Gameplan Admin role |
| Control Dashboard URL | External link button (e.g. Dieture 2.2 Control Dashboard HTML) |
| Weekly Scorecard URL | External link button |
| Health thresholds | Overdue counts, stale days, sprint completion % |

Run `bench migrate` after installing or upgrading Gameplan.

## Align teams with the Operating System

Create four **GP Teams** and assign **Team Lead** on each team overview:

| GP Team | Lead (OS role) |
|---------|----------------|
| Growth | Head of Growth |
| Operations | Head of Operations |
| Customer Experience | Head of CX |
| Product & Nutrition | Head of Product / Nutrition |

## Projects and goals

- One **GP Project** per major initiative under the correct team.
- Add up to three **goals** per project; update status weekly: On Track / At Risk / Done.
- Keep **progress** and tasks current.

## Task hygiene

- Every task: **due date**, **assignee**, linked **project** and **team**.
- Use **sprints** for weekly cadence; mark sprint Active with start/end dates.
- Close or reschedule overdue work before Monday Growth Review.

## Monday workflow

1. Sunday / Monday AM: Heads update goals and sprints.
2. CEO opens `/g/executive` and reviews red/amber teams and escalations.
3. Monday Growth Review: use escalations to assign owners and due dates on new tasks.

## Build frontend after code changes

```bash
cd apps/gameplan/frontend && yarn build
bench --site <your-site> migrate
bench --site <your-site> clear-cache
```

## Health rules (defaults)

- **Red:** 5+ overdue open tasks, any goal At Risk, or active sprint past end date below 70% completion.
- **Amber:** 1–4 overdue, 3+ stale in-progress tasks, or open project unchanged 14+ days.
- **Green:** otherwise.

Thresholds are configurable in GP Settings.
