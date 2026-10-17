import { test, expect } from "@playwright/test";

test("invalid input, multiple candidate analytics, incomplete scope and failed repair remain explicit", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill("browser-owner");
  await page
    .getByLabel("Password", { exact: true })
    .fill("Synthetic-browser-password-42");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page
    .getByRole("button", { name: "New workspace", exact: true })
    .click();
  const name = "Boundary review " + Date.now();
  await page.getByLabel("Workspace name", { exact: true }).fill(name);
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page.getByRole("button", { name: "Datasets", exact: true }).click();
  await page
    .getByLabel("Choose CSV file", { exact: true })
    .setInputFiles({
      name: "invalid.csv",
      mimeType: "text/csv",
      buffer: Buffer.from("same,same\nA,B\n"),
    });
  await expect(page.getByRole("alert")).toContainText(
    "Headers must be nonblank, unique",
  );
  await page
    .getByRole("button", { name: "Delete pending invalid.csv", exact: true })
    .click();
  for (const file of [
    { name: "cohort-one.csv", csv: "segment,measure\nA,2\nA,4\n" },
    { name: "cohort-two.csv", csv: "segment,measure\nA,10\nB,12\n" },
  ]) {
    await page
      .getByLabel("Choose CSV file", { exact: true })
      .setInputFiles({
        name: file.name,
        mimeType: "text/csv",
        buffer: Buffer.from(file.csv),
      });
    await expect(
      page.getByRole("heading", { name: file.name, exact: true }),
    ).toBeVisible();
    await page
      .getByLabel("measure type", { exact: true })
      .selectOption("number");
    await page
      .getByLabel("One row represents", { exact: true })
      .selectOption("person");
    await page
      .getByRole("button", { name: "Confirm and import", exact: true })
      .click();
    await expect(
      page
        .getByRole("row")
        .filter({ has: page.getByText(file.name, { exact: true }) })
        .getByRole("button", { name: "Inspect", exact: true }),
    ).toBeVisible();
  }
  await page
    .getByRole("button", { name: "Release scenarios", exact: true })
    .click();
  await page
    .getByRole("group", { name: "Candidate versions to share", exact: true })
    .getByLabel("cohort-one.csv")
    .check();
  await page
    .getByRole("group", { name: "Candidate versions to share", exact: true })
    .getByLabel("cohort-two.csv")
    .check();
  for (const file of ["cohort-one.csv", "cohort-two.csv"]) {
    await page
      .getByLabel("Candidate for analytical controls", { exact: true })
      .selectOption({ label: file });
    await page
      .getByRole("group", {
        name: "Within-file quasi-identifier combination · " + file,
        exact: true,
      })
      .getByLabel("segment", { exact: true })
      .check();
    await page
      .getByRole("group", {
        name: "Protected columns (cannot be transformed or removed)",
        exact: true,
      })
      .getByLabel("measure", { exact: true })
      .check();
    await page
      .getByLabel("Analytical goal", { exact: true })
      .selectOption("mean");
    await page
      .getByLabel("Group / date column", { exact: true })
      .selectOption({ label: "segment" });
    await page
      .getByLabel("Numeric value", { exact: true })
      .selectOption({ label: "measure" });
    await page
      .getByRole("button", { name: "Add analytical requirement", exact: true })
      .click();
  }
  await page
    .getByRole("button", { name: "Save scenario snapshot", exact: true })
    .click();
  await page.getByRole("button", { name: "Run audit", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Findings and evidence", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "No eligible confirmed linkage path. Multi-file linkage is unassessed.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(page.locator(".finding")).toHaveCount(2);
  await page.screenshot({
    path: "../docs/screenshots/incomplete-scope.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Repair comparison", exact: true })
    .click();
  await page
    .getByLabel("Column", { exact: true })
    .selectOption({ label: "segment" });
  await page
    .getByLabel("Transformation", { exact: true })
    .selectOption("numeric_bucket");
  await page
    .getByRole("button", { name: "Add to recipe", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Evaluate full repair", exact: true })
    .click();
  await expect(
    page.getByText(/Numeric buckets require a reviewed numeric column/),
  ).toBeVisible();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("Type “" + name + "” to delete", { exact: true })
    .fill(name);
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
});
