# Nollm 当前状态：V3.9 有界近似 Coverage 重估

**日期**：2026-07-15
**输入 HEAD**：`871f7820`

## 已验证并保留

```text
真实 OpenClaw Formation/Placement/Recall；
P1 写入和重启召回；
Physical/Surface 地址分离；
单入口 physical entry；
无 Cursor；
硬旋转/尺度参数；
source-centered polygon Oracle；
Surface Order 0..8 API；
原子失败回滚。
```

## 当前根本限制

```text
生产 Coverage 每 Cell 约 0.12 秒；
Surface eager 构建全部 Orders；
小数据也出现分钟级几何耗时；
精确面积和 signed-64 全闭包超出当前需求；
尚未进入 Stitch 和多物理层语义 Placement。
```

## 新决定

```text
精确 polygon/Decimal → Lab Oracle；
生产 Coverage → 固定点等面积 quadrature；
允许阈值以下 support 误差；
用 weighted error Gate；
产品坐标域限制为 hex radius <= 2^31-1；
Surface 改为惰性构建。
```
