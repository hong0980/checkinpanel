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
const crypto = require('crypto');
const puppeteer = require('puppeteer-extra').use(
    require('puppeteer-extra-plugin-stealth')()
);

async function setupBrowser() {
    const userDataDir = '/tmp/puppeteer_profile';
    const browser = await puppeteer.launch({
        headless: true,
        userDataDir,
        executablePath: '/usr/bin/chromium-browser',
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36'
    );
    await page.setExtraHTTPHeaders({
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    });

    return { browser, page, userDataDir };
}

async function attachNetworkLogger(page, tag = 'default', options = {}) {
    const {
        logDir = '', urlPatterns = [], maxBodyLength = 0, saveBodies = false,
        logRequests = false, onlyHtmlJson = false, logResponses = false, includeHeaders = false,
    } = options;

    for (const file of await fs.readdir(logDir)) {
        file.startsWith('body_') && await fs.rm(path.join(logDir, file), { force: true });
    }

    const logFile = path.join(logDir, `52pojie_${tag}.log`);
    const logStream = await fs.open(logFile, 'w');
    await logStream.appendFile(`# 网络日志记录已启动于 ${magicJS.now()}\n`);
    await logStream.appendFile(`# 页面: ${tag}\n`);
    await logStream.appendFile(`# 日志文件: ${logFile}\n`);
    await logStream.appendFile('==========================================\n\n');

    function makeSafeFilename(url) {
        const hash = crypto.createHash('md5').update(url).digest('hex');
        return `body_${tag}_${hash}`;
    }

    function getFileExtension(url, contentType) {
        if (!contentType) contentType = '';
        if (contentType.includes('json')) return 'json';
        if (contentType.includes('javascript')) return 'js';
        if (contentType.includes('css')) return 'css';
        if (contentType.includes('png')) return 'png';
        if (contentType.includes('jpeg') || contentType.includes('jpg')) return 'jpg';
        if (contentType.includes('gif')) return 'gif';
        if (contentType.includes('svg')) return 'svg';
        if (contentType.includes('html') || contentType.includes('text')) return 'html';

        const match = url.match(/\.(html|js|css|png|jpg|jpeg|gif|svg)$/i);
        if (match) return match[1].toLowerCase();
        return 'bin';
    }

    function matchesPatterns(url, patterns) {
        if (!patterns || patterns.length === 0) return true;
        return patterns.some(p => new RegExp(p).test(url));
    }

    function shouldLog(url, contentType) {
        const ext = getFileExtension(url, contentType);
        return ['json', 'js', 'html'].includes(ext);
    }

    if (logRequests) {
        page.on('request', async req => {
            const url = req.url();
            if (!matchesPatterns(url, urlPatterns)) return;

            const ct = req.headers()['content-type'] || '';
            if (!shouldLog(url, ct)) return;

            try {
                const postData = req.postData();
                let logContent = [
                    `请求时间 ${magicJS.now()}`,
                    `方法: ${req.method()}`,
                    `地址: ${url}`,
                    `资源类型: ${req.resourceType()}`,
                    `所属框架: ${req.frame()?.url() || '主框架'}`
                ];
                if (includeHeaders) logContent.push(`请求头: ${$.toStr(req.headers(), null, 2)}`);
                if (postData) logContent.push(`POST 数据: ${postData.length > maxBodyLength ? postData.substring(0, maxBodyLength) + '...' : postData}`);
                logContent.push('----------------------\n');
                await logStream.appendFile(logContent.join('\n') + '\n');
            } catch (e) {
                console.error('请求日志记录错误:', e);
            }
        });
    }

    if (logResponses) {
        page.on('response', async res => {
            const url = res.url();
            if (!matchesPatterns(url, urlPatterns)) return;

            const contentType = res.headers()['content-type'] || '';
            if (!shouldLog(url, contentType)) return;

            try {
                const request = res.request();
                const buffer = await res.buffer();
                const ext = getFileExtension(url, contentType);

                let bodyFile = null;
                if (saveBodies && (!onlyHtmlJson || ['html', 'json'].includes(ext))) {
                    bodyFile = path.join(logDir, makeSafeFilename(url) + '.' + ext);
                    await fs.writeFile(bodyFile, buffer);
                }

                let textPreview = buffer.toString('utf8', 0, Math.min(buffer.length, maxBodyLength));
                const logContent = [
                    `响应时间 ${magicJS.now()}`,
                    `状态: ${res.status()}`,
                    `地址: ${url}`,
                    `来源请求: ${request?.method()} ${request?.url()}`,
                    includeHeaders ? `响应头: \n${$.toStr(res.headers(), null, 2)}` : '',
                    `响应体预览: \n${textPreview}`,
                    bodyFile ? `完整响应体保存位置: ${bodyFile}` : '',
                    '======================\n'
                ];
                await logStream.appendFile(logContent.join('\n') + '\n');
            } catch (err) {
                await logStream.appendFile(`响应错误 ${magicJS.now()} ${url} - ${err.message}\n`);
            }
        });
    }

    console.log(`📡 网络日志记录已启动: ${logFile}`);

    return async () => {
        try {
            await logStream.appendFile(`# 网络日志记录已停止于 ${magicJS.now()}\n`);
            await logStream.close();
            console.log(`📋 网络日志已保存: ${logFile}`);
        } catch (err) {
            console.error('关闭日志流出错:', err);
        }
    };
}

async function sign(cookie, index) {
    let msg = '';
    const { browser, page, userDataDir } = await setupBrowser();
    const closeLogger = await attachNetworkLogger(page, index, {
        urlPatterns: ['mod=task&do=apply&id=2'],
        logDir: '/tmp',
        maxBodyLength: 2000,
        saveBodies: true,
        logRequests: true,
        onlyHtmlJson: true,
        logResponses: true,
        includeHeaders: true
    });

    try {
        const cookies = cookie.split('; ').map(c => {
            const [name, value] = c.split('=');
            return { name, value, domain: '.52pojie.cn', path: '/' };
        });
        await page.setCookie(...cookies);

        await page.goto('https://www.52pojie.cn/forum.php', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        const pageContent = await page.content();
        if (pageContent.includes('自动登录')) {
            return `账号 ${index}: ❌ Cookie 可能失效，请重新获取`;
        }

        const username = await page.evaluate(() => {
            const el = document.querySelector('strong.vwmy a[href*="uid="]');
            return el ? el.textContent.trim() : '未知用户';
        });
        const integral = await page.evaluate(() => {
            const el = document.querySelector('#extcreditmenu');
            return el ? el.textContent.trim() : '未知';
        });
        const upmine = await page.evaluate(() => {
            const el = document.querySelector('#g_upmine');
            return el ? el.textContent.trim() : '未知';
        });

        msg = `---- 账号 ${index}: ${username} ----\n`;

        const alreadySigned = await page.$('img.qq_bind[src*="wbs.png"]');
        if (alreadySigned) {
            return `${msg}✅ 今天已经签到过了\n积分: ${integral} | 威望: ${upmine}`;
        }
        await page.waitForSelector('#um', { timeout: 5000 });
        await page.evaluate(() => {
            let qiandao = document.querySelector('#um a[href^="home.php?mod=task&do=apply&id=2"]');
            if (!qiandao) return;
            let iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = qiandao.href;
            document.body.appendChild(iframe);
            qiandao.href = 'javascript:void(0);';
        });

        magicJS.sleep(3000);
        await page.reload({ waitUntil: ['networkidle0'] });

        const signedInAfter = await page.$('img.qq_bind[src*="wbs.png"]');
        if (signedInAfter) {
            msg += `✅ 签到成功\n积分: ${integral} | 威望: ${upmine}`;
        } else {
            msg += `❌ 签到失败\n积分: ${integral} | 威望: ${upmine}`;
        }
        await closeLogger();
    } catch (err) {
        msg += `❌ 异常: ${err.message}`;
    } finally {
        await browser.close();
        await fs.rm(userDataDir, { recursive: true, force: true });
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
