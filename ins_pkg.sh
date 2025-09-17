#!/usr/bin/env bash

<<'COMMENT'
cron: 1 1 1 1 *
new Env('签到依赖');
COMMENT

pl_mods="File::Slurp JSON5 TOML::Dumper"
alpine_pkgs="py3-pip libffi-dev openssl-dev perl-app-cpanminus perl-dev make"
py_reqs="cryptography dateparser feedparser peewee requests_html schedule tomli lxml_html_clean"
js_pkgs="@types/node axios@1.7.7 crypto-js console-table-printer@2.12.0 cheerio ds date-fns dotenv download form-data fs global-agent got@11.8.6 https-proxy-agent@7.0.5 js-base64 jsdom md5 moment png-js qrcode-terminal redis@4.7.0 request sharp toml tough-cookie ts-md5 tslib tunnel ws"

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
    pip3 install --user --root-user-action=ignore --upgrade pip -q >/dev/null 2>&1

    requests_html_info=$(pip3 show 'requests_html') || return
    requests_html_path=$(echo "$requests_html_info" | awk '/Location: / {print $2}')"/requests_html.py"
    if [ -f "$requests_html_path" ] && ! grep -q 'executablePath' "$requests_html_path"; then
        sed -i \
            -e "s|self, mock_browser|self, executablePath : str = None, mock_browser|" \
            -e "s|args=self.__browser_args)|args=self.__browser_args, executablePath=self.executablePath)|" \
            -e "/browser_args = browser_args/a\        self.executablePath = executablePath" \
            "$requests_html_path"
    fi
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

install_perl_modules() {
    echo -e "\n===== 开始安装 Perl 模块 ====="
    if command -v cpm >/dev/null 2>&1; then
        echo "ℹ️ App::cpm 已安装"
    else
        install "cpanm --quiet -fn --notest App::cpm >/dev/null 2>&1" "cpanm -fn App::cpm"
        if ! command -v cpm >/dev/null 2>&1; then
            curl -fsSL https://cdn.jsdelivr.net/gh/Oreomeow/checkinpanel/cpm >cpm && chmod +x cpm && ./cpm --version
        fi
    fi
    for pkg in $pl_mods; do
        if perldoc -l "$pkg" > /dev/null 2>&1; then
            printf "ℹ️ %-30s 已安装\n" "$pkg"
            continue
        fi
        echo "....... 安装 $pkg ......."
        install "cpm install -g --static-install $pkg" "$pkg"
    done
}

install_alpine_packages
install_python_packages
install_node_packages
install_perl_modules
