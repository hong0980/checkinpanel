/*
吾爱破解
cron "3 0,11 * * *" ck_pojie.js
 */

// 导入工具模块
const utils = require('./utils');
const sendNotify = require('./sendNotify');
const Env = utils.Env;
const MagicJS = utils.MagicJS;
const getData = utils.getData;

// 初始化环境
const $ = new Env('吾爱破解');
const notify = $.isNode() ? require('./notify') : '';
const magicJS = MagicJS('吾爱破解', 'INFO');
const COOKIES_POJIE = getData().POJIE;
const fs = require('fs').promises;
const path = require('path');
const { getEnv } = require('jsutils');
const puppeteer = require('puppeteer-extra').use(
    require('puppeteer-extra-plugin-stealth')()
);

/**
 * 设置浏览器实例
 * @returns {Promise<Object>} 浏览器和页面对象
 */
async function setupBrowser() {
    // 启动浏览器实例
    const browser = await puppeteer.launch({
        headless: true, // 无头模式（不显示界面）
        executablePath: '/usr/bin/chromium', // Chromium 可执行文件路径
        args: [
            '--no-sandbox', // 禁用沙盒（在容器环境中常用）
            '--disable-dev-shm-usage', // 禁用共享内存（解决容器内存问题）
            '--disable-gpu', // 禁用 GPU 加速
            '--disable-software-rasterizer', // 禁用软件光栅化
            '--disable-blink-features=AutomationControlled', // 隐藏自动化控制特征
            '--ignore-gpu-blocklist', // 忽略 GPU 黑名单
        ],
    });

    // 创建新页面
    const page = await browser.newPage();
    // 设置用户代理（模拟真实浏览器）
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    // 设置额外的 HTTP 头
    await page.setExtraHTTPHeaders({
        'Accept-Language': 'zh-CN,zh;q=0.8', // 接受中文语言
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    });

    // 增强 stealth 功能，绕过反爬虫检测
    await page.evaluateOnNewDocument(() => {
        // 隐藏 webdriver 属性
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        // 设置平台为 Windows
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        // 禁用调试器
        Object.defineProperty(window, 'debugger', { value: undefined, writable: false });

        // 重写 setInterval 以防止调试器检测
        const originalSetInterval = window.setInterval;
        window.setInterval = function (callback, timeout) {
            if (typeof callback === 'function' && callback.toString().includes('debugger')) return;
            if (typeof callback === 'string' && callback.includes('debugger')) return;
            return originalSetInterval.apply(this, arguments);
        };

        // 重写 setTimeout 以防止调试器检测
        const originalSetTimeout = window.setTimeout;
        window.setTimeout = function (callback, timeout) {
            if (typeof callback === 'function' && callback.toString().includes('debugger')) return;
            if (typeof callback === 'string' && callback.includes('debugger')) return;
            return originalSetTimeout.apply(this, arguments);
        };
    });

    return { browser, page };
}

/**
 * 执行签到功能
 * @param {string} cookie - 用户 Cookie
 * @param {number} index - 账号索引
 * @returns {Promise<string>} 签到结果消息
 */
