#!/usr/bin/env python3
"""
Meltwater 数据自动导入脚本
功能:
1. 读取 CSV 文件
2. 对比现有数据,剔除重复的 Document ID
3. 只导入新增记录
4. 发送消息卡片到飞书群和邮箱
"""

import requests
import json
import time
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

# 从环境变量读取配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("BITABLE_TABLE_ID")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
CSV_FILE = os.getenv("CSV_FILE_PATH")

# 批次大小
BATCH_SIZE = 15

# API 端点
AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


class FeishuBitableClient:
    """飞书多维表格客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expire_time = 0

    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expire_time:
            return self.access_token

        print(f"→ 正在获取 tenant_access_token...")
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(AUTH_URL, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception(f"获取 token 失败: {result}")

            self.access_token = result["tenant_access_token"]
            self.token_expire_time = current_time + (2 * 3600) - 300

            print(f"✓ 成功获取 access_token")
            return self.access_token

        except Exception as e:
            print(f"✗ 获取 access_token 失败: {e}")
            raise

    def get_existing_document_ids(
        self,
        app_token: str,
        table_id: str
    ) -> Set[str]:
        """获取现有表格中的所有 Document ID"""
        access_token = self.get_tenant_access_token()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        print(f"→ 正在获取现有表格中的 Document ID...")

        document_ids = set()
        page_token = None

        while True:
            params = {
                "page_size": 500
            }
            if page_token:
                params["page_token"] = page_token

            data = {
                "field_names": ["Document ID"]
            }

            try:
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    print(f"✗ 获取记录失败: {result}")
                    break

                records = result.get("data", {}).get("items", [])

                for record in records:
                    doc_id_field = record.get("fields", {}).get("Document ID")
                    if isinstance(doc_id_field, list) and doc_id_field:
                        doc_id_text = doc_id_field[0].get("text", "")
                        doc_id = doc_id_text.strip('"').strip()
                        if doc_id:
                            document_ids.add(doc_id)

                has_more = result.get("data", {}).get("has_more", False)
                if not has_more:
                    break

                page_token = result.get("data", {}).get("page_token")

            except Exception as e:
                print(f"✗ 获取现有 Document ID 失败: {e}")
                break

        print(f"✓ 找到 {len(document_ids)} 个现有 Document ID")
        return document_ids

    def batch_create_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]],
        user_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """批量创建记录"""
        access_token = self.get_tenant_access_token()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        params = {
            "user_id_type": user_id_type
        }

        data = {
            "records": records
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            return result

        except requests.exceptions.RequestException as e:
            print(f"✗ HTTP 请求失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"  响应内容: {e.response.text}")
            raise
        except Exception as e:
            print(f"✗ 批量创建记录失败: {e}")
            raise

    def send_message_card(
        self,
        chat_id: str,
        title: str,
        content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """发送消息卡片到群"""
        access_token = self.get_tenant_access_token()

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        params = {
            "receive_id_type": "chat_id"
        }

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": content
        }

        data = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card)
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            return result

        except Exception as e:
            print(f"✗ 发送消息卡片失败: {e}")
            raise

    def send_message_to_email(
        self,
        email: str,
        title: str,
        content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """发送消息卡片到邮箱"""
        access_token = self.get_tenant_access_token()

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        params = {
            "receive_id_type": "email"
        }

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": content
        }

        data = {
            "receive_id": email,
            "msg_type": "interactive",
            "content": json.dumps(card)
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            return result

        except Exception as e:
            print(f"✗ 发送消息卡片失败: {e}")
            raise


def parse_date(date_str: str) -> int:
    """
    将日期字符串转换为毫秒级时间戳
    支持格式: YYYY-MM-DD 或 DD/MM/YYYY
    """
    if not date_str or date_str.strip() == "":
        return None

    try:
        date_str = date_str.strip()
        if '-' in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            dt = datetime.strptime(date_str, "%d/%m/%Y")

        timestamp_ms = int(dt.timestamp() * 1000)
        return timestamp_ms
    except Exception as e:
        print(f"  ⚠ 日期解析失败: {date_str} - {e}")
        return None


def read_csv_data(
    csv_file: str,
    existing_doc_ids: Set[str]
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """读取 CSV 文件并过滤重复记录"""
    new_records = []
    duplicate_count = 0

    date_range = {
        "min": None,
        "max": None
    }

    print(f"→ 读取 CSV 文件: {csv_file}")

    encodings = ['utf-16', 'utf-16-le', 'utf-8', 'latin-1']
    encoding_used = None

    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter='\t')
                first_row = next(reader, None)
                if first_row:
                    encoding_used = encoding
                    print(f"✓ 使用编码: {encoding}")
                    break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if not encoding_used:
        raise Exception("无法识别 CSV 文件编码")

    with open(csv_file, 'r', encoding=encoding_used) as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            title = row.get('Title', '').strip()
            document_id = row.get('Document ID', '').strip().strip('"')
            reach = row.get('Reach', '').strip()
            ave = row.get('AVE', '').strip()
            author_name = row.get('Author Name', '').strip()
            source_name = row.get('Source Name', '').strip()
            date_str = row.get('Date', '').strip()
            url = row.get('URL', '').strip()

            if not title and not document_id:
                continue

            if document_id in existing_doc_ids:
                duplicate_count += 1
                continue

            date_timestamp = parse_date(date_str)

            if date_timestamp:
                date_obj = datetime.fromtimestamp(date_timestamp / 1000)
                date_str_formatted = date_obj.strftime('%Y-%m-%d')

                if date_range["min"] is None or date_str_formatted < date_range["min"]:
                    date_range["min"] = date_str_formatted
                if date_range["max"] is None or date_str_formatted > date_range["max"]:
                    date_range["max"] = date_str_formatted

            record = {
                "fields": {
                    "Title/Coverage": title,
                    "Document ID": document_id,
                    "Reach": reach,
                    "AVE": ave,
                    "Source Name": source_name
                }
            }

            if url:
                record["fields"]["URL/Link"] = {
                    "link": url,
                    "text": url
                }

            if author_name:
                record["fields"]["Author Name"] = author_name

            if date_timestamp:
                record["fields"]["Date"] = date_timestamp

            new_records.append(record)

    total_in_csv = len(new_records) + duplicate_count

    stats = {
        "total_in_csv": total_in_csv,
        "duplicate_count": duplicate_count,
        "new_count": len(new_records),
        "date_range": date_range
    }

    print(f"✓ CSV 总记录数: {total_in_csv}")
    print(f"✓ 重复记录数: {duplicate_count}")
    print(f"✓ 新增记录数: {len(new_records)}")

    return new_records, stats


def split_into_batches(
    records: List[Dict[str, Any]],
    batch_size: int
) -> List[List[Dict[str, Any]]]:
    """将记录分割成批次"""
    batches = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batches.append(batch)
    return batches


def import_data(
    client: FeishuBitableClient,
    records: List[Dict[str, Any]]
) -> tuple[int, int]:
    """导入数据到飞书多维表格"""

    if not records:
        print(f"→ 没有新增记录需要导入")
        return 0, 0

    print(f"\n{'='*60}")
    print(f"开始导入数据到飞书多维表格")
    print(f"目标表格: {APP_TOKEN}/{TABLE_ID}")
    print(f"总记录数: {len(records)}")
    print(f"批次大小: {BATCH_SIZE}")
    print(f"{'='*60}\n")

    batches = split_into_batches(records, BATCH_SIZE)
    print(f"→ 分割为 {len(batches)} 个批次\n")

    total_success = 0
    total_failed = 0

    for i, batch in enumerate(batches, 1):
        print(f"[{i}/{len(batches)}] 处理批次 {i}")
        print(f"  → 包含 {len(batch)} 条记录")

        try:
            print(f"  → 正在插入...")
            result = client.batch_create_records(APP_TOKEN, TABLE_ID, batch)

            if result.get("code") == 0:
                inserted_count = len(result.get("data", {}).get("records", []))
                print(f"  ✓ 成功插入 {inserted_count} 条记录")
                total_success += inserted_count
            else:
                print(f"  ✗ 插入失败: {result}")
                total_failed += len(batch)

            if i < len(batches):
                time.sleep(1)

        except Exception as e:
            print(f"  ✗ 处理批次失败: {e}")
            total_failed += len(batch)
            continue

    print(f"\n{'='*60}")
    print(f"导入完成!")
    print(f"成功: {total_success} 条")
    print(f"失败: {total_failed} 条")
    print(f"总计: {total_success + total_failed} 条")
    success_rate = (total_success / (total_success + total_failed) * 100) if (total_success + total_failed) > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    print(f"{'='*60}\n")

    return total_success, total_failed


def main():
    """主函数"""
    start_time = datetime.now()

    # 检查环境变量
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, APP_TOKEN, TABLE_ID, CSV_FILE]):
        print("✗ 缺少必要的环境变量配置!")
        print("请设置以下环境变量:")
        print("  - FEISHU_APP_ID")
        print("  - FEISHU_APP_SECRET")
        print("  - BITABLE_APP_TOKEN")
        print("  - BITABLE_TABLE_ID")
        print("  - CSV_FILE_PATH")
        return

    if not Path(CSV_FILE).exists():
        print(f"✗ CSV 文件不存在: {CSV_FILE}")
        return

    client = FeishuBitableClient(FEISHU_APP_ID, FEISHU_APP_SECRET)

    existing_doc_ids = client.get_existing_document_ids(APP_TOKEN, TABLE_ID)

    new_records, stats = read_csv_data(CSV_FILE, existing_doc_ids)

    success_count, failed_count = import_data(client, new_records)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    try:
        date_range_str = f"{stats['date_range']['min']} 至 {stats['date_range']['max']}" if stats['date_range']['min'] else "无"

        card_elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**导入时间:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**数据时间范围:** {date_range_str}"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**CSV 总记录数:** {stats['total_in_csv']}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**重复记录数:** {stats['duplicate_count']}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**新增记录数:** {stats['new_count']}"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**成功导入:** {success_count} 条"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**导入失败:** {failed_count} 条"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**耗时:** {duration:.1f} 秒"
                }
            }
        ]

        if success_count > 0:
            card_title = "✅ Meltwater 数据导入成功"
        elif stats['new_count'] == 0:
            card_title = "ℹ️ Meltwater 数据无新增"
        else:
            card_title = "❌ Meltwater 数据导入失败"

        # 发送到群
        if TARGET_CHAT_ID:
            client.send_message_card(TARGET_CHAT_ID, card_title, card_elements)
            print(f"✓ 消息卡片已发送到群: {TARGET_CHAT_ID}")

        # 发送给个人邮箱
        if NOTIFICATION_EMAIL:
            try:
                client.send_message_to_email(NOTIFICATION_EMAIL, card_title, card_elements)
                print(f"✓ 消息卡片已发送到邮箱: {NOTIFICATION_EMAIL}")
            except Exception as e:
                print(f"⚠ 发送到邮箱失败: {e}")

    except Exception as e:
        print(f"✗ 发送消息卡片失败: {e}")

    # 增加运行计数(用于管理每日/每周切换)
    try:
        import subprocess
        script_dir = Path(__file__).parent
        manage_script = script_dir / "manage_meltwater_schedule.py"
        if manage_script.exists():
            subprocess.run([
                "python3",
                str(manage_script),
                "increment"
            ], capture_output=True)
    except Exception as e:
        print(f"⚠ 更新运行计数失败: {e}")


if __name__ == "__main__":
    main()
