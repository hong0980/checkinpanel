/*
OurBits 签到
cron "1 0,11 * * *" ck_ourbits.js
 */

const utils = require('./utils');
const Env = utils.Env;
const MagicJS = utils.MagicJS;
const getData = utils.getData;

const $ = new Env('OurBits 签到');
const notify = $.isNode() ? require('./notify') : '';
const magicJS = MagicJS('OurBits', 'INFO');
const COOKIES_OURBITS = getData().OURBITS;

const fs = require('fs');
const path = require('path');
const { rimraf } = require('rimraf');
const { chromium } = require('playwright-extra');
const stealthPlugin = require('puppeteer-extra-plugin-stealth');
chromium.use(stealthPlugin());

async function injectAdvancedStealth(page) {
    await page.addInitScript(() => {
        try {
            // navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => false });

            // window.chrome
            window.chrome = window.chrome || {};
            window.chrome.runtime = {};
            window.chrome.csi = () => {};
            window.chrome.loadTimes = () => {};
            window.chrome.webstore = {};

            // hardware / memory / languages
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US'] });

            // connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    downlink: 10,
                    effectiveType: '4g',
                    rtt: 50,
                    saveData: false,
                    addEventListener: () => {},
                    removeEventListener: () => {}
                })
            });

            // plugins & mimeTypes
            const makePlugin = (name, filename, description) => ({ name, filename, description });
            const plugins = [
                makePlugin('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format'),
                makePlugin('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', ''),
                makePlugin('Native Client', 'internal-nacl-plugin', '')
            ];
            const pluginArray = plugins.slice();
            pluginArray.item = i => pluginArray[i] || null;
            pluginArray.namedItem = n => pluginArray.find(p => p.name === n) || null;
            Object.defineProperty(navigator, 'plugins', { get: () => pluginArray });

            const mimeTypes = [
                { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
            ];
            const mimeArray = mimeTypes.slice();
            mimeArray.item = i => mimeArray[i] || null;
            mimeArray.namedItem = t => mimeArray.find(m => m.type === t) || null;
            Object.defineProperty(navigator, 'mimeTypes', { get: () => mimeArray });

            // Canvas
            const origGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function (type, ...args) {
                const ctx = origGetContext.apply(this, [type, ...args]);
                if (type === '2d' && ctx) {
                    const origGetImageData = ctx.getImageData;
                    ctx.getImageData = function (x, y, w, h) {
                        const img = origGetImageData.apply(this, [x, y, w, h]);
                        for (let i = 0; i < img.data.length; i += 4) {
                            img.data[i] ^= 0x01;
                        }
                        return img;
                    };
                }
                return ctx;
            };

            const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function (...args) {
                const result = origToDataURL.apply(this, args);
                const img = new Image();
                img.src = result;
                const canvas = document.createElement('canvas');
                canvas.width = this.width;
                canvas.height = this.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
                for (let i = 0; i < data.data.length; i += 4) {
                    data.data[i] += Math.random() * 0.1;
                }
                ctx.putImageData(data, 0, 0);
                return canvas.toDataURL(...args);
            };

            // WebGL
            const proto = WebGLRenderingContext && WebGLRenderingContext.prototype;
            if (proto) {
                const origGetParam = proto.getParameter;
                proto.getParameter = function (p) {
                    if (p === 37445) return 'Intel Inc.';
                    if (p === 37446) return 'Intel Iris OpenGL Engine';
                    return origGetParam.apply(this, [p]);
                };
                const origGetShaderPrecision = proto.getShaderPrecisionFormat;
                proto.getShaderPrecisionFormat = function () {
                    return { rangeMin: -126, rangeMax: 127, precision: 23 };
                };
            }

            // AudioContext
            const origGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function () {
                const data = origGetChannelData.apply(this, arguments);
                const out = new Float32Array(data.length);
                for (let i = 0; i < data.length; i++) out[i] = data[i] + 1e-7;
                return out;
            };

            // mediaDevices
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                const origEnum = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
                navigator.mediaDevices.enumerateDevices = async function () {
                    try {
                        const d = await origEnum();
                        if (d && d.length) return d;
                    } catch {}
                    return [
                        { kind: 'audioinput', label: 'Default Microphone', deviceId: 'default' },
                        { kind: 'videoinput', label: 'Integrated Camera', deviceId: 'camera1' }
                    ];
                };
            }

            // Fonts
            Object.defineProperty(window, 'FontFace', {
                value: class FontFace {
                    constructor(family, src) {
                        this.family = family;
                        this.src = src;
                    }
                }
            });
            const fonts = ['Arial', 'Helvetica', 'Times New Roman', 'Georgia', 'Courier New'];
            Object.defineProperty(document, 'fonts', {
                get: () => ({
                    forEach: (cb) => fonts.forEach(f => cb({ family: f })),
                    size: fonts.length
                })
            });
        } catch {}
    });
}

