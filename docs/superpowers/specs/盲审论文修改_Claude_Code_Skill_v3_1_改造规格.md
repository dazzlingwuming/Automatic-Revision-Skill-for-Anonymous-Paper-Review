# 盲审论文修改 Claude Code Skill v3.1 改造规格

> 目标读者：终端 Codex / Claude Code 项目实现者  
> 版本：v3.1  
> 核心改造：结构化论文解析、多模态图表证据、全文压缩上下文、多位置映射、正文级修改建议

---

## 0. 本次改造要解决的问题

当前版本生成的修改报告存在以下问题：

1. **PDF 切分过于机械**：不能再按固定字符数切割论文。固定长度 chunk 会切断章节、段落、公式、图表和上下文，导致后续定位不准。
2. **每条意见只对应一个 chunk**：盲审意见常常跨章节、跨模型、跨实验、跨结论。每条意见必须支持多个相关位置，而不是 top-1 chunk。
3. **上下文供给不足**：revision-planner 不能只看到一个局部片段。每个子代理应看到全文压缩摘要、章节树、相关章节完整原文、相关图表/公式/表格、相关前后文。
4. **图表没有进入上下文**：PDF 中的图、表、公式、页面截图都应作为 evidence asset 被提取、编号、挂到章节树上，并按需发送给子代理。
5. **修改建议过空**：禁止只输出“建议补充”“建议加强”“建议说明”。重点修改意见必须输出可直接放入论文的新增/替换正文、插入位置、原文定位锚点和评审回复。

---

## 1. 新总体架构

```text
输入文件
  ├── paper.pdf / paper.docx
  └── review.pdf / review.docx / review.txt

      ↓

Paper Ingestion Layer
  ├── 文本提取
  ├── Markdown 标准化
  ├── 章节树构建
  ├── 段落 / 公式 / 图题 / 表题 block 提取
  ├── 图片 / 表格 / 页面区域 asset 提取
  └── 全文压缩摘要与章节摘要生成

      ↓

Review Parsing Layer
  └── 盲审意见结构化拆分

      ↓

Mapping Layer
  ├── 多位置候选召回
  ├── 章节级 / 段落级 / 图表级证据选择
  └── 每条意见生成 context_bundle

      ↓

Revision Planning Layer
  └── 每条意见一个 revision-planner 子代理
      输出正文级修改方案

      ↓

Quality Audit Layer
  ├── 检查是否编造数据、实验、引用
  ├── 检查是否有具体正文
  ├── 检查是否绑定证据位置
  └── 检查是否只输出泛泛建议

      ↓

Report Writer Layer
  ├── 修改报告.md
  ├── 盲审回应表.md / docx
  ├── 待作者补充清单.md
  └── 可选：标注版 PDF / 修改建议版 DOCX
```

---

## 2. 新目录结构

```text
thesis-blind-review-revision/
├── .claude/
│   ├── skills/
│   │   └── thesis-review-revision/
│   │       ├── SKILL.md
│   │       ├── schemas/
│   │       │   ├── paper_blocks.schema.json
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
│       ├── paper-structure-analyzer.md
│       ├── section-summarizer.md
│       ├── multi-location-mapper.md
│       ├── context-bundle-reviewer.md
│       ├── revision-planner.md
│       ├── visual-table-reviewer.md
│       ├── quality-auditor.md
│       └── response-writer.md
│
├── scripts/
│   ├── ingest_paper.py
│   ├── extract_pdf_blocks.py
│   ├── extract_docx_blocks.py
│   ├── normalize_to_markdown.py
│   ├── build_section_tree.py
│   ├── extract_visual_assets.py
│   ├── extract_tables.py
│   ├── crop_pdf_regions.py
│   ├── build_asset_catalog.py
│   ├── build_context_bundle.py
│   ├── validate_json.py
│   ├── render_report.py
│   └── patch_docx_suggestions.py
│
├── src/
│   ├── models.py
│   ├── ingestion/
│   │   ├── pdf_blocks.py
│   │   ├── docx_blocks.py
│   │   ├── markdown_normalizer.py
│   │   ├── section_tree.py
│   │   ├── assets.py
│   │   └── tables.py
│   ├── retrieval/
│   │   ├── candidate_recall.py
│   │   ├── section_ranker.py
│   │   ├── asset_ranker.py
│   │   └── context_bundle.py
│   ├── reporting/
│   │   ├── report_renderer.py
│   │   └── response_table.py
│   └── utils/
│       ├── text.py
│       ├── jsonio.py
│       └── paths.py
│
└── tests/
    ├── test_section_tree.py
    ├── test_asset_catalog.py
    ├── test_context_bundle.py
    ├── test_multi_location_mapping.py
    ├── test_revision_plan_schema.py
    └── test_report_quality.py
```

---

## 3. Paper Ingestion Layer

### 3.1 输入优先级

