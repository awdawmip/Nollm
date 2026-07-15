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

## 已完成

```text
K=96 固定点等面积 quadrature 通过误差 Gate；
生产 Coverage 无 Decimal/polygon 动态路径；
Surface 按需逐阶构建并可删除缓存；
11-cell 27.829ms，217-cell 823.615ms；
真实 R1/R2/R3/P1 和重启召回通过；
旧数据经非破坏 v5 -> v6 registry 迁移保留。
```

## 当前状态

```text
FAST_BOUNDED_APPROXIMATE_COVERAGE_SURFACE_VALIDATED_AT_<FINAL_DELIVERY_HEAD>
```

最终 HEAD 由不可变完成 Tag 和 Bundle heads 提供。活动域仍为 hex radius
`<= 2^31-1`、default chart、null phase；Stitch、多层语义 Placement、PB 和
持久 Surface cache 未开启。
