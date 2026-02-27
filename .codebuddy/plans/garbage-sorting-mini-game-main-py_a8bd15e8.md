---
name: garbage-sorting-mini-game-main-py
overview: 使用 Pygame 在根目录单文件 main.py 实现带开始菜单/帮助/计分/拖拽投放的垃圾分类小游戏，分辨率 1440x900，满足 4 类 50 物体与 10 秒限时等要求。
design:
  architecture:
    framework: html
  styleKeywords:
    - 童真
    - 明亮配色
    - 卡通图标
    - 轻量动效
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 44px
      weight: 700
    subheading:
      size: 26px
      weight: 600
    body:
      size: 20px
      weight: 500
  colorSystem:
    primary:
      - "#4A90E2"
      - "#F5A623"
      - "#7ED321"
      - "#D0021B"
    background:
      - "#F7FAFF"
      - "#FFFFFF"
    text:
      - "#333333"
      - "#FFFFFF"
    functional:
      - "#2ECC71"
      - "#E74C3C"
      - "#F1C40F"
todos:
  - id: setup-main-structure
    content: 在 main.py 建立常量、工具函数与垃圾数据表结构
    status: completed
  - id: implement-game-core
    content: 实现拖拽投放、计分、倒计时与垃圾切换逻辑
    status: completed
    dependencies:
      - setup-main-structure
  - id: implement-ui-states
    content: 实现菜单、帮助、结果页面绘制与状态切换
    status: completed
    dependencies:
      - implement-game-core
  - id: polish-visuals
    content: 完善童真图标绘制与交互反馈、文本排版与提示信息
    status: completed
    dependencies:
      - implement-ui-states
---

## User Requirements

- 使用 Python 编写垃圾分类小游戏，所有代码集中在单个 `main.py` 文件
- 包含 4 种垃圾类别、共 50 种不同垃圾物体
- 上方显示当前垃圾的图标与名称，下方放置对应垃圾桶
- 10 秒内完成拖拽分类，正确加分、错误扣分
- 提供开始菜单与帮助说明
- 界面风格童真、适合儿童；代码结构简洁清晰，工具函数与常量置于文件开头
- 总体代码 200–400 行左右

## Product Overview

一款儿童向垃圾分类拖拽小游戏，玩家在倒计时内把垃圾拖到对应分类垃圾桶，通过得分反馈完成分类学习。

## Core Features

- 开始菜单与帮助说明页面
- 4 类垃圾桶与 50 种垃圾对象轮流出现
- 拖拽投放、10 秒倒计时、得分增减与总分展示
- 童真风格图标与简洁交互反馈

## Tech Stack Selection

- 语言：Python 3
- 图形与交互：Pygame（单文件实现）

## Implementation Approach

- 采用单文件结构：先定义常量/工具函数/数据，再按“菜单→帮助→游戏→结算”分函数组织。
- 以状态机管理页面切换，主循环只分发事件与渲染。
- 垃圾对象以数据表驱动（4 类共 50 名称），图标使用 Pygame 基础形状绘制，避免外部资源。
- 计时与拖拽检测基于帧时间，碰撞用矩形检测，逻辑清晰可读。
- 性能重点在绘制与事件处理：每帧 O(1) 更新（仅当前垃圾对象），避免不必要的遍历。

## Implementation Notes

- 参考现有项目中字体选择与绘制风格的实现方式（`duck_game`），在单文件内复刻简化版中文字体获取逻辑。
- 避免引入外部资产文件，确保单文件可直接运行。
- 得分规则明确、倒计时到期即进入结果页，保持逻辑闭环与稳定性。

## Architecture Design

- 单文件分区式结构：
- 常量/数据（窗口尺寸、颜色、垃圾数据）
- 工具函数（字体、绘制、文本居中）
- 轻量类（按钮、垃圾桶、当前垃圾）
- 状态处理函数（菜单/帮助/游戏/结果）
- 主循环与入口

## Directory Structure Summary

本实现新增单文件游戏逻辑，不修改现有 `duck_game` 模块。

/Users/wondery/Work/ghx/
├── main.py  # [NEW] 垃圾分类小游戏单文件实现。包含常量、工具函数、垃圾数据、状态机、拖拽逻辑、计分与倒计时、菜单与帮助页面绘制。

## 设计方向

- 童真可爱、色彩明亮的卡通风格，适合儿童。
- 页面层次清晰：上方展示当前垃圾图标与名称，中间留白用于拖拽，下方整齐排列 4 个彩色垃圾桶。
- 交互强调“拖拽投放”和“正确/错误反馈”，用轻微动画与色块提示强化学习感。

## 页面规划

- 开始菜单：标题、开始按钮、帮助入口
- 帮助说明：操作说明与分类提示
- 游戏主界面：垃圾展示区 + 4 类垃圾桶 + 倒计时/得分
- 结果页：总分与再来一次/返回菜单