```text
DOCX > LaTeX source > PDF > TXT
```

如果用户同时提供 DOCX 和 PDF：

- DOCX 用于正文结构、段落、标题、表格；
- PDF 用于页码、图像、页面截图和位置标注；
- 两者通过标题、段落文本相似度和页码估计对齐。

如果只有 PDF，则从 PDF 中重建近似结构。

### 3.2 禁止固定字符切分

禁止逻辑：

```python
chunks = split_text_every_n_chars(text, 1000)
```

必须改成结构化切分：

```text
Heading → Section
Paragraph → Atomic Block
Formula → Formula Block
Figure Caption → Figure Asset
Table Caption → Table Asset
Reference Item → Reference Block
```

### 3.3 paper_blocks.json

每个 block 是论文的最小语义单位。

```json
{
  "blocks": [
    {
      "block_id": "b_000321",
      "type": "heading",
      "text": "4.2.1 面向算力规划的多区域CGE模型构建",
      "page": 51,
      "bbox": [72, 88, 520, 112],
      "section_id": "sec_4_2_1",
      "section_path": ["第四章", "4.2", "4.2.1"],
      "order": 321
    },
    {
      "block_id": "b_000322",
      "type": "paragraph",
      "text": "本文构建多区域CGE模型...",
      "page": 51,
      "bbox": [72, 120, 520, 190],
      "section_id": "sec_4_2_1",
      "section_path": ["第四章", "4.2", "4.2.1"],
      "order": 322
    }
  ]
}
```

`type` 允许值：

```text
heading
paragraph
formula
figure_caption
table_caption
reference_item
footnote
list_item
unknown
```

### 3.4 paper_structure.json

章节树不是 chunk 列表，而是论文结构骨架。

```json
{
  "paper_title": "xxx",
  "total_pages": 88,
  "sections": [
    {
      "section_id": "sec_4",
      "level": 1,
      "title": "第四章 面向算力规划的CGE模型与宏观评估",
      "page_start": 49,
      "page_end": 74,
      "parent": null,
      "children": ["sec_4_1", "sec_4_2", "sec_4_3", "sec_4_4", "sec_4_5"],
      "blocks": ["b_000900", "b_000901"],
      "figures": [],
      "tables": [],
      "formulas": []
    },
    {
      "section_id": "sec_4_2_1",
      "level": 3,
      "title": "4.2.1 面向算力规划的多区域CGE模型构建",
      "page_start": 51,
      "page_end": 52,
      "parent": "sec_4_2",
      "children": [],
      "blocks": ["b_000321", "b_000322", "b_000323"],
      "figures": [],
      "tables": [],
      "formulas": ["eq_4_1", "eq_4_2"]
    }
  ]
}
```

### 3.5 paper.md

同时生成整篇论文的 Markdown 版本，便于调试和人工审查。

要求：

1. 保留章节标题层级。
2. 保留图题、表题、公式编号。
3. 表格尽量转为 Markdown。
4. 对无法解析的图片位置插入占位符。

---

## 4. 图表与多模态证据提取

### 4.1 设计目标

论文中的图、表、公式、页面区域不是附属信息，而是独立证据。它们必须进入：

1. `asset_catalog.json`
2. `paper_structure.json`
3. 每条相关意见的 `context_bundle`

### 4.2 视觉资产类型

```text
figure        普通图、流程图、结构图、折线图、柱状图等
table         表格
formula       公式
page_region   页面局部截图
page_image    整页截图
```

### 4.3 asset_catalog.json

```json
{
  "assets": [
    {
      "asset_id": "fig_3_2",
      "asset_type": "figure",
      "label": "图3.2",
      "caption": "基于贝叶斯优化的混合MILP求解算法流程图",
      "page": 29,
      "section_id": "sec_3_4",
      "section_title": "3.4 基于贝叶斯优化的混合MILP求解算法",
      "bbox": [72, 130, 520, 640],
      "image_path": "workdir/assets/figures/fig_3_2.png",
      "markdown_path": null,
      "csv_path": null,
      "nearby_text_before": "为提高模型求解效率，本文设计了如下求解流程。",
      "nearby_text_after": "该流程首先初始化MILP模型参数...",
      "extraction_method": "caption_region_crop",
      "quality": {
        "has_caption": true,
        "has_preceding_intro": true,
        "parse_confidence": 0.78,
        "needs_manual_check": false
      }
    },
    {
      "asset_id": "tab_3_1",
      "asset_type": "table",
      "label": "表3.1",
      "caption": "实验参数设置",
      "page": 31,
      "section_id": "sec_3_5_1",
      "section_title": "3.5.1 实验设置",
      "bbox": [60, 210, 540, 610],
      "image_path": "workdir/assets/tables/tab_3_1.png",
      "markdown_path": "workdir/assets/tables/tab_3_1.md",
      "csv_path": "workdir/assets/tables/tab_3_1.csv",
      "nearby_text_before": "实验参数设置如表3.1所示。",
      "nearby_text_after": "基于上述参数，本文开展对比实验。",
      "extraction_method": "pymupdf_find_tables",
      "quality": {
        "has_caption": true,
        "has_preceding_intro": true,
        "parse_confidence": 0.86,
        "needs_manual_check": false
      }
    }
  ]
}
```

