#!/usr/bin/env bash

# shellcheck disable=SC2005,2188
<<'COMMENT'
cron: 1 1 1 1 *
new Env('安装 selenium tesseract);
COMMENT

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

py_reqs="pytesseract selenium-stealth PyVirtualDisplay undetected-chromedriver"
alpine_pkgs="tesseract-ocr-data-eng chromium-chromedriver libexif eudev xvfb"

install() {
    local count=0 flag=$1
    while true; do
        local result=$3
        flag=$((result > 0 ? 0 : 1))
        if [ "$flag" -eq "$1" ]; then
            echo -e "---------- ${2##* } 安装成功 ----------\n"
            break
        else
            count=$((count + 1))
            if [ "$count" -eq 3 ]; then
                echo "!! 自动安装失败，请尝试进入容器后执行 $2 !!"
                break
            fi
            echo ".......... 3 秒后重试 ........."
            sleep 3
        fi
    done
}

install_alpine_pkgs() {
    apk update >/dev/null 2>&1
    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            echo "$pkg 已安装"
        else
            echo ".......... 开始安装 $pkg ........."
            install 0 "apk add --no-cache $pkg" "$(apk add --no-cache "$pkg" | grep -c 'OK')"
        fi
    done
}

install_py_reqs() {
    pip3 install --root-user-action=ignore --upgrade pip -q
    for pkg in $py_reqs; do
        if pip show "$pkg" >/dev/null 2>&1; then
            echo "$pkg 已安装"
        else
            echo ".......... 开始安装 $pkg ........."
            install 0 "pip3 install $pkg" \
            "$(pip3 install --disable-pip-version-check --root-user-action=ignore "$pkg" | grep -c 'Successfully')"
        fi
    done
}

install_alpine_pkgs
install_py_reqs
