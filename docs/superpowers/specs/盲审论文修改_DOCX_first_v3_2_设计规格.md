# 盲审论文修改 Claude Code Skill v3.2：DOCX-first 设计规格

> 目标：先放弃 PDF-first 主链路，以 Word/DOCX 作为论文主事实源，重新设计论文解析、图表提取、上下文包、修改建议生成和 Word 回写能力。  
> 使用对象：终端 Codex / Claude Code 项目实现者  
> 状态：工程实现规格

---

## 0. 设计原则

### 0.1 一句话原则

以 DOCX 作为论文主事实源，以 PDF 作为可选页码、版式和标注辅助源。

### 0.2 为什么改成 DOCX-first

PDF 更适合展示，不适合作为结构化修改源。PDF 中的标题、段落、图表和公式需要从坐标、字体和页面布局中反推，容易出错。DOCX 本身保存了段落、样式、表格、图片、题注、编号等结构信息，更适合论文修改任务。

### 0.3 MVP 明确范围

MVP 强制论文主输入为 DOCX。

PDF-only 不作为高质量主路径。若用户只有 PDF，可以进入 degraded mode，但不承诺稳定章节结构、图表定位和正文回写。

---

## 1. 输入策略

### 1.1 主输入

```text
paper.docx          必需
review.pdf/docx/txt 可选格式
paper.pdf           可选，仅用于页码、版式核对和 PDF 标注
```

### 1.2 输入优先级

```text
论文正文事实源：DOCX
页码和最终版式源：PDF，可选
盲审意见源：PDF / DOCX / TXT / Markdown
```

### 1.3 降级模式

```yaml
modes:
  docx_first:
    quality: high
    requirements:
      - paper.docx
  docx_with_pdf_alignment:
    quality: highest
    requirements:
      - paper.docx
      - paper.pdf
  pdf_only:
    quality: degraded
    requirements:
      - paper.pdf
    limitations:
      - section tree may be inaccurate
      - figures/tables may be incomplete
      - docx patch output unavailable
```

---

## 2. 新总体工作流

```text
paper.docx
  ↓
DOCX 解包与结构读取
  ↓
按 Word 顺序提取 blocks
  ↓
构建 section tree
  ↓
提取图片、表格、公式、题注
  ↓
生成 paper.md / paper_blocks.json / paper_structure.json / asset_catalog.json
  ↓
生成 section_summaries.json / paper_brief.md
  ↓
解析盲审意见 review_comments.json
  ↓
多位置映射 comment_mappings.json
  ↓
为每条意见构建 context_bundle
  ↓
revision-planner 生成正文级修改方案
  ↓
quality-auditor 审核
  ↓
输出：
    - 修改报告.md
    - 盲审回应表.md
    - 作者待补充事项.md
    - 修改建议版.docx
    - 可选标注版 PDF
```

---

## 3. 项目目录结构

