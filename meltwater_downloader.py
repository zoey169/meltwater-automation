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
                # 如果 Alerts 没有现成文件,需要点击 ANZ Coverage 2025 链接进入其页面
                logger.warning("Alerts 区域没有找到 ANZ Coverage 文件,点击进入 ANZ Coverage 2025 页面...")

                # 步骤1: 在 Home 页面找到 ANZ Coverage 2025 链接并点击
                logger.info("步骤1: 查找并点击 ANZ Coverage 2025 链接...")

                # 先保存截图,看看 Home 页面上有什么
                debug_screenshot = os.path.join(self.download_path, "debug_before_link_search.png")
                self.page.screenshot(path=debug_screenshot, full_page=True)
                logger.info(f"已保存搜索前完整页面截图: {debug_screenshot}")

                # 使用 JavaScript 列出页面上所有的链接文本和 href
                logger.info("获取页面上所有链接...")
                try:
                    all_links = self.page.evaluate("""() => {
                        const links = Array.from(document.querySelectorAll('a'));
                        return links.map(link => ({
                            text: link.textContent.trim().substring(0, 100),
                            href: link.href,
                            visible: link.offsetParent !== null
                        })).filter(link => link.text.length > 0);
                    }""")
                    logger.info(f"找到 {len(all_links)} 个链接:")
                    for i, link in enumerate(all_links[:20]):  # 只显示前20个
                        logger.info(f"  链接 {i+1}: text='{link['text'][:50]}' href='{link['href'][:80]}' visible={link['visible']}")
                    if len(all_links) > 20:
                        logger.info(f"  ... 还有 {len(all_links) - 20} 个链接")
                except Exception as e:
                    logger.warning(f"无法获取链接列表: {e}")

                anz_coverage_selectors = [
                    'a:has-text("ANZ Coverage 2025")',
                    'text=ANZ Coverage 2025',
                    '[href*="2062364"]',  # 使用 search ID
                    'a:has-text("ANZ Coverage")',  # 不带年份的版本
                    'text=ANZ Coverage',  # 更宽松的匹配
                    '[href*="monitor"]',  # 任何监控相关的链接
                ]

                anz_clicked = False
                for selector in anz_coverage_selectors:
                    try:
                        locator = self.page.locator(selector)
                        count = locator.count()
                        logger.info(f"尝试选择器: {selector}, 找到 {count} 个元素")
                        if count > 0:
                            logger.info(f"✅ 找到 ANZ Coverage 2025 链接: {selector}")
                            locator.first.click(timeout=10000)
                            logger.info(f"✅ 已点击链接")
                            anz_clicked = True
                            break
                    except Exception as e:
                        logger.warning(f"链接选择器失败: {selector} - {str(e)}")
                        continue

                if not anz_clicked:
                    logger.error("❌ 未找到 ANZ Coverage 2025 链接")
                    screenshot_path = os.path.join(self.download_path, "error_no_anz_link.png")
                    self.page.screenshot(path=screenshot_path, full_page=True)
                    raise Exception("未找到 ANZ Coverage 2025 链接")

                # 等待页面完全加载
                logger.info("等待 ANZ Coverage 页面加载...")
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
                screenshot_path = os.path.join(self.download_path, "debug_anz_coverage_page.png")
                self.page.screenshot(path=screenshot_path)
                logger.info(f"已保存 ANZ Coverage 页面截图: {screenshot_path}")

                # 在 ANZ Coverage 页面触发导出
                logger.info("步骤2: 在 ANZ Coverage 页面触发导出...")

                # 实际的 UI 流程 (在 ANZ Coverage 2025 页面):
                # 1. 查找并点击下载图标 (xxx results 右边,魔法棒旁边,向下箭头 + 横线)
                # 2. 等待对话框出现
                # 3. 点击对话框中的确认按钮 (使用默认选项)
                # 4. 等待数据准备完成
                # 5. 检测右上角的浮动通知窗口
                # 6. 点击浮动窗口下载,或者从铃铛图标的通知中心下载

                export_triggered = False

                # Step 2.1: 查找下载按钮
                # 用户描述: xxx results 的右边,魔法棒旁边,向下箭头 + 横线
                logger.info("步骤2.1: 查找下载按钮(向下箭头图标)...")
                download_icon_selectors = [
                    # 直接查找下载图标 - 向下箭头
                    'button[aria-label*="Download"]',
                    'button[title*="Download"]',
                    'button[aria-label*="download"]',
                    'button[title*="download"]',

                    # SVG 图标相关
                    'svg[data-icon="download"]',
                    'button:has(svg[data-icon="download"])',

                    # 可能包含下载类名的按钮
                    'button:has([class*="download"])',
                    'button:has([class*="Download"])',
                    '[class*="download-icon"]',
                    '[class*="downloadIcon"]',
                    '[data-testid*="download"]',

                    # 尝试通过 results 文本附近查找
                    'text=/.*results.*/ >> .. >> button',
                    'text=/.*results.*/ >> xpath=.. >> button',
                ]

                icon_clicked = False
                for selector in download_icon_selectors:
                    try:
                        locator = self.page.locator(selector)
                        count = locator.count()
                        if count > 0:
                            logger.info(f"✅ 找到 {count} 个下载图标元素: {selector}")
                            # 保存截图查看图标位置
                            # 清理文件名中的特殊字符
                            safe_selector = selector.replace(':', '_').replace('[', '').replace(']', '').replace('*', '_').replace('"', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '').replace('/', '_')[:30]
                            screenshot_path = os.path.join(self.download_path, f"debug_found_icon_{safe_selector}.png")
                            self.page.screenshot(path=screenshot_path)

                            # 尝试点击第一个
                            locator.first.click(timeout=5000)
                            logger.info(f"✅ 已点击下载图标: {selector}")
                            icon_clicked = True
                            time.sleep(2)  # 等待对话框出现
                            break
                    except Exception as e:
                        logger.debug(f"下载图标选择器失败: {selector} - {str(e)}")
                        continue

                # 如果没找到特定的下载图标,使用 JavaScript 全局搜索
                if not icon_clicked:
                    logger.info("未找到明确的下载图标,使用 JavaScript 全局搜索...")
                    try:
                        icons_info = self.page.evaluate("""
                            () => {
                                const elements = [];
                                document.querySelectorAll('button, a, [role="button"]').forEach((el, index) => {
                                    const text = el.textContent?.trim() || '';
                                    const ariaLabel = el.getAttribute('aria-label') || '';
                                    const title = el.getAttribute('title') || '';
                                    const className = el.className || '';

                                    // 查找包含 download 相关关键词的元素
                                    const keywords = ['download', '下载'];
                                    const hasKeyword = keywords.some(keyword =>
                                        text.toLowerCase().includes(keyword.toLowerCase()) ||
                                        ariaLabel.toLowerCase().includes(keyword.toLowerCase()) ||
                                        title.toLowerCase().includes(keyword.toLowerCase()) ||
                                        className.toLowerCase().includes(keyword.toLowerCase())
                                    );

                                    if (hasKeyword) {
                                        el.setAttribute('data-download-index', index.toString());
                                        elements.push({
                                            index: index,
                                            text: text.substring(0, 50),
                                            ariaLabel: ariaLabel,
                                            title: title,
                                            className: className,
                                            tagName: el.tagName
                                        });
                                    }
                                });
                                return elements;
                            }
                        """)

                        logger.info(f"JavaScript 找到 {len(icons_info)} 个可能的下载元素:")
                        for icon in icons_info:
                            logger.info(f"  - [{icon['index']}] {icon['tagName']}: {icon['text']} (aria-label: {icon['ariaLabel']})")

                        # 尝试点击找到的元素
                        for icon in icons_info:
                            try:
                                logger.info(f"尝试点击元素 [{icon['index']}]...")
                                selector = f"[data-download-index='{icon['index']}']"
                                self.page.click(selector, timeout=5000)
                                logger.info(f"✅ 已点击元素: {icon['text']}")
                                icon_clicked = True
                                time.sleep(2)
                                break
                            except Exception as e:
                                logger.debug(f"点击元素失败: {icon['text']} - {str(e)}")
                                continue
                    except Exception as e:
                        logger.error(f"JavaScript 搜索失败: {e}")

                # Step 2.2: 检测并处理对话框
                if icon_clicked:
                    logger.info("步骤2.2: 检测导出对话框...")

                    # 保存截图查看对话框
                    screenshot_path = os.path.join(self.download_path, "debug_after_icon_click.png")
                    self.page.screenshot(path=screenshot_path)
                    logger.info(f"已保存点击后截图: {screenshot_path}")

                    # 查找对话框中的确认/导出/下载按钮
                    dialog_confirm_selectors = [
                        '[role="dialog"] button:has-text("Confirm")',
                        '[role="dialog"] button:has-text("确认")',
                        '[role="dialog"] button:has-text("Export")',
                        '[role="dialog"] button:has-text("导出")',
                        '[role="dialog"] button:has-text("Download")',
                        '[role="dialog"] button:has-text("下载")',
                        '[role="dialog"] button:has-text("OK")',
                        '[role="dialog"] button[type="submit"]',
                        # 可能不在 dialog role 中
                        '[class*="dialog"] button:has-text("Confirm")',
                        '[class*="modal"] button:has-text("Confirm")',
                        '[class*="dialog"] button:has-text("Export")',
                        '[class*="modal"] button:has-text("Export")',
                    ]

                    dialog_confirmed = False
                    for selector in dialog_confirm_selectors:
                        try:
                            locator = self.page.locator(selector)
                            if locator.count() > 0:
                                logger.info(f"✅ 找到对话框确认按钮: {selector}")
                                locator.first.click(timeout=5000)
                                logger.info("✅ 已点击确认按钮")
                                dialog_confirmed = True
                                export_triggered = True
                                time.sleep(2)
                                break
                        except Exception as e:
                            logger.debug(f"对话框按钮选择器失败: {selector} - {str(e)}")
                            continue

                    if not dialog_confirmed:
                        logger.warning("⚠️ 未检测到对话框确认按钮,可能直接触发了导出")
                        export_triggered = True  # 假设已触发

                # Step 2.3: 等待并检测浮动通知窗口
                if export_triggered:
                    logger.info("步骤2.3: 等待数据准备完成...")
                    logger.info("将监控右上角的浮动通知窗口...")

                    # 保存当前截图
                    screenshot_path = os.path.join(self.download_path, "debug_waiting_export.png")
                    self.page.screenshot(path=screenshot_path)

                    # 等待导出完成 - 最多等待 5 分钟
                    max_wait_time = 300  # 5分钟
                    check_interval = 10  # 每10秒检查一次
                    elapsed_time = 0
                    download_found = False

                    while elapsed_time < max_wait_time and not download_found:
                        logger.info(f"⏳ 等待中... ({elapsed_time}/{max_wait_time}秒)")
                        time.sleep(check_interval)
                        elapsed_time += check_interval

                        # 查找右上角的浮动通知窗口
                        floating_window_selectors = [
                            '[class*="notification"]',
                            '[class*="toast"]',
                            '[class*="snackbar"]',
                            '[class*="alert"]',
                            '[role="alert"]',
                            '[role="status"]',
                            # 可能包含特定文本
                            'div:has-text("ready")',
                            'div:has-text("complete")',
                            'div:has-text("已准备好")',
                            'div:has-text("完成")',
                        ]

                        for selector in floating_window_selectors:
                            try:
                                locator = self.page.locator(selector)
                                count = locator.count()
                                if count > 0:
                                    # 检查是否包含下载相关文本
                                    for i in range(count):
                                        try:
                                            text = locator.nth(i).text_content()
                                            if text and any(keyword in text.lower() for keyword in ['ready', 'complete', 'download', '下载', '准备好', '完成']):
                                                logger.info(f"✅ 检测到浮动通知: {selector}")
                                                logger.info(f"通知内容: {text}")

                                                # 保存截图
                                                screenshot_path = os.path.join(self.download_path, "debug_notification_found.png")
                                                self.page.screenshot(path=screenshot_path)

                                                # 在通知中查找下载链接或按钮
                                                download_selectors_in_notification = [
                                                    f"{selector} >> nth={i} >> a",
                                                    f"{selector} >> nth={i} >> button",
                                                    f"{selector} >> nth={i} >> a:has-text('Download')",
                                                    f"{selector} >> nth={i} >> button:has-text('Download')",
                                                ]

                                                for dl_selector in download_selectors_in_notification:
                                                    try:
                                                        dl_locator = self.page.locator(dl_selector)
                                                        if dl_locator.count() > 0:
                                                            logger.info(f"✅ 找到下载链接: {dl_selector}")

                                                            # 尝试下载
                                                            with self.page.expect_download(timeout=30000) as download_info:
                                                                dl_locator.first.click(timeout=5000)
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
                                                        logger.debug(f"通知中下载链接失败: {dl_selector} - {str(e)}")
                                                        continue
                                        except Exception as e:
                                            continue
                            except Exception as e:
                                logger.debug(f"浮动通知选择器失败: {selector} - {str(e)}")
                                continue

                        # 如果没找到浮动窗口,尝试点击铃铛图标查看通知中心
                        if not download_found and elapsed_time >= 30:  # 30秒后开始尝试铃铛图标
                            logger.info("尝试通过铃铛图标查看通知...")
                            bell_icon_selectors = [
                                'button[aria-label*="notification"]',
                                'button[aria-label*="Notification"]',
                                'button[aria-label*="alert"]',
                                'button[aria-label*="Alert"]',
                                '[data-testid*="notification"]',
                                'button:has(svg[data-icon="bell"])',
                                '[class*="notification-icon"]',
                                '[class*="bell-icon"]',
                            ]

                            for bell_selector in bell_icon_selectors:
                                try:
                                    bell_locator = self.page.locator(bell_selector)
                                    if bell_locator.count() > 0:
                                        logger.info(f"✅ 找到铃铛图标: {bell_selector}")
                                        bell_locator.first.click(timeout=5000)
                                        logger.info("✅ 已点击铃铛图标")
                                        time.sleep(2)

                                        # 保存截图查看通知中心
                                        screenshot_path = os.path.join(self.download_path, "debug_notification_center.png")
                                        self.page.screenshot(path=screenshot_path)

                                        # 在通知中心查找下载链接
                                        notification_download_selectors = [
                                            'a:has-text("Download")',
                                            'a:has-text("下载")',
                                            'a:has-text("CSV")',
                                            'a:has-text("ready")',
                                            'a:has-text("完成")',
                                            'button:has-text("Download")',
                                            'a[href*=".csv"]',
                                        ]

                                        for nd_selector in notification_download_selectors:
                                            try:
                                                nd_locator = self.page.locator(nd_selector)
                                                if nd_locator.count() > 0:
                                                    logger.info(f"✅ 在通知中心找到下载链接: {nd_selector}")

                                                    # 尝试下载
                                                    with self.page.expect_download(timeout=30000) as download_info:
                                                        nd_locator.first.click(timeout=5000)
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
                                                logger.debug(f"通知中心下载链接失败: {nd_selector} - {str(e)}")
                                                continue

                                        break  # 只点击一次铃铛图标
                                except Exception as e:
                                    logger.debug(f"铃铛图标选择器失败: {bell_selector} - {str(e)}")
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
                    screenshot_path = os.path.join(self.download_path, "error_no_download_icon.png")
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
