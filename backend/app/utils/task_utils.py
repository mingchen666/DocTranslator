# utils/task_utils.py
import datetime

def generate_task_no():
    """生成任务编号[^3]"""
    now = datetime.datetime.now()
    return f"T{now.strftime('%Y%m%d%H%M%S')}"