```text
thesis-blind-review-revision/
├── .claude/
│   ├── skills/
│   │   └── thesis-review-revision/
│   │       ├── SKILL.md
│   │       ├── schemas/
│   │       │   ├── docx_blocks.schema.json
│   │       │   ├── paper_structure.schema.json
│   │       │   ├── asset_catalog.schema.json
│   │       │   ├── section_summaries.schema.json
│   │       │   ├── review_comments.schema.json
│   │       │   ├── comment_mappings.schema.json
│   │       │   ├── context_bundle.schema.json
│   │       │   ├── revision_plan.schema.json
│   │       │   └── quality_audit.schema.json
│   │       └── templates/
│   │           ├── 修改报告模板.md
│   │           ├── 盲审回应表模板.md
│   │           └── 作者待补充事项模板.md
│   │
│   └── agents/
│       ├── review-parser.md
│       ├── docx-structure-analyzer.md
│       ├── section-summarizer.md
│       ├── multi-location-mapper.md
│       ├── context-bundle-reviewer.md
│       ├── revision-planner.md
│       ├── visual-table-reviewer.md
│       ├── docx-patch-planner.md
│       ├── quality-auditor.md
│       └── response-writer.md
│
├── scripts/
│   ├── ingest_docx.py
│   ├── unpack_docx.py
│   ├── extract_docx_blocks.py
│   ├── extract_docx_assets.py
│   ├── extract_docx_tables.py
│   ├── build_docx_section_tree.py
│   ├── normalize_docx_to_markdown.py
│   ├── build_context_bundle.py
│   ├── patch_docx_suggestions.py
│   ├── validate_json.py
│   └── render_report.py
│
├── src/
│   ├── models.py
│   ├── docx_ingestion/
│   │   ├── package.py
│   │   ├── iterator.py
│   │   ├── blocks.py
│   │   ├── styles.py
│   │   ├── sections.py
│   │   ├── captions.py
│   │   ├── images.py
│   │   ├── tables.py
│   │   ├── formulas.py
│   │   └── markdown.py
│   ├── retrieval/
│   │   ├── candidate_recall.py
│   │   ├── section_ranker.py
│   │   ├── asset_ranker.py
│   │   └── context_bundle.py
│   ├── patching/
│   │   ├── anchors.py
│   │   ├── comments.py
│   │   ├── highlights.py
│   │   └── docx_writer.py
│   └── reporting/
│       ├── report_renderer.py
│       └── response_table.py
│
├── workdir/
│   ├── inputs/
│   │   ├── paper.docx
│   │   ├── paper.pdf
│   │   └── review.pdf
│   ├── docx/
│   │   ├── document.xml
│   │   ├── styles.xml
│   │   ├── numbering.xml
│   │   └── media/
│   ├── paper/
│   │   ├── paper.md
│   │   ├── paper_blocks.json
│   │   ├── paper_structure.json
│   │   ├── section_summaries.json
│   │   ├── paper_brief.md
│   │   └── sections/
│   ├── assets/
│   │   ├── figures/
│   │   ├── tables/
│   │   ├── formulas/
│   │   └── asset_catalog.json
│   ├── review/
│   ├── mappings/
│   ├── bundles/
│   ├── revision_plans/
│   ├── audits/
│   └── outputs/
│       ├── 修改报告.md
│       ├── 盲审回应表.md
│       ├── 作者待补充事项.md
│       └── 修改建议版.docx
```

---

## 4. DOCX 解析层设计

### 4.1 不要只用 paragraphs

`python-docx` 的 `Document.paragraphs` 只能拿到段落，`Document.tables` 只能拿到表格，但这两个列表分开后会丢失文档顺序。论文修改必须保留 Word 原始顺序。

因此必须实现一个 body-level iterator：

```python
iter_docx_blocks(document)
```

按 `document.element.body` 里的 XML 顺序遍历：

```text
w:p   → paragraph block
w:tbl → table block
```

段落中如含图片、公式、脚注、题注，也需要进一步解析 run-level 元素。

---

### 4.2 block 类型

```text
heading
paragraph
list_item
figure
figure_caption
table
table_caption
formula
reference_item
footnote
endnote
comment
unknown
```

---

### 4.3 paper_blocks.json

```json
{
  "blocks": [
    {
      "block_id": "b_000421",
      "order": 421,
      "type": "heading",
      "text": "4.2.1 面向算力规划的多区域CGE模型构建",
      "style_name": "Heading 3",
      "style_id": "Heading3",
      "section_id": "sec_4_2_1",
      "section_path": ["第四章", "4.2", "4.2.1"],
      "docx_locator": {
        "body_index": 421,
        "xml_tag": "w:p",
        "xpath_hint": "/w:document/w:body/w:p[421]"
      },
      "assets": [],
      "raw_xml_path": null
    },
    {
      "block_id": "b_000422",
      "order": 422,
      "type": "paragraph",
      "text": "本文构建多区域CGE模型...",
      "style_name": "Normal",
      "style_id": "Normal",
      "section_id": "sec_4_2_1",
      "section_path": ["第四章", "4.2", "4.2.1"],
      "docx_locator": {
        "body_index": 422,
        "xml_tag": "w:p"
      },
      "assets": []
    }
  ]
}
```

---

## 5. 章节树构建

### 5.1 优先依据

按优先级判断标题：

1. Word 样式：
   - Heading 1
   - Heading 2
   - Heading 3
   - 标题 1
   - 标题 2
   - 标题 3
2. 正则编号：
   - `第[一二三四五六七八九十]+章`
   - `\d+(\.\d+)+`
   - `一、`
   - `（一）`
3. 格式辅助：
   - 加粗
   - 居中
   - 字号明显大于正文

