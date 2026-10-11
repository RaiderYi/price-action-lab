# 失败归因：double_top/bottom 证伪记录

> 来源：原 `data/reviews/` 自迭代 #1 记录 + Focus v1 随机5股回测对照

## 证伪过程

自迭代 #1（早期回测）：double_bottom/double_top 信号在下降趋势中做双底反转，**13/13 全部亏损，累计 -10.4R**。

Brooks 原理印证：*"在下降趋势中做双底，本质是在逆势抄底。所有小型双顶/双底本质上是 L2/H2——它们是顺势入场点，不是反转信号。"*

## 处置

- 检测代码保留（`_is_double_bottom_top`），信号生成禁用
- 注册表条目保留但 enabled=False，notes 标注"本质是L2/H2的形态化表达，recommended_action=LINK_TO_H2_L2_STRICT"
- Focus v1 维持 disabled

## 教训

**形态名字 ≠ 交易逻辑**。同一个"双底"图形：
- 下降趋势中出现 → 逆势抄底（证伪：13/13 亏）
- 上升趋势回调中出现 → 本质是 H2（顺势二买，39%胜率+正期望）

context（趋势方向）决定形态的含义，这正是三层架构中 qualification 层做方向仲裁的原因。
