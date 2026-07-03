# 读书 Skill

基于《如何阅读一本书》的分析阅读法，帮助你深度分析书籍，输出结构化读书笔记，并生成专属 AI Skill。

---

## 功能特点

- **7 步分析阅读法 (RIA++)**：分类 → 骨架 → 关键词 → 三重验证 → 评价 → 笔记 → 生成 Skill
- **支持多种格式**：`.pdf` / `.epub` / `.docx` / `.txt` / `.md`
- **多层回退链**：每种格式自动降级（如 PDF: docling → pdftotext → pypdf → pdfminer）
- **成本估算**：处理前预估 token 和费用（默认 GLM-5.2 计价）
- **章节检测**：自动识别中文/英文/日文章节和目录
- **专属 Skill 生成**：每本书生成 SKILL.md + glossary.md + patterns.md + cheatsheet.md + metadata.json
- **RIA++ 方法论**：六段结构（R/I/A1/A2/E/B）+ 三重验证

---

## 快速开始

### 1. 触发 Skill

```
/read-book
```

或说「帮我读一本书」、「分析这本书」、「生成读书笔记」

### 2. 提供书籍文件

支持 `.pdf` / `.epub` / `.docx` / `.txt` / `.md` 格式

### 3. 分析阅读

按 7 步流程进行深度分析：
1. **Step 0**：提取书籍文本（自动识别格式）
2. **Step 0.5**：成本估算（大文件必做）
3. **Step 0.6**：章节检测
4. **Step 1-4**：分析阅读（分类 → 骨架 → 关键词 → 评价）
5. **Step 3.5**：三重验证
6. **Step 5**：生成 RIA++ 六段笔记
7. **Step 6**：生成专属 AI Skill

---

## 使用示例

### 示例：分析《刻意练习》

#### Step 1: 上传书籍

用户上传 `刻意练习.pdf` / `刻意练习.epub` / `刻意练习.docx` 等

#### Step 2: 读取内容（统一入口）

```bash
uv run python scripts/extract.py --file "刻意练习.pdf" --output "./temp/刻意练习.txt"
```

PDF 额外参数：`--technical`（技术类书籍优先 docling）、`--start N --end N`（指定页码范围）

#### Step 2.5: 成本估算（大文件必做）

```bash
uv run python scripts/cost_estimator.py --file "./temp/刻意练习.txt"
```

#### Step 2.6: 章节检测

```bash
uv run python scripts/chapter_detector.py --file "./temp/刻意练习.txt"
```

#### Step 3-5: 分析过程

按分析阅读 7 步法进行，最终输出到 `~/.config/opencode/skill/books/book-deliberate-practice/`：
- 读书笔记：`note.md`
- 专属 Skill：`SKILL.md` + `glossary.md` + `patterns.md` + `cheatsheet.md` + `metadata.json`

#### Step 6: 生成专属 Skill

```bash
uv run python scripts/skill_generator.py \
  --book-title "刻意练习" \
  --note-path "~/.config/opencode/skill/books/book-deliberate-practice/note.md"
```

生成的专属 Skill 包含 RIA++ 六段结构化方法论（R 原文引用 / I 方法论骨架 / A1 案例 / A2 触发场景 / E 可执行步骤 / B 边界），每项方法论经过三重验证（V1 跨域 / V2 预测力 / V3 独特性），未通过的单元被移至 `rejected/` 目录。

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
├── SKILL.md                    # 主技能定义（7 步 RIA++ 流程）
├── README.md                   # 本文件
├── pyproject.toml              # Python 项目配置
├── .python-version             # Python 版本锁定
├── .github/workflows/
│   └── ci.yml                  # CI: test + lint + skill 验证
├── scripts/
│   ├── extract.py              # 统一提取入口（自动识别格式）
│   ├── pdf_extractor.py        # PDF 提取（docling → pdftotext → pypdf → pdfminer）
│   ├── epub_extractor.py       # EPUB 提取（ebooklib → zipfile 回退）
│   ├── docx_extractor.py       # DOCX 提取（python-docx → zipfile 回退）
│   ├── text_extractor.py       # TXT/MD 读取（BOM 感知解码）
│   ├── chapter_detector.py     # 多语言章节/目录检测
│   ├── cost_estimator.py       # Token 成本预估（GLM-5.2）
│   ├── skill_generator.py      # RIA++ 专属 Skill 生成器（含三重验证）
│   └── metadata.py             # 元数据聚合
├── prompts/
│   ├── step1_classify.md       # 书籍分类
│   ├── step2_skeleton.md       # 骨架搭建
│   ├── step3_keywords.md       # 关键词提取
│   ├── step4_evaluate.md       # 评价作者
│   ├── step5_note.md           # 读书笔记模板
│   └── step6_builder.md        # 专属 Skill 生成模板
├── references/
│   ├── analysis_rules.md       # 分析阅读规则
│   └── read_level.md           # 四层次阅读说明
├── tests/
│   ├── test_chapter_detector.py
│   ├── test_cost_estimator.py
│   └── test_skill_generator.py
└── temp/                       # 提取缓存（可清理）
    └── *.txt                   # 书籍提取后的纯文本
```

---

## 管理命令

### 查看已分析的书籍

```bash
uv run python scripts/skill_generator.py --action list
```

### 查看某本书的读书笔记

```bash
cat ~/.config/opencode/skill/books/{slug}/note.md
```

### 查看被过滤的方法论

```bash
ls ~/.config/opencode/skill/books/{slug}/rejected/
```

### 调用生成的专属 Skill

```
/book-{slug}
```

---

## 依赖安装

```bash
# 基础依赖（仅 PDF + pypdf）
uv sync

# 全部安装（PDF 回退链 + EPUB + DOCX）
uv sync --all-extras
```

等价于逐个添加：
```bash
uv add pdfminer.six   # PDF 回退增强
uv add ebooklib beautifulsoup4  # EPUB 支持
uv add python-docx    # DOCX 支持
```

---

## 输出结构

生成的专属 Skill 目录位于 `~/.config/opencode/skill/books/{slug}/`：

```
├── SKILL.md           # 核心入口（~4K tokens）
├── glossary.md        # 术语表（~1.5K tokens，按需加载）
├── patterns.md        # 模式表（~2K tokens，按需加载）
├── cheatsheet.md      # 速查表（~1K tokens，按需加载）
├── note.md            # 原始读书笔记
├── metadata.json      # 统计元数据
└── rejected/          # 未通过验证的方法论单元
    └── {method}.md
```

---

## 核心方法论

本 Skill 基于《如何阅读一本书》的分析阅读法 + RIA++ 方法论框架：

```
Step 0   提取书籍文本（PDF/EPUB/DOCX/TXT/MD 自动识别）
Step 0.5 成本估算（>50K tokens 提示分章处理）
Step 0.6 章节检测（中文/英文/日文 + TOC 识别）
Step 1   书籍分类
Step 2   搭建骨架（一句话概括 + 结构拆解）
Step 3   提取关键词 + 主旨句
Step 3.5 三重验证（V1 跨域 / V2 预测力 / V3 独特性）
Step 4   评价作者
Step 5   生成 RIA++ 六段笔记（R/I/A1/A2/E/B）
Step 6   生成专属 AI Skill（SKILL.md + 补充文件）
```

详细规则见 `references/analysis_rules.md`