MVP 中，优先依赖 Word 样式。若样式混乱，再使用编号正则补救。

---

### 5.2 section_id 规则

```text
第一章 → sec_1
1.1 → sec_1_1
1.1.1 → sec_1_1_1
第四章 4.2.1 → sec_4_2_1
参考文献 → sec_references
摘要 → sec_abstract
结论 → sec_conclusion
```

---

### 5.3 paper_structure.json

```json
{
  "paper_title": "论文标题",
  "sections": [
    {
      "section_id": "sec_4_2_1",
      "level": 3,
      "title": "4.2.1 面向算力规划的多区域CGE模型构建",
      "parent": "sec_4_2",
      "children": [],
      "block_start": "b_000421",
      "block_end": "b_000455",
      "blocks": ["b_000421", "b_000422"],
      "figures": ["fig_4_1"],
      "tables": ["tab_4_1"],
      "formulas": ["eq_4_1", "eq_4_2"],
      "estimated_page_range": null
    }
  ]
}
```

---

## 6. Word 图片提取设计

### 6.1 图片来源

DOCX 是 ZIP 容器，图片通常位于：

```text
word/media/
```

但不能只把 media 目录复制出来。必须知道每张图片在正文中出现的位置、前后段落和题注。

---

### 6.2 图片解析流程

```text
遍历正文 block
  ↓
遇到段落 w:p
  ↓
检查其中是否有 w:drawing / a:blip
  ↓
读取 r:embed relationship id
  ↓
从 document.xml.rels 找到 media 路径
  ↓
复制图片到 workdir/assets/figures/
  ↓
创建 figure asset
  ↓
在前后 block 中寻找 caption
```

---

### 6.3 图片 asset schema

```json
{
  "asset_id": "fig_3_2",
  "asset_type": "figure",
  "label": "图3.2",
  "caption": "基于贝叶斯优化的混合MILP求解算法流程图",
  "section_id": "sec_3_4",
  "section_title": "3.4 基于贝叶斯优化的混合MILP求解算法",
  "block_id": "b_000302",
  "image_path": "workdir/assets/figures/fig_3_2.png",
  "original_media_path": "word/media/image7.png",
  "nearby_text_before": "为提高模型求解效率，本文设计了如下求解流程。",
  "nearby_text_after": "该流程首先初始化MILP模型参数...",
  "caption_position": "after",
  "quality": {
    "has_caption": true,
    "caption_confidence": 0.91,
    "has_preceding_intro": true,
    "needs_manual_check": false
  }
}
```

---

### 6.4 caption 匹配规则

识别：

```text
图3.2 xxx
图 3.2 xxx
图3-2 xxx
Figure 3.2 xxx
Fig. 3.2 xxx
```

在图片前后 N 个 block 中搜索，默认：

```yaml
caption_search_window:
  before_blocks: 3
  after_blocks: 3
```

匹配优先级：

1. 图片后紧邻段落是图题；
2. 图片前紧邻段落是图题；
3. 附近段落出现图号；
4. 无图号但出现“图”“Figure”等关键词；
5. 匹配失败则生成临时编号 `fig_auto_001` 并标记人工检查。

---

## 7. Word 表格提取设计

### 7.1 表格优势

DOCX 表格是结构化对象，不需要像 PDF 一样通过坐标和线条猜。每个表格应输出三种表示：

```text
1. JSON 结构
2. Markdown 表格
3. CSV 文件
```

如果表格有合并单元格，CSV 可以退化，Markdown 可以标记 `merged_cell_warning`。

---

### 7.2 table asset schema

```json
{
  "asset_id": "tab_3_1",
  "asset_type": "table",
  "label": "表3.1",
  "caption": "实验参数设置",
  "section_id": "sec_3_5_1",
  "section_title": "3.5.1 实验设置",
  "block_id": "b_000356",
  "markdown_path": "workdir/assets/tables/tab_3_1.md",
  "csv_path": "workdir/assets/tables/tab_3_1.csv",
  "json_path": "workdir/assets/tables/tab_3_1.json",
  "nearby_text_before": "实验参数设置如表3.1所示。",
  "nearby_text_after": "基于上述参数，本文开展对比实验。",
  "caption_position": "before",
  "quality": {
    "has_caption": true,
    "caption_confidence": 0.94,
    "has_preceding_intro": true,
    "merged_cells_detected": false,
    "needs_manual_check": false
  }
}
```