### 4.4 图片提取策略

实现 `scripts/extract_visual_assets.py`。

MVP 策略：

1. 用 PyMuPDF 渲染每页为 PNG：
   - `workdir/assets/pages/page_029.png`
2. 正则识别图题：
   - `图3.2`
   - `图 3.2`
   - `图3-2`
   - `Fig. 3.2`
3. 根据图题位置向上或向下裁剪页面区域。
4. 保存为：
   - `workdir/assets/figures/fig_3_2.png`
5. 记录 caption、page、bbox、section_id、前后文。
6. 如果无法判断图的区域，保存整页截图并标记：
   - `needs_manual_check: true`

注意：

- 不要只用 `page.get_images()`，因为流程图、框图可能是 PDF 矢量对象，不是嵌入式图片。
- 优先 caption-region crop。
- 如果发现嵌入图片，也可以保存，但不能依赖它覆盖全部图。

### 4.5 表格提取策略

实现 `scripts/extract_tables.py`。

MVP 策略：

1. 优先用 PyMuPDF `page.find_tables()`。
2. 失败则用 pdfplumber fallback。
3. 每个表格输出：
   - Markdown
   - CSV
   - PNG 截图
   - caption
   - nearby_text_before
   - nearby_text_after
4. 如果表格结构复杂、合并单元格严重或置信度低，标记：
   - `needs_manual_check: true`

输出：

```text
workdir/assets/tables/
├── tab_3_1.md
├── tab_3_1.csv
└── tab_3_1.png
```

### 4.6 图表前后文检测

对每个图表 asset，必须记录：

```json
{
  "nearby_text_before": "...",
  "nearby_text_after": "...",
  "has_preceding_intro": true,
  "intro_sentence": "实验结果如图3.8所示。",
  "asset_after_heading_without_intro": false
}
```

这用于处理：

- “标题下直接展示图”
- “图表引出句应在图表之前”
- “表格也是如此”

---

## 5. 章节摘要与全文压缩上下文

### 5.1 新增 section-summarizer 子代理

新增 `.claude/agents/section-summarizer.md`。

职责：

1. 读取 `paper_structure.json` 和每个 section 的 Markdown。
2. 为每个章节/小节生成摘要。
3. 提取关键模型、变量、实验、结论、图表。
4. 生成 `section_summaries.json` 和 `paper_brief.md`。

### 5.2 section_summaries.json

```json
{
  "sections": [
    {
      "section_id": "sec_4_2_1",
      "title": "4.2.1 面向算力规划的多区域CGE模型构建",
      "level": 3,
      "page_range": "51-52",
      "summary_short": "本节构建多区域CGE模型，并将算力服务纳入生产结构。",
      "summary_detailed": "本节首先说明多区域CGE模型的基本结构，然后在生产模块中引入算力服务变量...",
      "key_claims": [
        "算力服务进入生产模块",
        "生产函数采用CES结构",
        "模型用于刻画算力资源对区域经济和能源环境的影响"
      ],
      "key_terms": ["CGE", "CES", "算力服务", "资本", "劳动", "能源"],
      "related_assets": ["eq_4_1", "eq_4_2"],
      "potential_review_topics": [
        "理论基础",
        "生产要素替代关系",
        "模型设定解释"
      ]
    }
  ]
}
```

### 5.3 paper_brief.md

每个 revision-planner 默认都要拿到 `paper_brief.md`。

结构：

```md
# 论文压缩上下文

## 论文主题
...

## 研究问题
...

## 方法体系
- 微观优化模型：...
- 宏观评估模型：...
- 两者关系：...

## 章节结构
- 第一章：...
- 第二章：...
- 第三章：...
- 第四章：...
- 第五章：...

## 核心变量与模型
...

## 主要实验与验证
...

## 结论与创新点
...

## 图表目录摘要
- 图3.2：...
- 图3.8：...
- 表3.1：...
```

---

## 6. 多位置映射

### 6.1 替换 comment-mapper 为 multi-location-mapper

原来每条意见输出一个 `related_section` 和一个 `chunk`，必须废弃。

新输出必须支持：

```text
core_revision_location      正文主要修改位置
supporting_context          辅助理解位置
consistency_update_location  需要同步修改的位置
visual_or_table_asset        图表证据
author_input_location        需要作者补材料的位置
```

