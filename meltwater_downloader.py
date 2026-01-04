#!/usr/bin/env python3
"""
Meltwater 自动登录和下载脚本
功能:
1. 自动登录 Meltwater 平台
2. 导出过去一年的数据为 CSV
3. 下载 CSV 文件到本地
"""

import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 从环境变量读取 Meltwater 登录信息
MELTWATER_EMAIL = os.getenv("MELTWATER_EMAIL")
MELTWATER_PASSWORD = os.getenv("MELTWATER_PASSWORD")
MELTWATER_URL = os.getenv("MELTWATER_URL", "https://app.meltwater.com")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")


class MeltwaterDownloader:
    """Meltwater 自动下载器"""

    def __init__(self, email: str, password: str, url: str, download_path: str):
        self.email = email
        self.password = password
        self.url = url
        self.download_path = download_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 确保下载目录存在
        os.makedirs(self.download_path, exist_ok=True)

    def start_browser(self):
        """启动浏览器"""
        logger.info("启动浏览器...")
        self.playwright = sync_playwright().start()

        # 启动 Chromium 浏览器
        self.browser = self.playwright.chromium.launch(
            headless=True,  # GitHub Actions 中使用 headless 模式
            args=['--no-sandbox', '--disable-dev-shm-usage']  # 云环境优化
        )

        # 创建浏览器上下文,设置下载路径
        self.context = self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )

        self.page = self.context.new_page()
        logger.info("浏览器启动成功")

    def login(self):
        """登录 Meltwater (包含 Solution 选择和两步登录)"""
        logger.info(f"访问 Meltwater: {self.url}")
        self.page.goto(self.url, wait_until='networkidle', timeout=60000)

        # 等待登录页面加载
        time.sleep(3)

        # 保存初始页面截图用于调试
        try:
            screenshot_path = os.path.join(self.download_path, "debug_step1_initial.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存初始页面截图: {screenshot_path}")
        except:
            pass

        # 第一步: 输入邮箱
        logger.info("第一步: 输入邮箱...")
        email_selector = 'input[type="email"], input[name="email"], input[id="email"]'
        self.page.wait_for_selector(email_selector, timeout=30000)
        self.page.fill(email_selector, self.email)

        # 保存填写邮箱后的截图
        try:
            screenshot_path = os.path.join(self.download_path, "debug_step2_email_filled.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存邮箱填写后截图: {screenshot_path}")
        except:
            pass

        # 查找并点击 Next/Continue 按钮
        logger.info("点击 Next 按钮...")
        next_button_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button[type="submit"]',
            'input[type="submit"]',
            'button',  # 最后尝试所有按钮
        ]

        next_clicked = False
        for selector in next_button_selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    self.page.click(selector, timeout=5000)
                    logger.info(f"已点击 Next 按钮: {selector}")
                    next_clicked = True
                    break
            except:
                continue

        if not next_clicked:
            logger.warning("未找到 Next 按钮,可能是单页登录,继续...")
            # 保存未找到按钮时的截图
            try:
                screenshot_path = os.path.join(self.download_path, "debug_no_next_button.png")
                self.page.screenshot(path=screenshot_path)
                logger.info(f"已保存未找到Next按钮截图: {screenshot_path}")
            except:
                pass

        # 等待页面跳转
        time.sleep(3)

        # 保存等待后的截图
        try:
            screenshot_path = os.path.join(self.download_path, "debug_step3_after_wait.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存等待后截图: {screenshot_path}")
        except:
            pass

        # 第二步: 输入密码
        logger.info("第二步: 输入密码...")
        password_selector = 'input[type="password"], input[name="password"], input[id="password"]'
        self.page.wait_for_selector(password_selector, timeout=30000)

        # 先清空密码框,然后使用 type() 逐字符输入(处理特殊字符)
        self.page.click(password_selector)
        time.sleep(0.5)  # 等待字段获得焦点
        self.page.fill(password_selector, '')  # 清空
        time.sleep(0.3)  # 等待清空完成

        # 逐字符输入密码
        logger.info(f"开始输入密码(长度: {len(self.password)})")
        self.page.type(password_selector, self.password, delay=100)  # 增加延迟到100ms
        time.sleep(0.5)  # 等待输入完成

        # 验证密码是否被输入(检查 value 属性)
        password_value = self.page.input_value(password_selector)
        logger.info(f"密码字段当前值长度: {len(password_value)}")
        if len(password_value) == 0:
            logger.error("❌ 密码字段为空,输入失败!")
        elif len(password_value) != len(self.password):
            logger.warning(f"⚠️ 密码长度不匹配: 期望 {len(self.password)}, 实际 {len(password_value)}")

        # 保存密码填写后的截图
        try:
            screenshot_path = os.path.join(self.download_path, "debug_step4_password_filled.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存密码填写后截图: {screenshot_path}")
        except:
            pass

        # 点击登录按钮
        logger.info("点击登录按钮...")
        time.sleep(1)  # 等待1秒再点击登录
        login_button_selector = 'button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")'
        self.page.click(login_button_selector)

        logger.info("等待登录完成...")
        # 等待页面跳转,检查是否成功登录
        try:
            # 等待仪表板或主页元素出现
            self.page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(2)

            # 处理 passkey 弹窗 - 点击"Continue without passkeys"
            passkey_continue_selectors = [
                'a:has-text("Continue without passkeys")',
                'button:has-text("Continue without passkeys")',
                'text=Continue without passkeys',
                '[href*="continue"]',
            ]

            for selector in passkey_continue_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.click(selector, timeout=5000)
                        logger.info(f"✅ 已点击跳过 passkey: {selector}")
                        time.sleep(3)
                        break
                except:
                    continue

            logger.info("登录成功!")
        except PlaywrightTimeout:
            logger.error("登录超时,可能需要验证码或凭证错误")
            raise

    def export_data(self, days_back: int = 365):
        """
        导出数据
        新策略: 直接从 Home 页的 Alerts 区域下载已就绪的文件

        Args:
            days_back: 导出过去多少天的数据,默认 365 天(一年)
        """
        logger.info(f"开始导出过去 {days_back} 天的数据...")

        try:
            # 等待页面完全加载,确保所有动态内容都已渲染
            logger.info("等待页面完全加载...")

            # 等待页面中的关键元素出现(说明页面已完全加载)
            try:
                self.page.wait_for_selector('text=Hello', timeout=10000)
                logger.info("✅ 检测到欢迎信息")
            except:
                logger.warning("未检测到欢迎信息,但继续执行")

            # 额外等待以确保动态内容(包括 Alerts 区域)完全加载
            # 使用 wait_for_load_state 等待网络空闲
            logger.info("等待网络空闲...")
            try:
                self.page.wait_for_load_state('networkidle', timeout=15000)
                logger.info("✅ 网络已空闲")
            except:
                logger.warning("网络未完全空闲,但继续执行")

            # 再等待 10 秒确保所有 React/JS 渲染完成
            logger.info("额外等待 10 秒以确保动态内容完全渲染...")
            time.sleep(10)

            # 保存初始页面截图
            screenshot_path = os.path.join(self.download_path, "debug_home_page.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"已保存 Home 页面截图: {screenshot_path}")

            # 新策略: 直接从 Home 页的 Alerts 区域下载
            # 根据截图,Alerts 区域显示 "ANZ_Coverage_2025" 文件已就绪
            logger.info("步骤1: 在 Alerts 区域查找 ANZ Coverage 2025 下载按钮...")

            # 尝试找到 Alerts 区域中包含 "ANZ_Coverage_2025" 的下载按钮
            # 可能的选择器策略:
            # 1. 找到包含 "ANZ_Coverage_2025" 文本的元素,然后找其附近的 Download 按钮
            # 2. 直接找所有 Download 按钮,选择最新的一个

            # 策略: 根据截图分析,需要点击 ANZ_Coverage 文件旁边的三点菜单按钮
            # 然后从菜单中选择下载选项

            download_found = False

            # 先检查是否有 ANZ_Coverage_2025 相关文件
            anz_text_selectors = [
                'text=ANZ_Coverage_2025',
                'text=ANZ Coverage 2025',
                '[title*="ANZ_Coverage_2025"]',
                '[aria-label*="ANZ_Coverage_2025"]',
            ]

            anz_file_exists = False
            for selector in anz_text_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        logger.info(f"✅ 找到 ANZ Coverage 文件: {selector}")
                        anz_file_exists = True
                        break
                except:
                    continue

            if anz_file_exists:
                logger.info("步骤2: 在 Alerts 区域点击 Download 按钮...")

                # 根据截图分析,Alerts 面板中每个通知都有一个直接的 "Download" 按钮
                # 策略: 找到包含 ANZ_Coverage_2025 的通知,然后在该通知容器中找 Download 元素

                # 监听下载事件
                logger.info("开始监听下载事件...")
                with self.page.expect_download(timeout=180000) as download_info:
                    # 尝试多种方式找到并点击 Download 按钮/链接
                    download_button_selectors = [
                        # === 按钮 ===
                        # 通过文本匹配的按钮
                        'button:has-text("Download")',
                        'button:text-is("Download")',
                        '[role="button"]:has-text("Download")',

                        # === 链接 ===
                        # 可能是链接元素
                        'a:has-text("Download")',
                        'a:text-is("Download")',
                        '[role="link"]:has-text("Download")',

                        # === 特定区域内的按钮/链接 ===
                        # Alerts 面板内的所有 Download 元素
                        '[aria-label="Alerts"] button:has-text("Download")',
                        '[aria-label="Alerts"] a:has-text("Download")',
                        '[aria-label="Alerts"] [role="button"]:has-text("Download")',

                        # === 父元素导航 ===
                        # 在 ANZ_Coverage 附近查找
                        'text=ANZ_Coverage_2025 >> .. >> button',
                        'text=ANZ_Coverage_2025 >> .. >> a',
                        'text=ANZ_Coverage_2025 >> .. >> .. >> button',
                        'text=ANZ_Coverage_2025 >> .. >> .. >> a',
                        'text=ANZ_Coverage_2025 >> .. >> .. >> .. >> button',
                        'text=ANZ_Coverage_2025 >> .. >> .. >> .. >> a',

                        # 在 "Your CSV file is ready" 附近查找
                        'text=Your CSV file is ready >> .. >> button',
                        'text=Your CSV file is ready >> .. >> a',
                        'text=Your CSV file is ready >> .. >> .. >> button',
                        'text=Your CSV file is ready >> .. >> .. >> a',

                        # === 通过 CSS 类或其他属性 ===
                        # 查找所有按钮样式的元素(可能是 div 或其他)
                        '[class*="button"]:has-text("Download")',
                        '[class*="btn"]:has-text("Download")',
                        'div:has-text("Download")[role="button"]',

                        # === 通过 aria-label ===
                        'button[aria-label*="Download"]',
                        'a[aria-label*="Download"]',
                        '[aria-label*="Download"]',

                        # === CSV 文件链接 ===
                        # 可能有直接的 CSV 下载链接
                        'a[href*=".csv"]',
                        '[aria-label="Alerts"] a[href*=".csv"]',
                    ]

                    for selector in download_button_selectors:
                        try:
                            locator = self.page.locator(selector)
                            count = locator.count()
                            if count > 0:
                                logger.info(f"✅ 找到 {count} 个下载元素: {selector}")
                                # 点击第一个(最新的)
                                locator.first.click(timeout=5000)
                                logger.info(f"✅ 已点击下载元素: {selector}")
                                download_found = True
                                break
                        except Exception as e:
                            logger.debug(f"尝试下载元素选择器失败: {selector} - {str(e)}")
                            continue

                    if not download_found:
                        logger.error("未找到下载按钮")
                        screenshot_path = os.path.join(self.download_path, "error_no_download_button.png")
                        self.page.screenshot(path=screenshot_path)
                        raise Exception("未找到下载按钮")

                    logger.info("等待下载完成...")

                # 保存下载的文件
                download = download_info.value
                filename = f"meltwater_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.download_path, filename)
                download.save_as(filepath)

                logger.info(f"✅ 文件下载成功: {filepath}")
                return filepath

            else:
                # 如果 Alerts 没有现成文件,先主动发起导出请求
                logger.warning("Alerts 区域没有找到 ANZ Coverage 文件,主动发起导出请求...")

                # 直接导航到监控视图 (使用用户提供的直达URL,避免在 Tags 页面查找标签)
                monitor_url = "https://app.meltwater.com/a/monitor/view?searches=2062364&type=tag"
                logger.info(f"直接访问监控视图: {monitor_url}")
                self.page.goto(monitor_url, wait_until='load', timeout=60000)

                # 等待页面完全加载 - GitHub Actions 环境可能需要更长时间
                logger.info("等待页面完全加载...")
                time.sleep(5)

                # 等待网络空闲
                try:
                    self.page.wait_for_load_state('networkidle', timeout=20000)
                    logger.info("✅ 网络已空闲")
                except:
                    logger.warning("网络未完全空闲,但继续执行")

                # 额外等待以确保 JavaScript 渲染完成
                logger.info("等待 JavaScript 渲染完成...")
                time.sleep(10)

                # 保存截图
                screenshot_path = os.path.join(self.download_path, "debug_monitor_view.png")
                self.page.screenshot(path=screenshot_path)
                logger.info(f"已保存监控视图截图: {screenshot_path}")

                # 在监控视图页面找到并点击下载按钮
                logger.info("步骤4: 触发导出请求...")

                # 新策略: 先触发导出请求,而不是查找现有的下载按钮
                # 因为 GitHub Actions 环境是全新的,没有预先存在的导出文件

                # 查找并点击 Export/导出 按钮来触发新的导出请求
                export_triggered = False
                export_selectors = [
                    'button:has-text("Export")',
                    'button:has-text("导出")',
                    'a:has-text("Export")',
                    'a:has-text("导出")',
                    '[aria-label*="Export"]',
                    '[aria-label*="导出"]',
                    'button:has-text("Download")',
                    'button:has-text("下载")',
                    # 可能需要先打开菜单
                    'button[aria-label="Actions"]',
                    'button[aria-label="More options"]',
                    'button:has-text("Actions")',
                    'button:has-text("More")',
                ]

                logger.info("尝试找到 Export 按钮...")
                for selector in export_selectors:
                    try:
                        locator = self.page.locator(selector)
                        if locator.count() > 0:
                            logger.info(f"✅ 找到可能的导出按钮: {selector}")
                            locator.first.click(timeout=5000)
                            logger.info(f"✅ 已点击按钮: {selector}")
                            time.sleep(2)  # 等待响应

                            # 保存点击后的截图
                            screenshot_path = os.path.join(self.download_path, f"debug_after_click_{selector.replace(':', '_').replace('[', '').replace(']', '')[:30]}.png")
                            self.page.screenshot(path=screenshot_path)

                            # 检查是否打开了菜单或对话框
                            # 如果是菜单按钮,继续查找导出选项
                            if "Action" in selector or "More" in selector or "menu" in selector.lower():
                                logger.info("可能打开了菜单,继续查找导出选项...")
                                time.sleep(1)

                                # 在菜单中查找导出选项
                                menu_export_selectors = [
                                    'button:has-text("Export")',
                                    'a:has-text("Export")',
                                    '[role="menuitem"]:has-text("Export")',
                                    'li:has-text("Export")',
                                ]

                                for menu_selector in menu_export_selectors:
                                    try:
                                        menu_locator = self.page.locator(menu_selector)
                                        if menu_locator.count() > 0:
                                            logger.info(f"✅ 在菜单中找到导出选项: {menu_selector}")
                                            menu_locator.first.click(timeout=5000)
                                            logger.info("✅ 已点击导出选项")
                                            export_triggered = True
                                            time.sleep(2)
                                            break
                                    except Exception as e:
                                        logger.debug(f"菜单导出选项失败: {menu_selector} - {str(e)}")
                                        continue
                            else:
                                export_triggered = True

                            if export_triggered:
                                break
                    except Exception as e:
                        logger.debug(f"导出按钮选择器失败: {selector} - {str(e)}")
                        continue

                if not export_triggered:
                    logger.warning("⚠️ 未能触发导出请求,尝试备用方案...")

                    # 备用方案: 使用 JavaScript 查找所有可能的导出按钮
                    logger.info("使用 JavaScript 查找导出按钮...")
                    try:
                        buttons_info = self.page.evaluate("""
                            () => {
                                const buttons = [];
                                document.querySelectorAll('button, a, [role="button"], [role="menuitem"]').forEach((el, index) => {
                                    const text = el.textContent?.trim() || '';
                                    const ariaLabel = el.getAttribute('aria-label') || '';
                                    const title = el.getAttribute('title') || '';

                                    const keywords = ['export', 'download', '导出', '下载'];
                                    const hasKeyword = keywords.some(keyword =>
                                        text.toLowerCase().includes(keyword.toLowerCase()) ||
                                        ariaLabel.toLowerCase().includes(keyword.toLowerCase()) ||
                                        title.toLowerCase().includes(keyword.toLowerCase())
                                    );

                                    if (hasKeyword) {
                                        el.setAttribute('data-export-index', index.toString());
                                        buttons.push({
                                            index: index,
                                            text: text,
                                            ariaLabel: ariaLabel,
                                            title: title,
                                            tagName: el.tagName
                                        });
                                    }
                                });
                                return buttons;
                            }
                        """)

                        logger.info(f"JavaScript 找到 {len(buttons_info)} 个可能的导出按钮:")
                        for btn in buttons_info:
                            logger.info(f"  - [{btn['index']}] {btn['tagName']}: {btn['text'][:50]}")

                        # 尝试点击找到的按钮
                        for btn in buttons_info:
                            try:
                                logger.info(f"尝试点击按钮 [{btn['index']}]: {btn['text'][:30]}...")
                                selector = f"[data-export-index='{btn['index']}']"
                                self.page.click(selector, timeout=5000)
                                logger.info(f"✅ 已点击按钮: {btn['text'][:30]}")
                                export_triggered = True
                                time.sleep(2)
                                break
                            except Exception as e:
                                logger.debug(f"点击按钮失败: {btn['text'][:30]} - {str(e)}")
                                continue
                    except Exception as e:
                        logger.error(f"JavaScript 查找失败: {e}")

                # 步骤5: 等待导出完成并从 Alerts 下载
                if export_triggered:
                    logger.info("步骤5: 导出已触发,等待文件生成...")
                    logger.info("将定期检查 Home 页面的 Alerts 区域...")

                    # 等待导出完成 - 最多等待 5 分钟
                    max_wait_time = 300  # 5分钟
                    check_interval = 30  # 每30秒检查一次
                    elapsed_time = 0
                    download_found = False

                    while elapsed_time < max_wait_time and not download_found:
                        logger.info(f"⏳ 等待中... ({elapsed_time}/{max_wait_time}秒)")
                        time.sleep(check_interval)
                        elapsed_time += check_interval

                        # 访问 Home 页面检查 Alerts
                        logger.info("检查 Home 页面 Alerts...")
                        self.page.goto(f"{self.url}/a/home", wait_until='networkidle', timeout=60000)
                        time.sleep(3)

                        # 查找 Alerts 区域中的 CSV 下载链接
                        alert_selectors = [
                            'a:has-text("Your CSV file is ready")',
                            'a:has-text("CSV")',
                            '[class*="alert"] a:has-text("Download")',
                            '[class*="notification"] a:has-text("Download")',
                            'a[href*=".csv"]',
                        ]

                        for selector in alert_selectors:
                            try:
                                locator = self.page.locator(selector)
                                if locator.count() > 0:
                                    logger.info(f"✅ 在 Alerts 中找到 CSV 下载链接: {selector}")

                                    # 尝试下载
                                    with self.page.expect_download(timeout=30000) as download_info:
                                        locator.first.click(timeout=5000)
                                        logger.info("✅ 已点击下载链接")

                                    download = download_info.value
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"meltwater_export_{timestamp}.csv"
                                    filepath = os.path.join(self.download_path, filename)
                                    download.save_as(filepath)
                                    logger.info(f"✅ 文件已保存: {filepath}")

                                    download_found = True
                                    return filepath
                            except Exception as e:
                                logger.debug(f"Alert 选择器失败: {selector} - {str(e)}")
                                continue

                        if not download_found:
                            logger.info(f"⏳ 文件尚未就绪,{check_interval}秒后再次检查...")

                    if not download_found:
                        logger.error("❌ 等待超时,导出文件未在规定时间内生成")
                        screenshot_path = os.path.join(self.download_path, "error_export_timeout.png")
                        self.page.screenshot(path=screenshot_path, full_page=True)
                        logger.info(f"已保存超时截图: {screenshot_path}")
                        raise Exception("导出文件生成超时")
                else:
                    logger.error("❌ 未能触发导出请求")
                    screenshot_path = os.path.join(self.download_path, "error_no_export_button.png")
                    self.page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"已保存错误截图: {screenshot_path}")

                    # 输出页面 HTML 用于调试
                    html_path = os.path.join(self.download_path, "error_page.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(self.page.content())
                    logger.info(f"已保存页面 HTML: {html_path}")

                    raise Exception("未能触发导出请求")

        except Exception as e:
            logger.error(f"导出数据时出错: {str(e)}")
            # 保存截图用于调试
            screenshot_path = os.path.join(self.download_path, "error_screenshot.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存错误截图: {screenshot_path}")
            raise

    def close(self):
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")

    def download(self, days_back: int = 365) -> str:
        """
        完整的下载流程

        Args:
            days_back: 导出过去多少天的数据

        Returns:
            下载的文件路径
        """
        try:
            self.start_browser()
            self.login()
            filepath = self.export_data(days_back)
            return filepath
        finally:
            self.close()


def main():
    """主函数"""
    # 检查必要的环境变量
    if not MELTWATER_EMAIL or not MELTWATER_PASSWORD:
        logger.error("错误: 缺少 MELTWATER_EMAIL 或 MELTWATER_PASSWORD 环境变量")
        return None

    logger.info("=" * 50)
    logger.info("Meltwater 自动下载开始")
    logger.info("=" * 50)

    # 创建下载器实例
    downloader = MeltwaterDownloader(
        email=MELTWATER_EMAIL,
        password=MELTWATER_PASSWORD,
        url=MELTWATER_URL,
        download_path=DOWNLOAD_PATH
    )

    try:
        # 下载过去一年的数据
        filepath = downloader.download(days_back=365)
        logger.info(f"✅ 下载完成: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ 下载失败: {str(e)}")
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print(f"SUCCESS:{result}")
    else:
        print("FAILED")
        exit(1)