---

### 7.3 表格 Markdown 输出

```md
表3.1 实验参数设置

| 参数 | 含义 | 取值 |
|---|---|---|
| α | 学习率 | 0.01 |
| β | 碳成本权重 | 0.3 |
```

---

### 7.4 表格 caption 匹配规则

识别：

```text
表3.1 xxx
表 3.1 xxx
表3-1 xxx
Table 3.1 xxx
```

默认前后搜索窗口：

```yaml
caption_search_window:
  before_blocks: 3
  after_blocks: 3
```

表格 caption 更常见于表格前，但不能写死。

---

## 8. 公式提取设计

### 8.1 MVP 策略

Word 公式可能是：

```text
Office Math OMML
图片公式
普通文本公式
```

MVP 不强制完整转换 LaTeX，但必须识别公式位置和编号。

输出：

```json
{
  "asset_id": "eq_4_1",
  "asset_type": "formula",
  "label": "公式4.1",
  "section_id": "sec_4_2_1",
  "block_id": "b_000431",
  "text": "OMML 或提取文本",
  "latex": null,
  "nearby_text_before": "...",
  "nearby_text_after": "...",
  "quality": {
    "parse_confidence": 0.6,
    "needs_manual_check": true
  }
}
```

### 8.2 后续增强

可加入：

```text
omml2mathml
mathml2latex
pandoc 转换辅助
```

但 MVP 不依赖公式完美转换。

---

## 9. asset_catalog.json

统一保存图片、表格、公式。

```json
{
  "assets": [
    {
      "asset_id": "fig_3_2",
      "asset_type": "figure",
      "label": "图3.2",
      "caption": "...",
      "section_id": "sec_3_4",
      "image_path": "workdir/assets/figures/fig_3_2.png"
    },
    {
      "asset_id": "tab_3_1",
      "asset_type": "table",
      "label": "表3.1",
      "caption": "...",
      "section_id": "sec_3_5_1",
      "markdown_path": "workdir/assets/tables/tab_3_1.md",
      "csv_path": "workdir/assets/tables/tab_3_1.csv"
    },
    {
      "asset_id": "eq_4_1",
      "asset_type": "formula",
      "label": "公式4.1",
      "section_id": "sec_4_2_1",
      "text": "..."
    }
  ]
}
```

---

## 10. Markdown 生成

### 10.1 paper.md

从 DOCX 生成 `paper.md`，用于人工审查和模型上下文。

要求：

1. 标题转为 Markdown heading。
2. 段落保持原顺序。
3. 表格转 Markdown。
4. 图片用相对路径嵌入。
5. 公式保留编号。
6. 图表题注保留。
7. 每个章节生成独立 `.md` 文件。

示例：

```md
# 第三章 CEOP-MILP模型

## 3.4 基于贝叶斯优化的混合MILP求解算法

为提高模型求解效率，本文设计了如下求解流程。

![图3.2 基于贝叶斯优化的混合MILP求解算法流程图](../assets/figures/fig_3_2.png)

图3.2 基于贝叶斯优化的混合MILP求解算法流程图

该流程首先初始化 MILP 模型参数...
```

---

## 11. 章节摘要与 paper_brief

### 11.1 section_summaries.json

由 `section-summarizer` 生成：

```json
{
  "sections": [
    {
      "section_id": "sec_4_2_1",
      "title": "4.2.1 面向算力规划的多区域CGE模型构建",
      "summary_short": "本节构建多区域CGE模型，并将算力服务纳入生产结构。",
      "summary_detailed": "本节首先说明多区域CGE模型的基本结构，然后在生产模块中引入算力服务变量...",
      "key_claims": [
        "算力服务进入生产模块",
        "生产函数采用CES结构",
        "模型用于刻画算力资源对区域经济和能源环境的影响"
      ],
      "related_assets": ["eq_4_1", "eq_4_2"]
    }
  ]
}
```

### 11.2 paper_brief.md

每个 revision-planner 都要默认拿到：

```md
# 论文压缩上下文

## 论文主题
...

## 研究问题
...

## 方法体系
...

## 章节结构
...

## 核心模型与变量
...

## 实验与验证
...

## 结论与创新点
...

## 图表目录摘要
...
```

---

## 12. 多位置映射

