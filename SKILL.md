---
name: read-book
description: "读书 Skill - 基于《如何阅读一本书》的分析阅读法，深度分析书籍并生成专属 AI Skill 助手"
argument-hint: "[书籍文件名]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
use_case: |
  当用户需要深度分析一本书并生成结构化读书笔记和 RIA++ 格式的 AI Skill 时调用。
  支持 PDF / EPUB / DOCX / TXT / Markdown 格式。
  包含成本预估、章节检测、三重验证等质量控制步骤。
---

> 本 Skill 基于《如何阅读一本书》的分析阅读法，帮助你深度分析书籍，输出 RIA++ 结构化读书笔记，并生成专属 AI Skill。

## 触发条件

当用户说以下内容时启动：
- `/read-book`
- "帮我读一本书"
- "分析这本书"
- "生成读书笔记"
- 上传 `.pdf` / `.epub` / `.docx` / `.txt` / `.md` 文件

当用户想继续基于已分析的书籍进行问答时：
- 调用生成的专属 Skill（如 `/book-xxx`）

---

## 工具使用规则

| 任务                  | 使用工具                                                                 |
| --------------------- | ------------------------------------------------------------------------ |
| 读取书籍内容          | `Bash` + `uv run python scripts/extract.py --file "{path}" --output "./temp/{slug}.txt"` |
| 成本估算              | `Bash` + `uv run python scripts/cost_estimator.py` (读取提取后的文本)    |
| 章节检测              | `Bash` + `uv run python scripts/chapter_detector.py`                     |
| 写入读书笔记          | `Write` 工具                                                             |
| 追加评价/思考         | `Edit` 工具                                                              |
| 创建 Skill 目录       | `Bash` 工具                                                              |
| 生成专属 Skill        | `Bash` + `uv run python scripts/skill_generator.py`                      |
| 列出已分析书籍        | `Bash` + `uv run python scripts/skill_generator.py --action list`        |
| 大文件探测            | 优先用 `Grep` / `Glob` 而非 `Read` 全文（>5000 行时）                   |

**输出目录**：生成的读书笔记和 Skill 写入 `~/.config/opencode/skill/books/{slug}/`

---

## 路径约定

本 skill 当中的所有的引用及运行脚本的路径请优先从当前 skill 目录查找，例如：
- 引用 `references/analysis_rules.md`
- 运行脚本 `uv run python scripts/extract.py`
- 章节检测 `uv run python scripts/chapter_detector.py`
- 成本估算 `uv run python scripts/cost_estimator.py`

---

## 核心流程：分析阅读 7 步法 (RIA++)

### Step 0: 读取书籍内容

**根据文件类型选择读取方式**：

```
格式       命令
───       ───
.pdf      uv run python scripts/extract.py --file "{path}" --output "./temp/{slug}.txt" [--technical]
.epub     uv run python scripts/extract.py --file "{path}" --output "./temp/{slug}.txt"
.docx     uv run python scripts/extract.py --file "{path}" --output "./temp/{slug}.txt"
.txt/.md  uv run python scripts/extract.py --file "{path}" --output "./temp/{slug}.txt"
```

PDF 参数说明：
- `--technical`：技术类书籍，优先使用 docling（需安装）
- `--start N`：从第 N 页开始
- `--end N`：到第 N 页结束

**回退链**（自动降级）：
- PDF：docling → pdftotext(poppler) → pypdf → pdfminer.six
- EPUB：ebooklib+BeautifulSoup → zipfile+xml
- DOCX：python-docx → zipfile+xml

---

### Step 0.5: 成本估算（大文件必做）

**目标**：预估处理成本，避免超长文档意外消耗过多 token

**步骤**：
1. 提取文本后，运行成本估算（默认 GLM-5.2 计价）：
   ```bash
   uv run python scripts/cost_estimator.py --file "./temp/{slug}.txt"
   ```
2. 估算包含：字符数、预估 token 数、预估成本（元）
3. 如果预估 token > 50K，询问用户是否继续：
   - 用户确认 → 继续
   - 用户取消 → 终止，建议用章节检测后分步处理

**GLM-5.2 定价**：
- 输入：8元/百万token
- 输出：28元/百万token
- 缓存命中：2元/百万token
- 上下文窗口：1M tokens

**输出**：成本估算摘要

---

### Step 0.6: 章节检测

**目标**：快速了解书籍结构，识别章节边界

**步骤**：
1. 运行章节检测：
   ```bash
   uv run python scripts/chapter_detector.py --file "./temp/{slug}.txt"
   ```
2. 获取章节列表和目录检测结果
3. 如果检测到目录(TOC)，优先从目录区域读取结构
4. 如果文本 > 5000 行，建议按章节分步处理而非一次性读取全文

**输出**：章节列表 + 目录检测结果

---

### Step 1: 书籍分类

**目标**：判断书籍类型，确定分析方法

**步骤**：
1. 读取 `prompts/step1_classify.md` 获取分类指导
2. 阅读书籍前言/目录/序言（用 Grep 快速定位）
3. 判断书籍类型：
   - **虚构小说类** → 阅读故事的方法
   - **理论性作品**（历史、科学、哲学、数学） → 关注观点与论证
   - **实用性作品**（方法论、自我提升） → 关注可执行的方法
   - **社会科学类** → 关注人与社会的关系

**输出**：记录书籍类型，后续分析以此为依据调整方法

---

### Step 2: 搭建骨架

**目标**：理解书籍整体结构