### 6.2 comment_mappings.json

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
          "page_range": "51-52",
          "reason": "评审意见要求解释CGE模型中算力与传统要素的替代关系，本节是CGE生产模块核心位置。",
          "include_mode": "full_text",
          "confidence": 0.92
        },
        {
          "role": "supporting_context",
          "section_id": "sec_1_3",
          "title": "1.3 研究内容与创新点",
          "page_range": "5-7",
          "reason": "如论文创新点中提到算力资源配置或模型贡献，应与第四章补充内容保持一致。",
          "include_mode": "full_text",
          "confidence": 0.78
        },
        {
          "role": "consistency_update_location",
          "section_id": "sec_5_1",
          "title": "5.1 研究结论",
          "page_range": "75-76",
          "reason": "结论中需要同步强化算力作为生产要素的经济学含义。",
          "include_mode": "summary_plus_target_paragraphs",
          "confidence": 0.74
        }
      ],
      "assets": [],
      "requires_author_input": false,
      "confidence": 0.86
    }
  ]
}
```

### 6.3 候选召回规则

不能只取 top-1。

实现 `src/retrieval/candidate_recall.py`：

1. 对每条评审意见，召回候选：
   - 标题匹配；
   - 关键词匹配；
   - section summary 匹配；
   - 图表 caption 匹配；
   - 公式编号 / 图号 / 表号匹配；
   - 全文主题相关性。
2. 初始候选数量：
   - sections: top 20
   - blocks: top 50
   - assets: top 20
3. 交给 `multi-location-mapper` 精排。
4. 最终保留：
   - core locations: 1-3
   - supporting locations: 2-8
   - consistency locations: 0-3
   - assets: 按需。

---

## 7. Context Bundle

### 7.1 设计目标

每条意见的子代理输入不是“一个 chunk”，而是一个完整上下文包。

上下文包包含：

1. 评审意见；
2. 全文压缩上下文；
3. 章节摘要；
4. 多个相关位置；
5. 相关完整原文；
6. 相关图表/表格/公式；
7. 输出要求。

### 7.2 context_bundle schema

```json
{
  "comment_id": "R1-C001",
  "comment": {
    "original_text": "...",
    "category": "理论基础",
    "severity": "重点修改",
    "action_type": "补充理论解释"
  },
  "paper_brief": {
    "path": "workdir/paper/paper_brief.md",
    "inline_summary": "..."
  },
  "global_outline": [
    {
      "section_id": "sec_1",
      "title": "第一章 绪论",
      "summary_short": "..."
    }
  ],
  "evidence_pack": {
    "must_read_full_text": [
      {
        "section_id": "sec_4_2_1",
        "title": "4.2.1 面向算力规划的多区域CGE模型构建",
        "page_range": "51-52",
        "text_path": "workdir/paper/sections/sec_4_2_1.md",
        "reason": "核心修改位置"
      }
    ],
    "also_read_full_text": [
      {
        "section_id": "sec_1_3",
        "title": "1.3 研究内容与创新点",
        "page_range": "5-7",
        "text_path": "workdir/paper/sections/sec_1_3.md",
        "reason": "同步检查创新点表述"
      }
    ],
    "summary_only_sections": [
      {
        "section_id": "sec_2",
        "title": "第二章 文献综述",
        "summary_detailed": "..."
      }
    ],
    "formulas": [
      {
        "asset_id": "eq_4_1",
        "label": "公式4.1",
        "text": "...",
        "section_id": "sec_4_2_1"
      }
    ],
    "visual_assets": [
      {
        "asset_id": "fig_3_2",
        "label": "图3.2",
        "caption": "...",
        "image_path": "workdir/assets/figures/fig_3_2.png",
        "nearby_text_before": "...",
        "nearby_text_after": "...",
        "inspection_task": "检查图元和线条规范性"
      }
    ],
    "table_assets": [
      {
        "asset_id": "tab_3_1",
        "label": "表3.1",
        "caption": "...",
        "markdown_path": "workdir/assets/tables/tab_3_1.md",
        "csv_path": "workdir/assets/tables/tab_3_1.csv",
        "image_path": "workdir/assets/tables/tab_3_1.png"
      }
    ]
  },
  "output_contract": {
    "must_include_insert_position": true,
    "must_include_anchor_text": true,
    "must_include_new_or_revised_text": true,
    "must_include_reviewer_response": true,
    "forbidden_generic_advice": true
  }
}
```

### 7.3 context_bundle 组装规则

实现 `scripts/build_context_bundle.py`。

规则：

1. 每个 bundle 都包含 `paper_brief.md`。
2. `core_revision_location` 必须全文提供。
3. `supporting_context` 根据长度决定：
   - 短小节：全文提供；
   - 长章节：提供详细摘要 + 目标段落。
4. `consistency_update_location` 至少提供摘要，必要时提供目标段落。
5. 图表类意见必须包含目标 asset。
6. 表格类意见必须同时提供 Markdown/CSV/PNG。
7. 如果意见明确提到图号/表号/页码，必须强制召回对应 asset 或页面截图。
8. 如果无法找到对应位置，标记：
   - `mapping_type: uncertain`
   - `needs_human_location_check: true`

---

## 8. Revision Planner 新标准

### 8.1 废弃泛泛建议

禁止输出：

```text
建议补充相关说明
建议加强论证
建议完善实验设计
建议统一格式
建议增加经济学解释
```

除非后面紧跟具体正文、插入位置和原文锚点。

### 8.2 revision_plan.json

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
        "section_title": "4.2.1 面向算力规划的多区域CGE模型构建",
        "page_range": "51-52"
      },
      "anchor_text": "定位到原文中介绍CES生产函数或算力服务变量进入生产模块的段落之后。",
      "original_text": "",
      "new_text": "在本文的CGE生产模块中，算力服务并非被视为完全独立于传统生产要素之外的外生变量，而是作为数字化生产条件下能够改变资本、劳动和能源配置效率的新型投入要素纳入生产结构。具体而言，算力服务一方面可以通过提升数据处理、任务调度和资源配置效率，对部分重复性劳动和传统管理投入形成替代效应；另一方面，算力服务的使用依赖服务器、网络设备、数据中心基础设施以及稳定能源供给，因此又与资本投入和能源投入表现出较强的互补关系。基于这一特征，本文采用CES嵌套结构刻画算力服务与传统要素之间的有限替代关系，而非假定二者可以完全替代。该设定意味着，在给定替代弹性的条件下，算力服务投入增加能够在一定程度上降低单位产出对部分传统要素的需求，但其作用受到资本设备、能源成本和产业结构条件的约束。当区域电价、碳成本或资本存量条件发生变化时，算力服务对经济产出的边际贡献也会随之调整。因此，将算力服务嵌入CGE生产模块，可以更合理地反映算力基础设施建设对区域经济增长、能源消耗和碳排放之间联动关系的影响。",
      "rationale": "该段直接回应评审专家关于算力与资本、劳动力替代关系缺乏讨论的问题，并解释CES嵌套结构的经济学含义。",
      "requires_author_input": false
    }
  ],
  "reviewer_response": "感谢专家意见。针对算力与资本、劳动力等传统要素替代关系讨论不足的问题，本文已在第4.2.1节生产模块构建部分补充算力服务进入CGE模型的经济学解释，说明算力服务与劳动投入之间可能存在部分替代关系，同时与资本设备、能源供给和数据中心基础设施存在互补关系，并进一步解释本文采用CES嵌套结构刻画有限替代关系的原因。",
  "author_input_needed": [],
  "risks": [],
  "confidence": 0.84
}
```

