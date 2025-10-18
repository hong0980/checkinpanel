/*
吾爱破解
cron "2 0,11 * * *" ck_pojie.js
 */

const utils = require('./utils');
const notify = require('./notify');
const Env = utils.Env;

const $ = new Env('吾爱破解 签到');
const magicJS = utils.MagicJS('吾爱破解', 'INFO');
const COOKIES_POJIE = utils.getData().POJIE;

const fs = require('fs');
// const { rimraf } = require('rimraf');
const { chromium } = require('playwright');

async function setupBrowser() {
    const browser = await chromium.launch({
        headless: true,
        ignoreHTTPSErrors: true,
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-gpu',
            '--ignore-gpu-blocklist',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const context = await browser.newContext({
        baseURL: 'https://www.52pojie.cn',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        extraHTTPHeaders: {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    });
    await context.addInitScript(() => {
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
        }
    });
    return { browser, context };
}

async function sign(cookie, index) {
    const signKey = `pojie_sign_${index}`;
    if (magicJS.read(signKey) === magicJS.today()) return `账号 ${index}: ✅ 今日已签到`;

    let msg = '';
    const msgHead = `---- 账号 ${index}: `;
    const opts = { waitUntil: 'networkidle', timeout: 20000 };
    const { browser, context } = await setupBrowser();
    const page = await context.newPage();
    const cookies = cookie.split('; ').map(c => {
        const [name, value] = c.split('=');
        return { name, value, domain: '.52pojie.cn', path: '/', sameSite: 'Lax' };
    });
    await context.addCookies(cookies);

    try {
        await page.goto('/forum.php', opts);
        const [upmine, integral, username] = await Promise.allSettled([
            page.locator('#g_upmine').textContent({ timeout: 2000 }),
            page.locator('#extcreditmenu').textContent({ timeout: 2000 }),
            page.locator('strong.vwmy a[href*="uid="]').textContent({ timeout: 2000 })
        ]).then(r => r.map(x => x.status === 'fulfilled' ? x.value : null));

        if (!username) return `${msgHead}❌ Cookie 可能失效，请重新获取`;

        msg = `${msgHead}${username} ----\n`;

        const task = await page.$('#um a[href*="mod=task&id=2"]', opts);
        if (task) {
            const taskLink = await task.getAttribute('href');
            await page.goto(taskLink, opts);
            await magicJS.sleep(2000);
            await page.goto('/forum.php', opts);
        }

        await magicJS.sleep(1000);
        const signed = await page.locator('#um a[href*="mod=task&id=2"]').count() === 0;
        if (signed) {
            magicJS.write(signKey, magicJS.today())
            msg += `${magicJS.today()} '✅ 签到成功'\n`;
        } else {
            msg += `${magicJS.today()} '❌ 签到失败'\n`;
        }
        msg += `积分: ${integral} | 威望: ${upmine}`

        const content = await page.content()
        fs.writeFileSync('/tmp/52pojie.html', content);
        await page.screenshot({ path: '/tmp/52pojie.png', fullPage: true });

    } catch (err) {
        msg += `❌ 异常: ${err.message}`;
    } finally {
        await browser.close().catch(() => {});
    }
    return msg;
}

async function main() {
    let msgAll = '=== 吾爱破解 签到结果 ===\n';
    let notifyMsg = '=== 吾爱破解 签到结果 ===\n';

    for (let i = 0; i < COOKIES_POJIE.length; i++) {
        const cookie = COOKIES_POJIE[i].cookie;
        let signMsg;

        if (!cookie) {
            signMsg = `账号 ${i + 1}: ❌ Cookie 为空`;
        } else {
            signMsg = await sign(cookie, i + 1);
        }
        msgAll += `${signMsg}\n-----------------------------------\n\n`;
        if (!signMsg.includes('签到过了')) {
            notifyMsg += `${signMsg}\n-----------------------------------\n\n`;
        }

        if (i < COOKIES_POJIE.length - 1) await magicJS.sleep(3000);
    }

    $.log(msgAll);
    magicJS.done();
    if (/成功|失败|异常|失效/.test(notifyMsg)) notify.sendNotify('吾爱破解 签到', notifyMsg);
}

main().catch(err => {
    console.error('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