原来只返回一个 chunk 的设计必须废弃。

### 12.1 comment_mappings.json

```json
{
  "mappings": [
    {
      "comment_id": "R1-C001",
      "mapping_type": "multi_section",
      "locations": [
        {
          "role": "core_revision_location",
          "section_id": "sec_4_2_1",
          "title": "4.2.1 面向算力规划的多区域CGE模型构建",
          "reason": "CGE生产模块是回应算力与传统要素替代关系的核心位置。",
          "include_mode": "full_text",
          "confidence": 0.92
        },
        {
          "role": "supporting_context",
          "section_id": "sec_1_3",
          "title": "1.3 研究内容与创新点",
          "reason": "创新点部分需要与第四章补充表述保持一致。",
          "include_mode": "full_text",
          "confidence": 0.78
        },
        {
          "role": "consistency_update_location",
          "section_id": "sec_5_1",
          "title": "5.1 研究结论",
          "reason": "结论部分应同步补充经济学含义。",
          "include_mode": "summary_plus_target_paragraphs",
          "confidence": 0.74
        }
      ],
      "assets": [],
      "requires_author_input": false
    }
  ]
}
```

---

## 13. Context Bundle

### 13.1 每条意见一个 context bundle

```json
{
  "comment_id": "R2-C007",
  "comment": {
    "original_text": "图3.2，建议重新绘制，注意判断条件图元和相应线条的规范化。",
    "category": "图表规范",
    "severity": "重点修改"
  },
  "paper_brief": {
    "path": "workdir/paper/paper_brief.md"
  },
  "evidence_pack": {
    "must_read_full_text": [
      {
        "section_id": "sec_3_4",
        "title": "3.4 基于贝叶斯优化的混合MILP求解算法",
        "text_path": "workdir/paper/sections/sec_3_4.md"
      }
    ],
    "visual_assets": [
      {
        "asset_id": "fig_3_2",
        "label": "图3.2",
        "caption": "基于贝叶斯优化的混合MILP求解算法流程图",
        "image_path": "workdir/assets/figures/fig_3_2.png",
        "nearby_text_before": "...",
        "nearby_text_after": "...",
        "inspection_task": "检查流程图图元、判断条件、箭头方向和线条规范性。"
      }
    ],
    "table_assets": []
  }
}
```

### 13.2 图表意见硬规则

如果意见明确提到图号或表号：

```text
必须将对应 asset 放入 context_bundle。
如果未找到，必须放入 needs_human_location_check。
```

---

## 14. Revision Planner 输出标准

### 14.1 禁止泛泛建议

禁止只输出：

```text
建议补充说明。
建议加强论证。
建议完善模型解释。
建议统一格式。
```

必须输出：

```text
插入位置
原文锚点
新增正文 / 替换正文
修改原因
给评审专家的回复
```

---

### 14.2 revision_plan.json

```json
{
  "comment_id": "R1-C001",
  "revision_status": "text_ready",
  "overall_strategy": "在CGE生产模块补充算力与传统要素替代/互补关系的经济学解释，并在结论中同步强化模型设定依据。",
  "actions": [
    {
      "action_id": "A1",
      "type": "insert_after_paragraph",
      "target": {
        "section_id": "sec_4_2_1",
        "section_title": "4.2.1 面向算力规划的多区域CGE模型构建"
      },
      "anchor_text": "定位到原文中介绍CES生产函数或算力服务变量进入生产模块的段落之后。",
      "original_text": "",
      "new_text": "在本文的CGE生产模块中，算力服务并非被视为完全独立于传统生产要素之外的外生变量，而是作为数字化生产条件下能够改变资本、劳动和能源配置效率的新型投入要素纳入生产结构。具体而言，算力服务一方面可以通过提升数据处理、任务调度和资源配置效率，对部分重复性劳动和传统管理投入形成替代效应；另一方面，算力服务的使用依赖服务器、网络设备、数据中心基础设施以及稳定能源供给，因此又与资本投入和能源投入表现出较强的互补关系。基于这一特征，本文采用CES嵌套结构刻画算力服务与传统要素之间的有限替代关系，而非假定二者可以完全替代。",
      "rationale": "该段直接回应评审专家关于算力与资本、劳动力替代关系缺乏讨论的问题。",
      "requires_author_input": false
    }
  ],
  "reviewer_response": "感谢专家意见。针对算力与资本、劳动力等传统要素替代关系讨论不足的问题，本文已在第4.2.1节生产模块构建部分补充算力服务进入CGE模型的经济学解释..."
}
```

