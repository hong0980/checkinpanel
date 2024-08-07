#!/usr/bin/env sh

# shellcheck disable=SC2005,2188
<<'COMMENT'
cron: 1 1 1 1 *
new Env('签到依赖');
COMMENT

. utils_env.sh
get_some_path
checkinpanel_master=$(find "${SCR_PATH}" -type d -name "*checkinpanel_master" -print -quit 2>/dev/null)
checkinpanel_master=${checkinpanel_master##*/}
checkinpanel_master=${checkinpanel_master:-"OreosLab_checkinpanel_master"}

pl_mods="File::Slurp JSON5 TOML::Dumper"
js_pkgs="@iarna/toml axios cron-parser crypto-js got"
alpine_pkgs="libffi-dev make openssl-dev perl-app-cpanminus perl-dev py3-pip"
py_reqs="cryptography dateparser feedparser peewee pytest requests_html schedule tomli lxml_html_clean"

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
    pip3 install --root-user-action=ignore --upgrade pip
    for req in $py_reqs; do
        if pip show "$req" >/dev/null 2>&1; then
            echo "$req 已安装"
        else
            install 0 "pip3 install $req" \
            "$(pip3 install --disable-pip-version-check --root-user-action=ignore "$req" | grep -c 'Successfully')"
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
        cd "${SCR_PATH}/${checkinpanel_master}" || return
        cp "${REPO_PATH}/${checkinpanel_master}/package.json" "${SCR_PATH}/${checkinpanel_master}/package.json"
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
    npm install || return
}

install_js_pkgs_each() {
    is_empty=$(npm ls "$1" | grep empty)
    has_err=$(npm ls "$1" | grep ERR)
    
    if [ -z "$is_empty" ] && [ -z "$has_err" ]; then
        echo "$1 已正确安装"
    else
        if [ -n "$has_err" ]; then
            npm uninstall "$1"
            rm -rf "$(pwd)/node_modules/$1"
            rm -rf /usr/local/lib/node_modules/lodash/*
            npm cache clear --force
        fi
        install 1 "npm install $1" "$(npm install --force "$1" && npm ls --force "$1" | grep -cE '(empty)|ERR')"
    fi
}

install_js_pkgs_all() {
    install_js_pkgs_initial
    for i in $js_pkgs; do
        install_js_pkgs_each "$i"
    done
    npm ls --depth 0
}

install_pl_mods() {
    if command -v cpm >/dev/null 2>&1; then
        echo "App::cpm 已安装"
    else
        install 1 "cpanm -fn App::cpm" "$(cpanm -fn App::cpm | grep -c 'FAIL')"
        
        if ! command -v cpm >/dev/null 2>&1; then
            if [ -f ./cpm ]; then
                chmod +x cpm && ./cpm --version
            else
                cp -f /ql/repo/${checkinpanel_master}/cpm ./ && chmod +x cpm && ./cpm --version ||
                curl -fsSL https://cdn.jsdelivr.net/gh/Oreomeow/checkinpanel/cpm >cpm && chmod +x cpm && ./cpm --version
            fi
        fi
    fi
    
    for i in $pl_mods; do
        if perldoc -l "$i" > /dev/null 2>&1; then
            echo "$i 已安装"
        else
            install 1 "cpm install -g $i" "$(cpm install -g "$i" | grep -c 'FAIL')"
        fi
    done
}

install_alpine_pkgs
install_py_reqs
install_js_pkgs_all
install_pl_mods
