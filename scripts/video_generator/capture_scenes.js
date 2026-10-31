const puppeteer = require('./node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const OUT_DIR = path.join(__dirname, 'output', 'screenshots');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function capture() {
  console.log('🚀 Launching Chromium for automated scene capture...');
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--font-render-hinting=max',
      '--enable-font-antialiasing',
      '--window-size=1920,1080'
    ],
    defaultViewport: {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1
    }
  });

  const page = await browser.newPage();

  // Auto-dismiss all alert dialogs so they don't block
  page.on('dialog', async dialog => {
    console.log(`[Dialog auto-handled]: ${dialog.message()}`);
    await dialog.accept();
  });

  await page.evaluateOnNewDocument(() => {
    window.alert = (msg) => console.log('Alert intercepted:', msg);
  });

  console.log('🌐 Navigating to http://localhost:8000...');
  await page.goto('http://localhost:8000', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1200));

  const shoot = async (name) => {
    const filePath = path.join(OUT_DIR, `${name}.png`);
    await page.screenshot({ path: filePath });
    console.log(`📸 Captured: ${name}.png`);
  };

  // 1. Executive Dashboard
  console.log('Capturing Scene 1: Executive Dashboard...');
  await page.evaluate(() => {
    const tab = document.querySelector('[data-tab="dashboard"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  await shoot('scene_01_dashboard');

  // 2. Catalog & Plans
  console.log('Capturing Scene 2: Catalog & Plans...');
  await page.evaluate(() => {
    const tab = document.querySelector('[data-tab="catalog"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await shoot('scene_02_catalog');

  // 3. Subscriptions Lifecycle
  console.log('Capturing Scene 3: Subscriptions Lifecycle...');
  await page.evaluate(() => {
    const tab = document.querySelector('[data-tab="subscriptions"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await shoot('scene_03_subscriptions');

  // 4. Invoices & Golden Calculation
  console.log('Capturing Scene 4: Invoices & Golden Vector...');
  await page.evaluate(() => {
    const tab = document.querySelector('[data-tab="invoices"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await shoot('scene_04_invoices');

  // 5. Payment Modal
  console.log('Capturing Scene 5: Payment Modal...');
  await page.evaluate(() => {
    const payBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Pay');
    if (payBtn) payBtn.click();
  });
  await new Promise(r => setTimeout(r, 800));
  await shoot('scene_05_payments');

  // Close payment modal
  await page.evaluate(() => {
    const modal = document.getElementById('modal-payment');
    if (modal) modal.classList.add('hidden');
  });
  await new Promise(r => setTimeout(r, 500));

  // 6. AI Copilot Overview
  console.log('Capturing Scene 6: AI Copilot Overview...');
  await page.evaluate(() => {
    const tab = document.querySelector('[data-tab="ai-copilot"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await shoot('scene_06_ai_copilot');

  // 7. Smart Dunning Generator
  console.log('Capturing Scene 7: Smart Dunning Generator...');
  await page.evaluate(() => {
    const dunningBtn = document.getElementById('btn-generate-dunning');
    if (dunningBtn) dunningBtn.click();
  });
  await new Promise(r => setTimeout(r, 1200));
  await shoot('scene_07_smart_dunning');

  // 8. Time-Travel Virtual Clock
  console.log('Capturing Scene 8: Time-Travel Engine...');
  await page.evaluate(() => {
    // Scroll to top and highlight header
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const tab = document.querySelector('[data-tab="dashboard"]');
    if (tab) tab.click();
    const advBtn = document.getElementById('btn-advance-month');
    if (advBtn) advBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  await shoot('scene_08_time_travel');

  // 9. Customer Self-Service Portal
  console.log('Capturing Scene 9: Customer Self-Service Portal...');
  await page.evaluate(() => {
    const roleSel = document.getElementById('role-selector');
    if (roleSel) {
      roleSel.value = 'customer';
      roleSel.dispatchEvent(new Event('change'));
    }
    const tab = document.querySelector('[data-tab="portal"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1200));
  await shoot('scene_09_customer_portal');

  // 10. Platform Overview & Summary
  console.log('Capturing Scene 10: Platform Overview...');
  await page.evaluate(() => {
    const roleSel = document.getElementById('role-selector');
    if (roleSel) {
      roleSel.value = 'admin';
      roleSel.dispatchEvent(new Event('change'));
    }
    const tab = document.querySelector('[data-tab="dashboard"]');
    if (tab) tab.click();
  });
  await new Promise(r => setTimeout(r, 1200));
  await shoot('scene_10_architecture');

  await browser.close();
  console.log('✨ All 10 scenes successfully captured!');
}

capture().catch(err => {
  console.error('Error during capture:', err);
  process.exit(1);
});
