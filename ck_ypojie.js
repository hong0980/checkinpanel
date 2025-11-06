/*
亿破姐 签到
cron "1 0,11 * * *" ck_ypojie.js
*/

const { Env, networkLog, MagicJS, getData } = require('./utils');
const $ = new Env('亿破姐 签到');
const notify = $.isNode() ? require('./notify') : '';
const magicJS = MagicJS('亿破姐', 'INFO');
const COOKIES_YPOJIE = getData().YPOJIE;

const fs = require('fs');
const { chromium } = require('playwright');
let browser, success;

async function setupBrowser() {
    if (!browser) {
        browser = await chromium.launch({
            headless: true,
            executablePath: '/usr/bin/chromium-browser',
        });
    }

    const context = await browser.newContext({
        baseURL: 'https://www.ypojie.com',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    });

    return { browser, context };
}

async function getAssets(page) {
    try {
        fs.writeFileSync('/tmp/ypojie.html', await page.content());
        await page.screenshot({ path: '/tmp/ypojie.png', fullPage: true });
        return await page.locator('table.erphpdown-sc-table:has-text("可用余额")')
            .evaluate(el => el.textContent.trim().replace(/\s+/g, '：'));
    } catch {
        return '无法获取余额信息';
    }
}

async function sign(browser, username, password, index, context) {
    const signKey = `ypojie_sign_${index}`;
    if (magicJS.read(signKey) === magicJS.today()) return `账号 ${index}: ✅ 今日已签到`;

    let msg = '签到失败 ❌';
    const msgHead = `账号 ${index}: `;
    const page = await context.newPage();
    const opts = { waitUntil: 'networkidle', timeout: 20000 };
    const logger = await networkLog(page, {
        saveToFile: true,
        filter: ['www.ypojie.com'],
        filename: `ypojie_log_${index}.json`,
        excludeExtensions: ['js']
    });

    try {
        await page.goto('/wp-login.php', { waitUntil: 'domcontentloaded' });
        await page.fill('#user_login', username);
        await page.fill('#user_pass', password);
        await Promise.all([
            page.waitForNavigation(),
            page.click('#wp-submit')
        ]);

        if (!(await page.locator(`text=${username}`).isVisible({ timeout: 2000 })))
            return `${msgHead} ❌ 登录失败，用户名或密码错误`;

        await page.goto('/vip', opts);
        const checkinBtn = page.locator('a.erphp-checkin');
        if (await checkinBtn.isVisible({ timeout: 2000 })) {
            await checkinBtn.click().catch(() => {});
            await page.waitForLoadState('networkidle');
            await page.reload(opts);
            success = await page.locator('text=已签到').isVisible({ timeout: 2000 });
            if (success) {
                msg = '✅ 签到成功'
            };
        } else {
            msg = 'ℹ️ 已签到过'
        }
        magicJS.write(signKey, magicJS.today())
        logger.stop();

        const assets = await getAssets(page);
        return `${magicJS.now()}\n${msgHead}${username}\n${msg}\n${assets}`;
    } catch (err) {
        return `${msgHead} ❌ 异常: ${err.message}`;
    } finally {
        await page.close().catch(() => {});
    }
}

async function main() {
    const { browser, context } = await setupBrowser();
    let msgAll = '=== 亿破姐 签到结果 ===\n';

    for (let i = 0; i < COOKIES_YPOJIE.length; i++) {
        const { username, password } = COOKIES_YPOJIE[i] || {};
        const signMsg = (!username || !password)
            ? `账号 ${i + 1}: ❌ 用户名或密码为空`
            : await sign(browser, username, password, i + 1, context);
        msgAll += signMsg;
        if (i < COOKIES_YPOJIE.length - 1) await magicJS.sleep(2000);
    }

    $.log(msgAll);
    magicJS.done();
    if (/成功|失败|异常|失效/.test(msgAll)) notify.sendNotify('亿破姐 签到', msgAll);
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
}

main().catch(err => {
    $.logErr('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
