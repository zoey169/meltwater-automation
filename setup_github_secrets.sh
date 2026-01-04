#!/bin/bash
#
# 配置 GitHub Secrets 脚本
# 使用方法: ./setup_github_secrets.sh
#

set -e

echo "========================================"
echo "配置 GitHub Secrets"
echo "========================================"
echo ""

# 检查 gh CLI 是否已安装
if ! command -v gh &> /dev/null; then
    echo "❌ 未找到 gh CLI"
    echo "请先安装: brew install gh"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ 未登录 GitHub"
    echo "请先运行: gh auth login"
    exit 1
fi

echo "✓ gh CLI 已就绪"
echo ""

# 从本地环境读取配置
echo "请输入以下配置信息:"
echo ""

read -p "飞书 APP ID [cli_a702c225665e100d]: " FEISHU_APP_ID
FEISHU_APP_ID=${FEISHU_APP_ID:-cli_a702c225665e100d}

read -sp "飞书 APP SECRET [5D7PoQaMtb8Er1qqfUnGpfcYiFekaX2b]: " FEISHU_APP_SECRET
echo ""
FEISHU_APP_SECRET=${FEISHU_APP_SECRET:-5D7PoQaMtb8Er1qqfUnGpfcYiFekaX2b}

read -p "多维表格 APP TOKEN [ExoBbLPZoajFihsvegNcDvUsnce]: " BITABLE_APP_TOKEN
BITABLE_APP_TOKEN=${BITABLE_APP_TOKEN:-ExoBbLPZoajFihsvegNcDvUsnce}

read -p "多维表格 TABLE ID [tblqmDCzRUdDMI3x]: " BITABLE_TABLE_ID
BITABLE_TABLE_ID=${BITABLE_TABLE_ID:-tblqmDCzRUdDMI3x}

read -p "目标群 ID [oc_8a3dc5b72d6ed10d57582b925d138223]: " TARGET_CHAT_ID
TARGET_CHAT_ID=${TARGET_CHAT_ID:-oc_8a3dc5b72d6ed10d57582b925d138223}

read -p "通知邮箱 [zoey.yuan@anker.com]: " NOTIFICATION_EMAIL
NOTIFICATION_EMAIL=${NOTIFICATION_EMAIL:-zoey.yuan@anker.com}

echo ""
echo "========================================"
echo "开始配置 Secrets..."
echo "========================================"
echo ""

# 设置 GitHub Secrets
gh secret set FEISHU_APP_ID --body "$FEISHU_APP_ID"
echo "✓ FEISHU_APP_ID 已设置"

gh secret set FEISHU_APP_SECRET --body "$FEISHU_APP_SECRET"
echo "✓ FEISHU_APP_SECRET 已设置"

gh secret set BITABLE_APP_TOKEN --body "$BITABLE_APP_TOKEN"
echo "✓ BITABLE_APP_TOKEN 已设置"

gh secret set BITABLE_TABLE_ID --body "$BITABLE_TABLE_ID"
echo "✓ BITABLE_TABLE_ID 已设置"

gh secret set TARGET_CHAT_ID --body "$TARGET_CHAT_ID"
echo "✓ TARGET_CHAT_ID 已设置"

gh secret set NOTIFICATION_EMAIL --body "$NOTIFICATION_EMAIL"
echo "✓ NOTIFICATION_EMAIL 已设置"

echo ""
echo "========================================"
echo "✅ 所有 Secrets 配置完成!"
echo "========================================"
echo ""
echo "现在可以运行 GitHub Actions 了:"
echo "  gh workflow run meltwater-import.yml"
echo ""