**步骤**：
1. 读取 `prompts/step2_skeleton.md` 获取骨架指导
2. 回答三个问题：
   - 这本书在谈什么？（用一句话概括）
   - 作者如何依次发展这个主题？
   - 作者想要解决什么问题？
3. 列出全书的重要部分

**输出**：骨架摘要（一句话概括 + 结构拆解 + 作者要解决的问题）

---

### Step 3: 提取关键词 + 主旨句

**目标**：与作者达成共识，理解核心概念

**步骤**：
1. 读取 `prompts/step3_keywords.md` 获取提取指导
2. 找出 5-10 个反复出现的关键概念
3. 确认理解与作者一致
4. 找出作者最核心的主旨句

**输出**：核心概念表格 + 核心主旨列表

---

### Step 3.5: 三重验证

**目标**：对提取的核心概念/方法论候选进行质量过滤

**步骤**：
1. 对每个方法论单元执行三项验证：
   - **V1 跨域验证**：书中是否有 ≥2 处独立段落佐证？
   - **V2 预测力验证**：能否用它回答一个书中未明说的新问题？
   - **V3 独特性验证**：不是常识？
2. 三 ✓ → 进入 Step 5
3. 含 ✗ → 标记为"待审"，由脚本在 Step 6 自动过滤

**输出**：验证记录列表

---

### Step 4: 评价作者

**目标**：形成自己的观点

**步骤**：
1. 读取 `prompts/step4_evaluate.md` 获取评价指导
2. 回答四个问题：
   - 这本书说的是真的吗？
   - 同意/反对的理由？
   - 与我何干？
   - 读完后有什么改变？

**输出**：评价与思考段落

---

### Step 5: 生成结构化读书笔记

**目标**：将分析结果整理为可复用的笔记，按方法论单元组织

**步骤**：
1. 读取 `prompts/step5_note.md` 获取笔记模板
2. 整合 Step 1-4 的所有分析结果
3. 方法论内容拆分为独立单元，每个单元填充 R/I/A1/A2/E/B 六段 + 验证记录
4. 填充模板，生成完整读书笔记

**输出路径**：`~/.config/opencode/skill/books/{slug}/note.md`

**笔记结构**：
```
## 方法论拆解
### {方法论1} → R / I / A1 / A2 / E / B / 验证记录
### {方法论2} → R / I / A1 / A2 / E / B / 验证记录
## 核心概念 → 概念表格
## 我的评价 / 与我何干
## 精彩摘录
## 附录：分析过程记录
```

---

### Step 6: 生成专属 AI Skill（RIA++）

**目标**：将书籍方法论封装为 RIA++ 结构的可执行 Skill

**步骤**（推荐使用脚本自动生成）：
```bash
uv run python scripts/skill_generator.py \
  --book-title "{书名}" \
  --note-path "~/.config/opencode/skill/books/{slug}/note.md"
```

脚本执行流程：
1. 解析笔记中的方法论单元（`## 方法论拆解` 部分）
2. **三重验证过滤**（V1/V2/V3）
3. 生成 RIA++ 结构化 SKILL.md + glossary.md + patterns.md + cheatsheet.md

**输出路径**：
```
~/.config/opencode/skill/books/{slug}/
├── SKILL.md          # 核心触发入口（~4K tokens）
├── glossary.md       # 术语表（~1.5K tokens）
├── patterns.md       # 技术/模式表（~2K tokens）
├── cheatsheet.md     # 决策规则速查（~1K tokens）
└── rejected/         # 被过滤的方法论单元
```

**触发词**：`/book-{slug}`

---

### Step 7: 验证生成的 Skill

**目标**：确保生成的 RIA++ Skill 结构完整

**步骤**：
1. **RIA++ 完整性检查**：每个方法论单元确认包含全部六段
2. **路径检查**：确认文件位于 `~/.config/opencode/skill/books/{slug}/`
3. **问答测试**：调用 `/book-{slug}` 测试
4. **修复问题**：如果发现问题，检查笔记格式后重新生成

---

## 管理命令

### 列出已分析的书籍
```bash
uv run python scripts/skill_generator.py --action list
```

### 查看某本书的笔记
```bash
cat ~/.config/opencode/skill/books/{slug}/note.md
```

### 查看被过滤的方法论单元
```bash
ls ~/.config/opencode/skill/books/{slug}/rejected/
```

### 调用生成的专属 Skill
```
/book-{slug}
```

---

## 输出文件结构

生成的专属 Skill 目录：
```
~/.config/opencode/skill/books/{slug}/
├── SKILL.md           # 核心：frontmatter + 方法论卡片 + 索引
├── glossary.md        # 术语表：书中关键概念定义
├── patterns.md        # 模式表：技术、算法、设计模式
├── cheatsheet.md      # 速查表：决策规则、快速参考
├── note.md            # 原始读书笔记
├── metadata.json      # 元数据：提取统计、验证统计
└── rejected/          # 未通过三重验证的方法论
    ├── {method}.md
    └── ...
```

### 各文件 token 预算

| 文件 | 预算 | 用途 |
|------|------|------|
| SKILL.md | ~4K tokens | 核心框架 + 方法论索引 + 第一屏方法论卡片 |
| glossary.md | ~1.5K tokens | 所有术语定义（按需加载） |
| patterns.md | ~2K tokens | 技术/模式描述（按需加载） |
| cheatsheet.md | ~1K tokens | 决策表（按需加载） |

---

## 参考资料

- 详细分析阅读规则：`references/analysis_rules.md`
- 完整阅读层次说明：`references/read_level.md`
