import { test, expect } from "@chromatic-com/playwright";
import { loginAsRandomUser } from "../utils/auth";
import { sendMessage } from "../utils/chatActions";

test.describe("Message Edit and Regenerate Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Clear cookies and log in as a random user
    await page.context().clearCookies();
    await loginAsRandomUser(page);

    // Navigate to the chat page
    await page.goto("http://localhost:3000/chat");
    await page.waitForLoadState("networkidle");
  });

  test("Complete message editing functionality", async ({ page }) => {
    // Step 1: Send initial message
    await sendMessage(page, "What is 2+2?");
    await page.waitForSelector('[data-testid="onyx-ai-message"]');
    await page.waitForTimeout(3000);

    // Step 2: Test cancel editing
    let userMessage = page.locator("#onyx-human-message").first();
    await userMessage.hover();
    let editButton = userMessage.locator('[data-testid="edit-button"]').first();
    await editButton.click();

    let textarea = userMessage.locator("textarea");
    await textarea.fill("This edit will be cancelled");

    const cancelButton = userMessage.locator('button:has-text("Cancel")');
    await cancelButton.click();

    // Verify original message is preserved
    let messageContent = await userMessage.textContent();
    expect(messageContent).toContain("What is 2+2?");
    expect(messageContent).not.toContain("This edit will be cancelled");

    // Step 3: Edit the message for real
    await userMessage.hover();
    editButton = userMessage.locator('[data-testid="edit-button"]').first();
    await editButton.click();

    textarea = userMessage.locator("textarea");
    await textarea.fill("What is 3+3?");

    let submitButton = userMessage.locator('button:has-text("Submit")');
    await submitButton.click();
    await page.waitForTimeout(3000);

    // Verify edited message is displayed
    messageContent = await page
      .locator("#onyx-human-message")
      .first()
      .textContent();
    expect(messageContent).toContain("What is 3+3?");

    // Step 4: Verify version switcher appears and shows 2/2
    // Look for the switcher by finding text containing "2 / 2"
    await page.waitForTimeout(1000); // Give switcher time to appear
    let messageSwitcher = page.locator('span:has-text("2 / 2")').first();
    await expect(messageSwitcher).toBeVisible();

    // Get the parent div that contains the whole switcher
    messageSwitcher = messageSwitcher.locator("..").first();

    // Step 5: Edit again to create a third version
    userMessage = page.locator("#onyx-human-message").first();
    await userMessage.hover();
    editButton = userMessage.locator('[data-testid="edit-button"]').first();
    await editButton.click();

    textarea = userMessage.locator("textarea");
    await textarea.fill("What is 4+4?");

    submitButton = userMessage.locator('button:has-text("Submit")');
    await submitButton.click();
    await page.waitForTimeout(3000);

    // Step 6: Verify navigation between versions
    // Find the switcher showing "3 / 3"
    let switcherSpan = page.locator('span:has-text("3 / 3")').first();
    await expect(switcherSpan).toBeVisible();

    // Navigate to previous version - click the first svg icon's parent (left chevron)
    await switcherSpan
      .locator("..")
      .locator("svg")
      .first()
      .locator("..")
      .click();
    await page.waitForTimeout(1000);

    // Check we're now at "2 / 3"
    switcherSpan = page.locator('span:has-text("2 / 3")').first();
    await expect(switcherSpan).toBeVisible();

    // Navigate to first version - re-find the button each time
    await switcherSpan
      .locator("..")
      .locator("svg")
      .first()
      .locator("..")
      .click();
    await page.waitForTimeout(1000);

    // Check we're now at "1 / 3"
    switcherSpan = page.locator('span:has-text("1 / 3")').first();
    await expect(switcherSpan).toBeVisible();

    // Navigate forward using next button - click the last svg icon's parent (right chevron)
    await switcherSpan
      .locator("..")
      .locator("svg")
      .last()
      .locator("..")
      .click();
    await page.waitForTimeout(1000);

    // Check we're back at "2 / 3"
    switcherSpan = page.locator('span:has-text("2 / 3")').first();
    await expect(switcherSpan).toBeVisible();
  });

  test("Message regeneration with model selection", async ({ page }) => {
    // Step 1: Send initial message
    await sendMessage(page, "hi!");
    await page.waitForSelector('[data-testid="onyx-ai-message"]');
    await page.waitForTimeout(3000);

    // Step 2: Capture the original AI response text (just the message content, not buttons/switcher)
    const aiMessage = page.locator('[data-testid="onyx-ai-message"]').first();
    // Target the actual message content div (the one with select-text class)
    const messageContent = aiMessage.locator(".select-text").first();
    const originalResponseText = await messageContent.textContent();

    // Step 3: Hover over AI message to show regenerate button
    await aiMessage.hover();

    // Step 4: Click regenerate button using its data-testid
    const regenerateButton = aiMessage.locator(
      '[data-testid="regenerate-button"]'
    );
    await regenerateButton.click();

    // Step 5: Wait for dropdown to appear and select GPT-4o-mini
    await page.waitForTimeout(500);

    // Look for the GPT-4o-mini option in the dropdown
    const gpt4oMiniOption = page.locator("text=/.*GPT.?4o.?Mini.*/i").first();
    await gpt4oMiniOption.click();

    // Step 6: Wait for regeneration to complete by waiting for feedback buttons to appear
    // The feedback buttons (copy, like, dislike, regenerate) appear when streaming is complete
    await page.waitForSelector('[data-testid="regenerate-button"]', {
      state: "visible",
      timeout: 10000,
    });

    // Step 7: Verify version switcher appears showing "2 / 2"
    const messageSwitcher = page.locator('span:has-text("2 / 2")').first();
    await expect(messageSwitcher).toBeVisible();

    // Step 8: Capture the regenerated response text (just the message content)
    const regeneratedResponseText = await messageContent.textContent();

    // Step 9: Verify that the regenerated response is different from the original
    expect(regeneratedResponseText).not.toBe(originalResponseText);

    // Step 10: Navigate to previous version
    await messageSwitcher
      .locator("..")
      .locator("svg")
      .first()
      .locator("..")
      .click();
    await page.waitForTimeout(1000);

    // Verify we're at "1 / 2"
    let switcherSpan = page.locator('span:has-text("1 / 2")').first();
    await expect(switcherSpan).toBeVisible();

    // Step 11: Verify we're back to the original response
    const firstVersionText = await messageContent.textContent();
    expect(firstVersionText).toBe(originalResponseText);

    // Step 12: Navigate back to regenerated version
    await switcherSpan
      .locator("..")
      .locator("svg")
      .last()
      .locator("..")
      .click();
    await page.waitForTimeout(1000);

    // Verify we're back at "2 / 2"
    switcherSpan = page.locator('span:has-text("2 / 2")').first();
    await expect(switcherSpan).toBeVisible();

    // Step 13: Verify we're back to the regenerated response
    const secondVersionText = await messageContent.textContent();
    expect(secondVersionText).toBe(regeneratedResponseText);
  });
});
