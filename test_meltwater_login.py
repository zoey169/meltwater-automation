#!/usr/bin/env python3
"""
测试 Meltwater 登录流程
用于诊断实际的登录界面和元素选择器
"""

import os
import time
from playwright.sync_api import sync_playwright

# 使用提供的凭证
MELTWATER_EMAIL = "tove.berkhout@anker.com"
MELTWATER_PASSWORD = "P3$NwcskGq6!!s3"
MELTWATER_URL = "https://app.meltwater.com"

def test_login():
    with sync_playwright() as p:
        # 启动浏览器 (非 headless 模式以便观察)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print("访问 Meltwater...")
        page.goto(MELTWATER_URL, wait_until='networkidle', timeout=60000)

        # 保存初始截图
        page.screenshot(path="downloads/step1_initial.png")
        print("已保存初始页面截图: downloads/step1_initial.png")

        # 等待并查看页面内容
        time.sleep(3)

        # 尝试查找邮箱输入框
        print("\n查找邮箱输入框...")
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="邮箱" i]'
        ]

        email_input = None
        for selector in email_selectors:
            try:
                if page.locator(selector).count() > 0:
                    email_input = selector
                    print(f"✅ 找到邮箱输入框: {selector}")
                    break
            except:
                continue

        if not email_input:
            print("❌ 未找到邮箱输入框")
            page.screenshot(path="downloads/error_no_email.png")
            browser.close()
            return

        # 填写邮箱
        print(f"填写邮箱: {MELTWATER_EMAIL}")
        page.fill(email_input, MELTWATER_EMAIL)
        page.screenshot(path="downloads/step2_email_filled.png")

        # 查找 "Next" 或 "Continue" 按钮
        print("\n查找 Next/Continue 按钮...")
        next_button_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button:has-text("下一步")',
            'button[type="submit"]',
            'input[type="submit"]'
        ]

        next_button = None
        for selector in next_button_selectors:
            try:
                if page.locator(selector).count() > 0:
                    next_button = selector
                    print(f"✅ 找到 Next 按钮: {selector}")
                    break
            except:
                continue

        if next_button:
            print("点击 Next 按钮...")
            page.click(next_button)
            time.sleep(3)
            page.screenshot(path="downloads/step3_after_next.png")

        # 现在查找密码输入框
        print("\n查找密码输入框...")
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="密码" i]'
        ]

        password_input = None
        for selector in password_selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                password_input = selector
                print(f"✅ 找到密码输入框: {selector}")
                break
            except:
                continue

        if not password_input:
            print("❌ 未找到密码输入框")
            page.screenshot(path="downloads/error_no_password.png")
            browser.close()
            return

        # 填写密码
        print(f"填写密码")
        page.fill(password_input, MELTWATER_PASSWORD)
        page.screenshot(path="downloads/step4_password_filled.png")

        # 查找登录按钮
        print("\n查找登录按钮...")
        login_button_selectors = [
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            'button:has-text("登录")',
            'button[type="submit"]',
            'input[type="submit"]'
        ]

        login_button = None
        for selector in login_button_selectors:
            try:
                if page.locator(selector).count() > 0:
                    login_button = selector
                    print(f"✅ 找到登录按钮: {selector}")
                    break
            except:
                continue

        if not login_button:
            print("❌ 未找到登录按钮")
            page.screenshot(path="downloads/error_no_login_button.png")
            browser.close()
            return

        # 点击登录
        print("点击登录按钮...")
        page.click(login_button)

        print("等待登录完成...")
        time.sleep(10)
        page.screenshot(path="downloads/step5_after_login.png")

        print("\n✅ 测试完成!")
        print("所有截图已保存到 downloads/ 目录")
        print("请检查截图以了解登录流程")

        # 保持浏览器打开 30 秒以便观察
        print("\n浏览器将在 30 秒后关闭...")
        time.sleep(30)

        browser.close()

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    test_login()
