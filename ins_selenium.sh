#!/usr/bin/env bash

<<'COMMENT'
cron: 1 1 1 1 *
new Env('安装 selenium playwright tesseract');
COMMENT

js_pkgs="playwright playwright-extra puppeteer-extra-plugin-stealth
puppeteer-extra puppeteer-core rimraf"
py_reqs="selenium-stealth pytesseract PyVirtualDisplay undetected-chromedriver"
alpine_pkgs="freetype-dev ttf-freefont dbus chromium-chromedriver
tesseract-ocr-data-eng libexif eudev xvfb
alpine-sdk autoconf automake libtool font-noto-cjk"

install() {
    local max_retries=3 retry_count=0 cmd="$1" pkg="$2"
    while [ $retry_count -lt $max_retries ]; do
        [[ $retry_count -gt 0 ]] && echo "$pkg (第 $((retry_count + 1)) 次) 尝试安装"
        if eval "$cmd"; then
            printf "%-25s 安装成功 ✅\n\n" "$pkg"
            return
        fi
        retry_count=$((retry_count + 1))
        echo "⚠️ 安装失败，3 秒后重试..."
        sleep 3
    done
    echo "❌ $pkg 自动安装失败，请尝试进入容器后执行!!"
    return 1
}

install_alpine_packages() {
    echo -e "\n===== 开始安装 Alpine Linux 软件包 ====="
    apk update >/dev/null 2>&1
    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            printf "ℹ️ %-30s 已安装\n" "$pkg"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "apk add --no-cache --quiet $pkg" "$pkg"
    done
}

install_python_packages() {
    echo -e "\n===== 开始安装 Python 依赖包 ====="
    for pkg in $py_reqs; do
        if pip3 show "$pkg" >/dev/null 2>&1; then
            printf "ℹ️ %-30s 已安装\n" "$pkg"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "pip3 install --user -q --force-reinstall --disable-pip-version-check --root-user-action=ignore --use-pep517 $pkg" "$pkg"
    done
}

install_node_packages() {
    command -v pnpm &>/dev/null || install "npm install -g pnpm --silent" "pnpm"
    echo -e "\n===== 开始安装 Node.js 依赖包 ====="

    for pkg in $js_pkgs; do
        if [ -n "$(pnpm list -g $pkg --silent)" ]; then
            printf "ℹ️ %-30s 已安装\n" "$pkg"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "pnpm add -g --silent $pkg" "$pkg"
    done
    echo -e "\n===== 已经安装 Node.js 包 ====="
    pnpm list -g --depth 0
}

install_alpine_packages
install_python_packages
install_node_packages
