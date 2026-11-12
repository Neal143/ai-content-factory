#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
- Tên file: classify_vault_posts.py
- Last update: 10/11/2026 19:50 (GMT+7)
- Vai trò: Động cơ thực thi chuỗi 4 Skills tuần tự của PostClassifierAgent
  (post-jtbd-calibrator -> post-audience-matcher -> post-ki-product-tagger ->
  post-needs-extractor) qua Antigravity Headless CLI (agy.exe) hoặc qua cờ
  --apply-json cho các bài viết trong thư mục `vault/03-Content/Viral Posts/`.
- Được sử dụng khi nào?:
  1. Tự động chạy ngầm ngay sau khi user bấm "Lưu vào Vault" trên Obsidian.
  2. Khi user bấm nút "Phân loại Audience & Topics (AI)" trên Header Bảng 2.
  3. Khi PostClassifierAgent được kích hoạt trực tiếp trong Antigravity Chat.
- Output:
  1. File Audience .md mới trong vault/01-Atomic/Audiences/ (chuẩn cấu trúc
     audience-structure.md + vivid_circumstances) và cập nhật _audience_index.yaml.
  2. Cập nhật YAML Frontmatter của bài viết trong vault/03-Content/Viral Posts/
     với audience_target, topics (hợp nhất 5 nhóm topic_type sạch, xóa bỏ hoàn toàn
     tags* cũ), post_format, classification_status, classified_at.
  3. Đồng bộ các topics vào personas/<active-persona>/topic_map.yaml kèm topic_type
     (knowledge | insight | needs | product | event) và liên kết belongs_to_audience.
  4. Tự động dọn dẹp các Audience viral_post mồ côi không còn bài viết nào tham chiếu.
- Tóm tắt logic hoạt động:
  Đi qua 5 cổng kiểm soát chất lượng (Poka-Yoke Anti-Garbage Pipeline):
  - Cổng 0: extract_clean_post_body cắt bỏ hoàn toàn bình luận và khối chữ ký cuối bài.
  - Cổng 1 (post-jtbd-calibrator): Phân loại post_format, nếu là noise thì dừng ngay
    (no_jtbd_found: true). Nếu hợp lệ: khóa core_thesis + target_pillar + JTBDs.
  - Cổng 2 (post-audience-matcher): Ưu tiên reuse Audience hiện có, nếu bắt buộc create
    thì khóa parent_audience về Big Audience gốc (không để mồ côi).
  - Cổng 3 (post-ki-product-tagger): Trích xuất ứng viên Topic (knowledge, insight,
    product, event) kèm evidence (ẩn post_author để chống nhận nhầm Fanpage làm product).
    Hậu kiểm Python lọc sạch evidence giả và tên tác giả.
  - Cổng 4 (post-needs-extractor): Tạo tối đa 1 needs ODI chuẩn 4 thành phần và thực hiện
    Semantic Dedup toàn bộ ứng viên với topic_map.yaml trong cùng topic_type.
================================================================================
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Set

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Run: pip install pyyaml")


# ────────────────────────────────────────────────────────────────
# Nhóm 1: JSON Schemas Nội Bộ cho 4 Skills
# ────────────────────────────────────────────────────────────────

CANDIDATE_ITEM_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["label", "sub_type", "evidence"],
    "properties": {
        "label": {"type": "string"},
        "sub_type": {"type": "string"},
        "evidence": {"type": "string"},
    },
}

SKILL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "post-jtbd-calibrator": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["no_jtbd_found", "post_format", "core_thesis", "target_pillar", "calibrated_jtbds"],
        "properties": {
            "no_jtbd_found": {"type": "boolean"},
            "post_format": {
                "type": "string",
                "enum": ["deep_dive", "listicle", "summary", "news", "noise"],
            },
            "core_thesis": {"type": "string"},
            "target_pillar": {"type": "string"},
            "calibrated_jtbds": {
                "type": "array",
                "minItems": 0,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "required": [
                        "audience_Job_performer",
                        "audience_main_job",
                        "audience_circumstance",
                        "aliases",
                        "calibration_reason",
                    ],
                    "properties": {
                        "audience_Job_performer": {"type": "string"},
                        "audience_main_job": {"type": "string"},
                        "audience_circumstance": {"type": "string"},
                        "aliases": {"type": "array", "items": {"type": "string"}},
                        "calibration_reason": {"type": "string"},
                    },
                },
            },
        },
    },
    "post-audience-matcher": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["audiences"],
        "properties": {
            "audiences": {
                "type": "array",
                "minItems": 1,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "required": [
                        "action",
                        "audience_Job_performer",
                        "audience_main_job",
                        "audience_circumstance",
                        "audience_level",
                        "parent_audience",
                        "aliases",
                        "reasoning",
                    ],
                    "properties": {
                        "action": {"type": "string", "enum": ["reuse", "create"]},
                        "matched_file_ref": {"type": "string"},
                        "audience_filename": {"type": "string"},
                        "audience_level": {"type": "string", "enum": ["big", "little", "micro"]},
                        "audience_Job_performer": {"type": "string"},
                        "audience_main_job": {"type": "string"},
                        "audience_circumstance": {"type": "string"},
                        "parent_audience": {"type": "array", "items": {"type": "string"}},
                        "aliases": {"type": "array", "items": {"type": "string"}},
                        "reasoning": {"type": "string"},
                    },
                },
            }
        },
    },
    "post-ki-product-tagger": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
            "knowledge_candidates",
            "insight_candidates",
            "product_candidates",
            "event_candidates",
        ],
        "properties": {
            "knowledge_candidates": {"type": "array", "maxItems": 2, "items": CANDIDATE_ITEM_SCHEMA},
            "insight_candidates": {"type": "array", "maxItems": 2, "items": CANDIDATE_ITEM_SCHEMA},
            "product_candidates": {"type": "array", "maxItems": 1, "items": CANDIDATE_ITEM_SCHEMA},
            "event_candidates": {"type": "array", "maxItems": 1, "items": CANDIDATE_ITEM_SCHEMA},
        },
    },
    "post-needs-extractor": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["resolved_topics"],
        "properties": {
            "resolved_topics": {
                "type": "array",
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "required": [
                        "action",
                        "topic_type",
                        "matched_id",
                        "proposed_id",
                        "label",
                        "evidence",
                        "reasoning",
                    ],
                    "properties": {
                        "action": {"type": "string", "enum": ["reuse", "create"]},
                        "topic_type": {
                            "type": "string",
                            "enum": ["knowledge", "insight", "needs", "product", "event"],
                        },
                        "matched_id": {"type": "string"},
                        "proposed_id": {"type": "string"},
                        "label": {"type": "string"},
                        "evidence": {"type": "string"},
                        "reasoning": {"type": "string"},
                    },
                },
            }
        },
    },
}

VALID_TOPIC_TYPES: Set[str] = {"knowledge", "insight", "needs", "product", "event"}
LEGACY_TAG_KEYS = ("tags", "tags_knowledge", "tags_insight", "tags_product", "tags_needs")

TOPIC_MAP_HEADER = (
    "# BẢN ĐỒ TOPIC\n"
    "# id: English snake_case — dùng cho AI matching, script calls, frontmatter topics\n"
    "# label: Tiếng Việt đầy đủ dấu — dùng hiển thị và lưu trong trường topics của bài viết\n"
    "# topic_type: Phân loại bản chất chủ đề (knowledge | insight | needs | product | event)\n"
)


# ────────────────────────────────────────────────────────────────
# Nhóm 2: Định vị Antigravity CLI (agy.exe) và Cập nhật Tiến trình
# ────────────────────────────────────────────────────────────────

