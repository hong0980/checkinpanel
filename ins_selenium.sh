#!/usr/bin/env sh

# shellcheck disable=SC2005,2188
<<'COMMENT'
cron: 1 1 1 1 *
new Env('安装 selenium);
COMMENT

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

chromium_pkgs="chromium chromium-chromedriver libexif eudev xvfb"
pkgs="bash curl gcc git jq libffi-dev make musl-dev openssl-dev py3-pip python3 python3-dev wget"
alpine_pkgs="$pkgs $chromium_pkgs"
py_reqs="selenium-stealth PyVirtualDisplay undetected-chromedriver"

install() {
    count=0
    flag=$1
    while true; do
        echo ".......... 开始安装 ${2##* } .........."
        result=$3
        [ "$result" -gt 0 ] && flag=0 || flag=1
        if [ $flag -eq "$1" ]; then
            echo "---------- $2 成功安装 ----------"
            break
        else
            count=$((count + 1))
            if [ $count -eq 6 ]; then
                echo "!! 自动安装失败，请尝试进入容器后执行 $2 !!"
                break
            fi
            echo ".......... 5 秒后重试 .........."
            sleep 5
        fi
    done
}

install_alpine_pkgs() {
    apk update
    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            echo "$pkg 已安装"
        else
            install 0 "apk add $pkg" "$(apk add --no-cache "$pkg" | grep -c 'OK')"
        fi
    done
}

install_py_reqs() {
    pip3 install --upgrade pip
    for req in $py_reqs; do
        if pip show "$req" >/dev/null 2>&1; then
            echo "$req 已安装"
        else
            install 0 "pip3 install $req" "$(pip3 install "$req" | grep -c 'Successfully')"
        fi
    done
}

install_alpine_pkgs
install_py_reqs
