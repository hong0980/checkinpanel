/*
 * OurBits 破解
 * cron "1 0,11 * * *" ck_ourbits.js
 */

const utils = require('./utils');
const notify = require('./notify');
const $ = new utils.Env('OurBits');
const magicJS = utils.MagicJS('OurBits', 'INFO');
const COOKIES_OURBITS = utils.getData().OURBITS;
const path = require('path');
const fs = require('fs').promises;
const ua = require('./JS_USER_AGENTS.js');
const { chromium } = require('playwright-extra');
// const stealthPlugin = require('puppeteer-extra-plugin-stealth');
// chromium.use(stealthPlugin());

function getPlatformInfo(userAgent) {
    // 优先 Android 绕过 PAT
    if (userAgent.includes('Android')) {
        return {
            platform: 'Android',
            secChUa: '"Chromium";v="130", "Not:A-Brand";v="24", "Google Chrome";v="130"',
            secChUaPlatform: '"Android"',
            viewport: { width: 412, height: 915 }, // Redmi Note 7
        };
    } else if (userAgent.includes('iPad')) {
        return {
            platform: 'iPad',
            secChUa: '"Not;A=Brand";v="8", "Chromium";v="130", "Mobile Safari";v="17.0"',
            secChUaPlatform: '"iOS"',
            viewport: { width: 1024, height: 768 }, // iPad6,3
        };
    } else {
        return {
            platform: 'iPhone',
            secChUa: '"Not;A=Brand";v="8", "Chromium";v="130", "Mobile Safari";v="17.0"',
            secChUaPlatform: '"iOS"',
            viewport: { width: 390, height: 844 }, // iPhone 14
        };
    }
}

async function setupBrowser(userDataDir) {
    let userAgent = ua.USER_AGENT;
    if (!userAgent.includes('Android')) {
        userAgent = 'Mozilla/5.0 (Linux; Android 10; Redmi Note 7 Build/QKQ1.190910.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.73 Mobile Safari/537.36';
    }
    const { platform, secChUa, secChUaPlatform, viewport } = getPlatformInfo(userAgent);

    const browser = await chromium.launchPersistentContext(userDataDir, {
        headless: true, // 调试用 false，生产用 true
        ignoreHTTPSErrors: true,
        javaScriptEnabled: true,
        baseURL: 'https://ourbits.club/',
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-gpu',
            '--ignore-gpu-blocklist',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            `--window-size=${viewport.width},${viewport.height}`,
            '--disable-extensions',
            '--disable-background-networking',
            '--disable-sync',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ],
        userAgent: userAgent,
        extraHTTPHeaders: {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Sec-Ch-Ua': secChUa,
            'Sec-Ch-Ua-Platform': secChUaPlatform,
            'Sec-Ch-Ua-Mobile': '?1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Encoding': 'gzip, deflate, br',
        },
        viewport: viewport,
        locale: 'zh-CN',
        timezoneId: 'Asia/Shanghai',
        geolocation: { latitude: 39.9042, longitude: 116.4074 },
        permissions: ['geolocation'],
    });

    // 增强指纹伪装
    await browser.addInitScript((platform) => {
        // 隐藏自动化痕迹
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'platform', {
            get: () => platform === 'Android' ? 'Linux armv8l' : platform === 'iPad' ? 'iPad' : 'iPhone'
        });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 4 });
        Object.defineProperty(navigator, 'plugins', { get: () => [] });
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => platform === 'Android' ?
                'Mozilla/5.0 (Linux; Android 10; Redmi Note 7 Build/QKQ1.190910.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.73 Mobile Safari/537.36' :
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        });

        // Chrome 对象（仅 Android）
        Object.defineProperty(window, 'chrome', {
            get: () => platform === 'Android' ? ({ runtime: {}, loadTimes: () => ({}), csi: () => ({}) }) : undefined
        });

        // 屏幕分辨率
        Object.defineProperty(screen, 'availWidth', { get: () => platform === 'Android' ? 412 : platform === 'iPad' ? 1024 : 390 });
        Object.defineProperty(screen, 'availHeight', { get: () => platform === 'Android' ? 915 : platform === 'iPad' ? 768 : 844 });
        Object.defineProperty(window, 'outerWidth', { get: () => platform === 'Android' ? 412 : platform === 'iPad' ? 1024 : 390 });
        Object.defineProperty(window, 'outerHeight', { get: () => platform === 'Android' ? 915 : platform === 'iPad' ? 768 : 844 });

        // 防止 debugger 干扰
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

        // 模拟移动端触摸和滚动
        setInterval(() => {
            const touchX = Math.random() * window.innerWidth;
            const touchY = Math.random() * window.innerHeight;
            window.dispatchEvent(new TouchEvent('touchstart', {
                changedTouches: [{ clientX: touchX, clientY: touchY }],
                bubbles: true,
            }));
            window.dispatchEvent(new TouchEvent('touchmove', {
                changedTouches: [{ clientX: touchX + (Math.random() * 20 - 10), clientY: touchY + (Math.random() * 20 - 10) }],
                bubbles: true,
            }));
            window.scrollTo(0, Math.random() * document.body.scrollHeight);
        }, 1000 + Math.random() * 2000);

        // Canvas 噪声（增强）
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function (type) {
            if (type === '2d') {
                const context = originalGetContext.apply(this, arguments);
                const originalGetImageData = context.getImageData;
                context.getImageData = function (...args) {
                    const imageData = originalGetImageData.apply(this, args);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.2 - 0.1; // 增强噪声
                        imageData.data[i + 1] += Math.random() * 0.2 - 0.1;
                        imageData.data[i + 2] += Math.random() * 0.2 - 0.1;
                    }
                    return imageData;
                };
                return context;
            }
            return originalGetContext.apply(this, arguments);
        };

        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function (parameter) {
            if (parameter === 37446) return platform === 'Android' ? 'Qualcomm' : 'Apple Inc.'; // VENDOR
            if (parameter === 37447) return platform === 'Android' ? 'Adreno (TM) 615' : 'Apple GPU'; // RENDERER
            return originalGetParameter.call(this, parameter);
        };

        Object.defineProperty(window, 'devicePixelRatio', { get: () => platform === 'Android' ? 2.625 : 3 });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => platform === 'Android' ? 5 : 10 });
    }, platform);
    return browser;
}

