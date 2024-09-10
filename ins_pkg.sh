#!/usr/bin/env bash

# shellcheck disable=SC2005,2188
<<'COMMENT'
cron: 1 1 1 1 *
new Env('签到依赖');
COMMENT

. utils_env.sh
get_some_path
checkinpanel_master=$(find "${SCR_PATH}" -type d -name "*checkinpanel*" -print -quit 2>/dev/null \
                    || echo "OreosLab_checkinpanel_master")
checkinpanel_master=${checkinpanel_master##*/}

pl_mods="File::Slurp JSON5 TOML::Dumper"
js_pkgs="@iarna/toml axios cron-parser crypto-js got"
alpine_pkgs="libffi-dev make openssl-dev perl-app-cpanminus perl-dev py3-pip"
py_reqs="cryptography dateparser feedparser peewee pytest requests_html schedule tomli lxml_html_clean"

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
            install 0 "apk add $pkg" "$(apk add --no-cache "$pkg" | grep -c 'OK')"
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

    requests_html_info=$(pip show 'requests_html') || return
    requests_html_path=$(echo "$requests_html_info" | awk '/Location: / {print $2}')"/requests_html.py"
    if [ -f "$requests_html_path" ] && ! grep -q 'executablePath' "$requests_html_path"; then
        sed -i \
            -e "s|self, mock_browser|self, executablePath : str = None, mock_browser|" \
            -e "s|args=self.__browser_args)|args=self.__browser_args, executablePath=self.executablePath)|" \
            -e "/browser_args = browser_args/a\        self.executablePath = executablePath" \
            "$requests_html_path"
    fi
}

install_js_pkgs_initial() {
    if [ -d "${SCR_PATH}/${checkinpanel_master}" ]; then
        [ -f "${SCR_PATH}/${checkinpanel_master}/package.json" ] || \
        cp -v "${REPO_PATH}/${checkinpanel_master}/package.json" "${SCR_PATH}/${checkinpanel_master}/package.json"
    elif [ -d "/ql/scripts" ] && [ ! -f "/ql/scripts/package.bak.json" ]; then
        cd /ql/scripts || return
        rm -rf node_modules .pnpm-store
        mv package-lock.json package-lock.bak.json
        mv package.json package.bak.json
        mv pnpm-lock.yaml pnpm-lock.bak.yaml

        install 1 "npm install -g package-merge" "$(npm install -g package-merge && \
            npm ls -g package-merge | grep -cE '(empty)|ERR')" &&
            export NODE_PATH="/usr/local/lib/node_modules" &&
            node -e "
                const merge = require('package-merge');
                const fs = require('fs');
                const dst = fs.readFileSync('/ql/repo/${checkinpanel_master}/package.json');
                const src = fs.readFileSync('/ql/scripts/package.bak.json');
                fs.writeFile('/ql/scripts/package.json', merge(dst, src), function (err) {
                    if (err) {
                        console.log(err);
                    } else {
                        console.log('package.json merged successfully!');
                    }
                });
            " || return
    fi
    npm install >/dev/null 2>&1 || return
}

install_js_pkgs_all() {
    install_js_pkgs_initial
    for pkg in $js_pkgs; do
        ls_result=$(npm ls "$pkg" --silent)
        if grep -q 'empty' <<< "$ls_result"; then
            echo ".......... 开始安装 $pkg ........."
            install 1 "npm install $pkg" \
                "$(npm install --force --silent "$pkg" && npm ls "$pkg" --silent | grep -qE 'empty|ERR')"
        elif grep -q 'ERR' <<< "$ls_result"; then
            echo "...... $pkg 安装错误，开始删除 ....."
            npm uninstall "$pkg" --silent
            rm -rf "$(pwd)"/node_modules/"$pkg"
            rm -rf /usr/local/lib/node_modules/"$pkg"
            npm install > /dev/null 2>&1
            npm cache clean --force --silent
        else
            echo "$pkg 已正确安装"
        fi
    done
    npm ls --depth 0
}

install_pl_mods() {
    if command -v cpm >/dev/null 2>&1; then
        echo "App::cpm 已安装"
    else
        install 1 "cpanm -fn App::cpm" "$(cpanm -fn App::cpm | grep -c "FAIL")"
        if ! command -v cpm >/dev/null 2>&1; then
            if [ -f ./cpm ]; then
                chmod +x cpm && ./cpm --version
            else
                cp -vf /ql/repo/${checkinpanel_master}/cpm ./ && chmod +x cpm && ./cpm --version
                if [ ! -f ./cpm ]; then
                    curl -fsSL https://cdn.jsdelivr.net/gh/Oreomeow/checkinpanel/cpm >cpm && chmod +x cpm && ./cpm --version
                fi
            fi
        fi
    fi
    for i in $pl_mods; do
        if perldoc -l "$i" > /dev/null 2>&1; then
            echo "$i 已安装"
        else
            echo ".......... 开始安装 $i ........."
            install 1 "cpm install -g $i" "$(cpm install -g --static-install "$i" | grep -q "FAIL")"
        fi
    done
}

install_alpine_pkgs
install_py_reqs
install_js_pkgs_all
install_pl_mods
