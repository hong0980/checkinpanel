#!/usr/bin/env bash

<<'COMMENT'
cron: 45 12 */7 * *
new Env('国内加速');
COMMENT

# 日志输出函数
log() {
    local type="$1"
    local msg="$2"
    case "$type" in
        "INFO") echo -e "[\033[32mINFO\033[0m] $msg" ;;
        "WARN") echo -e "[\033[33mWARN\033[0m] ⚠️ $msg" ;;
        "ERROR") echo -e "[\033[31mERROR\033[0m] ❌ $msg" ;;
    esac
}

# 配置 Alpine 镜像源
config_alpine() {
    log INFO "📦 配置 Alpine 国内镜像源..."
    local repo_file="/etc/apk/repositories"
    if [ -f "$repo_file" ]; then
        sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' "$repo_file" || {
            log ERROR "Alpine 镜像源配置失败"
            return 1
        }
        apk update &>/dev/null && log INFO "Alpine 镜像源已配置为阿里云" || log ERROR "Alpine 软件源更新失败"
    else
        log WARN "Alpine 配置文件 $repo_file 不存在，跳过配置"
    fi
}

# 配置 Python pip 镜像源
config_pip() {
    log INFO "🐍 配置 Python pip 国内镜像源..."
    local pip_conf_dir="/root/.config/pip"
    local pip_conf_file="$pip_conf_dir/pip.conf"
    mkdir -p "$pip_conf_dir" || {
        log ERROR "无法创建 pip 配置目录 $pip_conf_dir"
        return 1
    }
cat > "$pip_conf_file" <<-EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
extra-index-url =
    https://mirrors.aliyun.com/pypi/simple/
    https://pypi.mirrors.ustc.edu.cn/simple/

[install]
trusted-host =
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.mirrors.ustc.edu.cn
EOF
    [ $? -eq 0 ] && log INFO "Python pip 源已配置（清华+阿里云+中科大）" || log ERROR "Python pip 配置失败"
}

# 配置 NPM 镜像源
config_npm() {
    log INFO "📦 配置 NPM 国内镜像源..."
    if command -v npm >/dev/null 2>&1; then
        local registry="https://registry.npmmirror.com"

        npm config set registry "$registry" >/dev/null 2>&1 || {
            log ERROR "NPM 镜像源配置失败，请检查日志：/root/.npm/_logs/*.log"
            return 1
        }

        local registry_output
        registry_output=$(npm config get registry 2>/dev/null | grep -v "npm warn")
        if echo "$registry_output" | grep -q "$registry"; then
            log INFO "✅ NPM 镜像源验证成功，设置为淘宝镜像 ($registry)"
        else
            log ERROR "NPM 镜像源验证失败，未设置为淘宝镜像"
        fi

        local bashrc_file="/root/.bashrc"
local node_mirror_config='
# Node.js and NPM mirrors
export NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node
export NODIST_NODE_MIRROR=https://npmmirror.com/mirrors/node
export PHANTOMJS_CDNURL=https://npmmirror.com/mirrors/phantomjs
export CHROMEDRIVER_CDNURL=https://npmmirror.com/mirrors/chromedriver
export OPERADRIVER_CDNURL=https://npmmirror.com/mirrors/operadriver
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export SASS_BINARY_SITE=https://npmmirror.com/mirrors/node-sass
export PUPPETEER_DOWNLOAD_HOST=https://npmmirror.com/mirrors
export DISTURL=https://npmmirror.com/dist
'

        if grep -q "NODEJS_ORG_MIRROR" "$bashrc_file" >/dev/null 2>&1; then
            log INFO "Node.js 镜像环境变量已存在于 $bashrc_file，跳过配置"
        else
            echo "$node_mirror_config" >> "$bashrc_file" || {
                log ERROR "无法写入 Node.js 镜像配置到 $bashrc_file"
                return 1
            }
            log INFO "已写入 Node.js 镜像环境变量到 $bashrc_file"
        fi

        source "$bashrc_file" >/dev/null 2>&1
        if env | grep -q "NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node"; then
            log INFO "✅ Node.js 镜像环境变量验证成功"
        else
            log WARN "Node.js 镜像环境变量验证失败，可能需手动 source $bashrc_file"
        fi
    else
        log WARN "NPM 未安装，跳过配置"
    fi
}

