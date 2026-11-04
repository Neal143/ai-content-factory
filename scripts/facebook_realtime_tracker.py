"""
================================================================================
THÔNG TIN MÔ TẢ FILE (RULE 7)
================================================================================
- Tên file: facebook_realtime_tracker.py
- Last update: 04/11/2026 11:20 (GMT+7)
- Vai trò: Engine thu thập tự động nội dung bài viết, chỉ số tương tác (Reactions,
  Comments, Shares, Views) và bình luận phân nhánh (Threaded Comments) từ URL bài viết,
  Fanpage công khai và Trang cá nhân Facebook theo Kiến trúc Phân luồng Kép (Dual-Context:
  Tầng 3 Không Cookie + Tầng 2 Có Cookie nick phụ cách ly).
- Được sử dụng khi nào?: Được gọi từ plugin Content Compass (nút Quét ngay / Đăng nhập FB phụ / Interval)
  hoặc chạy ngầm độc lập qua Windows Task Scheduler (pythonw.exe) mỗi 15 phút.
- Output là gì?:
  1. Cập nhật trạng thái tiến trình, trạng thái phiên nick phụ (`auth_status`) và lịch hẹn quét vào `vault/.content-pipeline/fb-tracker-state.json`.
  2. Lưu bộ đệm toàn văn bài viết & cây bình luận vào `vault/.content-pipeline/fb_cache/posts/<fb_post_id>.json` (chỉ tự động cập nhật bình luận vào file `.md` nếu bài viết đã tồn tại trong `vault/03-Content/`).
  3. Ghi bản ghi tương tác chuẩn JSONL vào `vault/.content-pipeline/engagement/YYYY-MM.json`.
- Tóm tắt logic hoạt động:
  1. Đọc danh sách theo dõi và cài đặt từ `fb-watchlist.json` (do Obsidian quản lý).
  2. Kiểm tra khóa `fb-tracker.lock` để chống chạy chồng tiến trình.
  3. Khởi tạo `Dual-Context Engine`: Mặc định dùng `ctx_anon` (Tầng 3 Không Cookie + TLS Chrome 120) cho >90% tác vụ; chỉ chuyển sang `ctx_auth` (Tầng 2 Có Cookie nick phụ + giãn cách 15-22s) khi gặp trang cá nhân khóa khách ẩn danh (`CometErrorRoute`).
  4. Quét các Fanpage / Trang cá nhân đến hạn bằng đúng 1 request GraphQL (đọc trực tiếp `post._data` để bỏ qua `_obtain_metadata()`).
  5. Truy vấn GraphQL tuần tự với thời gian nghỉ an toàn IP (`delay_seconds >= 6s`), tính toán lịch hẹn tiếp theo theo thuật toán Adaptive Polling (15p / 60p / 360p).
  6. Sanitize cú pháp `[[...]]` trong văn bản cào về để không gây lỗi giả trên `verify_referential_integrity.py`.
  7. Hỗ trợ `--login-auth` (mở Chrome/Edge thật với `--user-data-dir` cách ly để tự bắt Cookie qua CDP WebSocket), `--logout-auth`, `--register-task` và `--unregister-task`.
================================================================================
"""

import os
import re
import sys
import json
import time
import base64
import random
import socket
import unicodedata
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from curl_cffi import requests as cffi_requests
import facebook_gql_scraper as fgs
import facebook_gql_scraper.unifiedFacebookParser as ufp
from facebook_gql_scraper.exceptions import SessionExpiredError
from facebook_gql_scraper.facebookGraphql import CometSinglePostDialogContentQueryGraphQL
from facebook_gql_scraper.facebookConsolidater import consolidate_jsonl

# Vá lỗi thư viện facebook_gql_scraper khi bài đăng trên Fanpage chứa Video có trường null
_orig_parse_post_attachments = getattr(ufp, "_parse_post_attachments", None)
if callable(_orig_parse_post_attachments):
    def _safe_parse_post_attachments(attachments: Any) -> list:
        try:
            return _orig_parse_post_attachments(attachments or [])
        except Exception:
            return []

    ufp._parse_post_attachments = _safe_parse_post_attachments

_orig_parse_feed_post = getattr(ufp, "_parse_feed_post", None)
if callable(_orig_parse_feed_post):
    def _safe_parse_feed_post(edge: Any) -> Optional[Dict[str, Any]]:
        try:
            return _orig_parse_feed_post(edge)
        except Exception:
            node = (edge or {}).get("node") or {}
            post_id = node.get("post_id")
            if not post_id:
                return None
            story = ((node.get("comet_sections") or {}).get("content") or {}).get("story") or {}
            msg = story.get("message") or {}
            actors = node.get("actors") or [{}]
            first_actor = actors[0] if actors and isinstance(actors[0], dict) else {}
            return {
                "type": "post",
                "id": post_id,
                "creation_time": node.get("creation_time"),
                "url": story.get("wwwURL"),
                "author": {
                    "type": "profile",
                    "id": first_actor.get("id"),
                    "name": first_actor.get("name"),
                    "url": first_actor.get("url"),
                },
                "title": None,
                "text": msg.get("text"),
                "attachments": [],
                "reactions": {"total": 0, "breakdown": []},
                "reactors_visible": None,
                "share_count": 0,
                "comments_count": 0,
            }

    ufp._parse_feed_post = _safe_parse_feed_post

# Đảm bảo UTF-8 I/O trên Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Múi giờ chuẩn GMT+7 của hệ thống
TZ_VN = timezone(timedelta(hours=7))


# ==============================================================================
# NHÓM CODE 1: Các hàm tiện ích xử lý chuỗi, Sanitize Wikilink, Slug & File JSON
# Ý nghĩa: Chuẩn hóa tên file Markdown không dấu, thoát cặp dấu [[ ]] trong văn
# bản cào về để bảo vệ `verify_referential_integrity.py`, và ghi JSON nguyên tử.
# ==============================================================================
def now_vn() -> datetime:
    return datetime.now(TZ_VN)


def now_iso() -> str:
    return now_vn().isoformat(timespec="seconds")


def sanitize_markdown_body(text: str) -> str:
    """Thoát cặp dấu [[ và ]] trong văn bản bài viết/bình luận để không bị hiểu nhầm là Wikilink."""
    if not text:
        return ""
    return text.replace("[[", r"\[\[").replace("]]", r"\]\]")


def slugify_text(text: str, suffix_id: str, max_words: int = 8) -> str:
    if not text:
        return f"fb-post-{suffix_id}"
    normalized = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    words = re.findall(r"[a-z0-9]+", ascii_text)
    if not words:
        return f"fb-post-{suffix_id}"
    prefix = "-".join(words[:max_words])[:50].strip("-")
    short_id = suffix_id[-6:] if len(suffix_id) > 6 else suffix_id
    return f"{prefix}-{short_id}"


