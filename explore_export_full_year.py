#!/usr/bin/env python3
"""
探索 Meltwater 完整导出流程
目标：找到如何创建 "Last Year" 的导出任务
"""

import os
import time
from playwright.sync_api import sync_playwright, Page, expect

class MeltwaterExplorer:
    def __init__(self):
        self.email = os.getenv("MELTWATER_EMAIL")
        self.password = os.getenv("MELTWATER_PASSWORD")
        self.url = os.getenv("MELTWATER_URL", "https://app.meltwater.com")
        self.download_path = os.path.abspath(os.getenv("DOWNLOAD_PATH", "./downloads"))
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """启动浏览器"""
        print("启动浏览器（有头模式，方便观察）...")
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=False,  # 有头模式
            slow_mo=1000     # 减慢操作，方便观察
        )
        self.context = self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = self.context.new_page()
        print("✅ 浏览器启动成功")

    def login(self):
        """登录 Meltwater"""
        print(f"\n访问 Meltwater: {self.url}")
        self.page.goto(self.url, wait_until="networkidle", timeout=60000)

        # 等待并填写邮箱
        print("输入邮箱...")
        self.page.fill('input[type="email"]', self.email)
        self.page.screenshot(path=f"{self.download_path}/explore_1_email.png")

        # 点击 Next
        print("点击 Next...")
        self.page.click('button:has-text("Next")')
        self.page.wait_for_timeout(3000)

        # 填写密码
        print("输入密码...")
        self.page.fill('input[type="password"]', self.password)
        self.page.screenshot(path=f"{self.download_path}/explore_2_password.png")

        # 点击登录
        print("点击登录...")
        self.page.click('button[type="submit"]')
        self.page.wait_for_timeout(3000)

        # 跳过 passkey
        try:
            skip_button = self.page.locator('button:has-text("Continue without passkeys")')
            if skip_button.is_visible(timeout=5000):
                print("跳过 passkey...")
                skip_button.click()
                self.page.wait_for_timeout(2000)
        except:
            print("没有 passkey 弹窗")

        # 等待进入主页
        print("等待进入主页...")
        self.page.wait_for_url("**/home", timeout=30000)
        print("✅ 登录成功!")

    def explore_anz_coverage(self):
        """探索 ANZ Coverage 的操作选项"""
        print("\n" + "="*60)
        print("探索 ANZ Coverage 2025 的操作选项")
        print("="*60)

        # 等待页面加载
        self.page.wait_for_timeout(5000)
        self.page.screenshot(path=f"{self.download_path}/explore_3_home.png")

        # 查找 ANZ Coverage 2025
        print("\n查找 ANZ_Coverage_2025...")
        anz_element = self.page.locator('text=ANZ_Coverage_2025').first

        if anz_element.is_visible():
            print("✅ 找到 ANZ_Coverage_2025")

            # 截图当前状态
            anz_element.scroll_into_view_if_needed()
            self.page.screenshot(path=f"{self.download_path}/explore_4_anz_found.png")

            # 查找父容器，看看有什么按钮
            print("\n查找相关按钮...")
            parent = anz_element.locator('..')

            # 尝试查找各种可能的按钮
            buttons = [
                "Export",
                "Download",
                "Settings",
                "More",
                "⋮",  # 三点菜单
                "Options"
            ]

            for btn_text in buttons:
                try:
                    btn = parent.locator(f'button:has-text("{btn_text}")').first
                    if btn.is_visible(timeout=1000):
                        print(f"  ✅ 找到按钮: {btn_text}")
                except:
                    pass

            # 点击 ANZ_Coverage_2025 本身，看看会发生什么
            print("\n点击 ANZ_Coverage_2025 文字...")
            anz_element.click()
            self.page.wait_for_timeout(3000)
            self.page.screenshot(path=f"{self.download_path}/explore_5_after_click.png")

            # 查看当前 URL
            current_url = self.page.url
            print(f"当前 URL: {current_url}")

            # 在这个页面上查找导出相关的按钮
            print("\n在详情页面查找导出选项...")
            export_buttons = self.page.locator('button, a').all()

            for btn in export_buttons[:20]:  # 只检查前20个
                try:
                    text = btn.inner_text(timeout=500)
                    if any(keyword in text.lower() for keyword in ['export', 'download', 'save']):
                        print(f"  📥 找到可能的导出按钮: {text}")
                except:
                    pass

            self.page.screenshot(path=f"{self.download_path}/explore_6_detail_page.png")

        else:
            print("❌ 未找到 ANZ_Coverage_2025")

    def explore_export_options(self):
        """探索导出选项（如果能找到导出按钮）"""
        print("\n" + "="*60)
        print("尝试查找导出/下载按钮")
        print("="*60)

        # 尝试多种可能的选择器
        selectors = [
            'button:has-text("Export")',
            'button:has-text("Download")',
            'a:has-text("Export")',
            'a:has-text("Download")',
            '[aria-label*="export"]',
            '[aria-label*="download"]',
        ]

        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    print(f"\n✅ 找到元素: {selector}")
                    print("点击查看选项...")
                    element.click()
                    self.page.wait_for_timeout(2000)
                    self.page.screenshot(path=f"{self.download_path}/explore_7_export_options.png")

                    # 查找时间范围选项
                    print("\n查找时间范围选项...")
                    time_options = self.page.locator('text=/Last Year|Past Year|365 days|12 months/i')
                    if time_options.count() > 0:
                        print(f"✅ 找到 {time_options.count()} 个时间选项:")
                        for i in range(time_options.count()):
                            print(f"  - {time_options.nth(i).inner_text()}")

                    break
            except Exception as e:
                continue

        self.page.screenshot(path=f"{self.download_path}/explore_8_final.png")

    def interactive_pause(self):
        """暂停并等待手动操作"""
        print("\n" + "="*60)
        print("⏸️  浏览器将保持打开状态")
        print("请在浏览器中手动操作，找到导出 Last Year 数据的方法")
        print("完成后在终端按 Enter 继续...")
        print("="*60)
        input()

    def close(self):
        """关闭浏览器"""
        if self.browser:
            print("\n关闭浏览器...")
            self.browser.close()
            print("✅ 浏览器已关闭")

    def run(self):
        """运行完整探索流程"""
        try:
            self.start_browser()
            self.login()
            self.explore_anz_coverage()
            self.explore_export_options()
            self.interactive_pause()
        finally:
            self.close()

if __name__ == "__main__":
    explorer = MeltwaterExplorer()
    explorer.run()