async function simulateHumanMouse(page) {
    const viewport = await page.viewportSize();
    const centerX = viewport.width / 2;
    const centerY = viewport.height / 2;
    await page.mouse.move(0, 0);
    await page.waitForTimeout(100);
    for (let i = 0; i < 5; i++) {
        const x = centerX + Math.random() * 100 - 50;
        const y = centerY + Math.random() * 100 - 50;
        await page.mouse.move(x, y, { steps: 10 });
        await page.waitForTimeout(200 + Math.random() * 300);
    }
    await page.mouse.click(centerX, centerY);
}

async function setupBrowser() {
    const userAgents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
    ];
    const viewports = [
        { width: 1366, height: 768 },
        { width: 1920, height: 1080 },
        { width: 1440, height: 900 }
    ];

    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1366,768'
        ]
    });

    const context = await browser.newContext({
        locale: 'zh-CN',
        timezoneId: 'Asia/Shanghai',
        permissions: ['geolocation'],
        baseURL: 'https://ourbits.club',
        userAgent: userAgents[Math.floor(Math.random() * userAgents.length)],
        viewport: viewports[Math.floor(Math.random() * viewports.length)],
        geolocation: { latitude: 39.9042, longitude: 116.4074 },
        extraHTTPHeaders: {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    });

    const page = await context.newPage();
    await injectAdvancedStealth(page);
    await simulateHumanMouse(page);
    return { browser, context, page };
}

async function sign(cookie, index) {
    const msgHead = `---- 账号 ${index}: `;
    let msg = '', result = '', signed = '';
    const { browser, context, page } = await setupBrowser();

    const cookies = cookie.split('; ').map(c => {
        const [name, value] = c.split('=');
        return { name, value, domain: 'ourbits.club', path: '/', sameSite: 'Lax' };
    });
    await context.addCookies(cookies);

    try {
        await page.goto('/torrents.php', { timeout: 30000 });

        // 这里可做自动化交互：模拟真实用户的鼠标/键盘行为
        await page.mouse.move(100, 100);
        await page.mouse.down();
        await page.mouse.move(200, 200, { steps: 10 });
        await page.mouse.up();
        await page.waitForTimeout(1200);

        const username = await page.locator('a.CrazyUser_Name b')
            .textContent({ timeout: 5000 }).catch(() => {});
        if (!username) return `${msgHead} ❌ Cookie 可能失效，请重新获取 ----`;

        const html = await page.$eval('span.medium', el => el.outerHTML);
        const pattern = /魔力值[^:]*:\s*([\d,]+\.\d+).*?分享率：<\/span>\s*([\d.]+).*?上传量：<\/font>\s*([\d.]+)\s*TB.*?下载量：<\/font>\s*([\d.]+)\s*GB.*?当前做种[^>]*>(\d+)/s;
        const match = html.match(pattern);
        if (match) {
            result = `魔力值: ${match[1]}\n分享率： ${match[2]}\n上传量： ${match[3]} TB\n下载量： ${match[4]} GB\n做种中: ${match[5]}`;
        }

        if (html.includes('签到已得')) return `${magicJS.now()}\n${msgHead}${username} ✅ 今天已经签到过了 ----\n${result}`;

        const { logs, stop, getToken } = await utils.networkLog(page, {
            saveToFile: true,
            body_length: 1000,
            filename: "OurBits-log.json",
            filter: ["cloudflare", "turnstile"],
        });

        await page.goto('/attendance.php',
            { timeout: 30000, waitUntil: 'networkidle' }
        ).catch(() => console.log('❌ ❌ ❌ 执行完成'));

        const main = await page.locator('#outer table.main[width="940"]')
            .evaluate(el => el.outerHTML)
            .catch(() => '签到表单未找到');
        console.log(main)

        // const token = await page.waitForFunction(() => {
        //     const input = document.querySelector('input[name="cf-turnstile-response"]');
        //     return input?.value || null; // 返回 value 或继续等待
        // }, { timeout: 20000 }).catch(() => {});

        // if (token) {
        //     console.log('✅ Token:', token);
        //     await page.evaluate(() => {
        //         document.querySelector('form#attendance').submit();
        //     });
        // } else {
        //     console.log('❌ Turnstile 未返回 token');
        // }

        const content = await page.content()
        fs.writeFileSync('/tmp/OurBits.html', content);
        // const element = await page.$('form#attendance'); // 选中元素截图
        await page.screenshot({ path: '/tmp/OurBits.png', fullPage: true });

        // console.log(content)
        const sigContent = await page.content();
        if (sigContent.includes('签到成功')) {
            signed = await page.locator('#outer table[cellspacing="0"][border="1"] td.text')
                .textContent({ timeout: 3000 }).catch(() => {});
        }
        msg = `${magicJS.now()}\n${msgHead}${username} ${signed ? `签到成功 ✅\n${signed} ----` : `签到失败 ❌ ----`}\n${result}`;

    } catch (err) {
        msg += `❌ 异常: ${err.message}`;
    } finally {
        await browser.close().catch(() => {});
        await rimraf('/tmp/puppeteer_dev*', { glob: true }).catch(() => {});
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
            await magicJS.sleep(3000)
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