### 8.3 revision_status 允许值

```text
text_ready              可直接给出新增/替换正文
text_ready_with_caveat  可给正文，但需要作者核对细节
needs_author_input      需要真实实验、数据、图源文件或文献核查
visual_redraw_needed    需要重绘图，但可以给出重绘规范和图前说明
format_fix_ready        格式类问题，可给具体检查/修改清单
explain_only            只能解释原因，不能代写
not_applicable          意见与论文内容不匹配
```

### 8.4 对不同意见类型的输出要求

#### 理论基础 / 方法设计 / 结构逻辑

必须输出：

1. 插入或替换位置；
2. 原文锚点；
3. 新增正文或替换正文；
4. 与评审意见的对应关系；
5. 评审回复。

#### 数据实验

如果没有真实数据，不能编造实验结果。必须输出：

1. 作者需要补充的数据；
2. 可新增的小节结构；
3. 实验设计模板；
4. 结果表格模板；
5. 不带具体虚假数值的正文模板；
6. 评审回复草稿。

#### 图表规范

必须输出：

1. 目标图/表；
2. 前后文是否需要调整；
3. 图前引导句；
4. caption 修改建议；
5. 如果要重绘，给重绘规范；
6. 如可行，给 Mermaid / Graphviz / 伪流程图结构。

#### 参考文献

不能编造 DOI、期刊、卷期页码。必须输出：

1. 需要核查的文献编号；
2. 现有条目摘录；
3. 需要补全字段；
4. 检索关键词；
5. 格式统一规则；
6. 评审回复草稿。

---

## 9. 图表类意见处理示例

### 9.1 图3.2 重绘

