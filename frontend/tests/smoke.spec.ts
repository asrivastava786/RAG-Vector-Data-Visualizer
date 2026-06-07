import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page, request }) => {
  const response = await request.post("http://127.0.0.1:8000/api/auth/login", {
    data: {
      email: "owner@demo.example.com",
      password: "ChangeMeDemo123!"
    }
  });
  const tokens = await response.json();
  await page.addInitScript((accessToken: string) => {
    window.localStorage.setItem("rvo_access_token", accessToken);
  }, tokens.access_token);
});

test("dashboard renders real project links and navigates", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByText("RAG Visual Optimizer")).toBeVisible();
  await expect(page.getByText("Workspace Dashboard")).toBeVisible();
  await expect(page.getByText("HR Policy Assistant Optimization")).toBeVisible({ timeout: 20_000 });

  const projectRow = page.getByRole("row", { name: /HR Policy Assistant Optimization/ });
  await projectRow.getByRole("link", { name: "Query", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/.+\/query/);
  await expect(page.getByRole("heading", { name: "Query Analysis" })).toBeVisible();

  await page.getByRole("link", { name: "Comparison", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/.+\/compare/);
  await expect(page.getByRole("heading", { name: "Strategy Comparison" })).toBeVisible();

  await page.getByRole("link", { name: "Data Layer", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/.+\/data-layer/);
  await expect(page.getByRole("heading", { name: "Polyglot Data Layer Strategy" })).toBeVisible();
  await expect(page.getByText("Recommended Architecture")).toBeVisible();

  await page.getByRole("link", { name: "Reports", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/.+\/reports/);
  await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();

  await page.goto("/dashboard");
  await page.getByRole("link", { name: "New project" }).click();
  await expect(page).toHaveURL(/\/projects\/new/);
  await expect(page.getByRole("heading", { name: "Create Project" })).toBeVisible();
});
