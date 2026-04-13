# 读书 Skill

基于《如何阅读一本书》的分析阅读法，帮助你深度分析书籍，输出结构化读书笔记，并生成专属 AI Skill。

---

## 功能特点

- **6 步分析阅读法**：分类 → 骨架 → 关键词 → 评价 → 笔记 → 生成 Skill
- **支持多种格式**：`.txt` 和 `.pdf`
- **专属 Skill 生成**：每本书生成一个可调用的 AI 助手

---

## 快速开始

### 1. 触发 Skill

```
/read-book
```
或说「帮我读一本书」

### 2. 提供书籍文件

上传 `.txt` 或 `.pdf` 格式的书籍文件

### 3. 分析阅读

按 6 步流程进行深度分析：
1. 书籍分类
2. 搭建骨架
3. 提取关键词
4. 评价作者
5. 生成读书笔记
6. 生成专属 AI Skill

---

## 使用示例

### 示例：分析《刻意练习》

#### Step 1: 上传书籍

用户上传 `刻意练习.txt` 或 `刻意练习.pdf`

#### Step 2: 读取内容

- `.txt` 文件：直接用 Read 工具读取
- `.pdf` 文件：用 pdf_extractor.py 转换

```bash
uv run python scripts/pdf_extractor.py --file "刻意练习.pdf" --output "./temp/刻意练习.txt"
```

#### Step 3-5: 分析过程

按分析阅读 6 步法进行，最终输出：
- 读书笔记：`books/book-deliberate-practice/note.md`
- 专属 Skill：`books/book-deliberate-practice/SKILL.md`

#### Step 6: 生成专属 Skill

生成的专属 Skill 包含：
- 核心观点
- 关键概念
- 适用场景
- 边界/局限
- 方法/框架

---

## 生成的专属 Skill 使用示例

假设你已经分析了《刻意练习》这本书，生成了专属 Skill，触发词是 `/book-deliberate-practice`。

### 示例 1：询问核心观点

```
用户：这本书的核心观点是什么？
book-deliberate-practice：
这本书的核心观点是：
1. 刻意练习是有目的的练习，不是简单的重复
2. 刻意练习需要走出舒适区
3. 刻意练习需要及时反馈
4. 刻意练习需要专注和投入
5. 长期坚持刻意练习可以成为专家
```

### 示例 2：应用方法解决实际问题

```
用户：我想学习写作，如何运用刻意练习？
book-deliberate-practice：
运用刻意练习学习写作的建议：

1. 明确目标
   - 设定具体的写作技能目标，如"写出吸引人的开头"

2. 走出舒适区
   - 尝试不同文体、主题，挑战自己的写作边界

3. 获得及时反馈
   - 找老师批改、加入写作小组、请教资深写作者

4. 专注投入
   - 每天固定写作时间，排除干扰

5. 持续迭代
   - 根据反馈不断修改完善

建议从短文开始，逐步增加难度和长度。
```

### 示例 3：理解关键概念

```
用户：什么是"心理表征"？
book-deliberate-practice：
心理表征是《刻意练习》中的核心概念：

定义：
指在头脑中形成的对某个主题或技能的专门知识结构

作用：
- 帮助专家快速识别模式和问题
- 使专家能够在复杂情境中快速做出决策
- 让专家能够预见未来的发展

例子：
- 棋手通过大量对局形成的棋局记忆
- 医生通过案例积累形成的诊断直觉
- 音乐家对曲目形成的整体感知

如何培养：
通过长期刻意练习，在大脑中建立专门的心理表征。
```

### 示例 4：获取推荐书单

```
用户：还有哪些书可以进一步阅读？
book-deliberate-practice：
相关书籍推荐：

1. 《异类》- 马尔科姆·格拉德威尔
   - 介绍一万小时定律

2. 《学习之道》- 芭芭拉·奥克利
   - 关于如何学习和掌握技能

3. 《认知天性》- 彼得·布朗
   - 介绍间隔练习等学习方法

4. 《终身成长》- 卡罗尔·德韦克
   - 关于成长型思维模式
```

---

## 文件结构

```
read-book-skill/
├── SKILL.md                    # 主技能定义
├── README.md                   # 本文件
├── tools/
│   ├── pdf_extractor.py        # PDF 转文本工具
│   └── skill_generator.py      # 专属 Skill 生成工具
├── prompts/
│   ├── step1_classify.md       # 书籍分类
│   ├── step2_skeleton.md       # 骨架搭建
│   ├── step3_keywords.md       # 关键词提取
│   ├── step4_evaluate.md       # 评价作者
│   ├── step5_note.md           # 读书笔记模板
│   └── step6_builder.md        # 专属 Skill 生成模板
└── references/
    ├── analysis_rules.md       # 分析阅读规则
    └── 阅读层次指南.md         # 四层次阅读说明
```

---

## 管理命令

### 查看已分析的书籍

```bash
ls -la ./books/
```

### 查看某本书的读书笔记

```bash
cat ./books/book-{slug}/note.md
```

### 调用生成的专属 Skill

```bash
/book-{slug}
```

### 列出所有专属 Skill

```bash
uv run python scripts/skill_generator.py --action list
```

---

## 依赖安装

```bash
uv add pypdf
```

---

## 核心方法论

本 Skill 基于《如何阅读一本书》的分析阅读法，包含三个阶段：

**阶段一：这本书在谈些什么？**
- 分类
- 一句话概括
- 结构拆解
- 找出问题

**阶段二：如何叙述的？**
- 关键词共识
- 找出主旨
- 找出论述
- 找出答案

**阶段三：评价与批评**
- 评价前先理解
- 理性表达不同意
- 评价标准

详细规则见 `references/analysis_rules.md`
