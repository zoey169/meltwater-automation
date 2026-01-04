#!/usr/bin/env python3
"""
调试脚本 - 分析监控视图页面的 DOM 结构,找出下载按钮的实际选择器
"""
import os
import time
from playwright.sync_api import sync_playwright

def analyze_monitor_view():
    """分析监控视图页面,找出所有可能的下载按钮"""

    email = os.getenv('MELTWATER_EMAIL')
    password = os.getenv('MELTWATER_PASSWORD')

    if not email or not password:
        print("❌ 请设置 MELTWATER_EMAIL 和 MELTWATER_PASSWORD 环境变量")
        return

    print("=" * 80)
    print("监控视图页面 DOM 结构分析")
    print("=" * 80)

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 步骤1: 登录
            print("\n步骤1: 登录...")
            page.goto("https://app.meltwater.com/", wait_until='load', timeout=60000)
            time.sleep(3)

            page.fill('input[type="email"]', email)
            page.click('button[type="submit"]')
            time.sleep(2)

            page.type('input[type="password"]', password, delay=100)
            time.sleep(1)
            page.click('button[type="submit"]')

            print("等待登录完成...")
            # 等待页面加载完成而不是等待特定 URL
            time.sleep(10)  # 给足够时间加载

            # 跳过 passkey 弹窗
            try:
                page.click('a:has-text("Continue without passkeys")', timeout=5000)
                print("✅ 已跳过 passkey")
                time.sleep(3)
            except:
                print("⚠️ 未找到 passkey 弹窗,继续...")

            print("✅ 登录成功")

            # 步骤2: 访问监控视图
            print("\n步骤2: 访问监控视图...")
            monitor_url = "https://app.meltwater.com/a/monitor/view?searches=2062364&type=tag"
            page.goto(monitor_url, wait_until='load', timeout=60000)
            time.sleep(10)  # 等待页面完全加载
            print("✅ 已进入监控视图")

            # 保存截图
            page.screenshot(path="./downloads/debug_monitor_dom.png", full_page=True)
            print("✅ 已保存全页截图: ./downloads/debug_monitor_dom.png")

            # 步骤3: 分析页面上的所有按钮和链接
            print("\n步骤3: 分析页面上的所有可点击元素...")
            print("-" * 80)

            # 查找所有按钮
            print("\n🔍 所有 <button> 元素:")
            buttons = page.query_selector_all('button')
            for i, btn in enumerate(buttons[:50]):  # 只显示前50个
                try:
                    text = btn.inner_text()
                    aria_label = btn.get_attribute('aria-label')
                    title = btn.get_attribute('title')
                    class_name = btn.get_attribute('class')

                    if any(keyword in str(x).lower() for x in [text, aria_label, title, class_name]
                           for keyword in ['download', 'export', 'csv', 'save', 'action']):
                        print(f"\n  [{i}] 🎯 可能的下载按钮:")
                        print(f"      文本: {text}")
                        print(f"      aria-label: {aria_label}")
                        print(f"      title: {title}")
                        print(f"      class: {class_name[:100] if class_name else None}...")
                except:
                    pass

            # 查找所有链接
            print("\n🔍 所有 <a> 元素 (包含 download/export):")
            links = page.query_selector_all('a')
            for i, link in enumerate(links[:50]):
                try:
                    text = link.inner_text()
                    href = link.get_attribute('href')
                    aria_label = link.get_attribute('aria-label')
                    title = link.get_attribute('title')
                    class_name = link.get_attribute('class')

                    if any(keyword in str(x).lower() for x in [text, href, aria_label, title, class_name]
                           for keyword in ['download', 'export', 'csv', 'save']):
                        print(f"\n  [{i}] 🎯 可能的下载链接:")
                        print(f"      文本: {text}")
                        print(f"      href: {href}")
                        print(f"      aria-label: {aria_label}")
                        print(f"      title: {title}")
                        print(f"      class: {class_name[:100] if class_name else None}...")
                except:
                    pass

            # 查找 role="button" 的元素
            print("\n🔍 所有 [role='button'] 元素:")
            role_buttons = page.query_selector_all('[role="button"]')
            for i, btn in enumerate(role_buttons[:50]):
                try:
                    text = btn.inner_text()
                    aria_label = btn.get_attribute('aria-label')
                    title = btn.get_attribute('title')
                    class_name = btn.get_attribute('class')

                    if any(keyword in str(x).lower() for x in [text, aria_label, title, class_name]
                           for keyword in ['download', 'export', 'csv', 'save', 'action', 'menu']):
                        print(f"\n  [{i}] 🎯 可能的按钮:")
                        print(f"      文本: {text}")
                        print(f"      aria-label: {aria_label}")
                        print(f"      title: {title}")
                        print(f"      class: {class_name[:100] if class_name else None}...")
                except:
                    pass

            # 查找任何包含 "actions", "menu", "toolbar" 的容器
            print("\n🔍 查找操作区域容器:")
            containers = page.query_selector_all('[class*="action"], [class*="menu"], [class*="toolbar"], [class*="header"]')
            for i, container in enumerate(containers[:20]):
                try:
                    class_name = container.get_attribute('class')
                    print(f"\n  [{i}] 容器: {class_name}")

                    # 在容器中查找按钮
                    inner_buttons = container.query_selector_all('button, a, [role="button"]')
                    for j, inner_btn in enumerate(inner_buttons[:5]):
                        try:
                            text = inner_btn.inner_text()
                            if text:
                                print(f"      > 按钮 {j}: {text[:50]}")
                        except:
                            pass
                except:
                    pass

            # 尝试使用 Playwright 的 accessibility tree
            print("\n🔍 分析可访问性树中的下载相关元素:")
            try:
                snapshot = page.accessibility.snapshot()
                def find_download_nodes(node, path=""):
                    if not node:
                        return

                    name = node.get('name', '')
                    role = node.get('role', '')

                    if any(keyword in str(name).lower() for keyword in ['download', 'export', 'csv', 'save']):
                        print(f"\n  🎯 找到: {role} - {name}")
                        print(f"     路径: {path}")

                    for child in node.get('children', []):
                        find_download_nodes(child, path + f" > {role}:{name}")

                find_download_nodes(snapshot)
            except Exception as e:
                print(f"  ⚠️ 无法分析可访问性树: {e}")

            print("\n" + "=" * 80)
            print("分析完成! 浏览器窗口将保持打开60秒,请手动检查页面...")
            print("=" * 80)
            time.sleep(60)

        except Exception as e:
            print(f"\n❌ 出错: {e}")
            page.screenshot(path="./downloads/debug_error.png")
            print("已保存错误截图")

        finally:
            browser.close()

if __name__ == "__main__":
    analyze_monitor_view()
