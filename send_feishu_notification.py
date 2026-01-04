#!/usr/bin/env python3
"""
发送飞书卡片消息通知工作流执行结果
"""
import os
import sys
import json
import requests
from datetime import datetime

def get_tenant_access_token():
    """获取 tenant_access_token"""
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    response = requests.post(url, json=data)
    result = response.json()

    if result.get("code") == 0:
        return result["tenant_access_token"]
    else:
        print(f"❌ 获取 token 失败: {result}")
        return None

def create_notification_card(workflow_status, download_info, import_info, bitable_url):
    """创建飞书卡片消息内容"""

    # 根据状态设置颜色和图标
    if workflow_status == "success":
        status_color = "green"
        status_text = "✅ 工作流执行成功"
        status_tag = "成功"
        tag_color = "green"
    else:
        status_color = "red"
        status_text = "❌ 工作流执行失败"
        status_tag = "失败"
        tag_color = "red"

    # 构建卡片内容
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "template": status_color,
            "title": {
                "tag": "plain_text",
                "content": "Meltwater 数据同步通知"
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{status_text}**"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**执行时间:**\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**工作流状态:**\n{status_tag}"
                        }
                    }
                ]
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**📥 下载统计**"
                }
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**下载记录数:**\n{download_info.get('records', 'N/A')}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**下载耗时:**\n{download_info.get('duration', 'N/A')}秒"
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**文件路径:**\n{download_info.get('file_path', 'N/A')}"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**📊 导入统计**"
                }
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**成功导入:**\n{import_info.get('success', 0)} 条"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**导入失败:**\n{import_info.get('failed', 0)} 条"
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**总记录数:**\n{import_info.get('total', 0)} 条"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**成功率:**\n{import_info.get('success_rate', '0')}%"
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**导入耗时:**\n{import_info.get('duration', 'N/A')}秒"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**重复记录:**\n{import_info.get('duplicates', 0)} 条"
                        }
                    }
                ]
            },
            {
                "tag": "hr"
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "查看数据表"
                        },
                        "type": "default",
                        "url": bitable_url
                    }
                ]
            }
        ]
    }

    return card

def send_card_message(card_content, receive_id_type="chat_id", receive_id=None):
    """发送卡片消息"""
    token = get_tenant_access_token()
    if not token:
        return False

    # 如果没有指定接收者,尝试从环境变量获取
    if not receive_id:
        receive_id = os.getenv('FEISHU_CHAT_ID')
        if not receive_id:
            print("❌ 未指定消息接收者 (FEISHU_CHAT_ID)")
            return False

    url = "https://open.feishu.cn/open-apis/im/v1/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    params = {
        "receive_id_type": receive_id_type
    }

    data = {
        "receive_id": receive_id,
        "msg_type": "interactive",
        "content": json.dumps(card_content)
    }

    print(f"\n📤 发送卡片消息到: {receive_id} (类型: {receive_id_type})")

    response = requests.post(url, headers=headers, params=params, json=data)
    result = response.json()

    if result.get("code") == 0:
        print(f"✅ 卡片消息发送成功!")
        print(f"📬 消息 ID: {result.get('data', {}).get('message_id')}")
        return True
    else:
        print(f"❌ 卡片消息发送失败: {result.get('msg')}")
        print(f"📄 详细响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return False

def send_to_multiple_recipients(card_content, recipients):
    """发送消息到多个接收者

    Args:
        card_content: 卡片内容
        recipients: 接收者列表,格式为 [(receive_id_type, receive_id), ...]
                   例如: [("email", "zoey.yuan@anker.com"), ("chat_id", "oc_xxx")]

    Returns:
        成功发送的数量
    """
    success_count = 0
    total_count = len(recipients)

    for receive_id_type, receive_id in recipients:
        if send_card_message(card_content, receive_id_type, receive_id):
            success_count += 1

    print(f"\n📊 发送统计: {success_count}/{total_count} 成功")
    return success_count

def main():
    """主函数"""
    print("=" * 60)
    print("发送飞书卡片消息通知")
    print("=" * 60)

    # 从环境变量或命令行参数获取工作流信息
    workflow_status = os.getenv('WORKFLOW_STATUS', 'success')

    # 下载信息
    download_info = {
        'records': os.getenv('DOWNLOAD_RECORDS', 'N/A'),
        'duration': os.getenv('DOWNLOAD_DURATION', 'N/A'),
        'file_path': os.getenv('DOWNLOAD_FILE', 'N/A')
    }

    # 导入信息
    import_info = {
        'success': int(os.getenv('IMPORT_SUCCESS', 0)),
        'failed': int(os.getenv('IMPORT_FAILED', 0)),
        'total': int(os.getenv('IMPORT_TOTAL', 0)),
        'success_rate': os.getenv('IMPORT_SUCCESS_RATE', '0'),
        'duration': os.getenv('IMPORT_DURATION', 'N/A'),
        'duplicates': int(os.getenv('IMPORT_DUPLICATES', 0))
    }

    # Bitable URL
    app_token = os.getenv('BITABLE_APP_TOKEN')
    table_id = os.getenv('BITABLE_TABLE_ID')
    bitable_url = f"https://anker-in.feishu.cn/base/{app_token}?table={table_id}"

    # 创建卡片
    card = create_notification_card(workflow_status, download_info, import_info, bitable_url)

    # 从环境变量读取接收者列表
    recipients_str = os.getenv('FEISHU_RECIPIENTS', '')

    if recipients_str:
        # 解析接收者列表: "email:zoey.yuan@anker.com,chat_id:oc_xxx"
        recipients = []
        for item in recipients_str.split(','):
            item = item.strip()
            if ':' in item:
                receive_id_type, receive_id = item.split(':', 1)
                recipients.append((receive_id_type.strip(), receive_id.strip()))

        if recipients:
            print(f"📋 接收者列表: {len(recipients)} 个")
            success_count = send_to_multiple_recipients(card, recipients)

            print("=" * 60)

            # 只要有一个发送成功就算成功
            if success_count > 0:
                print("SUCCESS")
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("❌ FEISHU_RECIPIENTS 格式错误")
            sys.exit(1)
    else:
        # 兼容旧的单接收者模式
        success = send_card_message(card)

        print("=" * 60)

        if success:
            print("SUCCESS")
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