```json
{
  "comment_id": "R2-C007",
  "revision_status": "visual_redraw_needed",
  "actions": [
    {
      "action_id": "A1",
      "type": "redraw_figure",
      "target": {
        "asset_id": "fig_3_2",
        "section_id": "sec_3_4",
        "page_range": "29"
      },
      "visual_diagnosis": [
        "判断条件应统一使用菱形图元",
        "处理步骤应统一使用矩形图元",
        "开始/结束应统一使用圆角矩形或椭圆",
        "箭头方向应保持自上而下或自左向右",
        "是/否分支需要在线条旁明确标注",
        "避免交叉线，必要时重新布局"
      ],
      "redraw_spec": {
        "nodes": [
          {"id": "start", "type": "terminator", "text": "开始"},
          {"id": "init", "type": "process", "text": "初始化模型参数"},
          {"id": "bayes", "type": "process", "text": "贝叶斯优化生成候选参数"},
          {"id": "milp", "type": "process", "text": "求解 MILP 模型"},
          {"id": "check", "type": "decision", "text": "是否满足收敛条件？"},
          {"id": "output", "type": "process", "text": "输出最优调度方案"},
          {"id": "end", "type": "terminator", "text": "结束"}
        ],
        "edges": [
          ["start", "init"],
          ["init", "bayes"],
          ["bayes", "milp"],
          ["milp", "check"],
          ["check", "output", "是"],
          ["check", "bayes", "否"],
          ["output", "end"]
        ]
      },
      "new_intro_text": "基于上述求解思路，本文将贝叶斯优化与MILP模型求解过程整理为图3.2所示的混合求解流程。该流程首先初始化模型参数，并通过贝叶斯优化生成候选参数组合，随后调用MILP模型进行调度求解，最终根据收敛条件判断是否继续迭代。",
      "caption_suggestion": "图3.2 基于贝叶斯优化的混合MILP求解流程",
      "requires_author_input": true,
      "author_input_reason": "需要作者根据原始图源文件或绘图工具重新绘制图像。"
    }
  ],
  "reviewer_response": "感谢专家意见。本文已重新规范图3.2的流程图表达方式，统一判断条件、处理步骤和起止节点的图元样式，并调整箭头方向和分支线条标注，使流程图表达更加清晰规范。"
}
```

### 9.2 图前引导句

```json
{
  "comment_id": "R1-C003",
  "revision_status": "text_ready",
  "actions": [
    {
      "action_id": "A1",
      "type": "insert_before_asset",
      "target": {
        "asset_id": "fig_3_8",
        "section_id": "sec_3_5_4",
        "page_range": "42"
      },
      "anchor_text": "定位到图3.8之前，尤其是若图3.8紧跟在3.5.4标题之后，应在标题与图之间插入下列文字。",
      "new_text": "为进一步比较不同调度策略在成本、能耗和服务质量约束下的优化效果，本文对各方案的综合表现进行对比分析。图3.8展示了不同场景下模型优化结果的变化情况，可以看出本文方法在综合成本控制和约束满足方面具有较好的稳定性。",
      "caption_suggestion": "保持原图题；如原图题过短，可调整为“图3.8 不同场景下优化结果对比”。",
      "requires_author_input": false
    }
  ],
  "reviewer_response": "感谢专家意见。本文已调整图3.8前后的图文顺序，在图3.8出现前增加结果分析引导语，避免章节标题下直接展示图件。"
}
```

---

## 10. Quality Auditor 强制规则

### 10.1 必须检查的失败模式

`quality-auditor` 必须拦截以下输出：

1. 只有“建议补充”但没有新增正文；
2. 只有“建议完善实验”但没有实验设计模板；
3. 没有 section_id/page_range/asset_id；
4. 编造实验结果或数据；
5. 编造参考文献；
6. 图表类意见没有读取或引用 asset；
7. 把“拟修改”写成“已修改”但没有正文证据；
8. 只对应一个位置，但意见明显跨章节；
9. 把需要作者确认的内容标成已完成；
10. 评审回复过短或没有具体动作。

### 10.2 quality_audit.json

```json
{
  "passed": false,
  "issues": [
    {
      "comment_id": "R1-C001",
      "severity": "blocker",
      "problem": "修改方案只有泛泛建议，没有提供可直接放入论文的新正文。",
      "required_fix": "revision-planner 必须输出 new_text，且不少于 150 个中文字符。"
    },
    {
      "comment_id": "R2-C007",
      "severity": "blocker",
      "problem": "图3.2意见未包含 fig_3_2 visual asset。",
      "required_fix": "重新构建 context_bundle，加入 fig_3_2.png、caption 和前后文。"
    }
  ]
}
```

---

## 11. Report Writer 新要求

报告不能再只显示“修改思路”。每条意见必须显示：

```md
### R1-C001

#### 评审意见
...

#### 定位依据
- 核心修改位置：...
- 辅助参考位置：...
- 同步修改位置：...

#### 具体修改 1：新增正文
- 插入位置：
- 原文锚点：
- 新增正文：

> ...

#### 具体修改 2：同步调整
- 修改位置：
- 修改前：
- 修改后：

#### 给评审专家的回复
> ...

#### 是否需要作者补充
无 / 需要补充...
```

如果是图表类意见：

```md
#### 目标图表
- 图3.2：...
- 图片路径：...

#### 图表问题诊断
...

#### 重绘/调整方案
...

#### 图前引导句
> ...
```