---

## 15. Word 修改建议版输出

### 15.1 输出目标

生成：

```text
outputs/修改建议版.docx
```

不是直接覆盖原文，而是在副本中：

1. 插入建议正文；
2. 使用高亮标记；
3. 加批注说明对应评审意见；
4. 对需要人工确认的内容只加批注，不直接写死；
5. 保留原文格式尽量不破坏。

---

### 15.2 patch 策略

MVP 不做复杂 Track Changes，先做：

```text
复制原 DOCX → 找 anchor → 插入新段落 → 黄色高亮 → 批注说明
```

如果 anchor 不精确：

```text
在对应 section 末尾插入“建议补充段落”，并标记需人工确认位置。
```

---

### 15.3 patch_plan.json

```json
{
  "patches": [
    {
      "comment_id": "R1-C001",
      "action_id": "A1",
      "patch_type": "insert_after_anchor",
      "section_id": "sec_4_2_1",
      "anchor_text": "CES生产函数",
      "new_text": "...",
      "comment_text": "回应 R1-C001：补充算力与传统要素替代/互补关系的经济学解释。",
      "highlight": true,
      "requires_manual_position_check": false
    }
  ]
}
```

---

## 16. Quality Auditor

必须拦截：

1. 没有 `new_text` 的重点修改；
2. 没有 `anchor_text` 的正文修改；
3. 图表意见没有 asset；
4. 表格意见没有 Markdown/CSV；
5. 实验意见编造结果；
6. 参考文献意见编造出处；
7. 只返回“建议补充/建议完善”的泛泛建议；
8. 需要作者补充的内容被写成已完成。

---

## 17. SKILL.md 必加规则

```md
## DOCX-first rules

1. The primary thesis source is DOCX.
2. Do not use PDF as the main structural source when DOCX is available.
3. Preserve document order across paragraphs, tables, images, captions, and formulas.
4. Build a section tree from Word styles first, then numbering regex.
5. Extract figures and tables into asset_catalog.json.
6. Map each review comment to multiple locations, not a single chunk.
7. Build a context bundle for each comment.
8. Every substantive revision must provide concrete new_text or revised_text.
9. The final report must include exact insertion/revision text.
10. Generate a suggestion DOCX copy when possible.
```

---

## 18. Codex 实现任务清单

### Phase 1：DOCX 解包与 block 遍历

- [ ] 实现 `unpack_docx.py`
- [ ] 实现 `iter_docx_blocks`
- [ ] 输出 `paper_blocks.json`
- [ ] 保留文档原始顺序

### Phase 2：章节树

- [ ] 从 Heading 样式构建 section tree
- [ ] 用编号正则补救
- [ ] 输出 `paper_structure.json`
- [ ] 输出 `sections/*.md`

### Phase 3：图表提取

- [ ] 提取 `word/media` 图片
- [ ] 在正文顺序中定位图片
- [ ] 匹配图题
- [ ] 提取表格为 JSON/Markdown/CSV
- [ ] 匹配表题
- [ ] 输出 `asset_catalog.json`

### Phase 4：Markdown 生成

- [ ] 生成 `paper.md`
- [ ] 图片以 Markdown image 引用
- [ ] 表格以 Markdown 表格输出
- [ ] 保留章节层级

### Phase 5：摘要与 brief

- [ ] `section-summarizer` 生成章节摘要
- [ ] 生成 `paper_brief.md`
- [ ] 纳入图表目录摘要

### Phase 6：多位置映射

- [ ] 实现多位置召回
- [ ] 输出 `comment_mappings.json`
- [ ] 图号/表号强制匹配 asset

### Phase 7：Context Bundle

- [ ] 每条意见生成一个 context bundle
- [ ] 必含 paper brief
- [ ] 必含 core section full text
- [ ] 图表意见必含 asset

### Phase 8：Revision Planner

- [ ] 强制输出正文级 `new_text/revised_text`
- [ ] 按意见类型输出不同模板
- [ ] 图表类意见输出图表调整方案

### Phase 9：Word 回写

