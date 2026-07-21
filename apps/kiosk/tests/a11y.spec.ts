import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Objetivo: WCAG 2.2 AA / EN 301 549 (PRD §14.5). axe se ejecuta contra la app
// real en Chromium, que es la única forma de comprobar de verdad el contraste,
// los roles y los nombres accesibles.
const WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function scan(page: Page) {
  return new AxeBuilder({ page }).withTags(WCAG_AA).analyze();
}

/** Resume las violaciones para que el fallo del test diga QUÉ y DÓNDE. */
function summarize(violations: Awaited<ReturnType<typeof scan>>["violations"]): string {
  return violations
    .map((v) => `${v.id} (${v.impact}): ${v.nodes.length}× — ${v.nodes[0]?.target.join(" ")}`)
    .join("\n");
}

async function chooseSpanish(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Castellano" }).click();
  await expect(page.getByRole("heading", { name: /Qué trámite/ })).toBeVisible();
}

async function enableHighContrast(page: Page) {
  await page.getByRole("button", { name: /Alto contraste/ }).click();
  await expect(page.locator(".kiosk.high-contrast")).toBeVisible();
}

test.describe("Accesibilidad (WCAG 2.2 AA)", () => {
  test("la página declara el idioma (lang)", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", /es|ca/);
  });

  test("pantalla de idioma sin violaciones", async ({ page }) => {
    await page.goto("/");
    const { violations } = await scan(page);
    expect(violations, summarize(violations)).toEqual([]);
  });

  test("pantalla de inicio (castellano) sin violaciones", async ({ page }) => {
    await chooseSpanish(page);
    const { violations } = await scan(page);
    expect(violations, summarize(violations)).toEqual([]);
  });

  test("pantalla de inicio en alto contraste sin violaciones", async ({ page }) => {
    await chooseSpanish(page);
    await enableHighContrast(page);
    const { violations } = await scan(page);
    expect(violations, summarize(violations)).toEqual([]);
  });

  test("ficha de trámite informativo sin violaciones", async ({ page }) => {
    await chooseSpanish(page);
    await page.getByRole("button", { name: /antecedentes penales/i }).click();
    await expect(page.getByRole("heading", { name: /antecedentes penales/i })).toBeVisible();
    const { violations } = await scan(page);
    expect(violations, summarize(violations)).toEqual([]);
  });

  test("pantalla en valenciano sin violaciones", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Valencià" }).click();
    await expect(page.getByRole("heading", { name: /Quin tràmit/ })).toBeVisible();
    const { violations } = await scan(page);
    expect(violations, summarize(violations)).toEqual([]);
  });

  test("operable por teclado: activar un trámite con Enter", async ({ page }) => {
    await chooseSpanish(page);
    const card = page.getByRole("button", { name: /antecedentes penales/i });
    await card.focus();
    await expect(card).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { name: /antecedentes penales/i })).toBeVisible();
  });

  test("objetivos táctiles con tamaño suficiente (>= 24px, WCAG 2.5.8)", async ({ page }) => {
    await chooseSpanish(page);
    const buttons = page.getByRole("button");
    const count = await buttons.count();
    const small: string[] = [];
    for (let i = 0; i < count; i++) {
      const box = await buttons.nth(i).boundingBox();
      const label = (await buttons.nth(i).textContent())?.trim().slice(0, 24) ?? "?";
      if (box && (box.width < 24 || box.height < 24)) {
        small.push(`${label} (${Math.round(box.width)}×${Math.round(box.height)})`);
      }
    }
    expect(small, `Objetivos táctiles pequeños: ${small.join(", ")}`).toEqual([]);
  });

  test("sin scroll horizontal con la letra al tamaño máximo (reflow, WCAG 1.4.10)", async ({
    page,
  }) => {
    await chooseSpanish(page);
    // Sube el tamaño de letra a su máximo (dos pulsaciones).
    const fontButton = page.getByRole("button", { name: /Tamaño de letra/ });
    await fontButton.click();
    await fontButton.click();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(overflow, "La página tiene scroll horizontal con la letra grande").toBe(false);
  });
});