---

## 12. SKILL.md 需要更新的核心规则

将以下规则加入 `.claude/skills/thesis-review-revision/SKILL.md`：

```md
## Non-negotiable rules

1. Do not split thesis text by fixed character count.
2. Always build a section tree from headings, paragraphs, formulas, figures, and tables.
3. Every review comment must be mapped to multiple possible locations unless it is clearly local.
4. Every revision-planner call must receive:
   - paper brief;
   - global outline;
   - full text of core revision sections;
   - summaries of non-core sections;
   - relevant formulas, figures, and tables.
5. Figure/table comments must include visual/table assets in the context bundle.
6. Do not output generic advice only.
7. For substantive comments, provide concrete insert/rewrite text.
8. For experimental comments, do not invent results; provide experiment design and author-input checklist.
9. For reference comments, do not invent bibliographic details.
10. All outputs must be JSON-valid before report rendering.
```

---

## 13. 新增 / 更新 Agent 文件

### 13.1 paper-structure-analyzer.md

职责：

- 审查 `paper_structure.json` 是否合理；
- 检查章节树是否有断裂；
- 检查标题层级是否错判；
- 检查图表是否挂到正确章节。

输出：

```json
{
  "structure_ok": true,
  "issues": [],
  "fix_suggestions": []
}
```

### 13.2 section-summarizer.md

职责：

- 为每个章节生成 short/detailed summary；
- 提取关键 claims；
- 提取潜在评审主题；
- 生成 paper_brief.md。

### 13.3 multi-location-mapper.md

职责：

- 对每条意见寻找所有相关位置；
- 区分 core/support/consistency/asset；
- 不允许只返回一个位置，除非给出充分理由。

### 13.4 context-bundle-reviewer.md

职责：

在调用 revision-planner 前检查 bundle 是否足够。

失败条件：

- 没有 paper brief；
- 没有 core section full text；
- 图表意见没有 asset；
- 数据实验意见没有实验设置/结果相关章节；
- 理论基础意见没有方法章节 + 创新/结论相关章节。

### 13.5 visual-table-reviewer.md

职责：

- 只处理图表类意见；
- 阅读 image_path / table markdown / csv / screenshot；
- 输出图表调整方案；
- 对流程图可输出 Mermaid / Graphviz 结构草稿；
- 对表格可输出修改后的 Markdown 表结构。

### 13.6 revision-planner.md

必须更新为正文级输出，不允许泛泛建议。

### 13.7 quality-auditor.md

必须新增 blocker 规则，阻止低质量报告进入最终输出。

---

## 14. Codex 实现任务清单

### Phase 1：数据模型与目录

- [ ] 更新 `src/models.py`
- [ ] 新增所有 JSON schema
- [ ] 新增 workdir 标准目录创建逻辑
- [ ] 新增 `validate_json.py`

### Phase 2：论文结构化解析

- [ ] 实现 `extract_pdf_blocks.py`
- [ ] 实现 `extract_docx_blocks.py`
- [ ] 实现 `normalize_to_markdown.py`
- [ ] 实现 `build_section_tree.py`
- [ ] 输出 `paper.md`
- [ ] 输出 `paper_blocks.json`
- [ ] 输出 `paper_structure.json`
- [ ] 输出 `sections/*.md`

### Phase 3：图表资产提取

- [ ] 实现每页 PNG 渲染
- [ ] 识别图题 / 表题
- [ ] 裁剪图区域
- [ ] 提取表格为 Markdown / CSV
- [ ] 保存表格截图
- [ ] 生成 `asset_catalog.json`
- [ ] 将 assets 挂到 section tree

### Phase 4：摘要生成

- [ ] 新增 `section-summarizer.md`
- [ ] 生成 `section_summaries.json`
- [ ] 生成 `paper_brief.md`
- [ ] 将图表目录摘要写入 paper brief

### Phase 5：多位置映射

- [ ] 替换旧 comment mapper
- [ ] 实现 `candidate_recall.py`
- [ ] 实现多候选召回
- [ ] 新增 `multi-location-mapper.md`
- [ ] 输出 `comment_mappings.json`

### Phase 6：Context Bundle

- [ ] 实现 `build_context_bundle.py`
- [ ] 每条意见输出一个 bundle
- [ ] 图表类意见必须包含 asset
- [ ] 理论/方法类意见必须包含 core full text + supporting context
- [ ] 新增 `context-bundle-reviewer.md`

### Phase 7：Revision Planner

- [ ] 更新 `revision-planner.md`
- [ ] 更新 `revision_plan.schema.json`
- [ ] 强制输出 `new_text` / `revised_text`
- [ ] 按意见类型输出不同模板
- [ ] 图表类意见走 `visual-table-reviewer`

### Phase 8：Quality Audit