- [ ] 生成 `patch_plan.json`
- [ ] 复制原 DOCX
- [ ] 插入建议正文
- [ ] 高亮新增内容
- [ ] 加批注或替代批注说明

### Phase 10：质量审计和报告

- [ ] 实现 quality-auditor
- [ ] 低质量方案不进入最终报告
- [ ] 报告显示具体正文、定位、评审回复

---

## 19. 验收标准

### 19.1 文件验收

必须生成：

```text
workdir/paper/paper_blocks.json
workdir/paper/paper_structure.json
workdir/paper/paper.md
workdir/assets/asset_catalog.json
workdir/paper/section_summaries.json
workdir/paper/paper_brief.md
workdir/bundles/*.context.json
workdir/revision_plans/*.plan.json
workdir/outputs/修改报告.md
workdir/outputs/修改建议版.docx
```

### 19.2 图表验收

对于 Word 中存在的图表：

```text
至少 90% 的图片进入 asset_catalog
至少 90% 的表格进入 asset_catalog
能匹配到题注的图表应使用 fig_3_2 / tab_3_1 这种编号
无法匹配题注的图表应标记 needs_manual_check
```

### 19.3 修改建议验收

重点修改意见必须包含：

```text
section_id
anchor_text
new_text 或 revised_text
rationale
reviewer_response
```

正文级意见的 `new_text` 原则上不少于 150 个中文字符。

---

# 20. 最终目标

本 Skill 的最终目标不是生成一份泛泛的“修改建议报告”，而是生成一个 **可执行的盲审论文修改包**。

所谓“可执行”，是指作者拿到输出后，能够明确知道：

1. 每条盲审意见对应论文中的哪些位置；
2. 这些位置为什么与该意见相关；
3. 论文当前缺少什么；
4. 应该如何修改；
5. 哪些正文可以直接插入或替换；
6. 哪些内容需要作者补充真实数据、实验结果、图源文件或参考文献信息；
7. Word 文档中应该在哪里插入、替换、批注或高亮；
8. 最终应如何正式回复盲审专家。

因此，最终交付物应包括以下文件：

```text
outputs/
├── 01_总览_修改任务看板.md
├── 02_逐条意见修改包.md
├── 03_盲审回复表.md
├── 04_作者待确认事项.md
└── 05_修改建议版.docx
```

---

## 20.1 核心交付物一：逐条意见修改包

`02_逐条意见修改包.md` 是最核心的输出。

每条盲审意见必须生成一个完整的 **Revision Card**，格式如下：

```md
## R1-C001：意见简短标题

### A. 评审意见原文

> 原始盲审意见。

### B. 问题诊断

解释评审专家为什么会提出这个问题，论文当前可能缺少什么，不能只复述意见。

### C. 论文证据与定位

| 角色 | 位置 | 证据 | 用途 |
|---|---|---|---|
| 核心修改位置 | 第X章第X节 | 原文锚点或摘要 | 主要修改处 |
| 辅助参考位置 | 第X章第X节 | 相关内容 | 保证上下文一致 |
| 同步修改位置 | 结论/创新点/摘要 | 相关表述 | 避免前后不一致 |
| 图表/表格/公式 | 图X.X/表X.X/公式X.X | asset_id | 如适用 |

### D. 修改策略

说明本条意见应该采用什么修改策略，例如：

- 新增理论解释；
- 重写模型说明；
- 补充实验设计；
- 调整图表；
- 统一格式；
- 核查参考文献；
- 同步修改结论或创新点。

### E. 具体修改方案

#### E1. 正文新增/替换

- 插入位置：
- 原文锚点：
- 新增正文 / 替换正文：

> 可直接放入论文的正文。

#### E2. 图表、表格或公式调整

如适用，给出具体调整方案，而不是只写“建议修改”。

#### E3. 章节一致性修改

如适用，给出摘要、结论、创新点或方法章节的同步修改文本。

### F. Word 回写动作

| patch_id | 操作 | 位置 | 内容 | 是否自动执行 |
|---|---|---|---|---|
| P001 | 插入新段落 | 第X节某段之后 | 新增正文 | 是/否 |
| P002 | 添加批注 | 图X.X旁 | 重绘说明 | 是/否 |

### G. 作者需要确认

明确列出是否需要作者补充：

- 真实实验数据；
- 新增实验结果；
- 图源文件；
- 参考文献出处；
- 导师/学校格式要求；
- 不可由模型编造的信息。

### H. 盲审回复文本

给出正式、可提交的回复文本。
```

