import { test, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
test("unfamiliar CSV: review, scenario, real audit, repairs, export, resume and deletion", async ({
  page,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill("browser-owner");
  await page
    .getByLabel("Password", { exact: true })
    .fill("Synthetic-browser-password-42");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "New workspace", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "New workspace", exact: true })
    .click();
  const workspace = "Browser acceptance " + Date.now();
  await page.getByLabel("Workspace name", { exact: true }).fill(workspace);
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page.getByRole("button", { name: "Datasets", exact: true }).click();
  async function importCSV(
    name: string,
    csv: string,
    role: string,
    dates: string[] = [],
    numeric: string[] = [],
  ) {
    await page
      .getByLabel("Choose CSV file", { exact: true })
      .setInputFiles({ name, mimeType: "text/csv", buffer: Buffer.from(csv) });
    await expect(
      page.getByRole("heading", { name, exact: true }),
    ).toBeVisible();
    await page.getByLabel("Delimiter", { exact: true }).selectOption(";");
    await page
      .getByRole("button", { name: "Update parsing preview", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Confirm and import", exact: true }),
    ).toBeVisible();
    for (const col of dates) {
      await page
        .getByLabel(col + " type", { exact: true })
        .selectOption("date");
      await page
        .getByLabel(col + " date format", { exact: true })
        .selectOption("%Y-%m-%d");
    }
    for (const col of numeric)
      await page
        .getByLabel(col + " type", { exact: true })
        .selectOption("number");
    await page.getByLabel("Dataset role", { exact: true }).selectOption(role);
    await page
      .getByLabel("One row represents", { exact: true })
      .selectOption("person");
    await page
      .getByRole("button", { name: "Confirm and import", exact: true })
      .click();
    await expect(
      page
        .getByRole("row")
        .filter({ has: page.getByText(name, { exact: true }) })
        .getByRole("button", { name: "Inspect", exact: true }),
    ).toBeVisible();
  }
  await importCSV(
    "observations-unfamiliar.csv",
    "token;occurred;team;score\r\n0001;2026-05-12;Blue;3\r\n0002;2026-05-13;Blue;5\r\n",
    "candidate",
    ["occurred"],
    ["score"],
  );
  await importCSV(
    "authorised-register.csv",
    "code;seen;entity_key\r\n0001;2026-05-12;FICT-A\r\n0002;2026-05-13;FICT-B\r\n",
    "reference",
    ["seen"],
  );
  await page
    .getByRole("button", { name: "Release scenarios", exact: true })
    .click();
  await page
    .getByRole("group", { name: "Candidate versions to share", exact: true })
    .getByLabel("observations-unfamiliar.csv")
    .check();
  await page
    .getByRole("group", {
      name: "Information available to this audience",
      exact: true,
    })
    .getByLabel("authorised-register.csv")
    .check();
  async function addRule(
    source: string,
    destination: string,
    sourceCol: string,
    targetCol: string,
    meaning: string,
  ) {
    await page
      .getByLabel("Source version", { exact: true })
      .selectOption({ label: source });
    await page
      .getByLabel("Destination version", { exact: true })
      .selectOption({ label: destination });
    await page
      .getByRole("group", {
        name: "Source components (selection order)",
        exact: true,
      })
      .getByLabel(sourceCol, { exact: true })
      .check();
    await page
      .getByRole("group", {
        name: "Destination components (matching order)",
        exact: true,
      })
      .getByLabel(targetCol, { exact: true })
      .check();
    await page.getByLabel("Intended meaning", { exact: true }).fill(meaning);
    await page
      .getByLabel("Predicate", { exact: true })
      .selectOption("compatible");
    await page
      .getByLabel(
        "I confirm the subject, component meanings, and time/cohort assumptions for this rule.",
        { exact: true },
      )
      .check();
    await page
      .getByRole("button", { name: "Profile fan-out", exact: true })
      .click();
    await expect(page.getByText(/possible record pairs/)).toBeVisible();
    await page
      .getByRole("button", { name: "Add confirmed rule", exact: true })
      .click();
  }
  await addRule(
    "observations-unfamiliar.csv",
    "authorised-register.csv",
    "token",
    "code",
    "Reviewed participant code within the same fictional cohort",
  );
  await addRule(
    "observations-unfamiliar.csv",
    "authorised-register.csv",
    "occurred",
    "seen",
    "Reviewed participation day within the same fictional cohort",
  );
  await page
    .getByLabel("Analytical goal", { exact: true })
    .selectOption("mean");
  await page
    .getByLabel("Group / date column", { exact: true })
    .selectOption({ label: "team" });
  await page
    .getByLabel("Numeric value", { exact: true })
    .selectOption({ label: "score" });
  await page.getByLabel("Maximum relative drift", { exact: true }).fill("0");
  await page
    .getByRole("button", { name: "Add analytical requirement", exact: true })
    .click();
  await page
    .getByRole("group", {
      name: "Protected columns (cannot be transformed or removed)",
      exact: true,
    })
    .getByLabel("team", { exact: true })
    .check();
  await page
    .getByRole("button", { name: "Save scenario snapshot", exact: true })
    .click();
  await page.getByRole("button", { name: "Run audit", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Findings and evidence", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /2 single-candidate record\/path pairs/ })
    .first()
    .click();
  await expect(
    page
      .getByText("One candidate under these assumptions", { exact: true })
      .first(),
  ).toBeVisible();
  fs.mkdirSync("../docs/screenshots", { recursive: true });
  await page.screenshot({
    path: "../docs/screenshots/audit-desktop.png",
    fullPage: true,
  });
  // Add a genuinely new audience-available export through the same browser import review.
  await page.getByRole("button", { name: "Datasets", exact: true }).click();
  await importCSV(
    "audience-extra.csv",
    "occurred;code\r\n2026-05-12;0001\r\n2026-05-13;0002\r\n",
    "available",
    ["occurred"],
  );
  await page
    .getByRole("button", { name: "Audits & findings", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run audit", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Release scenarios", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Revise this scope", exact: true })
    .first()
    .click();
  await page
    .getByRole("group", {
      name: "Information available to this audience",
      exact: true,
    })
    .getByLabel("audience-extra.csv")
    .check();
  await addRule(
    "observations-unfamiliar.csv",
    "audience-extra.csv",
    "occurred",
    "occurred",
    "Reviewed same participation day in the additional fictional export",
  );
  await addRule(
    "audience-extra.csv",
    "authorised-register.csv",
    "code",
    "code",
    "Reviewed participant code in the additional fictional export",
  );
  await page
    .getByRole("button", { name: "Save scenario snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run audit", exact: true }),
  ).toHaveCount(2);
  await page
    .getByRole("button", { name: "Run audit", exact: true })
    .last()
    .click();
  await expect(
    page.getByLabel("Select audit", { exact: true }).locator("option"),
  ).toHaveCount(2);
  await page
    .getByLabel("Before audit", { exact: true })
    .selectOption({ index: 1 });
  await page
    .getByLabel("After audit", { exact: true })
    .selectOption({ index: 2 });
  await page
    .getByRole("button", { name: "Compare addition", exact: true })
    .click();
  await expect(page.getByText(/New path from/).first()).toBeVisible();
  await page
    .getByRole("button", { name: "Repair comparison", exact: true })
    .click();
  async function addTransform(column: string, kind: string) {
    await page
      .getByLabel("Column", { exact: true })
      .selectOption({ label: column });
    await page.getByLabel("Transformation", { exact: true }).selectOption(kind);
    await page
      .getByRole("button", { name: "Add to recipe", exact: true })
      .click();
  }
  await page
    .getByLabel("Branch name", { exact: true })
    .fill("Unsuitable: statistic removed");
  await addTransform("score", "drop");
  await page
    .getByRole("button", { name: "Evaluate full repair", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Unsuitable: statistic removed",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "No tested satisfaction of your analytical requirements for this branch.",
      { exact: false },
    ),
  ).toBeVisible();
  // Rejecting an unsuitable option means leaving it unselected for export and testing another branch.
  await page
    .getByLabel("Branch name", { exact: true })
    .fill("Broader matches, useful means");
  await addTransform("token", "drop");
  await addTransform("occurred", "date_quarter");
  await page
    .getByRole("button", { name: "Evaluate full repair", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Broader matches, useful means",
      exact: true,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/repairs-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Release history", exact: true })
    .click();
  await page
    .getByLabel("Inspected audit / branch", { exact: true })
    .selectOption({
      label: await page
        .getByLabel("Inspected audit / branch", { exact: true })
        .locator("option")
        .filter({ hasText: "Broader matches, useful means" })
        .innerText(),
    });
  await page
    .getByLabel(
      "I reviewed residual findings, assumptions, unassessed records and coverage limits.",
      { exact: true },
    )
    .check();
  await page
    .getByRole("button", { name: "Build verified package", exact: true })
    .click();
  const dl = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download ZIP", exact: true })
    .last()
    .click();
  const download = await dl;
  const downloaded = await download.path();
  expect(downloaded).toBeTruthy();
  const python =
    process.platform === "win32"
      ? "../.venv/Scripts/python.exe"
      : "../.venv/bin/python";
  const verification = JSON.parse(
    execFileSync(python, ["../scripts/verify_package.py", downloaded!], {
      encoding: "utf-8",
    }),
  );
  expect(verification.verified).toBe(true);
  expect(fs.statSync(downloaded!).size).toBeGreaterThan(1000);
  await page.reload();
  await expect(
    page.getByRole("heading", {
      name: "A thoughtful release starts here.",
      exact: true,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/screenshots/overview-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.setViewportSize({ width: 1440, height: 1000 });
  const anon = await context.browser()!.newContext();
  const response = await anon.request.get(
    "http://127.0.0.1:8028/api/workspaces",
  );
  expect(response.status()).toBe(401);
  await anon.close();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("Type “" + workspace + "” to delete", { exact: true })
    .fill(workspace);
  await page
    .getByRole("button", {
      name: "Delete workspace and local data",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "A clearer view of what your data could reveal.",
      exact: true,
    }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