- [ ] 新增 `quality-auditor.md`
- [ ] 实现质量审计规则
- [ ] blocker 不通过时不生成最终报告
- [ ] 对失败意见要求重跑 revision-planner

### Phase 9：Report Writer

- [ ] 更新报告模板
- [ ] 展示定位依据
- [ ] 展示新增/替换正文
- [ ] 展示图表调整方案
- [ ] 展示作者待补充事项
- [ ] 展示评审回复

### Phase 10：测试

- [ ] 测试不再固定字符切分
- [ ] 测试一个意见可映射多个位置
- [ ] 测试图3.2类意见包含图片 asset
- [ ] 测试表格类意见包含 md/csv/png
- [ ] 测试泛泛建议被 quality-auditor 拦截
- [ ] 测试没有 new_text 的重点修改无法进入报告
- [ ] 测试需要作者补充的实验意见不会编造结果

---

## 15. 验收标准

### 15.1 结构验收

通过以下检查：

```text
workdir/paper/paper.md 存在
workdir/paper/paper_structure.json 存在
workdir/paper/section_summaries.json 存在
workdir/assets/asset_catalog.json 存在
workdir/bundles/*.context.json 存在
workdir/revision_plans/*.plan.json 存在
```

### 15.2 映射验收

对于以下类型意见：

```text
理论基础
方法设计
结构逻辑
数据实验
图表规范
参考文献
```

每条意见至少有：

```text
1 个 core_revision_location
1 个 supporting_context 或明确说明不需要
```

图表意见必须有：

```text
asset_id
image_path 或 table markdown/csv/png
nearby_text_before
nearby_text_after
```

### 15.3 输出质量验收

重点修改意见必须包含：

```text
target.section_id
target.page_range
anchor_text
new_text 或 revised_text
rationale
reviewer_response
```

`new_text` 不能少于 150 个中文字符，除非该意见是纯格式类或纯图表重绘类。

### 15.4 禁止输出

最终报告中禁止出现只有以下内容的方案：

```text
建议补充相关说明。
建议加强论证。
建议完善模型解释。
建议统一格式。
建议增加实验。
```

除非后面有具体正文、具体表格模板、具体图表调整方案或具体检查清单。

---

## 16. CLI 建议

新增命令：

```bash
python -m scripts.ingest_paper   --paper workdir/inputs/paper.pdf   --out workdir

python -m scripts.extract_visual_assets   --paper workdir/inputs/paper.pdf   --structure workdir/paper/paper_structure.json   --out workdir/assets

python -m scripts.build_context_bundle   --comment-id R1-C001   --workdir workdir   --out workdir/bundles/R1-C001.context.json

python -m scripts.validate_json   --schema .claude/skills/thesis-review-revision/schemas/context_bundle.schema.json   --json workdir/bundles/R1-C001.context.json
```

---

## 17. 最小可用版本范围

MVP 不需要完美实现所有 PDF 布局理解，但必须做到：

1. 不再按固定字符切分；
2. 能生成章节树；
3. 能生成章节摘要；
4. 每条意见能拿到全文压缩上下文；
5. 每条意见支持多个相关位置；
6. 图表意见能拿到对应截图或页面截图；
7. 修改建议必须给出可直接写入论文的正文。

---

## 18. 给 Codex 的首要实现顺序

请按以下顺序实现，不要先优化报告模板：

```text
1. 数据模型和 workdir 结构
2. paper_blocks + paper_structure
3. asset_catalog
4. section_summaries + paper_brief
5. multi-location mapping
6. context_bundle
7. revision_plan schema + prompt
8. quality_auditor
9. report_writer
```

原因：

```text
报告质量差的根源不在 report_writer，
而在 paper representation、context bundle 和 revision_plan。
```

---

## 19. 迁移旧设计时删除或改写的内容

删除：

```text
- 每 N 字符切 chunk
- 每条意见只传一个 paper_section
- related_section/page_ref/chunk 单位置 schema
- revision-planner 只输出 suggestion_summary
```

替换为：

```text
- section tree
- paper brief
- evidence pack
- multi-location mapping
- visual/table asset catalog
- context bundle
- text-ready revision plan
```

---

## 20. 最终目标

最终报告不应该像这样：

```text
建议在第四章补充经济学解释。
```

而应该像这样：

```text
插入位置：4.2.1 中 CES 生产函数说明之后。

新增正文：
在本文的CGE生产模块中，算力服务并非被视为完全独立于传统生产要素之外的外生变量，而是作为数字化生产条件下能够改变资本、劳动和能源配置效率的新型投入要素纳入生产结构。具体而言，算力服务一方面可以通过提升数据处理、任务调度和资源配置效率，对部分重复性劳动和传统管理投入形成替代效应；另一方面，算力服务的使用依赖服务器、网络设备、数据中心基础设施以及稳定能源供给，因此又与资本投入和能源投入表现出较强的互补关系……
```

这才是本 Skill 应该交付的结果。
