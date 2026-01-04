#!/usr/bin/env python3
"""
调试脚本: 检查 Alerts 面板的 DOM 结构
目标: 找到 Download 按钮的实际 HTML 结构和正确的 selector
"""

import os
import time
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inspect_alerts_dom():
    """检查 Alerts 面板的 DOM 结构"""

    email = os.getenv('MELTWATER_EMAIL')
    password = os.getenv('MELTWATER_PASSWORD')
    url = os.getenv('MELTWATER_URL')

    if not all([email, password, url]):
        logger.error("请设置环境变量: MELTWATER_EMAIL, MELTWATER_PASSWORD, MELTWATER_URL")
        return

    with sync_playwright() as p:
        logger.info("启动浏览器...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # 登录流程
            logger.info(f"访问 {url}")
            page.goto(url, wait_until='networkidle')
            time.sleep(2)

            logger.info("输入邮箱...")
            page.fill('input[type="email"]', email)
            page.click('button:has-text("Next")')
            time.sleep(3)

            logger.info("输入密码...")
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            time.sleep(3)

            # 跳过 passkey
            try:
                skip_button = page.locator('button:has-text("Continue without passkeys")')
                if skip_button.count() > 0:
                    skip_button.click()
                    time.sleep(2)
            except:
                pass

            logger.info("✅ 登录成功,等待页面加载...")
            page.wait_for_load_state('networkidle')
            time.sleep(10)

            logger.info("=" * 80)
            logger.info("开始检查 Alerts 面板的 DOM 结构")
            logger.info("=" * 80)

            # 1. 检查 Alerts 面板是否存在
            alerts_panel_js = """
                const alertsPanel = document.querySelector('[aria-label="Alerts"]');
                if (alertsPanel) {
                    return {
                        exists: true,
                        tagName: alertsPanel.tagName,
                        className: alertsPanel.className,
                        id: alertsPanel.id,
                        outerHTML: alertsPanel.outerHTML.substring(0, 500)
                    };
                }
                return { exists: false };
            """
            alerts_info = page.evaluate(alerts_panel_js)
            logger.info(f"\n1️⃣ Alerts 面板信息:")
            logger.info(f"   存在: {alerts_info.get('exists')}")
            if alerts_info.get('exists'):
                logger.info(f"   标签: {alerts_info.get('tagName')}")
                logger.info(f"   类名: {alerts_info.get('className')}")
                logger.info(f"   ID: {alerts_info.get('id')}")

            # 2. 查找所有包含 "ANZ_Coverage_2025" 的元素
            anz_elements_js = """
                const elements = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                while(walker.nextNode()) {
                    if (walker.currentNode.textContent.includes('ANZ_Coverage_2025')) {
                        const parent = walker.currentNode.parentElement;
                        elements.push({
                            text: walker.currentNode.textContent.trim(),
                            parentTag: parent.tagName,
                            parentClass: parent.className,
                            parentId: parent.id,
                            outerHTML: parent.outerHTML.substring(0, 300)
                        });
                    }
                }
                return elements;
            """
            anz_elements = page.evaluate(anz_elements_js)
            logger.info(f"\n2️⃣ 找到 {len(anz_elements)} 个包含 'ANZ_Coverage_2025' 的元素:")
            for i, elem in enumerate(anz_elements):
                logger.info(f"\n   元素 {i+1}:")
                logger.info(f"   文本: {elem['text'][:100]}")
                logger.info(f"   父标签: {elem['parentTag']}")
                logger.info(f"   父类名: {elem['parentClass']}")

            # 3. 查找所有包含 "Download" 文本的按钮
            download_buttons_js = """
                const buttons = [];
                const allButtons = document.querySelectorAll('button, a[role="button"], [role="button"]');

                allButtons.forEach((btn, index) => {
                    const text = btn.textContent.trim();
                    if (text.toLowerCase().includes('download') || btn.getAttribute('aria-label')?.toLowerCase().includes('download')) {
                        buttons.push({
                            index: index,
                            tagName: btn.tagName,
                            type: btn.type,
                            text: text,
                            ariaLabel: btn.getAttribute('aria-label'),
                            className: btn.className,
                            id: btn.id,
                            disabled: btn.disabled,
                            outerHTML: btn.outerHTML.substring(0, 400)
                        });
                    }
                });
                return buttons;
            """
            download_buttons = page.evaluate(download_buttons_js)
            logger.info(f"\n3️⃣ 找到 {len(download_buttons)} 个包含 'Download' 的按钮:")
            for i, btn in enumerate(download_buttons):
                logger.info(f"\n   按钮 {i+1}:")
                logger.info(f"   标签: {btn['tagName']}")
                logger.info(f"   类型: {btn.get('type')}")
                logger.info(f"   文本: {btn['text']}")
                logger.info(f"   aria-label: {btn.get('ariaLabel')}")
                logger.info(f"   类名: {btn['className'][:100] if btn['className'] else 'None'}")
                logger.info(f"   禁用: {btn.get('disabled')}")

            # 4. 查找 Alerts 面板内的所有按钮
            alerts_buttons_js = """
                const alertsPanel = document.querySelector('[aria-label="Alerts"]');
                if (!alertsPanel) return [];

                const buttons = [];
                const allButtons = alertsPanel.querySelectorAll('button, a[role="button"], [role="button"]');

                allButtons.forEach((btn, index) => {
                    buttons.push({
                        index: index,
                        tagName: btn.tagName,
                        type: btn.type,
                        text: btn.textContent.trim(),
                        ariaLabel: btn.getAttribute('aria-label'),
                        className: btn.className,
                        id: btn.id,
                        disabled: btn.disabled,
                        outerHTML: btn.outerHTML.substring(0, 400)
                    });
                });
                return buttons;
            """
            alerts_buttons = page.evaluate(alerts_buttons_js)
            logger.info(f"\n4️⃣ Alerts 面板内找到 {len(alerts_buttons)} 个按钮:")
            for i, btn in enumerate(alerts_buttons):
                logger.info(f"\n   按钮 {i+1}:")
                logger.info(f"   标签: {btn['tagName']}")
                logger.info(f"   文本: {btn['text']}")
                logger.info(f"   aria-label: {btn.get('ariaLabel')}")
                logger.info(f"   类名: {btn['className'][:100] if btn['className'] else 'None'}")

            # 5. 查找 "Your CSV file is ready" 附近的元素结构
            csv_ready_structure_js = """
                const results = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                while(walker.nextNode()) {
                    if (walker.currentNode.textContent.includes('Your CSV file is ready')) {
                        let elem = walker.currentNode.parentElement;
                        // 向上找 5 层父元素
                        for (let i = 0; i < 5 && elem; i++) {
                            const buttons = elem.querySelectorAll('button, a[role="button"], [role="button"]');
                            if (buttons.length > 0) {
                                results.push({
                                    level: i,
                                    parentTag: elem.tagName,
                                    parentClass: elem.className,
                                    buttonCount: buttons.length,
                                    buttons: Array.from(buttons).map(b => ({
                                        tag: b.tagName,
                                        text: b.textContent.trim(),
                                        ariaLabel: b.getAttribute('aria-label'),
                                        className: b.className
                                    }))
                                });
                            }
                            elem = elem.parentElement;
                        }
                        break;
                    }
                }
                return results;
            """
            csv_structure = page.evaluate(csv_ready_structure_js)
            logger.info(f"\n5️⃣ 'Your CSV file is ready' 附近的元素结构:")
            for i, struct in enumerate(csv_structure):
                logger.info(f"\n   层级 {struct['level']}:")
                logger.info(f"   父标签: {struct['parentTag']}")
                logger.info(f"   按钮数: {struct['buttonCount']}")
                for j, btn in enumerate(struct['buttons']):
                    logger.info(f"      按钮 {j+1}: {btn['tag']} - '{btn['text'][:50]}' - aria: {btn.get('ariaLabel')}")

            # 6. 保存完整的 Alerts 面板 HTML
            alerts_html_js = """
                const alertsPanel = document.querySelector('[aria-label="Alerts"]');
                return alertsPanel ? alertsPanel.innerHTML : '';
            """
            alerts_html = page.evaluate(alerts_html_js)

            html_file = "./downloads/alerts_panel_html.txt"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(alerts_html)
            logger.info(f"\n6️⃣ Alerts 面板完整 HTML 已保存到: {html_file}")
            logger.info(f"   HTML 长度: {len(alerts_html)} 字符")

            # 7. 保存截图
            screenshot_path = "./downloads/debug_dom_inspection.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"\n7️⃣ 已保存截图: {screenshot_path}")

            logger.info("\n" + "=" * 80)
            logger.info("DOM 检查完成!")
            logger.info("=" * 80)

            # 保持浏览器打开 30 秒以便手动检查
            logger.info("\n浏览器将保持打开 30 秒,您可以手动检查...")
            time.sleep(30)

        except Exception as e:
            logger.error(f"检查过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
            logger.info("浏览器已关闭")

if __name__ == "__main__":
    inspect_alerts_dom()
