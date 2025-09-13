#!/usr/bin/env bash

<<'COMMENT'
cron: 1 1 1 1 *
new Env('安装 selenium tesseract);
COMMENT

py_reqs="selenium-stealth pytesseract PyVirtualDisplay undetected-chromedriver psutil"
alpine_pkgs="freetype-dev ttf-freefont dbus chromium-chromedriver
tesseract-ocr-data-eng libexif eudev xvfb
alpine-sdk autoconf automake libtool"

install() {
    local max_retries=3 retry_count=0 cmd="$1" pkg="$2"
    while [ $retry_count -lt $max_retries ]; do
        [[ $retry_count != 0 ]] && echo "$pkg (第 $((retry_count + 1)) 次) 尝试安装"
        if eval "$cmd"; then
            echo -e "✅ $pkg 安装成功\n"
            return
        fi
        retry_count=$((retry_count + 1))
        echo "⚠️ 安装失败，3 秒后重试..."
        sleep 3
    done

    echo "❌ $pkg 自动安装失败，请尝试进入容器后执行!!"
    return 1
}

install_alpine_pkgs() {
    apk update >/dev/null 2>&1
    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "apk add --no-cache --quiet $pkg" "$pkg"
    done
}

install_py_reqs() {
    for pkg in $py_reqs; do
        if pip3 show "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "pip3 install --user -q --force-reinstall --disable-pip-version-check --root-user-action=ignore $pkg" "$pkg"
    done
}

install_alpine_pkgs
install_py_reqs