async function sign(cookie, index) {
    let msg = '';
    // 设置浏览器和页面
    const { browser, page } = await setupBrowser();
    // 创建临时目录用于存储调试文件
    const tempDir = `/tmp/52pojie_${index}_${Date.now()}`;
    await fs.mkdir(tempDir, { recursive: true });

    try {
        // 设置 Cookie
        const cookies = cookie.split('; ').map(c => {
            const [name, value] = c.split('=', 2);
            return { name, value, domain: '.52pojie.cn', path: '/' };
        });
        await page.setCookie(...cookies);

        // 导航到论坛首页
        await page.goto('https://www.52pojie.cn/forum.php', {
            waitUntil: 'networkidle2', // 等待网络空闲
            timeout: 30000 // 30 秒超时
        });

        // 检查是否已登录（通过检查登录按钮是否存在）
        const loginButton = await page.$('a[href*="member.php?mod=logging&action=login"]');
        if (loginButton) {
            return `❌ 无法登录！可能Cookie失效，请重新修改`;
        }

        // 获取用户名、积分和威望
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
        msg = `---- ${username} 吾爱破解 签到状态 ----\n`;

        // 检查今天是否已经签到
        const signedIn = await page.$('img.qq_bind[src*="wbs.png"]');
        if (signedIn) {
            return `${msg}<b><span style="color: green">✅ 今天已经签到过了</span></b>\n积分: ${integral} | 威望: ${upmine}`;
        }

        // 尝试访问签到页面
        const signUrl = 'https://www.52pojie.cn/home.php?mod=task&do=apply&id=2';
        let wafScript = null;

        // 监听网络响应，捕获 WAF 脚本
        page.on('response', async response => {
            const url = response.url();
            if (url.includes('waf_zw_verify') || url.endsWith('.js')) {
                const text = await response.text();
                if (text.includes('waf_zw_verify')) {
                    wafScript = text;
                    // 保存 WAF 脚本用于调试
                    await fs.writeFile(path.join(tempDir, `waf_script_${url.split('/').pop()}`), text);
                }
            }
        });

        // 导航到签到页面
        await page.goto(signUrl, { waitUntil: 'networkidle2', timeout: 30000 });

        // 检查页面内容，处理 WAF 验证
        const pageContent = await page.content();
        await fs.writeFile(path.join(tempDir, `page_content_${index}.txt`), pageContent);
        $.log('Page Content Preview:', pageContent.slice(0, 500));
        $.log('Current URL:', page.url());

        // 检测 WAF 验证页面
        if (page.url().includes('waf_text_verify.html') || pageContent.includes('waf_zw_verify') || pageContent.includes('请完成安全验证')) {
            // 提取 wzws_sid
            const cookies = await page.cookies();
            let wzwsSid = cookies.find(c => c.name === 'wzws_sid')?.value;
            if (!wzwsSid) {
                const sidMatch = pageContent.match(/wzws_sid["']?\s*[:=]\s*["']([^"']+)["']/i);
                wzwsSid = sidMatch ? sidMatch[1] : null;
            }
            if (!wzwsSid) {
                return `${msg}❌ 未获取到 wzws_sid，签到失败`;
            }

            // 尝试使用网络加载的 WAF 脚本
            let encryptedData = null;
            if (wafScript) {
                const funcMatch = wafScript.match(/function\s+(\w+)\s*\([^)]*\)\s*{[^}]*waf_zw_verify/i);
                const funcName = funcMatch ? funcMatch[1] : 'encrypt_wzws';
                encryptedData = await page.evaluate((sid, code, fname) => {
                    eval(code);
                    return typeof window[fname] === 'function' ? window[fname](sid) : null;
                }, wzwsSid, wafScript, funcName);
            }

            // 回退到内联脚本
            if (!encryptedData) {
                const jsMatch = pageContent.match(/<script[^>]*>([\s\S]*?waf_zw_verify[\s\S]*?)<\/script>/i);
                if (!jsMatch) {
                    $.logErr('未匹配到 WAF 脚本');
                    return `${msg}❌ 未找到 WAF 脚本，签到失败`;
                }
                const jsCode = jsMatch[1];
                const funcMatch = jsCode.match(/function\s+(\w+)\s*\([^)]*\)\s*{[^}]*waf_zw_verify/i);
                const funcName = funcMatch ? funcMatch[1] : 'encrypt_wzws';
                encryptedData = await page.evaluate((sid, code, fname) => {
                    eval(code);
                    return typeof window[fname] === 'function' ? window[fname](sid) : null;
                }, wzwsSid, jsCode, funcName);
            }

            if (encryptedData) {
                // 向 WAF 验证接口发送 POST 请求
                const verifyResponse = await page.evaluate(async (url, data, sid) => {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `data=${encodeURIComponent(data)}&sid=${encodeURIComponent(sid)}`,
                    });
                    return response.ok ? await response.json() : null;
                }, 'https://www.52pojie.cn/waf_zw_verify', encryptedData, wzwsSid);

                if (verifyResponse && verifyResponse.new_sid) {
                    // 设置新的会话 ID
                    await page.setCookie({
                        name: 'wzws_sid',
                        value: verifyResponse.new_sid,
                        domain: '.52pojie.cn',
                        path: '/',
                    });
                    $.log(`✅ WAF 验证成功，新 sid: ${verifyResponse.new_sid}`);
                } else {
                    return `${msg}❌ WAF 验证失败`;
                }
            } else {
                return `${msg}❌ 无法执行 WAF 加密脚本`;
            }

            // WAF 验证后重试签到
            await page.goto(signUrl, { waitUntil: 'networkidle2', timeout: 30000 });
        }

        // 完成签到（领取奖励）
        const drawUrl = 'https://www.52pojie.cn/home.php?mod=task&do=draw&id=2';
        await page.goto(drawUrl, { waitUntil: 'networkidle2', timeout: 30000 });

        // 检查签到结果
        const messageText = await page.evaluate(() => {
            const el = document.querySelector('#messagetext');
            return el ? el.textContent.trim() : '';
        });

        if (messageText.includes('恭喜')) {
            // 刷新页面获取更新后的积分信息
            await page.goto('https://www.52pojie.cn/forum.php', { waitUntil: 'networkidle2' });
            const newIntegral = await page.evaluate(() => {
                const el = document.querySelector('#extcreditmenu');
                return el ? el.textContent.trim() : '未知';
            });
            const newUpmine = await page.evaluate(() => {
                const el = document.querySelector('#g_upmine');
                return el ? el.textContent.trim() : '未知';
            });
            return `${msg}✅ 签到成功\n积分: ${newIntegral} | 威望: ${newUpmine}`;
        } else {
            return `${msg}❌ 签到失败: ${messageText || '未知错误'}`;
        }

    } catch (error) {
        // 异常处理
        return `${msg}<b><span style="color: red">异常：</span></b>\n${error.message}`;
    } finally {
        // 清理资源
        try {
            // 保存页面内容和截图用于调试
            await fs.writeFile(path.join(tempDir, `52pojie_${index}.html`), await page.content());
            await page.screenshot({ path: path.join(tempDir, `52pojie_${index}.png`) });
        } catch (e) {
            $.logErr(`保存调试文件失败: ${e.message}`);
        }
        // 关闭浏览器
        await browser.close();
        try {
            // 删除临时目录
            await fs.rm(tempDir, { recursive: true, force: true });
        } catch (e) {}
    }
}

/**
 * 主函数 - 处理所有账号的签到
 * @returns {Promise<void>}
 */
async function main() {
    let msgAll = '';
    let checkItems = COOKIES_POJIE || '';
    // 遍历所有账号进行签到
    for (let i = 0; i < checkItems.length; i++) {
        const cookie = checkItems[i].cookie;
        if (!cookie) {
            msgAll += `账号 ${i + 1} 签到状态: ❌ Cookie 为空\n\n`;
            continue;
        }
        const signMsg = await sign(cookie, i + 1);
        msgAll += `账号 ${i + 1} 签到状态: ${signMsg}\n\n`;
    }
    $.done;
    // 发送通知（已注释）
    notify.sendNotify('吾爱破解', msgAll);
    $.log(msgAll);
}

// 执行主函数并处理异常
main().catch(err => {
    $.logErr(err);
    process.exit(1);
});

module.exports = { main };
