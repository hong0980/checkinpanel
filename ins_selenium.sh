#!/usr/bin/env bash

# shellcheck disable=SC2005,2188
<<'COMMENT'
cron: 1 1 1 1 *
new Env('安装 selenium tesseract);
COMMENT

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

py_reqs="selenium-stealth pytesseract PyVirtualDisplay undetected-chromedriver"
alpine_pkgs="freetype-dev ttf-freefont dbus chromium-chromedriver tesseract-ocr-data-eng libexif eudev xvfb"

# 安装函数：自动重试 + 错误退出
install() {
    local max_retries=3
    local retry_count=0
    local cmd="$1"
    local pkg="$2"

    while [ $retry_count -lt $max_retries ]; do
        echo "尝试安装 $pkg (第 $((retry_count + 1)) 次)"
        if eval "$cmd"; then
            echo "✅ $pkg 安装成功"
            return 0
        fi
        retry_count=$((retry_count + 1))
        echo "⚠️ 安装失败，3 秒后重试..."
        sleep 3
    done

    echo "❌ $pkg 安装失败，请手动检查！"
    exit 1
}

# 安装 Alpine 依赖
install_alpine_pkgs() {
    echo "更新 Alpine 包索引..."
    apk update --no-cache

    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装，跳过"
        else
            install "apk add --no-cache $pkg" "$pkg"
        fi
    done
}

# 安装 Python 依赖
install_py_reqs() {
    echo "升级 pip..."
    pip3 install --root-user-action=ignore --upgrade pip

    for pkg in $py_reqs; do
        if pip show "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装，跳过"
        else
            install "pip3 install --root-user-action=ignore --disable-pip-version-check $pkg" "$pkg"
        fi
    done
}

# 验证关键工具
verify_installation() {
    echo "验证 Chromium 版本..."
    chromium-browser --version || { echo "❌ Chromium 未正确安装"; exit 1; }

    echo "验证 Tesseract 版本..."
    tesseract --version || { echo "❌ Tesseract 未正确安装"; exit 1; }

    echo "验证 Python 模块..."
    python3 -c "
import pytesseract, selenium, PIL
print('✅ 所有 Python 模块加载成功')
" || { echo "❌ Python 模块加载失败"; exit 1; }
}

# 主流程
main() {
    install_alpine_pkgs
    install_py_reqs
    verify_installation
    echo "🎉 所有依赖安装完成！"
}

main