def read_json_safe(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json_safe(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    for attempt in range(5):
        try:
            tmp_path.replace(path)
            return
        except PermissionError:
            time.sleep(0.08 * (attempt + 1))
    try:
        path.write_text(payload, encoding="utf-8")
        if tmp_path.exists():
            tmp_path.unlink()
    except Exception:
        pass


# ==============================================================================
# NHÓM CODE 2: Lõi kết nối Facebook Dual-Context GraphQL & TLS Impersonation
# Ý nghĩa: Duy trì song song 2 luồng:
#   - Luồng 1 (`self.ctx` - Tầng 3 Không Cookie): Xử lý >90% tác vụ (Fanpage công khai,
#     trang cá nhân mở Tầng 3 như `xnohat`, bài viết lẻ công khai và dò `doc_id`).
#   - Luồng 2 (`self.ctx_auth` - Tầng 2 Có Cookie nick phụ + TLS Chrome 120): Chỉ kích hoạt
#     khi gặp trang cá nhân hoặc bài viết chặn khách ẩn danh (`CometErrorRoute` / `node_v2=null`).
# ==============================================================================
def _create_chrome_tls_session(cookies_path: Optional[Path] = None) -> cffi_requests.Session:
    """
    Khởi tạo phiên HTTP/2 với chữ ký TLS BoringSSL (Chrome 120) đồng nhất,
    loại bỏ lỗi lệch Header Chrome 151/152 và TLS urllib3 của thư viện gốc.
    """
    session = cffi_requests.Session(impersonate="chrome120")
    session.headers.update({
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://web.facebook.com",
        "referer": "https://web.facebook.com/",
    })
    if cookies_path and cookies_path.exists():
        raw_cookies = read_json_safe(cookies_path, [])
        if isinstance(raw_cookies, list):
            cookie_dict = {
                str(c["name"]): str(c["value"])
                for c in raw_cookies
                if isinstance(c, dict) and c.get("name") and c.get("value") is not None
            }
            session.cookies.update(cookie_dict)
    return session


class PrivateProfileRequiresAuthError(ValueError):
    """Ngoại lệ đánh dấu trang cá nhân đóng Tầng 3 (cần chuyển sang luồng ctx_auth Tầng 2)."""
    pass


class FacebookTrackerEngine:
    def __init__(self, cache_dir: Path, tracker_state: Optional[Dict[str, Any]] = None):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tracker_state = tracker_state if tracker_state is not None else {}

        # 1. Luồng 1 (Tầng 3 - Không Cookie - Mặc định cho >90% tác vụ)
        self.cookie_file = self.cache_dir / "dummy_cookies.json"
        self.state_file = self.cache_dir / "facebook_state.json"
        if not self.cookie_file.exists():
            self.cookie_file.write_text("[]", encoding="utf-8")

        self.ctx = fgs.FacebookContext(
            cookies_file=str(self.cookie_file),
            state_file=str(self.state_file),
            quiet=True,
        )
        self.ctx.session = _create_chrome_tls_session(None)
        self.ctx.fb_dtsg = "NAcMCx_dummy_dtsg_token"
        # Luồng 1 là phiên Ẩn danh (Không Cookie) nên luôn có `set-login: logged-out` trên HTTP/2 Chrome
        self.ctx._check_session_dead = lambda response: False
        self.tls_session = _create_chrome_tls_session(None)

        # 2. Luồng 2 (Tầng 2 - Có Cookie nick phụ - Chỉ gọi khi gặp trang cá nhân đóng Tầng 3)
        self.auth_cookie_file = self.cache_dir / "auth_cookies.json"
        self.auth_state_file = self.cache_dir / "auth_facebook_state.json"
        self.ctx_auth: Optional[fgs.FacebookContext] = None
        self.auth_c_user: Optional[str] = None
        self.last_auth_request_ts: float = 0.0

        self._init_auth_context()

    def _init_auth_context(self) -> None:
        auth_st = self.tracker_state.setdefault("auth_status", {
            "connected": False,
            "c_user": None,
            "has_datr": False,
            "circuit_broken": False,
            "cookies_mtime": 0,
            "updated_at": None,
            "last_auth_error": None,
        })
        if not self.auth_cookie_file.exists():
            auth_st["connected"] = False
            auth_st["c_user"] = None
            return

        raw = read_json_safe(self.auth_cookie_file, [])
        if not isinstance(raw, list):
            auth_st["connected"] = False
            return

        cookie_map = {c.get("name"): str(c.get("value")) for c in raw if isinstance(c, dict) and c.get("name")}
        if "c_user" not in cookie_map or "xs" not in cookie_map:
            auth_st["connected"] = False
            return

        cur_mtime = int(self.auth_cookie_file.stat().st_mtime)
        # Nếu người dùng vừa đăng nhập lại file auth_cookies.json mới, tự động mở lại Cầu dao
        if cur_mtime != auth_st.get("cookies_mtime", 0):
            auth_st["circuit_broken"] = False
            auth_st["last_auth_error"] = None
            auth_st["cookies_mtime"] = cur_mtime

        self.auth_c_user = cookie_map["c_user"]
        auth_st["connected"] = not bool(auth_st.get("circuit_broken", False))
        auth_st["c_user"] = self.auth_c_user
        auth_st["has_datr"] = ("datr" in cookie_map)

        if auth_st.get("circuit_broken", False):
            return

        self.ctx_auth = fgs.FacebookContext(
            cookies_file=str(self.auth_cookie_file),
            state_file=str(self.auth_state_file),
            quiet=True,
        )
        self.ctx_auth.session = _create_chrome_tls_session(self.auth_cookie_file)

    def _sync_doc_ids_to_auth(self) -> None:
        """Đồng bộ bảng mã doc_id (*_facebookRelayOperation) từ ctx_anon sang ctx_auth để nick phụ không phải tải 50 file JS."""
        if not self.ctx_auth:
            return
        for op_name in (
            "ProfileCometTimelineFeedRefetchQuery_facebookRelayOperation",
            "CometSinglePostDialogContentQuery_facebookRelayOperation",
        ):
            if op_name not in self.ctx.operations:
                try:
                    self.ctx._resolve_doc_id(op_name, "https://www.facebook.com/facebook")
                except Exception:
                    pass
        if self.ctx.operations:
            self.ctx_auth.operations.update(self.ctx.operations)
            self.ctx_auth._save_state()

    def _ensure_auth_dtsg(self) -> None:
        """Đảm bảo ctx_auth có mã fb_dtsg hợp lệ (hỗ trợ cả DTSGInitialData lẫn input fb_dtsg) và lưu cache."""
        if not self.ctx_auth or self.ctx_auth.fb_dtsg:
            return
        nav_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
        }
        res = self.ctx_auth.session.get(
            "https://www.facebook.com/", headers=nav_headers, allow_redirects=True, timeout=25
        )
        if self.ctx_auth._check_session_dead(res) or "checkpoint" in str(res.url).lower():
            self._trip_auth_circuit_breaker("Phiên Cookie nick phụ đã hết hạn hoặc bị yêu cầu xác minh.")
            raise SessionExpiredError("Phiên Cookie nick phụ đã hết hạn khi lấy fb_dtsg.")

        for pat in (
            r'\{"name":"fb_dtsg","value":"([^"]+)"\}',
            r'"DTSGInitialData"\s*,\s*\[\]\s*,\s*\{"token"\s*:\s*"([^"]+)"',
            r'"DTSGInitData"\s*,\s*\[\]\s*,\s*\{"token"\s*:\s*"([^"]+)"',
            r'"fb_dtsg"\s*:\s*"([^"]+)"',
        ):
            m = re.search(pat, res.text)
            if m:
                self.ctx_auth.fb_dtsg = m.group(1)
                self.ctx_auth._save_state()
                return
        # Nếu Facebook không yêu cầu token trên route hiện tại, gán fallback để không gọi lặp _get_fb_dtsg()
        self.ctx_auth.fb_dtsg = "NAcMCx_auth_fallback_dtsg"
        self.ctx_auth._save_state()

    def _wait_auth_rate_limit(self) -> None:
        """Giãn cách ngẫu nhiên 15 - 22 giây giữa các lần gọi dùng Cookie nick phụ."""
        elapsed = time.time() - self.last_auth_request_ts
        min_wait = random.uniform(15.0, 22.0)
        if self.last_auth_request_ts > 0 and elapsed < min_wait:
            time.sleep(min_wait - elapsed)
        self.last_auth_request_ts = time.time()

    def _trip_auth_circuit_breaker(self, reason: str) -> None:
        """Ngắt Cầu dao bền vững vào tracker_state khi phát hiện Cookie hết hạn hoặc Checkpoint."""
        self.ctx_auth = None
        auth_st = self.tracker_state.setdefault("auth_status", {})
        auth_st["connected"] = False
        auth_st["circuit_broken"] = True
        auth_st["last_auth_error"] = reason
        auth_st["updated_at"] = now_iso()

    def resolve_url_to_post_id(self, url: str) -> str:
        """Phân giải URL bất kỳ sang post_id số nguyên (chỉ gọi 1 lần khi thêm bài mới)."""
        clean_url = url.strip()
        if re.fullmatch(r"\d{8,25}", clean_url):
            return clean_url

        m_num = re.search(r"/(?:posts|videos|reel)/(\d+)", clean_url, re.IGNORECASE) or re.search(
            r"(?:story_fbid|v)=(\d+)", clean_url, re.IGNORECASE
        )
        if m_num:
            return m_num.group(1)

        res = self.tls_session.get(clean_url, allow_redirects=True, timeout=25)
        if res.status_code != 200:
            raise ValueError(f"HTTP {res.status_code} khi phân giải URL: {clean_url}")

        final_url = str(res.url)
        m_final = re.search(r"/(?:posts|videos|reel)/(\d+)", final_url, re.IGNORECASE) or re.search(
            r"(?:story_fbid|v)=(\d+)", final_url, re.IGNORECASE
        )
        if m_final:
            return m_final.group(1)

        for pattern in (
            r'"subscription_target_id":"(\d+)"',
            r'"post_id":"(\d+)"',
            r'"top_level_post_id":"(\d+)"',
            r"/posts/[^/]+/(\d+)/",
        ):
            m = re.search(pattern, res.text)
            if m:
                return m.group(1)

        raise ValueError(f"Không tìm thấy post_id số từ URL: {clean_url}")

    def _extract_profile_id_from_html(self, final_url: str, html_text: str, exclude_id: Optional[str] = None) -> Optional[str]:
        for url_pat in (
            r"/people/[^/?#]+/(\d+)",
            r"[?&]id=(\d+)",
        ):
            m_url = re.search(url_pat, final_url)
            if m_url and m_url.group(1) != exclude_id:
                return m_url.group(1)

        # Ưu tiên các trường định danh của chính Profile đang xem (loại trừ exclude_id để không bắt nhầm c_user của nick phụ)
        for html_pat in (
            r"fb://profile/(\d+)",
            r"fb://page/(\d+)",
            r'"selectedID":"(\d+)"',
            r'"pageID":"(\d+)"',
            r'"delegate_page_id":"(\d+)"',
            r'"profile_id":(\d+)',
            r'"entity_id":"(\d+)"',
            r'"userID":"([1-9]\d+)"',
        ):
            for m_html in re.finditer(html_pat, html_text):
                cand = m_html.group(1)
                if cand and cand != "0" and cand != exclude_id:
                    return cand
        return None

    def resolve_page_identifier(self, page_input: str, use_auth: bool = False) -> str:
        """
        Phân giải mọi định dạng Fanpage / Trang cá nhân về `user_id` số chuẩn.
        - Mặc định dùng `tls_session` (Tầng 3 - Không Cookie).
        - Nếu gặp `CometErrorRoute` và `use_auth=True`, dùng `ctx_auth` (Tầng 2 - Có Cookie nick phụ).
        """
        val = page_input.strip().rstrip("/")
        if re.fullmatch(r"\d+", val):
            return val

        for direct_pat in (
            r"[?&]id=(\d+)",
            r"/people/[^/?#]+/(\d+)",
            r"/profile\.php\?id=(\d+)",
        ):
            m_dir = re.search(direct_pat, val)
            if m_dir:
                return m_dir.group(1)

        target_url = val if val.startswith("http") else f"https://www.facebook.com/{val.lstrip('/')}"
        nav_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
        }

        if not use_auth:
            res = self.tls_session.get(target_url, headers=nav_headers, allow_redirects=True, timeout=25)
            if res.status_code == 429:
                raise RuntimeError("RATE_LIMIT_429")
            found_id = self._extract_profile_id_from_html(str(res.url or ""), res.text, exclude_id=None)
            if found_id:
                return found_id
            if "CometErrorRoute" in res.text or '"privacy":true' in res.text:
                raise PrivateProfileRequiresAuthError(page_input)
            raise ValueError(f"Không thể phân giải ID số của trang từ địa chỉ: {page_input}")

        # Nhánh Tầng 2 (use_auth=True): Phân giải qua phiên Cookie nick phụ
        if not self.ctx_auth:
            raise ValueError(
                f"Trang '{page_input}' là Facebook cá nhân khóa khách ẩn danh. "
                f"Hãy bấm nút '🔑 Đăng nhập FB phụ (Quét trang cá nhân)' trong khung Thêm nguồn theo dõi để cấp quyền quét tự động."
            )
        self._wait_auth_rate_limit()
        res_auth = self.ctx_auth.session.get(target_url, headers=nav_headers, allow_redirects=True, timeout=25)
        if self.ctx_auth._check_session_dead(res_auth) or "checkpoint" in str(res_auth.url).lower():
            self._trip_auth_circuit_breaker("Phiên Cookie nick phụ đã hết hạn hoặc bị yêu cầu xác minh.")
            raise RuntimeError("Phiên Cookie nick phụ đã hết hạn. Đã tự động ngắt Cầu dao bảo vệ tài khoản.")

        found_auth_id = self._extract_profile_id_from_html(
            str(res_auth.url or ""), res_auth.text, exclude_id=self.auth_c_user
        )
        if found_auth_id:
            if not self.ctx_auth.fb_dtsg:
                for pat in (
                    r'\{"name":"fb_dtsg","value":"([^"]+)"\}',
                    r'"DTSGInitialData"\s*,\s*\[\]\s*,\s*\{"token"\s*:\s*"([^"]+)"',
                    r'"DTSGInitData"\s*,\s*\[\]\s*,\s*\{"token"\s*:\s*"([^"]+)"',
                ):
                    m_dtsg = re.search(pat, res_auth.text)
                    if m_dtsg:
                        self.ctx_auth.fb_dtsg = m_dtsg.group(1)
                        self.ctx_auth._save_state()
                        break
            return found_auth_id
        raise ValueError(f"Không thể phân giải ID trang cá nhân '{page_input}' ngay cả khi đã dùng Cookie nick phụ.")

    def _collect_posts_from_context(
        self, ctx: fgs.FacebookContext, clean_id: str, limit: int
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Khởi tạo trực tiếp `fgs.Profile(ctx, {"id": clean_id})` và đọc thẳng `post._data`
        để triệt tiêu 100% bẫy ngầm `_obtain_metadata()` của cả `Profile` lẫn `Post`
        (đảm bảo chỉ tốn đúng 1 request GraphQL duy nhất).
        """
        page_user = fgs.Profile(ctx, {"id": str(clean_id)})
        page_name = str(clean_id)
        results: List[Dict[str, Any]] = []
        for post in page_user.get_posts():
            raw_data = getattr(post, "_data", None) or {}
            post_id = str(raw_data.get("id") or "")
            if not post_id:
                continue
            author_obj = raw_data.get("author") or {}
            if isinstance(author_obj, dict) and author_obj.get("name"):
                page_name = str(author_obj["name"])
            raw_txt = str(raw_data.get("text") or "").strip()
            first_line = raw_txt.split("\n")[0].strip() if raw_txt else ""
            raw_post_url = raw_data.get("url") or f"https://www.facebook.com/{clean_id}/posts/{post_id}"
            clean_post_url = str(raw_post_url).replace("https://web.facebook.com/", "https://www.facebook.com/")
            reactions_total = int(((raw_data.get("reactions") or {}).get("total")) or 0)
            comments_cnt = int(raw_data.get("comments_count") or 0)
            shares_cnt = int(raw_data.get("share_count") or 0)
            results.append({
                "post_id": post_id,
                "creation_time": raw_data.get("creation_time"),
                "url": clean_post_url,
                "text_snippet": first_line[:140] if first_line else raw_txt[:140].replace("\n", " "),
                "full_text": raw_txt,
                "author_name": page_name,
                "metrics": {
                    "likes": reactions_total,
                    "comments": comments_cnt,
                    "shares": shares_cnt,
                    "views": 0,
                },
            })
            if len(results) >= limit:
                break
        return page_name, results

    def get_latest_posts_from_page(
        self, page_identifier: str, limit: int = 5, resolved_id: Optional[str] = None
    ) -> tuple[str, str, List[Dict[str, Any]]]:
        """
        Quét N bài viết mới nhất theo Kiến trúc Phân luồng Kép:
        - Bước 1: Luôn thử bằng `self.ctx` (Tầng 3 - Không Cookie).
        - Bước 2: Nếu trang cá nhân chặn Tầng 3 (`PrivateProfileRequiresAuthError` hoặc rỗng bài do quyền riêng tư),
          tự động chuyển sang `self.ctx_auth` (Tầng 2 - Có Cookie nick phụ + TLS Chrome 120).
        """
        used_auth_for_resolve = False
        if resolved_id and re.fullmatch(r"\d+", str(resolved_id)):
            clean_id = str(resolved_id)
        else:
            try:
                clean_id = self.resolve_page_identifier(page_identifier, use_auth=False)
            except PrivateProfileRequiresAuthError:
                clean_id = self.resolve_page_identifier(page_identifier, use_auth=True)
                used_auth_for_resolve = True

        # Nếu phân giải được ở Tầng 3 thì ưu tiên lấy bài ở Tầng 3 trước
        if not used_auth_for_resolve:
            try:
                page_name, results = self._collect_posts_from_context(self.ctx, clean_id, limit)
                if len(results) > 0 or not self.ctx_auth:
                    return str(clean_id), page_name, results
            except Exception:
                if not self.ctx_auth:
                    raise

        # Chuyển sang Tầng 2 (ctx_auth) cho các trang cá nhân như my.van.7902
        if not self.ctx_auth:
            raise ValueError(
                f"Trang '{page_identifier}' yêu cầu đăng nhập Facebook phụ (Tầng 2). "
                f"Hãy bấm nút '🔑 Đăng nhập FB phụ (Quét trang cá nhân)' để cấp quyền."
            )

        self._sync_doc_ids_to_auth()
        self._ensure_auth_dtsg()
        self._wait_auth_rate_limit()
        try:
            page_name, results = self._collect_posts_from_context(self.ctx_auth, clean_id, limit)
            return str(clean_id), page_name, results
        except SessionExpiredError as exp_err:
            self._trip_auth_circuit_breaker("Phiên Cookie nick phụ đã hết hạn hoặc bị đăng xuất.")
            raise RuntimeError(
                "Phiên Cookie nick phụ đã hết hạn. Hệ thống đã tự động ngắt Cầu dao bảo vệ tài khoản."
            ) from exp_err

    def fetch_post_metrics(
        self, post_id: str, fetch_comments_tree: bool = False, expand_sub_replies: bool = False
    ) -> Dict[str, Any]:
        """
        Truy vấn GraphQL lấy chỉ số tương tác realtime, nội dung và bình luận.
        Ưu tiên dùng `self.ctx` (Tầng 3 Không Cookie); nếu bài viết thuộc trang cá nhân Tầng 2
        trả về `node_v2 = null` và `self.ctx_auth` sẵn sàng, tự động fallback sang `self.ctx_auth`.
        """
        active_ctx = self.ctx
        resp = CometSinglePostDialogContentQueryGraphQL(self.ctx).send(postId=str(post_id))
        if resp.status_code == 429:
            raise RuntimeError("RATE_LIMIT_429")
        data = consolidate_jsonl(resp.text)
        node_v2 = data.get("data", {}).get("node_v2")

        if not node_v2 and self.ctx_auth:
            try:
                self._sync_doc_ids_to_auth()
                self._ensure_auth_dtsg()
                self._wait_auth_rate_limit()
                resp_auth = CometSinglePostDialogContentQueryGraphQL(self.ctx_auth).send(postId=str(post_id))
                if resp_auth.status_code == 429:
                    raise RuntimeError("RATE_LIMIT_429")
                data_auth = consolidate_jsonl(resp_auth.text)
                node_v2 = data_auth.get("data", {}).get("node_v2")
                if node_v2:
                    active_ctx = self.ctx_auth
            except SessionExpiredError:
                self._trip_auth_circuit_breaker("Phiên Cookie nick phụ đã hết hạn khi quét bài viết Tầng 2.")

        if not node_v2:
            return {"post_id": str(post_id), "inactive": True}

        story = node_v2.get("comet_sections", {}).get("content", {}).get("story", {})
        target = (
            node_v2.get("comet_sections", {})
            .get("feedback", {})
            .get("story", {})
            .get("story_ufi_container", {})
            .get("story", {})
            .get("feedback_context", {})
            .get("feedback_target_with_context", {})
        )

        fb = target.get("comet_ufi_summary_and_actions_renderer", {}).get("feedback", {})
        comment_renderer = (
            target.get("comment_list_renderer", {})
            .get("feedback", {})
            .get("comment_rendering_instance_for_feed_location", {})
            .get("comments", {})
        )

        reaction_breakdown = {}
        for edge in fb.get("top_reactions", {}).get("edges", []):
            loc_name = edge.get("node", {}).get("localized_name")
            cnt = edge.get("reaction_count", 0)
            if loc_name:
                reaction_breakdown[loc_name] = cnt

        reaction_count = (fb.get("reaction_count") or {}).get("count", 0) or 0
        comments_count = (
            comment_renderer.get("total_count")
            or (fb.get("comment_rendering_instance", {}).get("comments", {})).get("total_count", 0)
            or 0
        )
        share_count = (fb.get("share_count") or {}).get("count", 0) or 0
        video_views = fb.get("video_view_count") or 0

        actors = story.get("actors") or [{}]
        author_name = actors[0].get("name") if actors else "Facebook Page"
        post_text = (story.get("message") or {}).get("text") or ""

        result: Dict[str, Any] = {
            "post_id": str(post_id),
            "inactive": False,
            "creation_time": node_v2.get("creation_time"),
            "author_name": author_name,
            "post_text": post_text,
            "metrics": {
                "likes": int(reaction_count),
                "comments": int(comments_count),
                "shares": int(share_count),
                "views": int(video_views),
                "reaction_breakdown": reaction_breakdown,
            },
        }

        if fetch_comments_tree:
            result["comments_tree"] = self._extract_threaded_comments(
                target, post_id=str(post_id), expand_replies=expand_sub_replies, ctx=active_ctx
            )

        return result

    def _extract_threaded_comments(
        self,
        feedback_target: Dict[str, Any],
        post_id: str,
        expand_replies: bool = False,
        ctx: Optional[fgs.FacebookContext] = None,
    ) -> List[Dict[str, Any]]:
        """Bóc tách danh sách bình luận cấp 1 và phản hồi cấp 2."""
        comment_edges = (
            feedback_target.get("comment_list_renderer", {})
            .get("feedback", {})
            .get("comment_rendering_instance_for_feed_location", {})
            .get("comments", {})
            .get("edges", [])
        )

        threaded_comments = []
        for edge in comment_edges:
            node = edge.get("node", {})
            if not node:
                continue

            author = node.get("author", {})
            body = node.get("body", {})
            fb_info = node.get("feedback", {})
            reply_total = (fb_info.get("replies_fields") or {}).get("total_count", 0) or 0

            author_id = author.get("id")
            author_url = author.get("url")
            if not author_url and author_id:
                author_url = f"https://www.facebook.com/{author_id}"

            raw_id = node.get("id", "")
            try:
                decoded = base64.b64decode(raw_id).decode("utf-8")
                cid = decoded.split(":")[-1].split("_")[-1]
            except Exception:
                cid = raw_id

            sub_replies = []
            if expand_replies and reply_total > 0:
                try:
                    c_obj = fgs.Comment(ctx or self.ctx, {"id": cid, "post_id": post_id})
                    for r in c_obj.get_replies():
                        r_author = getattr(r, "owner", None)
                        r_url = getattr(r_author, "url", None) if r_author else None
                        r_id = getattr(r_author, "id", None) if r_author else None
                        if not r_url and r_id:
                            r_url = f"https://www.facebook.com/{r_id}"
                        sub_replies.append({
                            "comment_id": getattr(r, "id", ""),
                            "created_time": getattr(r, "created_time", None),
                            "text": getattr(r, "text", ""),
                            "reactions": getattr(r, "reaction_count", 0),
                            "author": {
                                "id": r_id,
                                "name": getattr(r_author, "name", "Người dùng") if r_author else "Người dùng",
                                "profile_url": r_url,
                            },
                        })
                except Exception:
                    pass

            threaded_comments.append({
                "comment_id": cid,
                "created_time": node.get("created_time"),
                "text": body.get("text") if body else "",
                "reactions": (fb_info.get("reactors") or {}).get("count_reduced", 0),
                "reply_count": reply_total,
                "author": {
                    "id": author_id,
                    "name": author.get("name", "Người dùng"),
                    "profile_url": author_url,
                },
                "replies": sub_replies,
            })

        return threaded_comments


# ==============================================================================
# NHÓM CODE 3: Lưu bộ đệm bài viết (Staging Cache) & Đồng bộ có chọn lọc vào Vault
# Ý nghĩa: Lưu toàn bộ văn bản và cây bình luận vào `.content-pipeline/fb_cache/posts/`
# để user xem trước và chọn lưu trên UI; chỉ tự động cập nhật bình luận vào file
# Markdown nếu bài viết đó đã tồn tại sẵn trong `03-Content/`.
# ==============================================================================
class VaultSyncManager:
    def __init__(self, vault_dir: Path):
        self.vault_dir = vault_dir
        self.pipeline_dir = vault_dir / ".content-pipeline"
        self.engagement_dir = self.pipeline_dir / "engagement"
        self.posts_cache_dir = self.pipeline_dir / "fb_cache" / "posts"
        self.posted_dir = vault_dir / "03-Content" / "Posted"
        self.viral_dir = vault_dir / "03-Content" / "Viral Posts"

    def find_existing_post_file(self, fb_post_id: str, preferred_slug: Optional[str] = None) -> Optional[Path]:
        """Tìm file Markdown trong Vault đã gắn fb_post_id hoặc trùng slug."""
        content_root = self.vault_dir / "03-Content"
        if not content_root.exists():
            return None

        pattern = re.compile(rf"^fb_post_id:\s*['\"]?{re.escape(fb_post_id)}['\"]?\s*$", re.MULTILINE)
        for md_file in content_root.rglob("*.md"):
            if preferred_slug and md_file.stem == preferred_slug:
                return md_file
            try:
                head = md_file.read_text(encoding="utf-8-sig")[:1500]
                if pattern.search(head):
                    return md_file
            except Exception:
                continue
        return None

    def has_post_cache(self, fb_post_id: str) -> bool:
        """Kiểm tra bài viết đã có file cache đầy đủ trong `.content-pipeline/fb_cache/posts/` hay chưa."""
        cache_file = self.posts_cache_dir / f"{fb_post_id}.json"
        return cache_file.exists()

    def save_scraped_post_cache(
        self,
        fb_post_id: str,
        fb_url: str,
        source_type: str,
        vault_slug: str,
        post_data: Dict[str, Any],
    ) -> None:
        """Lưu toàn văn bài viết và cây bình luận vào bộ đệm `.content-pipeline/fb_cache/posts/<fb_post_id>.json`."""
        self.posts_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.posts_cache_dir / f"{fb_post_id}.json"
        existing_cache = read_json_safe(cache_file, {})

        comments_tree = post_data.get("comments_tree")
        if comments_tree is None:
            comments_tree = existing_cache.get("comments_tree", [])

        new_text = (post_data.get("post_text") or "").strip()
        cached_text = (existing_cache.get("post_text") or "").strip()
        final_text = new_text if new_text else cached_text

        payload = {
            "fb_post_id": fb_post_id,
            "fb_url": fb_url,
            "source_type": source_type,
            "vault_slug": vault_slug,
            "author_name": post_data.get("author_name") or existing_cache.get("author_name") or "Facebook",
            "creation_time": post_data.get("creation_time") or existing_cache.get("creation_time"),
            "post_text": final_text,
            "metrics": post_data.get("metrics") or existing_cache.get("metrics") or {},
            "comments_tree": comments_tree,
            "updated_at": now_iso(),
        }
        write_json_safe(cache_file, payload)

    def sync_existing_markdown_note(
        self,
        fb_post_id: str,
        fb_url: str,
        source_type: str,
        post_data: Dict[str, Any],
        existing_slug: Optional[str] = None,
    ) -> tuple[str, bool, Optional[str]]:
        """
        Lưu cache bài viết; nếu bài viết ĐÃ CÓ file .md trong Vault thì cập nhật bình luận,
        nếu CHƯA CÓ thì không tự động tạo file .md để tránh làm bẩn Vault.
        Trả về: (vault_slug, saved_to_vault, vault_rel_path)
        """
        raw_post_text = (post_data.get("post_text") or "").strip()
        existing_file = self.find_existing_post_file(fb_post_id, existing_slug)
        vault_slug = existing_file.stem if existing_file else (existing_slug or slugify_text(raw_post_text, fb_post_id))

        self.save_scraped_post_cache(
            fb_post_id=fb_post_id,
            fb_url=fb_url,
            source_type=source_type,
            vault_slug=vault_slug,
            post_data=post_data,
        )

        if existing_file is not None and existing_file.exists():
            comments_tree = post_data.get("comments_tree")
            if comments_tree is not None and len(comments_tree) > 0:
                self._update_comments_section(existing_file, comments_tree)
            rel_path = existing_file.relative_to(self.vault_dir).as_posix()
            return existing_file.stem, True, rel_path

        return vault_slug, False, None

    def _update_comments_section(self, md_file: Path, comments_tree: List[Dict[str, Any]]) -> None:
        try:
            content = md_file.read_text(encoding="utf-8-sig")
        except Exception:
            return

        marker = "\n## 💬 Bình luận thu thập (Threaded Comments)\n"
        if marker in content:
            content = content.split(marker)[0].rstrip() + "\n"

        lines = [marker, f"*Cập nhật lúc: {now_vn().strftime('%d/%m/%Y %H:%M')} (GMT+7)*\n"]
        for c in comments_tree:
            author = c.get("author") or {}
            a_name = sanitize_markdown_body(author.get("name") or "Người dùng")
            a_url = author.get("profile_url") or "#"
            c_text = sanitize_markdown_body((c.get("text") or "").replace("\n", " "))
            c_react = c.get("reactions", 0)
            lines.append(f"- **[{a_name}]({a_url})** *(👍 {c_react})*: {c_text}")
            for r in c.get("replies") or []:
                r_author = r.get("author") or {}
                r_name = sanitize_markdown_body(r_author.get("name") or "Người dùng")
                r_url = r_author.get("profile_url") or "#"
                r_text = sanitize_markdown_body((r.get("text") or "").replace("\n", " "))
                r_react = r.get("reactions", 0)
                lines.append(f"  - ↳ **[{r_name}]({r_url})** *(👍 {r_react})*: {r_text}")

        md_file.write_text(content + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

    def append_engagement_record(self, post_id: str, metrics: Dict[str, Any]) -> None:
        """Ghi nối 1 dòng JSONL vào `.content-pipeline/engagement/YYYY-MM.json`."""
        self.engagement_dir.mkdir(parents=True, exist_ok=True)
        dt = now_vn()
        month_key = dt.strftime("%Y-%m")
        file_path = self.engagement_dir / f"{month_key}.json"

        record = {
            "post_id": post_id,
            "platform": "facebook",
            "collected_at": dt.isoformat(timespec="seconds"),
            "metrics": {
                "likes": int(metrics.get("likes", 0)),
                "comments": int(metrics.get("comments", 0)),
                "shares": int(metrics.get("shares", 0)),
                "views": int(metrics.get("views", 0)),
            },
        }
        line = json.dumps(record, ensure_ascii=False)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# ==============================================================================
# NHÓM CODE 4: Bộ điều phối Lịch quét phân tầng (Adaptive Polling) & Bảo vệ IP
# Ý nghĩa: Quản lý khóa tiến trình (lock file), tính toán lịch hẹn tiếp theo dựa
# trên độ tuổi bài viết, kiểm soát thời gian nghỉ giữa các request và xử lý
# cả 2 chế độ: Quét theo lịch hẹn (--run-due) và Quét cưỡng bức (--force-all / --force-id).
# ==============================================================================
class TrackerOrchestrator:
    def __init__(self, vault_dir: Path):
        self.vault_dir = vault_dir
        self.pipeline_dir = vault_dir / ".content-pipeline"
        self.watchlist_path = self.pipeline_dir / "fb-watchlist.json"
        self.state_path = self.pipeline_dir / "fb-tracker-state.json"
        self.lock_path = self.pipeline_dir / "fb-tracker.lock"
        self.cache_dir = self.pipeline_dir / "fb_cache"

        self.sync_mgr = VaultSyncManager(vault_dir)

    def acquire_lock(self) -> bool:
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists():
            try:
                lock_data = json.loads(self.lock_path.read_text(encoding="utf-8"))
                started_ts = lock_data.get("timestamp", 0)
                # Tự động giải phóng lock nếu tiến trình cũ bị treo quá 15 phút (900 giây)
                if time.time() - started_ts < 900:
                    return False
            except Exception:
                pass
        self.lock_path.write_text(
            json.dumps({"pid": os.getpid(), "timestamp": time.time()}), encoding="utf-8"
        )
        return True

    def release_lock(self) -> None:
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except Exception:
            pass

    def load_watchlist(self) -> Dict[str, Any]:
        default_wl = {
            "settings": {
                "poll_new_mins": 15,
                "poll_mid_mins": 60,
                "poll_old_mins": 360,
                "page_scan_mins": 60,
                "delay_seconds": 8,
                "max_batch_size": 20,
                "retention_mode": "max_days",
                "retention_max_posts": 20,
                "retention_max_days": 7,
                "fetch_comments": True,
                "expand_replies": False,
                "background_task_enabled": False,
            },
            "posts": [],
            "pages": [],
        }
        data = read_json_safe(self.watchlist_path, default_wl)
        if "settings" not in data:
            data["settings"] = default_wl["settings"]
        if "posts" not in data:
            data["posts"] = []
        if "pages" not in data:
            data["pages"] = []
        return data

    def load_state(self) -> Dict[str, Any]:
        default_st = {
            "status": {
                "is_running": False,
                "progress_text": "Sẵn sàng",
                "last_run_at": None,
                "last_error": None,
            },
            "auth_status": {
                "connected": False,
                "c_user": None,
                "has_datr": False,
                "circuit_broken": False,
                "cookies_mtime": 0,
                "updated_at": None,
                "last_auth_error": None,
            },
            "posts": {},
            "pages": {},
            "discovered_posts": [],
            "ignored_fb_ids": [],
        }
        data = read_json_safe(self.state_path, default_st)
        for k in ("status", "auth_status", "posts", "pages", "discovered_posts", "ignored_fb_ids"):
            if k not in data:
                data[k] = default_st[k]
        return data

    def update_status(self, state: Dict[str, Any], is_running: bool, text: str, error: Optional[str] = None) -> None:
        state["status"]["is_running"] = is_running
        state["status"]["progress_text"] = text
        if not is_running:
            state["status"]["last_run_at"] = now_iso()
        if error is not None:
            state["status"]["last_error"] = error
        write_json_safe(self.state_path, state)

    def compute_next_poll(
        self, creation_time: Optional[int], consecutive_no_change: int, settings: Dict[str, Any], custom_mins: int = 0
    ) -> str:
        """Tính thời điểm quét tiếp theo dựa trên thuật toán Adaptive Polling."""
        if custom_mins and custom_mins > 0:
            delta_mins = max(5, int(custom_mins))
        elif creation_time:
            age_hours = (time.time() - int(creation_time)) / 3600.0
            if age_hours < 12:
                delta_mins = int(settings.get("poll_new_mins", 15))
            elif age_hours < 48:
                delta_mins = int(settings.get("poll_mid_mins", 60))
            else:
                delta_mins = int(settings.get("poll_old_mins", 360))
        else:
            delta_mins = int(settings.get("poll_mid_mins", 60))

        # Nếu 3 lần liên tiếp không tăng tương tác trên bài > 48h thì giãn lịch
        if consecutive_no_change >= 3 and delta_mins < int(settings.get("poll_old_mins", 360)):
            delta_mins = int(settings.get("poll_old_mins", 360))

        next_dt = now_vn() + timedelta(minutes=max(5, delta_mins))
        return next_dt.isoformat(timespec="seconds")

    def is_due(self, next_poll_iso: Optional[str]) -> bool:
        if not next_poll_iso:
            return True
        try:
            next_dt = datetime.fromisoformat(next_poll_iso)
            return now_vn() >= next_dt
        except Exception:
            return True

    def recently_polled(self, last_polled_iso: Optional[str], cooldown_sec: int = 120) -> bool:
        if not last_polled_iso:
            return False
        try:
            last_dt = datetime.fromisoformat(last_polled_iso)
            return (now_vn() - last_dt).total_seconds() < cooldown_sec
        except Exception:
            return False

    def apply_retention_policy(
        self,
        watchlist: Dict[str, Any],
        state: Dict[str, Any],
        latest_page_post_ids: Dict[str, set],
    ) -> bool:
        """
        Áp dụng ngưỡng tự động ngừng quét bài cũ theo 1 trong 3 chế độ user chọn:
        - 'latest_only': Chỉ quét N bài mới nhất ở thời điểm quét của từng Fanpage (không cộng dồn bài cũ).
        - 'max_posts': Quét cộng dồn nhưng tối đa X bài đang bật theo dõi (vượt quá X thì tự động ngừng quét bài cũ nhất).
        - 'max_days': Quét cộng dồn nhưng chỉ quét bài cách thời điểm quét tối đa X ngày.
        Trả về True nếu có thay đổi trong watchlist/state cần lưu.
        """
        settings = watchlist.get("settings", {})
        retention_mode = str(settings.get("retention_mode", "max_days"))
        max_posts_limit = max(1, int(settings.get("retention_max_posts", 20)))
        max_days_limit = max(1, int(settings.get("retention_max_days", 7)))
        now_ts = time.time()
        changed = False

        discovered = state.get("discovered_posts", [])
        posts_state = state.get("posts", {})

        def get_post_sort_ts(item: Dict[str, Any]) -> float:
            iid = item.get("id", "")
            pst = posts_state.get(iid, {})
            ctime = pst.get("creation_time")
            if ctime:
                try:
                    return float(ctime)
                except Exception:
                    pass
            added_str = item.get("added_at")
            if added_str:
                try:
                    return datetime.fromisoformat(added_str).timestamp()
                except Exception:
                    pass
            return 0.0

        # 0. Kiểm tra tính nhất quán giữa Bảng 1 (watchlist.pages) và Bảng 2 (state.discovered_posts):
        # Bài viết thuộc Trang đã tạm dừng hoặc đã gỡ khỏi watchlist.pages phải luôn ở trạng thái tạm dừng quét.
        wl_pages = watchlist.get("pages", [])
        active_page_ids = {p.get("id") for p in wl_pages if p.get("enabled", True) and p.get("id")}
        active_page_idents = {
            str(p.get("page_identifier", "")).strip().lower()
            for p in wl_pages
            if p.get("enabled", True) and p.get("page_identifier")
        }
        all_page_ids = {p.get("id") for p in wl_pages if p.get("id")}
        all_page_idents = {
            str(p.get("page_identifier", "")).strip().lower()
            for p in wl_pages
            if p.get("page_identifier")
        }

        eligible_discovered: List[Dict[str, Any]] = []
        for dp in discovered:
            pid = dp.get("from_page_id")
            pident = str(dp.get("from_page") or "").strip().lower()
            if not pid and not pident:
                eligible_discovered.append(dp)
                continue
            if (pid and pid in active_page_ids) or (pident and pident in active_page_idents):
                eligible_discovered.append(dp)
            else:
                in_watchlist = (pid and pid in all_page_ids) or (pident and pident in all_page_idents)
                target_reason = "page_paused" if in_watchlist else "page_removed"
                if dp.get("enabled", True) or dp.get("auto_paused_reason") != target_reason:
                    dp["enabled"] = False
                    dp["auto_paused_reason"] = target_reason
                    changed = True

        # 1. Chế độ 1 (latest_only): Chỉ giữ bật quét cho đúng N bài mới nhất của từng Fanpage
        if retention_mode == "latest_only":
            page_limits = {p.get("id"): max(1, int(p.get("limit", 5))) for p in wl_pages}
            by_page: Dict[str, List[Dict[str, Any]]] = {}
            for dp in eligible_discovered:
                pid = dp.get("from_page_id") or dp.get("from_page") or "_default"
                by_page.setdefault(pid, []).append(dp)

            for pid, dp_list in by_page.items():
                fresh_ids = latest_page_post_ids.get(pid)
                if fresh_ids:
                    for dp in dp_list:
                        should_enable = str(dp.get("fb_post_id")) in fresh_ids
                        if dp.get("enabled", True) != should_enable:
                            dp["enabled"] = should_enable
                            dp["auto_paused_reason"] = None if should_enable else "latest_only"
                            changed = True
                else:
                    limit_n = page_limits.get(pid, 5)
                    sorted_dp = sorted(dp_list, key=get_post_sort_ts, reverse=True)
                    for idx, dp in enumerate(sorted_dp):
                        should_enable = idx < limit_n
                        if dp.get("enabled", True) != should_enable:
                            dp["enabled"] = should_enable
                            dp["auto_paused_reason"] = None if should_enable else "latest_only"
                            changed = True

        # 2. Chế độ 2 (max_posts): Cộng dồn nhưng chỉ giữ bật quét tối đa X bài mới nhất
        elif retention_mode == "max_posts":
            all_refs: List[Dict[str, Any]] = list(watchlist.get("posts", [])) + eligible_discovered
            sorted_all = sorted(all_refs, key=get_post_sort_ts, reverse=True)
            for idx, item in enumerate(sorted_all):
                if idx >= max_posts_limit and item.get("enabled", True):
                    item["enabled"] = False
                    item["auto_paused_reason"] = "max_posts"
                    changed = True
                elif idx < max_posts_limit and item.get("auto_paused_reason") in ("latest_only", "max_posts", "max_days", "page_paused"):
                    item["enabled"] = True
                    item["auto_paused_reason"] = None
                    changed = True

        # 3. Chế độ 3 (max_days): Cộng dồn nhưng chỉ quét bài trong vòng X ngày tính đến thời điểm quét
        elif retention_mode == "max_days":
            cutoff_ts = now_ts - (max_days_limit * 86400.0)
            all_refs = list(watchlist.get("posts", [])) + eligible_discovered
            for item in all_refs:
                pts = get_post_sort_ts(item)
                if pts > 0 and pts < cutoff_ts:
                    if item.get("enabled", True):
                        item["enabled"] = False
                        item["auto_paused_reason"] = "max_days"
                        changed = True
                elif pts >= cutoff_ts and item.get("auto_paused_reason") in ("latest_only", "max_posts", "max_days", "page_paused"):
                    item["enabled"] = True
                    item["auto_paused_reason"] = None
                    changed = True

        if changed:
            write_json_safe(self.watchlist_path, watchlist)
            write_json_safe(self.state_path, state)
        return changed

    def run(self, mode: str = "due", target_id: Optional[str] = None) -> None:
        if not self.acquire_lock():
            return

        state = self.load_state()
        try:
            watchlist = self.load_watchlist()
            settings = watchlist.get("settings", {})
            delay_sec = max(6, int(settings.get("delay_seconds", 8)))
            max_batch = max(1, min(100, int(settings.get("max_batch_size", 20))))
            fetch_comments = bool(settings.get("fetch_comments", True))
            expand_replies = bool(settings.get("expand_replies", False))

            self.update_status(state, True, "Đang khởi tạo phiên kết nối Facebook...", error="")
            engine = FacebookTrackerEngine(self.cache_dir, tracker_state=state)
            write_json_safe(self.state_path, state)

            # 1. Xử lý danh sách Fanpage (Page Scanner)
            scanned_page_idents = set()
            latest_page_post_ids: Dict[str, set] = {}
            pages = [p for p in watchlist.get("pages", []) if p.get("enabled", True)]
            for page_cfg in pages:
                p_id = page_cfg.get("id")
                p_ident = page_cfg.get("page_identifier", "").strip()
                if not p_ident:
                    continue
                if mode == "id" and p_id != target_id:
                    continue
                p_state = state["pages"].get(p_id, {})
                if mode == "due" and not self.is_due(p_state.get("next_poll_at")):
                    continue
                if mode == "force_all" and self.recently_polled(p_state.get("last_polled_at"), 120):
                    continue

                scanned_page_idents.add(p_ident)
                limit = max(1, min(20, int(page_cfg.get("limit", 5))))
                self.update_status(state, True, f"Đang quét Fanpage: {p_ident} (lấy {limit} bài)...")
                try:
                    cached_page_id = p_state.get("resolved_page_id")
                    resolved_pid, page_name, latest_posts = engine.get_latest_posts_from_page(
                        p_ident, limit=limit, resolved_id=cached_page_id
                    )
                    ignored_set = set(str(x) for x in state.get("ignored_fb_ids", []))
                    known_fb_ids = {
                        v.get("fb_post_id") for v in state["posts"].values() if v.get("fb_post_id")
                    } | ignored_set
                    new_discovered = 0
                    src_type = page_cfg.get("source_type", "external")
                    for lp in latest_posts:
                        fb_pid = str(lp["post_id"])
                        if fb_pid not in known_fb_ids:
                            disc_id = f"disc_{fb_pid}"
                            v_slug = slugify_text(lp.get("text_snippet", ""), fb_pid)
                            if not any(d.get("id") == disc_id for d in state["discovered_posts"]):
                                state["discovered_posts"].append({
                                    "id": disc_id,
                                    "url": lp["url"],
                                    "fb_post_id": fb_pid,
                                    "source_type": src_type,
                                    "enabled": True,
                                    "from_page_id": p_id,
                                    "from_page": p_ident,
                                    "from_page_name": page_name,
                                    "added_at": now_iso(),
                                })
                                init_metrics = lp.get("metrics") or {"likes": 0, "comments": 0, "shares": 0, "views": 0}
                                # Lưu ngay bộ đệm văn bản và chỉ số tương tác ban đầu từ Timeline
                                self.sync_mgr.save_scraped_post_cache(
                                    fb_post_id=fb_pid,
                                    fb_url=lp["url"],
                                    source_type=src_type,
                                    vault_slug=v_slug,
                                    post_data={
                                        "author_name": lp.get("author_name") or page_name,
                                        "creation_time": lp.get("creation_time"),
                                        "post_text": lp.get("full_text") or lp.get("text_snippet") or "",
                                        "metrics": init_metrics,
                                        "comments_tree": None,
                                    },
                                )
                                state["posts"].setdefault(
                                    disc_id,
                                    {
                                        "fb_post_id": fb_pid,
                                        "vault_slug": v_slug,
                                        "saved_to_vault": False,
                                        "vault_path": None,
                                        "author_name": lp.get("author_name") or page_name,
                                        "title_snippet": lp.get("text_snippet") or f"Bài viết {fb_pid}",
                                        "creation_time": lp.get("creation_time"),
                                        "last_polled_at": None,
                                        "next_poll_at": None,
                                        "last_metrics": init_metrics,
                                    },
                                )
                                known_fb_ids.add(fb_pid)
                                new_discovered += 1

                    page_mins = int(settings.get("page_scan_mins", 60))
                    state["pages"][p_id] = {
                        "page_identifier": p_ident,
                        "resolved_page_id": resolved_pid,
                        "page_name": page_name,
                        "last_polled_at": now_iso(),
                        "next_poll_at": (now_vn() + timedelta(minutes=max(15, page_mins))).isoformat(timespec="seconds"),
                        "last_discovered": new_discovered,
                    }
                    latest_page_post_ids[p_id] = {str(lp["post_id"]) for lp in latest_posts if lp.get("post_id")}
                    write_json_safe(self.state_path, state)
                    time.sleep(max(10, delay_sec))
                except Exception as ex:
                    state["status"]["last_error"] = f"Lỗi quét Page {p_ident}: {ex}"
                    write_json_safe(self.state_path, state)

            # 1.5. Áp dụng ngưỡng tự động ngừng quét bài cũ (Retention Policy: latest_only | max_posts | max_days)
            self.apply_retention_policy(watchlist, state, latest_page_post_ids)

            # 2. Gộp danh sách bài viết từ Watchlist + Bài viết phát hiện tự động từ Fanpage
            all_posts = list(watchlist.get("posts", []))
            existing_ids = {p.get("id") for p in all_posts}
            for dp in state.get("discovered_posts", []):
                if dp.get("id") not in existing_ids:
                    all_posts.append(dp)

            # Lọc danh sách bài viết cần quét trong phiên này
            due_posts = []
            for post_cfg in all_posts:
                if not post_cfg.get("enabled", True):
                    continue
                item_id = post_cfg.get("id")
                p_state = state["posts"].get(item_id, {})
                if mode == "id":
                    is_direct_match = (item_id == target_id)
                    is_from_target_page = (
                        post_cfg.get("from_page_id") == target_id
                        or (post_cfg.get("from_page") in scanned_page_idents and not p_state.get("last_polled_at"))
                    )
                    if is_direct_match or is_from_target_page:
                        due_posts.append(post_cfg)
                    continue

                if p_state.get("inactive", False):
                    continue
                if mode == "due" and not self.is_due(p_state.get("next_poll_at")):
                    continue
                if mode == "force_all" and self.recently_polled(p_state.get("last_polled_at"), 120):
                    continue
                due_posts.append(post_cfg)

            if mode != "id":
                due_posts = due_posts[:max_batch]

            # 3. Thực thi quét tuần tự từng bài viết với Rate-Limit Guard
            total_due = len(due_posts)
            for idx, post_cfg in enumerate(due_posts, start=1):
                item_id = post_cfg.get("id")
                url = post_cfg.get("url", "").strip()
                p_state = state["posts"].get(item_id, {})

                self.update_status(state, True, f"Đang quét bài viết ({idx}/{total_due})...")
                try:
                    # Nguyên tắc vàng 1: Chỉ phân giải URL sang fb_post_id 1 lần duy nhất
                    fb_post_id = p_state.get("fb_post_id") or post_cfg.get("fb_post_id")
                    if not fb_post_id:
                        fb_post_id = engine.resolve_url_to_post_id(url)
                        time.sleep(2)

                    prev_metrics = p_state.get("last_metrics") or {}
                    prev_comments = int(prev_metrics.get("comments", -1))
                    need_initial_comments = fetch_comments and (
                        prev_comments < 0
                        or not p_state.get("last_polled_at")
                        or not self.sync_mgr.has_post_cache(fb_post_id)
                    )

                    # Lần đầu lấy dữ liệu bài viết
                    post_data = engine.fetch_post_metrics(
                        fb_post_id,
                        fetch_comments_tree=need_initial_comments,
                        expand_sub_replies=expand_replies,
                    )

                    if post_data.get("inactive"):
                        fail_cnt = int(p_state.get("fail_count", 0)) + 1
                        p_state["fail_count"] = fail_cnt
                        if fail_cnt >= 3:
                            p_state["inactive"] = True
                        state["posts"][item_id] = p_state
                        write_json_safe(self.state_path, state)
                        continue

                    cur_metrics = post_data["metrics"]
                    # Nguyên tắc vàng 3: Chỉ cào lại cây bình luận khi số bình luận tăng lên
                    if fetch_comments and prev_comments >= 0 and cur_metrics["comments"] > prev_comments:
                        post_data = engine.fetch_post_metrics(
                            fb_post_id,
                            fetch_comments_tree=True,
                            expand_sub_replies=expand_replies,
                        )
                        cur_metrics = post_data["metrics"]

                    # Lưu bộ đệm JSON và chỉ cập nhật file Markdown nếu đã tồn tại trong Vault
                    vault_slug, is_saved, vault_rel_path = self.sync_mgr.sync_existing_markdown_note(
                        fb_post_id=fb_post_id,
                        fb_url=url,
                        source_type=post_cfg.get("source_type", "external"),
                        post_data=post_data,
                        existing_slug=p_state.get("vault_slug") or post_cfg.get("vault_slug"),
                    )

                    # Ghi điểm vào .content-pipeline/engagement/YYYY-MM.json
                    self.sync_mgr.append_engagement_record(vault_slug, cur_metrics)

                    # Kiểm tra mức độ biến động để tính lịch Adaptive Polling (Khóa cứng an toàn IP)
                    unchanged = (
                        cur_metrics.get("likes") == prev_metrics.get("likes")
                        and cur_metrics.get("comments") == prev_metrics.get("comments")
                        and cur_metrics.get("shares") == prev_metrics.get("shares")
                    )
                    no_change_cnt = (int(p_state.get("consecutive_no_change", 0)) + 1) if unchanged else 0
                    creation_time = post_data.get("creation_time") or p_state.get("creation_time")

                    next_poll = self.compute_next_poll(
                        creation_time=creation_time,
                        consecutive_no_change=no_change_cnt,
                        settings=settings,
                        custom_mins=0,
                    )

                    raw_text_full = (post_data.get("post_text") or "").strip()
                    first_sentence = raw_text_full.split("\n")[0].strip() if raw_text_full else ""
                    snippet_val = (first_sentence or p_state.get("title_snippet") or f"Bài viết {fb_post_id}")[:120]

                    state["posts"][item_id] = {
                        "fb_post_id": fb_post_id,
                        "vault_slug": vault_slug,
                        "saved_to_vault": is_saved,
                        "vault_path": vault_rel_path,
                        "author_name": post_data.get("author_name") or p_state.get("author_name") or "Facebook",
                        "title_snippet": snippet_val,
                        "creation_time": creation_time,
                        "last_polled_at": now_iso(),
                        "next_poll_at": next_poll,
                        "last_metrics": {
                            "likes": cur_metrics["likes"],
                            "comments": cur_metrics["comments"],
                            "shares": cur_metrics["shares"],
                            "views": cur_metrics["views"],
                        },
                        "consecutive_no_change": no_change_cnt,
                        "fail_count": 0,
                        "inactive": False,
                    }
                    write_json_safe(self.state_path, state)

                    if idx < total_due:
                        time.sleep(delay_sec)

                except RuntimeError as rex:
                    if "RATE_LIMIT_429" in str(rex):
                        # Circuit Breaker: Dừng ngay toàn bộ hàng đợi nếu bị cảnh báo Rate Limit
                        self.update_status(
                            state,
                            False,
                            "Tạm dừng bảo vệ IP (HTTP 429)",
                            error="Phát hiện giới hạn tốc độ từ Facebook. Đã tự động ngắt hàng đợi.",
                        )
                        return
                except Exception as ex:
                    state["status"]["last_error"] = f"Lỗi bài {url[:40]}: {ex}"
                    write_json_safe(self.state_path, state)

            self.update_status(state, False, f"Hoàn tất ({total_due} bài đã cập nhật)")
        finally:
            self.release_lock()


# ==============================================================================
# NHÓM CODE 5: Quản lý Tác vụ chạy ngầm Windows Task Scheduler & CLI Entrypoint
# Ý nghĩa: Đăng ký hoặc gỡ bỏ tác vụ chạy ẩn (`pythonw.exe`) mỗi 15 phút trên
# Windows để việc thu thập dữ liệu hoạt động độc lập ngay cả khi đóng Obsidian.
# ==============================================================================
TASK_NAME = "ContentCompass_FBTracker"


def manage_windows_task(enable: bool, script_path: Path, vault_dir: Path) -> None:
    wl_path = vault_dir / ".content-pipeline" / "fb-watchlist.json"
    wl_data = read_json_safe(wl_path, {"settings": {}, "posts": [], "pages": []})
    wl_data.setdefault("settings", {})

    if enable:
        py_exe = Path(sys.executable)
        pyw_exe = py_exe.with_name("pythonw.exe")
        runner = str(pyw_exe if pyw_exe.exists() else py_exe)
        task_cmd = f'"{runner}" "{script_path.resolve()}" --vault "{vault_dir.resolve()}" --run-due'
        subprocess.run(
            ["schtasks", "/Create", "/TN", TASK_NAME, "/TR", task_cmd, "/SC", "MINUTE", "/MO", "15", "/F"],
            check=True,
            capture_output=True,
            text=True,
        )
        wl_data["settings"]["background_task_enabled"] = True
    else:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
        wl_data["settings"]["background_task_enabled"] = False

    write_json_safe(wl_path, wl_data)


def _find_native_browser_exe() -> Optional[str]:
    """Tìm trình duyệt Google Chrome hoặc Microsoft Edge thật có sẵn trên Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def launch_isolated_browser_cookie_extractor(vault_dir: Path, timeout_sec: int = 300) -> None:
    """
    Phương án B: Mở một cửa sổ Chrome/Edge thật với hồ sơ cách ly hoàn toàn (`burner_chrome_profile`),
    tự động lắng nghe qua giao thức CDP nội bộ, ngay khi phát hiện người dùng đăng nhập xong nick phụ
    (có đủ `c_user`, `xs`, `datr`) thì trích xuất toàn bộ Cookie lưu vào `auth_cookies.json` và
    gửi lệnh CDP `Browser.close` để đóng trình duyệt êm ái.
    """
    orchestrator = TrackerOrchestrator(vault_dir)
    state = orchestrator.load_state()
    browser_exe = _find_native_browser_exe()
    if not browser_exe:
        orchestrator.update_status(
            state, False, "Lỗi mở trình duyệt", error="Không tìm thấy Google Chrome hoặc Microsoft Edge trên máy."
        )
        return

    profile_dir = orchestrator.cache_dir / "burner_chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    auth_cookie_path = orchestrator.cache_dir / "auth_cookies.json"
    port = _find_free_port()

    orchestrator.update_status(
        state,
        True,
        "Đang mở cửa sổ trình duyệt riêng cho nick Facebook phụ... Hãy đăng nhập trên cửa sổ vừa bật (tự động đóng sau khi xong).",
        error="",
    )

    cmd = [
        browser_exe,
        f"--user-data-dir={profile_dir.resolve()}",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "https://www.facebook.com/",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    http_local = cffi_requests.Session()
    start_ts = time.time()
    captured_cookies: List[Dict[str, Any]] = []

    try:
        while time.time() - start_ts < timeout_sec:
            if proc.poll() is not None:
                break
            try:
                resp = http_local.get(f"http://127.0.0.1:{port}/json", timeout=2)
                targets = resp.json() if resp.status_code == 200 else []
                ws_url = None
                for t in targets:
                    if isinstance(t, dict) and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    ws = http_local.ws_connect(ws_url, timeout=3)
                    try:
                        ws.send_json({"id": 1, "method": "Network.getAllCookies"})
                        msg = ws.recv_json(timeout=3)
                        all_cookies = ((msg or {}).get("result") or {}).get("cookies") or []
                        fb_cookies = [
                            c for c in all_cookies
                            if isinstance(c, dict) and "facebook.com" in str(c.get("domain", ""))
                        ]
                        names = {c.get("name") for c in fb_cookies}
                        if "c_user" in names and "xs" in names and "datr" in names:
                            captured_cookies = fb_cookies
                            try:
                                ws.send_json({"id": 2, "method": "Browser.close"})
                            except Exception:
                                pass
                            break
                    finally:
                        ws.close()
            except Exception:
                pass
            time.sleep(2.0)
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                pass

    if captured_cookies:
        write_json_safe(auth_cookie_path, captured_cookies)
        c_user_val = next((str(c.get("value")) for c in captured_cookies if c.get("name") == "c_user"), "")
        state["auth_status"] = {
            "connected": True,
            "c_user": c_user_val,
            "has_datr": True,
            "circuit_broken": False,
            "cookies_mtime": int(auth_cookie_path.stat().st_mtime),
            "updated_at": now_iso(),
            "last_auth_error": None,
        }
        orchestrator.update_status(
            state,
            False,
            f"Đã kết nối nick Facebook phụ (ID: {c_user_val}) thành công!",
            error="",
        )
    else:
        orchestrator.update_status(
            state,
            False,
            "Chưa nhận được phiên đăng nhập nick Facebook phụ (cửa sổ đã đóng).",
        )


def logout_auth_cookie(vault_dir: Path) -> None:
    """Xóa file auth_cookies.json và auth_facebook_state.json để ngắt kết nối nick Facebook phụ khỏi hệ thống."""
    orchestrator = TrackerOrchestrator(vault_dir)
    state = orchestrator.load_state()
    auth_cookie_path = orchestrator.cache_dir / "auth_cookies.json"
    auth_state_path = orchestrator.cache_dir / "auth_facebook_state.json"
    for p in (auth_cookie_path, auth_state_path):
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
    state["auth_status"] = {
        "connected": False,
        "c_user": None,
        "has_datr": False,
        "circuit_broken": False,
        "cookies_mtime": 0,
        "updated_at": now_iso(),
        "last_auth_error": None,
    }
    orchestrator.update_status(state, False, "Đã gỡ kết nối nick Facebook phụ (Chạy 100% chế độ Không Cookie).", error="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Facebook Realtime Tracker for Content Compass")
    parser.add_argument("--vault", type=str, default=None, help="Đường dẫn thư mục vault")
    parser.add_argument("--run-due", action="store_true", help="Quét các bài/Fanpage đã đến hạn")
    parser.add_argument("--force-all", action="store_true", help="Quét cập nhật ngay toàn bộ danh sách")
    parser.add_argument("--force-id", type=str, default=None, help="Quét ngay 1 mục theo ID")
    parser.add_argument("--login-auth", action="store_true", help="Mở cửa sổ Chrome cách ly để đăng nhập nick phụ")
    parser.add_argument("--logout-auth", action="store_true", help="Gỡ bỏ Cookie nick phụ khỏi hệ thống")
    parser.add_argument("--register-task", action="store_true", help="Đăng ký Windows Task Scheduler chạy ngầm")
    parser.add_argument("--unregister-task", action="store_true", help="Gỡ bỏ Windows Task Scheduler")
    args = parser.parse_args()

    script_file = Path(__file__).resolve()
    vault_dir = Path(args.vault).resolve() if args.vault else (script_file.parent.parent.parent / "vault").resolve()

    if args.register_task:
        manage_windows_task(True, script_file, vault_dir)
        return
    if args.unregister_task:
        manage_windows_task(False, script_file, vault_dir)
        return
    if args.login_auth:
        launch_isolated_browser_cookie_extractor(vault_dir)
        return
    if args.logout_auth:
        logout_auth_cookie(vault_dir)
        return

    orchestrator = TrackerOrchestrator(vault_dir)
    if args.force_id:
        orchestrator.run(mode="id", target_id=args.force_id)
    elif args.force_all:
        orchestrator.run(mode="force_all")
    else:
        orchestrator.run(mode="due")


if __name__ == "__main__":
    main()

