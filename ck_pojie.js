/*
 * 吾爱破解
 * cron "2 0,11 * * *" ck_pojie.js
 */

const utils = require('./utils');
const notify = require('./notify');
const $ = new utils.Env('吾爱破解');
const magicJS = utils.MagicJS('吾爱破解', 'INFO');
const COOKIES_POJIE = utils.getData().POJIE;
const path = require('path');
const fs = require('fs').promises;
const { chromium } = require('playwright');

async function setupBrowser(userDataDir) {
    const browser = await chromium.launchPersistentContext(userDataDir, {
        headless: true,
        ignoreHTTPSErrors: true,
        javaScriptEnabled: true,
        baseURL: 'https://www.52pojie.cn/',
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-gpu',
            '--ignore-gpu-blocklist',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--disable-blink-features=AutomationControlled'
        ],
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        extraHTTPHeaders: {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        },
        viewport: { width: 1280, height: 720 },
    });

    await browser.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        delete window.debugger;

        const originalSetTimeout = window.setTimeout;
        window.setTimeout = function (cb, timeout) {
            if (typeof cb === 'function' && cb.toString().includes('debugger')) return;
            if (typeof cb === 'string' && cb.includes('debugger')) return;
            return originalSetTimeout.call(this, cb, timeout);
        };

        const originalSetInterval = window.setInterval;
        window.setInterval = function (cb, timeout) {
            if (typeof cb === 'function' && cb.toString().includes('debugger')) return;
            if (typeof cb === 'string' && cb.includes('debugger')) return;
            return originalSetInterval.call(this, cb, timeout);
        };
    });

    return browser;
}

async function sign(cookie, index) {
    const userDataDir = '/tmp/pw_user_data';
    const context = await setupBrowser(userDataDir);
    const msgHead = `---- 账号 ${index}: `;
    let msg = '';

    const cookies = cookie.split('; ').map(c => {
        const [name, value] = c.split('=');
        return { name, value, domain: 'www.52pojie.cn', path: '/', sameSite: 'Lax' };
    });
    await context.addCookies(cookies);

    const opts = { waitUntil: 'networkidle', timeout: 20000 };

    try {
        const page = context.pages()[0] || await context.newPage();
        await page.goto('/forum.php', opts);

        const [upmine, integral, username] = await Promise.allSettled([
            page.locator('#g_upmine').textContent({ timeout: 2000 }),
            page.locator('#extcreditmenu').textContent({ timeout: 2000 }),
            page.locator('strong.vwmy a[href*="uid="]').textContent({ timeout: 2000 })
        ]).then(r => r.map(x => x.status === 'fulfilled' ? x.value : null));

        if (!upmine && !username)
            return `${msgHead}❌ Cookie 可能失效，请重新获取`;

        msg = `${msgHead}${username} ----\n`;

        const signLink = await page
            .locator('a[href*="mod=task&do=apply&id=2"]',
                { has: page.locator('img[title*="领取今日签到奖励"]') })
            .getAttribute('href', { timeout: 1500 })
            .catch(() => null);

        if (!signLink)
            return `${msg}✅ 今天已经签到过了\n积分: ${integral} | 威望: ${upmine}`;

        await page.goto(signLink, opts);
        await magicJS.sleep(3000);
        await page.goto('/forum.php', opts);

        const signed = await page
            .waitForSelector('a[href*="mod=task&do=apply&id=2"]', { state: 'detached', timeout: 1000 })
            .then(() => true)
            .catch(() => false);

        msg += `${magicJS.today()} ${signed ? '✅ 签到成功' : '❌ 签到失败'}\n积分: ${integral} | 威望: ${upmine}`;

    } catch (err) {
        msg += `❌ 异常: ${err.message}`;
    } finally {
        await context.close().catch(() => {});
        await fs.rm(userDataDir, { recursive: true, force: true }).catch(() => {});
    }

    return msg;
}

async function main() {
    let msgAll = '=== 吾爱破解 签到结果 ===\n';

    for (let i = 0; i < COOKIES_POJIE.length; i++) {
        const cookie = COOKIES_POJIE[i].cookie;
        let signMsg;

        if (!cookie) {
            signMsg = `账号 ${i + 1}: ❌ Cookie 为空`;
        } else {
            signMsg = await sign(cookie, i + 1);
        }

        msgAll += `${signMsg}\n-----------------------------------\n\n`;
    }

    console.log(msgAll);
    magicJS.done();
    notify.sendNotify('吾爱破解 签到', msgAll);
}

main().catch(err => {
    console.error('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
