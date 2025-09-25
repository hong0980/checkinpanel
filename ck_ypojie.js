/*
亿破姐 签到
cron "1 0,11 * * *" ck_ourbits.js
 */

const utils = require('./utils');
const Env = utils.Env;
const $ = new Env('亿破姐 签到');
const notify = $.isNode() ? require('./notify') : '';
const magicJS = utils.MagicJS('亿破姐', 'INFO');
const COOKIES_YPOJIE = utils.getData().YPOJIE;

const fs = require('fs');
const { rimraf } = require('rimraf');
const { chromium } = require('playwright');

async function setupBrowser({
    headless = true,
    baseURL = 'https://www.ypojie.com',
    executablePath = '/usr/bin/chromium-browser',
    userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
} = {}) {
    const browser = await chromium.launch({ headless, executablePath });
    const context = await browser.newContext({ baseURL, userAgent });
    const page = await context.newPage();

    return { browser, page };
}

async function getAssets(page) {
    try {
        const content = await page.content()
        fs.writeFileSync('/tmp/OurBits.html', content);
        await page.screenshot({ path: '/tmp/OurBits.png', fullPage: true });
        return await page.locator('table.erphpdown-sc-table:has-text("可用余额")')
            .evaluate(el => el.textContent.trim().replace(/\s+/g, '：'));
    } catch {
        return '无法获取余额信息';
    }
}

async function sign(username, password, index) {
    const msgHead = `---- 账号 ${index}: `;
    const opts = { waitUntil: 'networkidle', timeout: 20000 };
    const { browser, page } = await setupBrowser();

    try {
        await page.goto('/wp-login.php', opts);
        await page.fill('#user_login', username);
        await page.fill('#user_pass', password);
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle' }),
            page.click('#wp-submit')
        ]);

        if ((await page.locator(`text=${username}`).count()) === 0) {
            return `${msgHead} ❌ 登录不成功，用户名或密码可能错误。 ----`;
        }

        await page.goto('/vip', opts);
        // <li style="padding-top:0"><a href="javascript:;" class="usercheck erphpdown-sc-btn active">已签到</a></li>
        // <li style="padding-top:0"><a href="javascript:;" class="usercheck erphpdown-sc-btn erphp-checkin">今日签到</a></li>
        if ((await page.locator('text=已签到').count()) > 0) {
            return `${magicJS.now()}\n${msgHead}${username} ----\n✅ 今天已经签到过了\n${await getAssets(page)}`;
        }

        await page.click('a.erphp-checkin');
        await page.waitForLoadState('networkidle');

        const success = (await page.locator('text=成功').count()) > 0;
        return `${magicJS.now()}\n${msgHead}${username} ----\n${success ? '签到成功 ✅' : '签到失败 ❌'}\n${await getAssets(page)}`;

    } catch (err) {
        return `${msgHead} ❌ 异常: ${err.message}`;
    } finally {
        await browser.close().catch(() => {});
        // await rimraf('/tmp/puppeteer_dev*', { glob: true }).catch(() => {});
    }
}

async function main() {
    let msgAll = '=== 亿破姐 签到结果 ===\n';
    let notifyMsg = msgAll;

    for (let i = 0; i < COOKIES_YPOJIE.length; i++) {
        const { username, password } = COOKIES_YPOJIE[i] || {};
        const signMsg = (!username || !password)
            ? `账号 ${i + 1}: ❌ Cookie 为空`
            : await sign(username, password, i + 1);

        const formatted = `${signMsg}\n--------------------------\n\n`;
        msgAll += formatted;

        if (!signMsg.includes('签到过了')) notifyMsg += formatted;
        if (i < COOKIES_YPOJIE.length - 1) await magicJS.sleep(3000);
    }

    console.log(msgAll);
    magicJS.done();
    if (/成功|失败|异常|失效/.test(notifyMsg)) notify.sendNotify('亿破姐 签到', msgAll);
}

main().catch(err => {
    console.error('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
