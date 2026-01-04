#!/bin/bash

# Meltwater Secrets 配置脚本
# 用于配置 Meltwater 登录凭证到 GitHub Secrets

echo "🔐 配置 Meltwater GitHub Secrets"
echo "================================"
echo ""

# 检查是否安装了 gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ 错误: 未找到 GitHub CLI (gh)"
    echo "请先安装: https://cli.github.com/"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ 错误: 未登录 GitHub CLI"
    echo "请先运行: gh auth login"
    exit 1
fi

echo "📝 请提供 Meltwater 登录信息:"
echo ""

# 读取用户输入
read -p "Meltwater 邮箱地址: " MELTWATER_EMAIL
read -sp "Meltwater 密码: " MELTWATER_PASSWORD
echo ""
read -p "Meltwater 登录 URL (默认: https://app.meltwater.com): " MELTWATER_URL
MELTWATER_URL=${MELTWATER_URL:-https://app.meltwater.com}

echo ""
echo "🔒 正在设置 GitHub Secrets..."

# 设置 Secrets
gh secret set MELTWATER_EMAIL --body "$MELTWATER_EMAIL"
gh secret set MELTWATER_PASSWORD --body "$MELTWATER_PASSWORD"
gh secret set MELTWATER_URL --body "$MELTWATER_URL"

echo ""
echo "✅ Meltwater Secrets 配置完成!"
echo ""
echo "已配置的 Secrets:"
echo "  - MELTWATER_EMAIL: ${MELTWATER_EMAIL}"
echo "  - MELTWATER_PASSWORD: ********"
echo "  - MELTWATER_URL: ${MELTWATER_URL}"
echo ""
echo "🎉 现在可以运行完整的自动化流程了!"
echo ""
echo "验证配置:"
echo "  gh secret list"
