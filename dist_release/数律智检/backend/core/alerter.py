import re

def trigger_alert(clue_content: str, personnel_count: int, amount: float, source: str, duplicate_enterprise_count: int) -> tuple[str, list]:
    """
    基于预设规则进行多维碰撞分析:
    返回: alert_level (红色/黄色/蓝色), alert_factors (触发预警的原因列表)
    """
    alert_level = "蓝色预警"  # 默认蓝表头
    factors = []

    # 1. 群体风险碰撞
    if personnel_count >= 10 or amount >= 100000:
        alert_level = "红色预警"
        factors.append({"factor": "群体或重大金额", "severity": "高", "desc": f"涉及人数 {personnel_count}人，金额 {amount} 元，极易引发群体性事件"})
    elif personnel_count >= 5 or amount >= 50000:
        alert_level = "黄色预警" if alert_level != "红色预警" else alert_level
        factors.append({"factor": "较多聚集", "severity": "中", "desc": f"涉及人数 {personnel_count}人，金额 {amount} 元"})
    
    # 2. 行为风险探测
    red_keywords = ["跑路", "失联", "跳楼", "拉横幅", "暴力", "群体"]
    for kw in red_keywords:
        if kw in clue_content:
            alert_level = "红色预警"
            factors.append({"factor": "过激行为预警", "severity": "高", "desc": f"捕获到高度风险词汇：{kw}"})

    # 3. 关联企业重复性
    if duplicate_enterprise_count >= 2: # 包括自己这次
        prev = alert_level
        if alert_level == "蓝色预警": alert_level = "黄色预警"
        factors.append({"factor": "企业重复涉诉", "severity": "高" if duplicate_enterprise_count>3 else "中", "desc": f"该企业已有 {duplicate_enterprise_count} 条欠薪相关投诉"})
        
    if not factors:
        factors.append({"factor": "常规工单", "severity": "低", "desc": "未触发特殊预警阈值，执行常规核查"})

    return alert_level, factors