def resolve_agy_executable() -> str:
    """Tìm đường dẫn thực thi nhị phân của Antigravity CLI (agy.exe, tránh dùng .cmd để không bị giới hạn 8191 ký tự của cmd.exe)."""
    user_profile = os.environ.get("USERPROFILE", "")
    candidates = [
        os.path.join(user_profile, ".gemini", "bin", "agy.exe"),
        shutil.which("agy.exe") or "",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError("Không tìm thấy Antigravity CLI (agy.exe) tại ~/.gemini/bin/agy.exe")


def update_live_progress(vault_root: str, message: str, is_running: bool = True) -> None:
    """Cập nhật thông báo tiến trình vào .content-pipeline/fb-tracker-state.json để UI Obsidian hiển thị."""
    state_path = os.path.join(vault_root, ".content-pipeline", "fb-tracker-state.json")
    if not os.path.isfile(state_path):
        return
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        if "status" not in state or not isinstance(state["status"], dict):
            state["status"] = {}
        state["status"]["progress_text"] = message
        state["status"]["classifier_running"] = is_running
        state["status"]["classifier_updated_at"] = datetime.datetime.now().isoformat()
        tmp_path = state_path + ".cls.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, state_path)
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────
# Nhóm 3: Đọc/Ghi YAML Frontmatter của bài viết trong 03-Content/Viral Posts/
# ────────────────────────────────────────────────────────────────

def split_markdown_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Tách YAML Frontmatter và phần thân Markdown của bài viết."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1]) or {}
        if not isinstance(fm, dict):
            fm = {}
    except Exception:
        fm = {}
    return fm, parts[2]


def extract_clean_post_body(body_md: str) -> str:
    """
    Gate 0 (Anti-Garbage): Chỉ lấy phần nội dung chính của bài viết.
    - Cắt bỏ hoàn toàn khối `## 💬 Bình luận thu thập` và `## 📌 Thông tin nguồn`.
    - Lược bỏ header `## 📝 Nội dung bài viết`.
    - Dò dòng thông tin liên hệ (🏠/📍/☎️/✨ Tel/Hotline...) ở 40% cuối bài và lùi ngược
      lên vạch phân cách chữ ký (`───`/`---`/`⸻`) ngay phía trên để cắt sạch khối chữ ký
      mà không cắt nhầm dấu `⸻` ngắt đoạn kết luận.
    - Lọc bỏ các dòng chỉ chứa toàn hashtag.
    """
    cleaned = re.sub(r"<!--[\s\S]*?-->", "", body_md).strip()
    for marker in ("## 💬 Bình luận thu thập", "## 📌 Thông tin nguồn"):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()

    if "## 📝 Nội dung bài viết" in cleaned:
        cleaned = cleaned.split("## 📝 Nội dung bài viết", 1)[1].strip()

    lines = cleaned.splitlines()
    cut_idx = len(lines)
    min_footer_line = max(2, int(len(lines) * 0.60))
    footer_sep_re = re.compile(r"^\s*(?:[─━═\-_*]{3,}|⸻+)\s*$")
    contact_line_re = re.compile(
        r"^\s*(?:📍|☎️|📞|🏡|🏠|🌐|📩|✨\s*Tel|👉\s*Đăng ký|Địa chỉ\s*:|Hotline\s*:|Điện thoại\s*:|Tel\s*[&:]|Zalo\s*:|Liên hệ\s*:|Email\s*:|Website\s*:|Fanpage\s*:)",
        re.IGNORECASE,
    )

    contact_idx: Optional[int] = None
    for i in range(min_footer_line, len(lines)):
        if contact_line_re.match(lines[i]):
            contact_idx = i
            break

    if contact_idx is not None:
        cut_idx = contact_idx
        lookback_start = max(min_footer_line, contact_idx - 5)
        for j in range(contact_idx - 1, lookback_start - 1, -1):
            if footer_sep_re.match(lines[j]):
                between = [ln.strip() for ln in lines[j + 1 : contact_idx] if ln.strip()]
                if all(len(ln) <= 120 for ln in between):
                    cut_idx = j
                    break

    hashtag_line_re = re.compile(r"^\s*(?:#[^\s#]+\s*){2,}$")
    main_lines = [ln for ln in lines[:cut_idx] if not hashtag_line_re.match(ln.strip())]
    while main_lines and (not main_lines[-1].strip() or footer_sep_re.match(main_lines[-1])):
        main_lines.pop()

    return "\n".join(main_lines).strip()[:6000]


def is_in_viral_posts_dir(vault_root: str, file_path: str) -> bool:
    """Đảm bảo file nằm đúng trong thư mục `vault/03-Content/Viral Posts`."""
    viral_dir = os.path.normcase(os.path.abspath(os.path.join(vault_root, "03-Content", "Viral Posts")))
    target_abs = os.path.normcase(os.path.abspath(file_path))
    return target_abs.startswith(viral_dir + os.sep)


def needs_classification(vault_root: str, file_path: str, force: bool = False) -> bool:
    """Kiểm tra file có nằm trong 03-Content/Viral Posts và chưa có đủ audience_target + topics (hoặc còn trường tags* cũ) hay không."""
    if not os.path.isfile(file_path) or not is_in_viral_posts_dir(vault_root, file_path):
        return False
    if force:
        return True
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        fm, _ = split_markdown_frontmatter(content)
        has_legacy_tags = any(k in fm for k in LEGACY_TAG_KEYS)
        if has_legacy_tags:
            return True
        if fm.get("classification_status") == "skipped_no_jtbd":
            return False
        has_aud = isinstance(fm.get("audience_target"), list) and len(fm["audience_target"]) > 0
        has_topics = isinstance(fm.get("topics"), list) and len(fm["topics"]) > 0
        return not (has_aud and has_topics)
    except Exception:
        return False


# ────────────────────────────────────────────────────────────────
# Nhóm 4: Quản lý _audience_index.yaml và Tạo File Audience .md Mới
# ────────────────────────────────────────────────────────────────

def load_audience_index_summary(vault_root: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Đọc danh sách audiences hiện có từ _audience_index.yaml."""
    index_path = os.path.join(vault_root, "01-Atomic", "Audiences", "_audience_index.yaml")
    if not os.path.isfile(index_path):
        return index_path, []
    with open(index_path, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = raw.split("\n")
    body_lines = [l for l in lines if not l.startswith("#")]
    data = yaml.safe_load("\n".join(body_lines)) or {}
    audiences = data.get("audiences", [])
    return index_path, audiences if isinstance(audiences, list) else []


def load_audience_dashboard_template(factory_root: str) -> str:
    """Đọc dashboard template từ book-audience-matcher/references/audience-structure.md (Single Source of Truth)."""
    template_path = os.path.join(
        factory_root,
        ".agents",
        "skills",
        "book-audience-matcher",
        "references",
        "audience-structure.md",
    )
    if os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"## 3\. Khung Dashboard.*?````markdown\n(.*?)````", content, re.DOTALL)
        if match:
            return match.group(1)
    return (
        "# 🎯 [Job_performer] muốn [Main_job] [Circumstance]\n\n"
        "## 🧠 Bức tranh Tâm lý (Insights)\n"
        "*(Khu vực hiển thị tự động toàn bộ Insights đang bám rễ vào tập khách hàng này)*\n"
        "```dataview\n"
        "TABLE insight_type, source_name\n"
        'FROM "01-Atomic/Insights"\n'
        "WHERE contains(belongs_to_audience, this.file.link)\n"
        "```\n\n"
        "## 💊 Kho Giải pháp (Solutions)\n"
        "*(Truy vấn tự động các Solutions/Concepts đang phục vụ Insights thuộc tệp Audience này)*\n"
        "```dataview\n"
        "TABLE knowledge_type, source_name\n"
        'FROM "01-Atomic/Solutions" OR "01-Atomic/Concepts"\n'
        "FLATTEN supports_insight AS si\n"
        "WHERE contains(si.belongs_to_audience, this.file.link)\n"
        "```\n\n"
        "## 📖 Kho Evidences\n"
        "*(Truy vấn tự động các Data-Points, Stories, Quotes liên đới với tệp Audience này)*\n"
        "```dataview\n"
        "TABLE type, source_name\n"
        'FROM "01-Atomic/Data-Points" OR "01-Atomic/Stories" OR "01-Atomic/Quotes"\n'
        "FLATTEN supports_knowledge AS sk\n"
        "FLATTEN sk.supports_insight AS si\n"
        "WHERE contains(si.belongs_to_audience, this.file.link)\n"
        "```\n"
    )


def ensure_new_audience_created(
    vault_root: str,
    aud_item: Dict[str, Any],
    post_title: str,
    post_slug: str,
    post_rel_path: str,
) -> str:
    """Nếu action == 'create', tạo file Audience .md mới và cập nhật _audience_index.yaml chuẩn write_audience_files.py."""
    raw_filename = str(aud_item.get("audience_filename") or "").strip().replace("[[", "").replace("]]", "")
    if raw_filename.endswith(".md"):
        raw_filename = raw_filename[:-3]
    if not raw_filename:
        raise ValueError("Thiếu audience_filename khi action='create'")

    file_ref = f"[[{raw_filename}]]"
    audiences_dir = os.path.join(vault_root, "01-Atomic", "Audiences")
    os.makedirs(audiences_dir, exist_ok=True)
    md_path = os.path.join(audiences_dir, f"{raw_filename}.md")

    index_path, existing_audiences = load_audience_index_summary(vault_root)
    level_by_ref = {str(e.get("file_ref")): str(e.get("audience_level", "little")) for e in existing_audiences}
    root_big_ref = next(
        (str(e.get("file_ref")) for e in existing_audiences if str(e.get("audience_level")) == "big"),
        "",
    )

    parent_list = aud_item.get("parent_audience") or []
    if not isinstance(parent_list, list):
        parent_list = []
    norm_parents: List[str] = []
    for p in parent_list:
        clean_p = str(p).strip().replace("[[", "").replace("]]", "")
        if clean_p:
            ref_candidate = f"[[{clean_p}]]"
            if ref_candidate in level_by_ref and ref_candidate not in norm_parents:
                norm_parents.append(ref_candidate)

    if not norm_parents and root_big_ref:
        norm_parents = [root_big_ref]

    if not norm_parents:
        computed_level = "little"
    else:
        parent_levels = [level_by_ref.get(p, "big") for p in norm_parents]
        if any(lv in ("little", "micro") for lv in parent_levels):
            computed_level = "micro"
        else:
            computed_level = "little"

    performer = str(aud_item.get("audience_Job_performer") or "Độc giả").strip()
    main_job = str(aud_item.get("audience_main_job") or "").strip()
    circumstance = str(aud_item.get("audience_circumstance") or "").strip()
    aliases = aud_item.get("aliases") or [f"{performer} muốn {main_job} ({circumstance})"]

    # 1. Tạo file Audience .md vật lý theo đúng cấu trúc write_audience_files.py
    if not os.path.isfile(md_path):
        fm_data = {
            "audience_level": computed_level,
            "audience_Job_performer": performer,
            "audience_main_job": main_job,
            "audience_circumstance": circumstance,
            "vivid_circumstances": [],
            "vivid_circumstances_reserve": [],
            "parent_audience": norm_parents,
            "next_job_step": [],
            "is_buyer_job": None,
            "aliases": aliases,
            "source_type": "viral_post",
            "source_name": post_title,
            "source_link": f"[[{post_slug}]]",
            "source_path": post_rel_path.replace("\\", "/"),
        }
        fm_yaml = yaml.dump(fm_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        factory_root = os.path.dirname(vault_root)
        dashboard_tpl = load_audience_dashboard_template(factory_root)
        body = (
            dashboard_tpl.replace("[Job_performer]", performer)
            .replace("[Main_job]", main_job)
            .replace("[Circumstance]", circumstance)
        )
        tmp_md = md_path + ".tmp"
        with open(tmp_md, "w", encoding="utf-8") as f:
            f.write(f"--\n{fm_yaml}---\n{body}\n".replace("--\n", "---\n"))
        os.replace(tmp_md, md_path)

    # 2. Cập nhật _audience_index.yaml theo đúng chuẩn write_audience_files.py
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            raw_idx = f.read()
        idx_lines = raw_idx.split("\n")
        header_lines: List[str] = []
        body_start = 0
        for i, line in enumerate(idx_lines):
            if line.startswith("#") or line.strip() == "":
                header_lines.append(line)
                body_start = i + 1
            else:
                break
        header_str = "\n".join(header_lines)
        body_str = "\n".join(idx_lines[body_start:])
        idx_data = yaml.safe_load(body_str) or {}
        aud_list = idx_data.get("audiences", [])
        if not isinstance(aud_list, list):
            aud_list = []
        existing_refs = {str(e.get("file_ref")) for e in aud_list}
        if file_ref not in existing_refs:
            aud_list.append(
                {
                    "file_ref": file_ref,
                    "audience_level": computed_level,
                    "audience_Job_performer": performer,
                    "audience_main_job": main_job,
                    "audience_circumstance": circumstance,
                    "parent_audience": norm_parents,
                    "is_buyer_job": None,
                    "aliases": aliases,
                }
            )
            idx_data["audiences"] = aud_list
            new_body = yaml.dump(idx_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
            tmp_idx = index_path + ".tmp"
            with open(tmp_idx, "w", encoding="utf-8") as f:
                f.write(header_str + "\n" + new_body)
            os.replace(tmp_idx, index_path)

    return file_ref


def cleanup_orphan_viral_post_audiences(vault_root: str, factory_root: str) -> int:
    """
    Quét toàn bộ bài viết trong vault/03-Content/Viral Posts/*.md, thu thập tất cả
    audience_target đang được dùng. Thu hồi và xóa file Audience .md có source_type == 'viral_post'
    nếu không còn bài viết nào tham chiếu (và không có Audience nào khác làm con trỏ tới nó).
    Đồng thời gỡ bỏ khỏi _audience_index.yaml và topic_map.yaml.
    """
    viral_dir = os.path.join(vault_root, "03-Content", "Viral Posts")
    audiences_dir = os.path.join(vault_root, "01-Atomic", "Audiences")
    if not os.path.isdir(viral_dir) or not os.path.isdir(audiences_dir):
        return 0

    referenced_refs: Set[str] = set()
    for root, _, files in os.walk(viral_dir):
        for fn in files:
            if fn.endswith(".md"):
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        c = f.read()
                    fm, _ = split_markdown_frontmatter(c)
                    for a_ref in fm.get("audience_target") or []:
                        s = str(a_ref).strip()
                        if s:
                            referenced_refs.add(s)
                except Exception:
                    pass

    parent_refs: Set[str] = set()
    for root, _, files in os.walk(audiences_dir):
        for fn in files:
            if fn.endswith(".md"):
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        c = f.read()
                    fm, _ = split_markdown_frontmatter(c)
                    for p_ref in fm.get("parent_audience") or []:
                        s = str(p_ref).strip()
                        if s:
                            parent_refs.add(s)
                except Exception:
                    pass

    orphans_removed = 0
    removed_refs: Set[str] = set()

    for fn in os.listdir(audiences_dir):
        if not fn.endswith(".md") or fn == "_audience_index.yaml":
            continue
        fp = os.path.join(audiences_dir, fn)
        try:
            with open(fp, "r", encoding="utf-8") as f:
                c = f.read()
            fm, _ = split_markdown_frontmatter(c)
            if fm.get("source_type") == "viral_post":
                base_ref = f"[[{fn[:-3]}]]"
                if base_ref not in referenced_refs and base_ref not in parent_refs:
                    os.remove(fp)
                    removed_refs.add(base_ref)
                    orphans_removed += 1
        except Exception:
            pass

    if removed_refs:
        index_path = os.path.join(audiences_dir, "_audience_index.yaml")
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    raw_idx = f.read()
                idx_lines = raw_idx.split("\n")
                header_lines: List[str] = []
                body_start = 0
                for i, line in enumerate(idx_lines):
                    if line.startswith("#") or line.strip() == "":
                        header_lines.append(line)
                        body_start = i + 1
                    else:
                        break
                header_str = "\n".join(header_lines)
                body_str = "\n".join(idx_lines[body_start:])
                idx_data = yaml.safe_load(body_str) or {}
                aud_list = idx_data.get("audiences", [])
                if isinstance(aud_list, list):
                    filtered = [a for a in aud_list if str(a.get("file_ref")) not in removed_refs]
                    idx_data["audiences"] = filtered
                    new_body = yaml.dump(idx_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    tmp_idx = index_path + ".tmp"
                    with open(tmp_idx, "w", encoding="utf-8") as f:
                        f.write(header_str + "\n" + new_body)
                    os.replace(tmp_idx, index_path)
            except Exception:
                pass

        # Gỡ bỏ audience mồ côi khỏi topic_map.yaml
        tm_path, _, _ = load_pillars_and_topic_map(factory_root)
        if os.path.isfile(tm_path):
            try:
                with open(tm_path, "r", encoding="utf-8") as f:
                    tm_data = yaml.safe_load(f) or {}
                has_tm_change = False
                for t in tm_data.get("topics", []):
                    auds = t.get("belongs_to_audience", [])
                    new_auds = [a for a in auds if str(a).strip() not in removed_refs]
                    if len(new_auds) != len(auds):
                        t["belongs_to_audience"] = new_auds
                        has_tm_change = True
                if has_tm_change:
                    _write_topic_map_formatted(tm_data, tm_path)
            except Exception:
                pass

    return orphans_removed


# ────────────────────────────────────────────────────────────────
# Nhóm 5: Hàm Gọi 1 Skill Đơn Nhiệm qua Antigravity CLI (agy.exe)
# ────────────────────────────────────────────────────────────────

def run_skill_via_agy(
    agy_exe: str,
    factory_root: str,
    skill_name: str,
    context_payload: str,
    conversation_id: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Đọc SKILL.md duy nhất của skill, gọi agy.exe với cờ -p đặt ở cuối câu lệnh,
    tái sử dụng conversation_id nếu có, và bóc tách JSON từ trường `response`.
    """
    skill_md_path = os.path.join(factory_root, ".agents", "skills", skill_name, "SKILL.md")
    with open(skill_md_path, "r", encoding="utf-8") as f:
        skill_instructions = f.read()

    schema_str = json.dumps(SKILL_SCHEMAS[skill_name], ensure_ascii=False)

    prompt = (
        f"{skill_instructions}\n\n"
        f"================================================================\n"
        f"DỮ LIỆU ĐẦU VÀO CẦN XỬ LÝ:\n"
        f"{context_payload}\n\n"
        f"Không gọi tool bên ngoài. Hãy thực thi đúng nhiệm vụ của Skill `{skill_name}` và chỉ trả về JSON hợp lệ."
    )

    cmd = [
        agy_exe,
        "--output-format",
        "json",
        "--json-schema",
        schema_str,
        "--effort",
        "low",
        "--disable-slash-commands",
        "--dangerously-skip-permissions",
    ]
    if conversation_id:
        cmd.extend(["--conversation", conversation_id])
    # Đặt cờ `-p` kèm prompt ở cuối cùng
    cmd.extend(["-p", prompt])

    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        proc = subprocess.run(
            cmd,
            cwd=factory_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            startupinfo=startupinfo,
        )
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] agy.exe skill {skill_name} vuot qua 300s.")
        return None, conversation_id
    except Exception as e:
        print(f"[ERROR] agy.exe skill {skill_name} gap loi: {e}")
        return None, conversation_id

    raw_out = (proc.stdout or "").strip()
    if not raw_out:
        return None, conversation_id

    new_conv_id = conversation_id
    try:
        envelope = json.loads(raw_out)
        if isinstance(envelope, dict):
            if envelope.get("conversation_id"):
                new_conv_id = str(envelope["conversation_id"])
            for field_key in ("response", "structured_output", "result"):
                if field_key in envelope and envelope[field_key] is not None:
                    val = envelope[field_key]
                    if isinstance(val, dict):
                        return val, new_conv_id
                    if isinstance(val, str):
                        val_clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", val.strip())
                        try:
                            return json.loads(val_clean), new_conv_id
                        except Exception:
                            m_inner = re.search(r"\{[\s\S]*\}", val_clean)
                            if m_inner:
                                return json.loads(m_inner.group(0)), new_conv_id
            if any(
                k in envelope
                for k in (
                    "calibrated_jtbds",
                    "no_jtbd_found",
                    "audiences",
                    "knowledge_candidates",
                    "resolved_topics",
                )
            ):
                return envelope, new_conv_id
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", raw_out)
    if match:
        try:
            return json.loads(match.group(0)), new_conv_id
        except Exception:
            pass
    return None, new_conv_id


# ────────────────────────────────────────────────────────────────
# Nhóm 5.5: Quản lý topic_map.yaml & Kiểm định Cơ học Poka-Yoke
# ────────────────────────────────────────────────────────────────

def resolve_active_persona_dir(factory_root: str) -> str:
    """Tìm thư mục persona hoạt động (ưu tiên vuon-ong-steiner hoặc persona có topic_map.yaml)."""
    personas_dir = os.path.join(factory_root, "personas")
    candidate = os.path.join(personas_dir, "vuon-ong-steiner")
    if os.path.isdir(candidate):
        return candidate
    if os.path.isdir(personas_dir):
        for name in os.listdir(personas_dir):
            p = os.path.join(personas_dir, name)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "topic_map.yaml")):
                return p
    return candidate


def load_pillars_and_topic_map(factory_root: str) -> Tuple[str, Dict[str, str], List[Dict[str, Any]]]:
    """Đọc thông tin 4 Pillars từ pillars.yaml và danh sách topics từ topic_map.yaml."""
    persona_dir = resolve_active_persona_dir(factory_root)
    topic_map_path = os.path.join(persona_dir, "topic_map.yaml")
    pillars_path = os.path.join(persona_dir, "pillars.yaml")

    pillar_info: Dict[str, str] = {}
    if os.path.isfile(pillars_path):
        try:
            with open(pillars_path, "r", encoding="utf-8") as f:
                p_data = yaml.safe_load(f) or {}
            for p_key, p_val in p_data.get("pillars", {}).items():
                if isinstance(p_val, dict) and p_val.get("name"):
                    prefix = p_key.replace("pillar_", "p")
                    pillar_info[str(p_val["name"]).strip()] = prefix
                    pillar_info[p_key] = prefix
        except Exception:
            pass

    topics: List[Dict[str, Any]] = []
    if os.path.isfile(topic_map_path):
        try:
            with open(topic_map_path, "r", encoding="utf-8") as f:
                t_data = yaml.safe_load(f) or {}
            raw_t = t_data.get("topics", [])
            if isinstance(raw_t, list):
                topics = raw_t
        except Exception:
            pass

    return topic_map_path, pillar_info, topics


def _write_topic_map_formatted(data: Dict[str, Any], path: str) -> None:
    """Ghi topic_map.yaml chuẩn hóa, bảo toàn TOPIC_MAP_HEADER và thứ tự các trường."""
    lines = [TOPIC_MAP_HEADER.rstrip("\n"), "topics:"]
    for t in data.get("topics", []):
        safe_label = str(t.get("label") or "").replace('"', "'").strip()
        t_type = str(t.get("topic_type") or "knowledge").strip().lower()
        if t_type not in VALID_TOPIC_TYPES:
            t_type = "knowledge"
        lines.append(f"- id: {t['id']}")
        lines.append(f'  label: "{safe_label}"')
        lines.append(f"  topic_type: {t_type}")
        if "pillar_parents" in t and t["pillar_parents"]:
            lines.append("  pillar_parents:")
            for p in t["pillar_parents"]:
                safe_p = str(p).replace('"', "'").strip()
                lines.append(f'  - "{safe_p}"')
        else:
            lines.append("  pillar_parents: []")
        if "aliases" in t and t["aliases"]:
            lines.append("  aliases:")
            for al in t["aliases"]:
                safe_al = str(al).replace('"', "'").strip()
                lines.append(f'  - "{safe_al}"')
        if "belongs_to_audience" in t and t["belongs_to_audience"]:
            lines.append("  belongs_to_audience:")
            for a in t["belongs_to_audience"]:
                safe_a = str(a).replace('"', "'").strip()
                lines.append(f'  - "{safe_a}"')
        else:
            lines.append("  belongs_to_audience: []")
        lines.append("")

    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    os.replace(tmp_path, path)


def verify_evidence_in_body(evidence: str, clean_body: str, post_title: str = "") -> bool:
    """Kiểm tra cơ học xem câu evidence có thực sự tồn tại trong tiêu đề hoặc thân bài chính hay không (độ tương đồng từ khóa >= 80%)."""
    if not evidence or not clean_body:
        return False
    combined_source = f"{post_title}\n{clean_body}".lower()
    norm_body = re.sub(r"[^\w\s]", " ", combined_source)
    body_tokens = set(norm_body.split())
    norm_ev = re.sub(r"[^\w\s]", " ", evidence.lower())
    ev_tokens = [tok for tok in norm_ev.split() if len(tok) >= 2]
    if len(ev_tokens) < 2:
        return False
    matched = sum(1 for tok in ev_tokens if tok in body_tokens)
    return (matched / len(ev_tokens)) >= 0.80


def is_author_self_reference_product(label: str, post_author: str, clean_body: str) -> bool:
    """Chặn lấy chính tên tác giả / fanpage hoặc tên phương pháp chung làm product nếu thân bài không bán khóa học / dịch vụ cụ thể."""
    norm_lbl = label.lower().strip()
    norm_auth = post_author.lower().strip()
    # Danh sách các từ khóa tự tham chiếu và phương pháp giáo dục phổ quát
    generic_edu_terms = ("giáo dục steiner", "steiner", "waldorf", "montessori", "vườn ong", "vườn ong steiner", "ong vàng")
    for term in generic_edu_terms:
        if term in norm_lbl and (term in norm_auth or "ong" in norm_auth or "steiner" in norm_auth):
            # Nếu thân bài KHÔNG chứa thông tin tuyển sinh / khóa học thương mại cụ thể thì chặn
            commercial_markers = ("tuyển sinh", "học phí", "khóa học", "lớp học", "học bổng", "đăng ký khóa", "đăng ký lớp")
            if not any(m in clean_body.lower() for m in commercial_markers):
                return True
    return False


def validate_odi_need_label(label: str) -> bool:
    """Kiểm tra nhãn Needs có tuân thủ đúng công thức 4 thành phần ODI (bắt đầu bằng Giảm thiểu/Tối đa hóa và không chứa liên từ cấm)."""
    s = label.strip()
    if not re.match(r"^(?:Giảm thiểu|Tối đa hóa)\s+", s, re.IGNORECASE):
        return False
    # Kiểm tra liên từ gộp vi phạm đơn trị
    for conj in (" và ", " hoặc ", " kiêm ", " đồng thời "):
        if conj in s.lower():
            return False
    return True


def sync_resolved_topics_to_map(
    factory_root: str,
    target_pillar: str,
    resolved_topics: List[Dict[str, Any]],
    audience_refs: List[str],
    clean_body: str,
    post_author: str,
    post_title: str = "",
) -> List[str]:
    """
    Kiểm định cơ học từng topic trong resolved_topics, cập nhật vào topic_map.yaml và
    trả về danh sách nhãn (label) tiếng Việt chính tắc để lưu vào trường topics của bài viết.
    """
    topic_map_path, pillar_info, existing_topics = load_pillars_and_topic_map(factory_root)

    # Chuẩn hóa target_pillar về tên tiếng Việt chính tắc trong pillars.yaml
    canonical_pillar = target_pillar.strip()
    canonical_names = [k for k in pillar_info.keys() if not k.startswith("pillar_")]
    if canonical_pillar not in canonical_names:
        mapped_prefix = pillar_info.get(canonical_pillar)
        if mapped_prefix:
            for c_name in canonical_names:
                if pillar_info.get(c_name) == mapped_prefix:
                    canonical_pillar = c_name
                    break
        else:
            for c_name in canonical_names:
                if c_name.lower() in canonical_pillar.lower() or canonical_pillar.lower() in c_name.lower():
                    canonical_pillar = c_name
                    break
            else:
                if canonical_names:
                    canonical_pillar = canonical_names[0]

    pillar_prefix = pillar_info.get(canonical_pillar, "p1")

    topics_by_id = {t["id"]: t for t in existing_topics}
    topics_by_label_and_type = {
        (str(t.get("label", "")).strip().lower(), str(t.get("topic_type") or "knowledge").strip().lower()): t
        for t in existing_topics
    }

    canonical_labels: List[str] = []
    has_map_changes = False

    for item in resolved_topics:
        action = str(item.get("action") or "create").strip().lower()
        t_type = str(item.get("topic_type") or "knowledge").strip().lower()
        if t_type not in VALID_TOPIC_TYPES:
            t_type = "knowledge"

        lbl = str(item.get("label") or "").strip()
        evidence = str(item.get("evidence") or "").strip()

        # Gate 3: Hậu kiểm evidence
        if evidence and not verify_evidence_in_body(evidence, clean_body, post_title=post_title):
            print(f"[POKA-YOKE] Bác bỏ topic '{lbl}': Evidence không tồn tại trong thân bài.")
            continue

        # Gate 3.1: Hậu kiểm Product tự tham chiếu
        if t_type == "product" and is_author_self_reference_product(lbl, post_author, clean_body):
            print(f"[POKA-YOKE] Bác bỏ topic Product '{lbl}': Tự tham chiếu tên Fanpage tác giả/triết lý chung.")
            continue

        # Gate 4: Hậu kiểm định dạng ODI Needs
        if t_type == "needs" and not validate_odi_need_label(lbl):
            print(f"[POKA-YOKE] Bác bỏ topic Needs '{lbl}': Không tuân thủ công thức 4 thành phần ODI.")
            continue

        if not lbl:
            continue

        matched_id = str(item.get("matched_id") or "").strip()
        target_entry = None

        # Khóa cứng Poka-Yoke: Chỉ cho phép reuse khi cùng topic_type
        if action == "reuse" and matched_id and matched_id in topics_by_id:
            candidate_entry = topics_by_id[matched_id]
            cand_type = str(candidate_entry.get("topic_type") or "knowledge").strip().lower()
            if cand_type == t_type:
                target_entry = candidate_entry
        if target_entry is None and (lbl.lower(), t_type) in topics_by_label_and_type:
            target_entry = topics_by_label_and_type[(lbl.lower(), t_type)]

        if target_entry:
            # Tái sử dụng topic đã có (cùng topic_type)
            c_label = str(target_entry.get("label") or lbl).strip()
            if c_label not in canonical_labels:
                canonical_labels.append(c_label)
            # Cập nhật thêm audience nếu chưa có
            curr_auds = set(target_entry.get("belongs_to_audience") or [])
            for a_ref in audience_refs:
                if a_ref and a_ref not in curr_auds:
                    curr_auds.add(a_ref)
                    has_map_changes = True
            target_entry["belongs_to_audience"] = sorted(list(curr_auds))
        else:
            # Tạo mới topic hoàn toàn
            prop_id = str(item.get("proposed_id") or "").strip().lower()
            prop_id = re.sub(r"[^a-z0-9_]", "_", prop_id)
            if not prop_id.startswith(f"{pillar_prefix}_"):
                prop_id = f"{pillar_prefix}_{prop_id}".lstrip("_")
            prop_id = re.sub(r"_+", "_", prop_id)

            # Đảm bảo ID là duy nhất
            base_id = prop_id
            counter = 2
            while prop_id in topics_by_id:
                prop_id = f"{base_id}_{counter}"
                counter += 1

            new_topic = {
                "id": prop_id,
                "label": lbl,
                "topic_type": t_type,
                "pillar_parents": [canonical_pillar],
                "belongs_to_audience": sorted(list(set(audience_refs))),
            }
            existing_topics.append(new_topic)
            topics_by_id[prop_id] = new_topic
            topics_by_label_and_type[(lbl.lower(), t_type)] = new_topic
            if lbl not in canonical_labels:
                canonical_labels.append(lbl)
            has_map_changes = True

    if has_map_changes and os.path.exists(topic_map_path):
        _write_topic_map_formatted({"topics": existing_topics}, topic_map_path)

    return canonical_labels


# ────────────────────────────────────────────────────────────────
# Nhóm 6: Ghi Kết quả Hợp nhất vào Bài viết trong 03-Content/Viral Posts/
# ────────────────────────────────────────────────────────────────

def commit_classification_to_post_file(
    vault_root: str,
    factory_root: str,
    file_path: str,
    audiences_list: List[Dict[str, Any]],
    resolved_topics: List[Dict[str, Any]],
    target_pillar: str,
    post_format: str = "deep_dive",
    no_jtbd_found: bool = False,
    clean_body: str = "",
) -> Tuple[bool, List[str], List[str]]:
    """Xóa bỏ toàn bộ 5 trường tags* cũ, đồng bộ resolved_topics vào topic_map.yaml và ghi duy nhất trường topics + audience_target vào bài viết."""
    short_name = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()

    fm, body_md = split_markdown_frontmatter(full_content)
    if not fm:
        return False, [], []

    # Xóa bỏ triệt để các trường tags* cũ
    for legacy_key in LEGACY_TAG_KEYS:
        fm.pop(legacy_key, None)

    # Nếu là bài noise hoặc không có JTBD hợp lệ
    if no_jtbd_found or post_format == "noise":
        fm["audience_target"] = []
        fm["topics"] = []
        fm["post_format"] = "noise"
        fm["classification_status"] = "skipped_no_jtbd"
        fm["classified_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_fm_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip()
        tmp_file = file_path + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(f"---\n{new_fm_yaml}\n---{body_md}")
        os.replace(tmp_file, file_path)
        return True, [], []

    post_title = str(fm.get("title") or os.path.splitext(short_name)[0])
    post_author = str(fm.get("author") or "Facebook")
    post_slug = os.path.splitext(short_name)[0]
    rel_path = os.path.relpath(file_path, vault_root)

    audience_refs: List[str] = []
    for aud_item in audiences_list:
        action = str(aud_item.get("action") or "reuse").strip()
        resolved_ref = ""
        if action == "reuse" and aud_item.get("matched_file_ref"):
            resolved_ref = str(aud_item["matched_file_ref"]).strip()
            if not resolved_ref.startswith("[["):
                resolved_ref = f"[[{resolved_ref}]]"
        elif action == "create" and aud_item.get("audience_filename"):
            try:
                resolved_ref = ensure_new_audience_created(
                    vault_root, aud_item, post_title, post_slug, rel_path
                )
            except Exception as e:
                print(f"[WARN] Không thể tạo file Audience mới: {e}")
        if resolved_ref and resolved_ref not in audience_refs:
            audience_refs.append(resolved_ref)

    # Đồng bộ topics vào topic_map.yaml và lấy danh sách nhãn chính tắc
    canonical_topic_labels = sync_resolved_topics_to_map(
        factory_root=factory_root,
        target_pillar=target_pillar,
        resolved_topics=resolved_topics,
        audience_refs=audience_refs,
        clean_body=clean_body or extract_clean_post_body(body_md),
        post_author=post_author,
        post_title=post_title,
    )

    if audience_refs:
        fm["audience_target"] = audience_refs
    fm["topics"] = canonical_topic_labels
    fm["post_format"] = post_format
    fm["classification_status"] = "classified"
    fm["classified_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_fm_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip()
    tmp_file = file_path + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(f"---\n{new_fm_yaml}\n---{body_md}")
    os.replace(tmp_file, file_path)
    return True, audience_refs, canonical_topic_labels


# ────────────────────────────────────────────────────────────────
# Nhóm 7: Điều phối Tuần tự 4 Skills cho 1 Bài Viết (Headless CLI Mode)
# ────────────────────────────────────────────────────────────────

def execute_4_skill_pipeline_for_post(
    agy_exe: str,
    vault_root: str,
    factory_root: str,
    file_path: str,
    idx_label: str,
) -> bool:
    """Thực thi tuần tự 4 Skills của PostClassifierAgent cho 1 bài viết trong 03-Content/Viral Posts/."""
    short_name = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()

    fm, body_md = split_markdown_frontmatter(full_content)
    if not fm:
        return False

    post_title = str(fm.get("title") or os.path.splitext(short_name)[0])
    post_author = str(fm.get("author") or "Facebook")
    clean_body = extract_clean_post_body(body_md)
    if not clean_body or "(Bài viết dạng Video/Hình ảnh không có văn bản)" in clean_body:
        return False

    _, pillar_info, existing_topics = load_pillars_and_topic_map(factory_root)
    pillars_list_text = "\n".join([f"- {p_name}" for p_name in pillar_info.keys() if not p_name.startswith("pillar_")])

    conv_id: Optional[str] = None

    # ── BƯỚC 1/4: Skill `post-jtbd-calibrator` ──
    update_live_progress(
        vault_root,
        f"🤖 [{idx_label} - Bước 1/4] Hiệu đính JTBD & Phân loại hình thái bài viết: {short_name}...",
        is_running=True,
    )
    step1_input = (
        f"- Tiêu đề bài viết: {post_title}\n"
        f"- Tác giả / Nguồn: {post_author}\n"
        f"- Danh sách Trụ cột (Pillars):\n{pillars_list_text}\n"
        f"- Nội dung bài viết:\n{clean_body}"
    )
    step1_out, conv_id = run_skill_via_agy(
        agy_exe, factory_root, "post-jtbd-calibrator", step1_input, conversation_id=None
    )
    if not step1_out:
        return False

    # Kiểm tra cổng chặn bài tạp (noise)
    if step1_out.get("no_jtbd_found") or step1_out.get("post_format") == "noise":
        print(f"[SKIP] {short_name} là bài viết dạng noise/không có JTBD chức năng.")
        commit_classification_to_post_file(
            vault_root=vault_root,
            factory_root=factory_root,
            file_path=file_path,
            audiences_list=[],
            resolved_topics=[],
            target_pillar="",
            post_format="noise",
            no_jtbd_found=True,
            clean_body=clean_body,
        )
        return True

    core_thesis = str(step1_out.get("core_thesis") or "").strip()
    target_pillar = str(step1_out.get("target_pillar") or "").strip()
    post_format = str(step1_out.get("post_format") or "deep_dive").strip()
    calibrated_jtbds = step1_out.get("calibrated_jtbds") or []

    if not calibrated_jtbds:
        return False

    # ── BƯỚC 2/4: Skill `post-audience-matcher` ──
    update_live_progress(
        vault_root,
        f"🤖 [{idx_label} - Bước 2/4] Đối chiếu ngữ nghĩa với _audience_index.yaml: {short_name}...",
        is_running=True,
    )
    _, current_audiences = load_audience_index_summary(vault_root)
    compact_index = [
        {
            "file_ref": a.get("file_ref"),
            "level": a.get("audience_level"),
            "performer": a.get("audience_Job_performer"),
            "main_job": a.get("audience_main_job"),
            "circumstance": a.get("audience_circumstance"),
        }
        for a in current_audiences
    ]
    step2_input = (
        f"1. JTBD ĐÃ HIỆU ĐÍNH TỪ BƯỚC 1:\n"
        f"```json\n{json.dumps(calibrated_jtbds, ensure_ascii=False, indent=2)}\n```\n\n"
        f"2. DANH SÁCH AUDIENCE HIỆN CÓ TRONG `_audience_index.yaml`:\n"
        f"```json\n{json.dumps(compact_index, ensure_ascii=False, indent=2)}\n```"
    )
    step2_out, conv_id = run_skill_via_agy(
        agy_exe, factory_root, "post-audience-matcher", step2_input, conversation_id=conv_id
    )
    if not step2_out or not step2_out.get("audiences"):
        return False

    audiences_list = step2_out.get("audiences") or []
    locked_summary = [
        {
            "audience_Job_performer": a.get("audience_Job_performer"),
            "audience_main_job": a.get("audience_main_job"),
            "audience_circumstance": a.get("audience_circumstance"),
        }
        for a in audiences_list
    ]
    locked_jtbd_json = json.dumps(locked_summary, ensure_ascii=False, indent=2)

    # ── BƯỚC 3/4: Skill `post-ki-product-tagger` ──
    update_live_progress(
        vault_root,
        f"🤖 [{idx_label} - Bước 3/4] Trích xuất Ứng viên Topic (KI, Product, Event): {short_name}...",
        is_running=True,
    )
    # Lưu ý: Cổng 0 ẩn post_author để tránh LLM trích xuất nhầm Fanpage tác giả làm product
    step3_input = (
        f"1. THÔNG TIN ĐÃ KHÓA TỪ BƯỚC 1 & 2:\n"
        f"- Hình thái bài viết: {post_format}\n"
        f"- Luận điểm trung tâm (Core Thesis): {core_thesis}\n"
        f"- Trụ cột (Target Pillar): {target_pillar}\n"
        f"- Audience & Main Job đã khóa:\n```json\n{locked_jtbd_json}\n```\n\n"
        f"2. NỘI DUNG BÀI VIẾT:\n"
        f"- Tiêu đề: {post_title}\n"
        f"{clean_body}"
    )
    step3_out, conv_id = run_skill_via_agy(
        agy_exe, factory_root, "post-ki-product-tagger", step3_input, conversation_id=conv_id
    )
    step3_out = step3_out or {}

    # Lọc sơ bộ các ứng viên qua kiểm định cơ học
    raw_candidates: List[Dict[str, Any]] = []
    for cat_key, t_type in (
        ("knowledge_candidates", "knowledge"),
        ("insight_candidates", "insight"),
        ("product_candidates", "product"),
        ("event_candidates", "event"),
    ):
        for item in step3_out.get(cat_key) or []:
            if isinstance(item, dict) and item.get("label"):
                item_copy = dict(item)
                item_copy["topic_type"] = t_type
                raw_candidates.append(item_copy)

    # ── BƯỚC 4/4: Skill `post-needs-extractor` ──
    update_live_progress(
        vault_root,
        f"🤖 [{idx_label} - Bước 4/4] Xây dựng Needs ODI & Semantic Dedup Topics: {short_name}...",
        is_running=True,
    )
    # Lấy các topic hiện hữu thuộc target_pillar trong topic_map.yaml
    pillar_prefix = pillar_info.get(target_pillar, "p1")
    existing_pillar_topics = [
        {"id": t["id"], "label": t.get("label", ""), "topic_type": t.get("topic_type", "knowledge")}
        for t in existing_topics
        if t.get("id", "").startswith(f"{pillar_prefix}_") or target_pillar in (t.get("pillar_parents") or [])
    ]

    step4_input = (
        f"1. THÔNG TIN ĐÃ KHÓA TỪ BƯỚC 1 & 2:\n"
        f"- Luận điểm trung tâm (Core Thesis): {core_thesis}\n"
        f"- Trụ cột (Target Pillar): {target_pillar}\n"
        f"- Audience & Main Job đã khóa:\n```json\n{locked_jtbd_json}\n```\n\n"
        f"2. DANH SÁCH ỨNG VIÊN TỪ BƯỚC 3:\n"
        f"```json\n{json.dumps(raw_candidates, ensure_ascii=False, indent=2)}\n```\n\n"
        f"3. DANH SÁCH TOPICS HIỆN CÓ CỦA TRỤ CỘT `{target_pillar}` TRONG `topic_map.yaml`:\n"
        f"```json\n{json.dumps(existing_pillar_topics, ensure_ascii=False, indent=2)}\n```\n\n"
        f"4. NỘI DUNG BÀI VIẾT:\n"
        f"- Tiêu đề: {post_title}\n"
        f"{clean_body}"
    )
    step4_out, _ = run_skill_via_agy(
        agy_exe, factory_root, "post-needs-extractor", step4_input, conversation_id=conv_id
    )
    step4_out = step4_out or {}
    resolved_topics = step4_out.get("resolved_topics") or []

    ok, _, _ = commit_classification_to_post_file(
        vault_root=vault_root,
        factory_root=factory_root,
        file_path=file_path,
        audiences_list=audiences_list,
        resolved_topics=resolved_topics,
        target_pillar=target_pillar,
        post_format=post_format,
        no_jtbd_found=False,
        clean_body=clean_body,
    )
    return ok


# ────────────────────────────────────────────────────────────────
# Nhóm 8: Quản lý Khóa Đơn Tiến trình (Single-Instance Lock) & Hàng Đợi Vét Cạn (Drain Loop)
# ────────────────────────────────────────────────────────────────

def _is_pid_running(pid: int) -> bool:
    """Kiểm tra tiến trình có PID tương ứng còn đang chạy hay không (An toàn trên cả Windows và POSIX, tránh dùng os.kill(pid, 0) trên Windows vì 0 == CTRL_C_EVENT)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return exit_code.value == STILL_ACTIVE
                return False
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def enqueue_requests(vault_root: str, files: List[str], force: bool) -> None:
    """Đẩy danh sách file cần phân loại vào hàng đợi chung .content-pipeline/classifier_queue.json."""
    pipeline_dir = os.path.join(vault_root, ".content-pipeline")
    os.makedirs(pipeline_dir, exist_ok=True)
    queue_path = os.path.join(pipeline_dir, "classifier_queue.json")
    data: Dict[str, Any] = {"items": []}
    if os.path.isfile(queue_path):
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and isinstance(loaded.get("items"), list):
                    data = loaded
        except Exception:
            pass

    existing_map = {str(item.get("path")): bool(item.get("force")) for item in data["items"] if isinstance(item, dict)}
    for f_path in files:
        norm_p = os.path.abspath(f_path)
        existing_map[norm_p] = existing_map.get(norm_p, False) or force

    data["items"] = [{"path": k, "force": v} for k, v in existing_map.items()]
    tmp_q = queue_path + ".tmp"
    with open(tmp_q, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_q, queue_path)


def pop_queued_requests(vault_root: str) -> List[Tuple[str, bool]]:
    """Lấy và xóa toàn bộ yêu cầu đang chờ trong .content-pipeline/classifier_queue.json."""
    queue_path = os.path.join(vault_root, ".content-pipeline", "classifier_queue.json")
    if not os.path.isfile(queue_path):
        return []
    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        os.remove(queue_path)
        items = loaded.get("items", []) if isinstance(loaded, dict) else []
        out: List[Tuple[str, bool]] = []
        for it in items:
            if isinstance(it, dict) and it.get("path"):
                out.append((str(it["path"]), bool(it.get("force"))))
        return out
    except Exception:
        return []


def acquire_classifier_lock(vault_root: str) -> Optional[str]:
    """Cố gắng chiếm khóa .content-pipeline/classifier.lock. Trả về đường dẫn lock nếu thành công, None nếu đang có tiến trình khác chạy."""
    pipeline_dir = os.path.join(vault_root, ".content-pipeline")
    os.makedirs(pipeline_dir, exist_ok=True)
    lock_path = os.path.join(pipeline_dir, "classifier.lock")
    now_ts = datetime.datetime.now().timestamp()

    if os.path.isfile(lock_path):
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                lock_info = json.load(f)
            pid = int(lock_info.get("pid") or 0)
            started_ts = float(lock_info.get("timestamp") or 0)
            if _is_pid_running(pid) and (now_ts - started_ts) < 900:
                return None
        except Exception:
            pass

    try:
        with open(lock_path, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "timestamp": now_ts}, f)
        return lock_path
    except Exception:
        return None


def collect_pending_Batch(vault_root: str, scan_all_unclassified: bool) -> List[str]:
    """Thu thập danh sách file từ hàng đợi + quét các file chưa phân loại trong 03-Content/Viral Posts."""
    targets: List[str] = []
    seen = set()

    for q_path, q_force in pop_queued_requests(vault_root):
        norm = os.path.normcase(os.path.abspath(q_path))
        if norm not in seen and needs_classification(vault_root, q_path, force=q_force):
            seen.add(norm)
            targets.append(os.path.abspath(q_path))

    if scan_all_unclassified:
        viral_posts_dir = os.path.join(vault_root, "03-Content", "Viral Posts")
        if os.path.isdir(viral_posts_dir):
            for root, _, files in os.walk(viral_posts_dir):
                for fn in files:
                    if fn.endswith(".md"):
                        full_p = os.path.abspath(os.path.join(root, fn))
                        norm = os.path.normcase(full_p)
                        if norm not in seen and needs_classification(vault_root, full_p, force=False):
                            seen.add(norm)
                            targets.append(full_p)

    return targets


# ────────────────────────────────────────────────────────────────
# Nhóm 9: Hàm Main (Chỉ quét thư mục `vault/03-Content/Viral Posts`)
# ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PostClassifierAgent Runner: Chạy chuỗi 4 Skills cho các bài viết trong 03-Content/Viral Posts."
    )
    parser.add_argument("--vault", required=True, help="Đường dẫn thư mục gốc của Obsidian Vault")
    parser.add_argument("--files", nargs="*", default=[], help="Danh sách file bài viết trong Viral Posts cần phân loại")
    parser.add_argument("--all-unclassified", action="store_true", help="Quét toàn bộ bài viết trong 03-Content/Viral Posts chưa có audience_target hoặc topics")
    parser.add_argument("--force", action="store_true", help="Phân loại lại đối với các file chỉ định trong --files")
    parser.add_argument("--post-file", default=None, help="Đường dẫn 1 file bài viết khi dùng kèm --apply-json")
    parser.add_argument("--apply-json", default=None, help="Đường dẫn file JSON chứa kết quả 4 bước do PostClassifierAgent chạy trực tiếp trong Antigravity Chat")
    args = parser.parse_args()

    vault_root = os.path.abspath(args.vault)
    factory_root = os.path.dirname(vault_root)

    # Chế độ 1: Ghi trực tiếp kết quả JSON từ phiên Interactive Chat của PostClassifierAgent
    if args.apply_json and args.post_file:
        abs_post = args.post_file if os.path.isabs(args.post_file) else os.path.join(vault_root, args.post_file)
        if not is_in_viral_posts_dir(vault_root, abs_post):
            sys.exit("❌ File bài viết phải nằm trong thư mục vault/03-Content/Viral Posts/")
        with open(args.apply_json, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # Hỗ trợ cả payload mới (resolved_topics) lẫn fallback tương thích
        resolved_topics = payload.get("resolved_topics") or []
        if not resolved_topics:
            for k in payload.get("knowledge_tags") or []:
                resolved_topics.append({"action": "create", "topic_type": "knowledge", "label": str(k), "evidence": ""})
            for i in payload.get("insight_tags") or []:
                resolved_topics.append({"action": "create", "topic_type": "insight", "label": str(i), "evidence": ""})
            for p in payload.get("product_tags") or []:
                resolved_topics.append({"action": "create", "topic_type": "product", "label": str(p), "evidence": ""})
            for n in payload.get("need_tags") or []:
                resolved_topics.append({"action": "create", "topic_type": "needs", "label": str(n), "evidence": ""})

        ok, refs, topics = commit_classification_to_post_file(
            vault_root=vault_root,
            factory_root=factory_root,
            file_path=abs_post,
            audiences_list=payload.get("audiences") or [],
            resolved_topics=resolved_topics,
            target_pillar=payload.get("target_pillar") or "Xác định triết lý giáo dục cho con",
            post_format=payload.get("post_format") or "deep_dive",
            no_jtbd_found=bool(payload.get("no_jtbd_found")),
        )
        cleanup_orphan_viral_post_audiences(vault_root, factory_root)
        if ok:
            print(f"✅ Đã cập nhật {os.path.basename(abs_post)} -> Audience: {refs}, Topics: {topics}")
            sys.exit(0)
        sys.exit(1)

    # Chế độ 2: Chạy ngầm tự động qua Antigravity CLI (agy.exe) kèm Single-Instance Lock & Drain Loop
    explicit_files = [
        (f_arg if os.path.isabs(f_arg) else os.path.join(vault_root, f_arg))
        for f_arg in (args.files or [])
    ]
    if explicit_files:
        enqueue_requests(vault_root, explicit_files, force=args.force)

    lock_path = acquire_classifier_lock(vault_root)
    if not lock_path:
        # Đã có một tiến trình classify_vault_posts.py đang chạy; nó sẽ tự động vét hàng đợi ở vòng lặp cuối
        return

    try:
        try:
            agy_exe = resolve_agy_executable()
        except FileNotFoundError as err:
            update_live_progress(vault_root, f"Lỗi: {err}", is_running=False)
            sys.exit(1)

        classified_count = 0
        total_processed = 0
        failed_files: Set[str] = set()

        # Vòng lặp Vét cạn (Drain Loop)
        while True:
            raw_batch = collect_pending_Batch(vault_root, scan_all_unclassified=args.all_unclassified)
            batch_files = [f for f in raw_batch if f not in failed_files]
            if not batch_files:
                break

            batch_len = len(batch_files)
            for idx, f_path in enumerate(batch_files, start=1):
                total_processed += 1
                try:
                    ok = execute_4_skill_pipeline_for_post(
                        agy_exe=agy_exe,
                        vault_root=vault_root,
                        factory_root=factory_root,
                        file_path=f_path,
                        idx_label=f"{idx}/{batch_len}",
                    )
                    if ok:
                        classified_count += 1
                    else:
                        failed_files.add(f_path)
                except Exception as exc:
                    print(f"[ERROR] Lỗi phân loại {os.path.basename(f_path)}: {exc}")
                    failed_files.add(f_path)

        # Thu dọn các Audience viral_post mồ côi
        orphans_cleaned = cleanup_orphan_viral_post_audiences(vault_root, factory_root)
        if orphans_cleaned > 0:
            print(f"🧹 Đã thu dọn {orphans_cleaned} file Audience viral_post mồ côi.")

        if total_processed > 0:
            update_live_progress(
                vault_root,
                f"✅ PostClassifierAgent hoàn tất: Đã gắn Audience & Topics cho {classified_count}/{total_processed} bài viết trong Viral Posts.",
                is_running=False,
            )
    finally:
        if lock_path and os.path.isfile(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass


if __name__ == "__main__":
    main()
