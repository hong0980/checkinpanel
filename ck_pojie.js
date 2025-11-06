/*
吾爱破解签到
cron "2 0,11 * * *" ck_pojie.js
*/

const fs = require('fs');
const notify = require('./notify')
const { chromium } = require('playwright');

const { Env, networkLog, MagicJS, getData } = require('./utils');
const $ = new Env('吾爱破解 签到');
const magicJS = MagicJS('吾爱破解', 'INFO');
const COOKIES_POJIE = getData().POJIE;

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

    const initScript = `
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        delete window.debugger;
        const filter = f => !(typeof f === 'function' && f.toString().includes('debugger'));
        const st = window.setTimeout, si = window.setInterval;
        window.setTimeout = (cb, t) => filter(cb) && st(cb, t);
        window.setInterval = (cb, t) => filter(cb) && si(cb, t);
    `;
    const context = await browser.newContext({
        baseURL: 'https://www.52pojie.cn',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        extraHTTPHeaders: {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
    });
    await context.addInitScript(initScript);

    return { browser, context };
}

async function sign(context, cookie, index) {
    const signKey = `pojie_sign_${index}`;
    if (magicJS.read(signKey) === magicJS.today()) return `账号 ${index}: ✅ 今日已签到`;

    let msg = '';
    const msgHead = `账号 ${index}: `;
    const page = await context.newPage();
    const opts = { waitUntil: 'networkidle', timeout: 20000 };
    const cookies = cookie.split(/;\s*/).map(c => {
        const [name, ...rest] = c.split('=');
        return { name, value: rest.join('='), domain: '.52pojie.cn', path: '/', sameSite: 'Lax' };
    });
    await context.clearCookies();
    await context.addCookies(cookies);

    const logger = await networkLog(page, {
        filter: ['forum.php', 'task', 'apply'],
        filename: `52pojie_log_${index}.json`,
    });

    try {
        await page.goto('/forum.php', opts);
        const [upmine, integral, username] = await Promise.allSettled([
            page.locator('#g_upmine').textContent({ timeout: 1500 }),
            page.locator('#extcreditmenu').textContent({ timeout: 1500 }),
            page.locator('strong.vwmy a[href*="uid="]').textContent({ timeout: 1500 })
        ]).then(r => r.map(x => x.status === 'fulfilled' ? x.value : null));
        if (!username) return `${msgHead} ❌ Cookie 失效`;

        msg += `${msgHead}${username}\n`;
        const qds = page.locator('#um img[src*="qds.png"]');
        if (await qds.isVisible({ timeout: 2000 })) {
            const href = await qds.first().evaluate(img => img.closest('a')?.href);
            await page.goto(href, opts);
            await page.waitForSelector('#um img[src*="wbs.png"]', { timeout: 5000 })
                .catch(() => null);

            await page.goto('/forum.php', opts);
            const signed = await page.locator('#um img[src*="wbs.png"]');
            if (signed.isVisible({ timeout: 2000 })) {
                msg += `${magicJS.today()} ✅ 签到成功\n`;
                magicJS.write(signKey, magicJS.today());
            }
        } else {
            msg += `${magicJS.today()} ℹ️ 已签到过\n`;
        }

        await page.goto('/home.php?mod=spacecp&ac=credit&op=base', opts);
        const wuaibi = (await page.locator('li:has(em:has-text("吾爱币"))').innerText({ timeout: 2000 })
            .catch(() => '')).match(/\d+\s*CB/)?.[0] || '未知';
        msg += `积分: ${integral} | 吾爱币: ${wuaibi} | 威望: ${upmine}\n`;

        fs.writeFileSync(`/tmp/52pojie_${index}.html`, await page.content());
        await page.screenshot({ path: `/tmp/52pojie_${index}.png`, fullPage: true });
        logger.stop();
    } catch (err) {
        msg += `❌ 异常: ${err.message}\n`;
    } finally {
        await page.close().catch(() => {});
    }

    return msg;
}

async function main() {
    const { browser, context } = await setupBrowser();

    let msgAll = '=== 吾爱破解 签到结果 ===\n';

    for (let i = 0; i < COOKIES_POJIE.length; i++) {
        const cookie = COOKIES_POJIE[i]?.cookie;
        let res = cookie ? await sign(context, cookie, i + 1)
            : `账号 ${i + 1}: ❌ Cookie 为空`;

        msgAll += res;
        if (i < COOKIES_POJIE.length - 1) await magicJS.sleep(2000);
    }

    $.log(msgAll);
    magicJS.done();
    if (/成功|异常|失效/.test(msgAll)) notify.sendNotify('吾爱破解 签到', msgAll);

    await context.close().catch(() => {});
    await browser.close().catch(() => {});
}

main().catch(err => {
    $.logErr('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