---

## 20.2 核心交付物二：修改建议版 Word

`05_修改建议版.docx` 是给作者直接打开审阅的文件。

它不应直接粗暴覆盖原文，而应采用“建议修改版”的形式：

```text
新增内容：高亮显示
替换建议：保留原文并添加批注
图表重绘：在图旁添加批注和重绘说明
需作者确认：用【待确认】标记
格式问题：可自动处理的直接处理，不确定的加批注
```

每处修改建议都应标明对应意见编号，例如：

```text
回应 R1-C001：补充算力服务与传统生产要素之间替代/互补关系的经济学解释。
```

---

## 20.3 核心交付物三：盲审回复表

`03_盲审回复表.md` 应面向最终提交。

格式建议：

```md
| 意见编号 | 评审意见摘要 | 修改情况 | 修改位置 | 回复说明 |
|---|---|---|---|
| R1-C001 | 算力与传统要素替代关系说明不足 | 已补充理论解释 | 第4.2.1节、第5章结论 | 感谢专家意见…… |
```

注意：

如果某项仍需作者补充实验或核查文献，不能写成“已完成修改”，应写成：

```text
拟补充 / 待作者确认 / 已提供修改模板
```

---

## 20.4 核心交付物四：作者待确认事项

`04_作者待确认事项.md` 用于集中列出不能由模型直接完成的事项。

例如：

```md
## R2-C002：超算中心节点数量支撑不足

### 需要作者确认

1. 实际选择这些节点的原因；
2. 是否有更多节点数据；
3. 是否可以补充敏感性分析；
4. 是否允许增加一张扩展实验表。

### 模型已提供

- 节点选择依据正文模板；
- 敏感性分析设计；
- 结果表格模板；
- 盲审回复草稿。
```

---

## 20.5 合格输出标准

对于理论、方法、结构类意见，最终输出必须包含：

```text
问题诊断
多位置定位
原文锚点
新增正文或替换正文
同步修改建议
Word 回写动作
盲审回复文本
```

对于数据、实验类意见，最终输出必须包含：

```text
需要作者补充的数据
可新增实验设计
结果表格模板
不编造数值的正文模板
盲审回复文本
```

对于图表类意见，最终输出必须包含：

```text
目标图表
图表问题诊断
图前/表前引导语
caption 修改建议
重绘规范或结构草案
Word 批注动作
盲审回复文本
```

对于参考文献类意见，最终输出必须包含：

```text
被点名文献编号
当前条目摘录
缺失字段
检索关键词
格式修改模板
盲审回复文本
```

---

## 20.6 不合格输出示例

以下输出视为不合格：

```text
建议补充经济学解释。
建议加强模型论证。
建议完善实验设计。
建议统一图表格式。
建议核查参考文献。
```

除非后面同时给出：

```text
具体修改位置
原文锚点
可直接写入的正文
图表调整方案
实验补充模板
参考文献核查字段
Word 回写动作
盲审回复文本
```

---

## 20.7 最终完成状态

Skill 运行完成后，聊天窗口只输出简短总结，例如：

```md
已完成盲审论文修改包生成。

本次共解析 13 条意见：

- 可直接给出正文修改：X 条
- 需要作者补充数据/实验：X 条
- 图表/格式类：X 条
- 参考文献核查类：X 条

主要输出：

1. 逐条意见修改包：outputs/02_逐条意见修改包.md
2. 盲审回复表：outputs/03_盲审回复表.md
3. 作者待确认事项：outputs/04_作者待确认事项.md
4. 修改建议版 Word：outputs/05_修改建议版.docx

其中 X 条意见需要作者确认后才能写成“已完成修改”，已单独列入待确认事项。
```

---

## 20.8 最终目标总结

本 Skill 最终要交付一个能直接指导作者改论文、能回写 Word、能生成盲审回复、能区分可代写与需作者确认事项的完整修改包。

它不是一个普通总结报告，而是一个由以下内容组成的可执行修改系统：

```text
问题诊断
证据定位
正文级修改
图表/表格/公式调整
实验与数据补充模板
参考文献核查任务
Word 回写动作
盲审回复文本
作者待确认清单
```