config_cpan() {
    log INFO "🐪 配置 CPAN 国内镜像源..."
    if command -v cpan >/dev/null 2>&1; then
        local cpan_conf_dir="/root/.cpan/CPAN"
        local cpan_conf_file="$cpan_conf_dir/MyConfig.pm"
        local mirror="http://mirrors.ustc.edu.cn/CPAN/"
        mkdir -p "$cpan_conf_dir" || {
            log ERROR "无法创建 CPAN 配置目录 $cpan_conf_dir"
            return 1
        }

        if [ -f "$cpan_conf_file" ]; then
            if grep -q "$mirror" "$cpan_conf_file"; then
                log INFO "CPAN 配置文件已包含中科大镜像，跳过追加"
            else
                perl -i -pe "s|'urllist' => \[(.*?)\]|'urllist' => [q[$mirror], $1]|" "$cpan_conf_file" || {
                    log ERROR "无法追加中科大镜像到 CPAN 配置"
                    return 1
                }
                log INFO "已追加中科大镜像到 CPAN 配置"
            fi
        else
cat > "$cpan_conf_file" <<-EOF
$CPAN::Config = {
  'allow_installing_module_downgrades' => q[ask/no],
  'allow_installing_outdated_dists' => q[ask/no],
  'applypatch' => q[],
  'auto_commit' => q[0],
  'build_cache' => q[100],
  'build_dir' => q[/root/.cpan/build],
  'build_dir_reuse' => q[0],
  'build_requires_install_policy' => q[yes],
  'bzip2' => q[/usr/bin/bzip2],
  'cache_metadata' => q[1],
  'check_sigs' => q[0],
  'cleanup_after_install' => q[0],
  'colorize_output' => q[0],
  'commandnumber_in_prompt' => q[1],
  'connect_to_internet_ok' => q[1],
  'cpan_home' => q[/root/.cpan],
  'ftp_passive' => q[1],
  'ftp_proxy' => q[],
  'getcwd' => q[cwd],
  'gpg' => q[],
  'gzip' => q[/bin/gzip],
  'halt_on_failure' => q[0],
  'histfile' => q[/root/.cpan/histfile],
  'histsize' => q[100],
  'http_proxy' => q[],
  'inactivity_timeout' => q[0],
  'index_expire' => q[1],
  'inhibit_startup_message' => q[0],
  'keep_source_where' => q[/root/.cpan/sources],
  'load_module_verbosity' => q[none],
  'make' => q[/usr/bin/make],
  'make_arg' => q[],
  'make_install_arg' => q[],
  'make_install_make_command' => q[/usr/bin/make],
  'makepl_arg' => q[],
  'mbuild_arg' => q[],
  'mbuild_install_arg' => q[],
  'mbuild_install_build_command' => q[./Build],
  'mbuildpl_arg' => q[],
  'no_proxy' => q[],
  'pager' => q[/usr/bin/less],
  'patch' => q[],
  'perl5lib_verbosity' => q[none],
  'prefer_external_tar' => q[1],
  'prefer_installer' => q[MB],
  'prefs_dir' => q[/root/.cpan/prefs],
  'prerequisites_policy' => q[follow],
  'recommends_policy' => q[1],
  'scan_cache' => q[atstart],
  'shell' => q[/bin/bash],
  'show_unparsable_versions' => q[0],
  'show_upload_date' => q[0],
  'show_zero_versions' => q[0],
  'suggests_policy' => q[0],
  'tar' => q[/bin/tar],
  'tar_verbosity' => q[none],
  'term_is_latin' => q[1],
  'term_ornaments' => q[1],
  'test_report' => q[0],
  'trust_test_report_history' => q[0],
  'unzip' => q[/usr/bin/unzip],
  'urllist' => [q[http://mirrors.ustc.edu.cn/CPAN/], q[http://mirrors.tuna.tsinghua.edu.cn/CPAN/]],
  'use_prompt_default' => q[0],
  'use_sqlite' => q[0],
  'version_timeout' => q[15],
  'wget' => q[/usr/bin/wget],
  'yaml_load_code' => q[0],
  'yaml_module' => q[YAML],
};
1;
EOF
            [ $? -eq 0 ] && log INFO "CPAN 配置文件已创建并配置中科大镜像" || {
                log ERROR "CPAN 配置文件创建失败"
                return 1
            }
        fi

        if cpan -J | grep -q "$mirror" >/dev/null 2>&1; then
            log INFO "✅ CPAN 源验证成功，包含中科大镜像"
        else
            log ERROR "CPAN 源验证失败，未找到中科大镜像"
        fi
    else
        log WARN "CPAN 未安装，跳过配置"
    fi
}

main() {
    log INFO "🚀 开始配置青龙面板国内加速源..."
    log INFO "=========================================="

    config_alpine
    config_pip
    config_npm
    config_cpan

    log INFO "=========================================="
    log INFO "🎉 青龙面板国内加速配置完成！"
    log INFO "📋 已配置："
    log INFO "   - Alpine 软件源 → 阿里云"
    log INFO "   - Python pip → 清华+阿里云+中科大"
    log INFO "   - NPM → 淘宝镜像 + Node.js 环境变量"
    log INFO "   - CPAN → 中科大镜像（追加或新建）"
    log INFO ""
}

main
