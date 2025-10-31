/*
吾爱破解
cron "2 0,11 * * *" ck_pojie.js
 */

const fs = require('fs');
const notify = require('./notify');
// const { rimraf } = require('rimraf');
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

    const logger = await networkLog(page, {
        saveToFile: true,                       // 是否保存到文件
        filter: ['home.php', 'task', 'apply'],  // 只捕获相关请求
        filename: `pojie_log_${index}.json`,    // 保存到 /tmp/pojie_log_1.json
    });

    try {
        await page.goto('/forum.php', opts);
        const [upmine, integral, username] = await Promise.allSettled([
            page.locator('#g_upmine').textContent({ timeout: 2000 }),
            page.locator('#extcreditmenu').textContent({ timeout: 2000 }),
            page.locator('strong.vwmy a[href*="uid="]').textContent({ timeout: 2000 })
        ]).then(r => r.map(x => x.status === 'fulfilled' ? x.value : null));

        if (!username) return `${msgHead} ❌ Cookie 可能失效，请重新获取`;

        msg = `${msgHead}${username} ----\n`;

        const qds = page.locator('#um img[src*="qds.png"]');

        if (await qds.count() > 0) {
            const parentHref = await qds.first().evaluate(img => img.closest('a')?.href);
            if (parentHref) {
                await page.goto(parentHref, opts);
                await page.waitForTimeout(2000);
                await page.goto('/forum.php', opts);
                await magicJS.sleep(1000);
            }
        }

        const wbs = page.locator('#um img[src*="wbs.png"]');
        if (await wbs.count() === 0) {
            magicJS.write(signKey, magicJS.today())
            msg += `${magicJS.today()} ✅ 签到成功\n`;
        } else {
            msg += `${magicJS.today()} ℹ️ 今天已经签到\n`;
        }
        await page.goto('/home.php?mod=spacecp&ac=credit&op=base', opts);
        const wuaibi = (await page.locator('li:has(em:has-text("吾爱币"))').innerText())
            .match(/\d+\s*CB/)?.[0] || null;
        msg += `积分: ${integral} | 吾爱币： ${wuaibi} | 威望: ${upmine}`

        const content = await page.content()
        fs.writeFileSync('/tmp/52pojie.html', content);
        await page.screenshot({ path: '/tmp/52pojie.png', fullPage: true });

        // ✅ 在最后停止捕获并保存日志
        logger.stop();

        // ✅ 你可以从 logger.logs 中直接获取请求响应
        const logSummary = logger.logs.map(l => `${l.类型} → ${l.请求地址 || l.地址 || '未知'}`).join('\n');
        fs.writeFileSync(`/tmp/pojie_summary_${index}.log`, logSummary);

        // 可选：打印出是否成功调用任务接口
        const taskApply = logger.logs.find(l => l.地址?.includes('mod=task') && l.类型 === '请求');
        if (taskApply) msg += `🕵️ 捕获到任务请求：${taskApply.请求地址}\n`;

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