async function sign(cookie, index) {
    const userDataDir = path.join('/tmp', `pw_user_data_${index}`);
    const context = await setupBrowser(userDataDir);
    const msgHead = `---- 账号 ${index}: `;
    let msg = '', result = '';

    const cookies = cookie.split('; ').map(c => {
        const [name, value] = c.split('=');
        return { name, value, domain: 'ourbits.club', path: '/', sameSite: 'Lax' };
    });
    await context.addCookies(cookies);

    try {
        const page = context.pages()[0] || await context.newPage();
        await page.goto('/torrents.php', { timeout: 30000 });
        await page.waitForTimeout(1000 + Math.random() * 2000);
        await page.mouse.move(Math.random() * 800 + 100, Math.random() * 600 + 100);
        await page.evaluate(() => window.scrollTo(0, Math.random() * document.body.scrollHeight));

        const username = await page.locator('a.CrazyUser_Name b').textContent({ timeout: 5000 }).catch(() => null);
        if (!username) return `❌ ${msgHead} Cookie 可能失效，请重新获取`;

        const html = await page.$eval('span.medium', el => el.outerHTML);
        const pattern = /魔力值[^:]*:\s*([\d,]+\.\d+).*?分享率：<\/span>\s*([\d.]+).*?上传量：<\/font>\s*([\d.]+)\s*TB.*?下载量：<\/font>\s*([\d.]+)\s*GB.*?当前做种[^>]*>(\d+)/s;
        const match = html.match(pattern);
        if (match) {
            result = `魔力值: ${match[1]}\n分享率： ${match[2]}\n上传量： ${match[3]} TB\n下载量： ${match[4]} GB\n做种中: ${match[5]}`;
        }

        if (html.includes('签到已得')) {
            return `✅ ${msgHead}${username} 今天已经签到过了\n${result}`;
        }

        utils.networkLog(page, {
            filter: "cloudflare",
            saveToFile: true,
            filename: "cloudflare-log.json"
        });
        await page.goto('https://ourbits.club/attendance.php', {
            timeout: 16000,
            waitUntil: 'networkidle'
        }).catch(null);

        msg += `\n${result}`;

    } catch (err) {
        msg += `❌ 异常: ${err.message}`;
    } finally {
        await context.close().catch(() => {});
        await fs.rm(userDataDir, { recursive: true, force: true }).catch(() => {});
        await fs.rm('/tmp/puppeteer_dev*', { recursive: true, force: true }).catch(() => {});
    }
    return msg
}

async function main() {
    let msgAll = '=== OurBits 签到结果 ===\n';

    for (let i = 0; i < COOKIES_OURBITS.length; i++) {
        const cookie = COOKIES_OURBITS[i].cookie;
        let signMsg;

        if (!cookie) {
            signMsg = `账号 ${i + 1}: ❌ Cookie 为空`;
        } else {
            signMsg = await sign(cookie, i + 1);
        }

        msgAll += `${signMsg}\n-----------------------------------\n\n`;
        if (i < COOKIES_OURBITS.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 5000 + Math.random() * 10000));
        }
    }

    console.log(msgAll);
    magicJS.done();
    // notify.sendNotify('OurBits 签到', msgAll);
}

main().catch(err => {
    console.error('❌ 脚本异常:', err);
    process.exit(1);
});

module.exports = { main };
