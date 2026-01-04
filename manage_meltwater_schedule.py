#!/usr/bin/env python3
"""
Meltwater 定时任务调度管理
用于追踪运行次数并自动调整运行频率
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 状态文件路径
STATE_FILE = Path(__file__).parent / "meltwater_schedule_state.json"


def load_state():
    """加载状态文件"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"run_count": 0, "last_run": None}


def save_state(state):
    """保存状态文件"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def increment_run():
    """增加运行次数"""
    state = load_state()
    state["run_count"] += 1
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    print(f"✓ 运行次数已更新: {state['run_count']}")

    if state["run_count"] >= 5:
        print("→ 已达到 5 次运行,建议切换到每周模式")

    return state


def get_schedule_mode():
    """获取当前应该使用的调度模式"""
    state = load_state()
    run_count = state.get("run_count", 0)

    if run_count < 5:
        return "daily"
    else:
        return "weekly"


def show_status():
    """显示当前状态"""
    state = load_state()
    mode = get_schedule_mode()

    print("=" * 60)
    print("Meltwater 定时任务调度状态")
    print("=" * 60)
    print(f"运行次数: {state['run_count']}")
    print(f"最后运行: {state.get('last_run', '未运行')}")
    print(f"当前模式: {mode}")
    print("=" * 60)

    if mode == "daily":
        remaining = 5 - state['run_count']
        print(f"→ 还有 {remaining} 次运行后将切换到每周模式")
    else:
        print("→ 当前为每周运行模式")


def reset_state():
    """重置状态"""
    state = {"run_count": 0, "last_run": None}
    save_state(state)
    print("✓ 状态已重置")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 manage_meltwater_schedule.py status   # 查看状态")
        print("  python3 manage_meltwater_schedule.py reset    # 重置状态")
        print("  python3 manage_meltwater_schedule.py increment # 增加运行次数")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        show_status()
    elif command == "reset":
        reset_state()
    elif command == "increment":
        increment_run()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
