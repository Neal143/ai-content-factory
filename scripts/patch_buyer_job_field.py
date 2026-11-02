"""
Tên file: patch_buyer_job_field.py
Last update: 23/10/2026 19:55 (GMT+7)
Vai trò: Bổ sung trường is_buyer_job vào toàn bộ 26 file Audience Markdown và _audience_index.yaml.
Được sử dụng khi nào?: Chạy một lần trong Phase P2 (Data Contract) hoặc khi cần migrate schema.
Output: Cập nhật 26 file trong vault/01-Atomic/Audiences/*.md và file _audience_index.yaml.
Tóm tắt logic hoạt động:
  1. Quét toàn bộ file .md trong vault/01-Atomic/Audiences/.
  2. Với mỗi file, kiểm tra Frontmatter: nếu chưa có 'is_buyer_job:', tìm vị trí kết thúc của 'next_job_step'
     (hỗ trợ cả inline 'next_job_step: []', block rỗng 'next_job_step:', hoặc danh sách lồng)
     và chèn dòng 'is_buyer_job:' (bỏ trống).
  3. Cập nhật _audience_index.yaml: chèn '  is_buyer_job:' sau 'parent_audience' cho từng audience entry.
  4. Ghi đè UTF-8 nguyên vẹn không làm hỏng format hay BOM.
"""

# Nhóm 1: Import thư viện hệ thống
import os
import re
import sys

# Đảm bảo UTF-8 cho console output trên Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Nhóm 2: Định nghĩa các đường dẫn cơ sở
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_FACTORY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
AUDIENCES_DIR = os.path.join(CONTENT_FACTORY_DIR, "vault", "01-Atomic", "Audiences")
INDEX_FILE = os.path.join(AUDIENCES_DIR, "_audience_index.yaml")

# Nhóm 3: Xử lý cập nhật các file Audience .md
def patch_audience_md_files():
    if not os.path.exists(AUDIENCES_DIR):
        print(f"❌ Không tìm thấy thư mục: {AUDIENCES_DIR}")
        return 0

    patched_count = 0
    skipped_count = 0

    md_files = [f for f in os.listdir(AUDIENCES_DIR) if f.endswith(".md")]
    print(f"🔍 Tìm thấy {len(md_files)} file Markdown trong {AUDIENCES_DIR}")

    for filename in sorted(md_files):
        filepath = os.path.join(AUDIENCES_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Kiểm tra khối Frontmatter
        if not content.startswith("---"):
            print(f"  ⚠️ Bỏ qua (không có frontmatter): {filename}")
            skipped_count += 1
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"  ⚠️ Bỏ qua (lỗi format frontmatter): {filename}")
            skipped_count += 1
            continue

        fm_text = parts[1]
        body = parts[2]

        # Kiểm tra xem trường is_buyer_job đã tồn tại chưa
        if re.search(r"^is_buyer_job:", fm_text, re.MULTILINE):
            print(f"  ⏭️ Đã có trường is_buyer_job: {filename}")
            skipped_count += 1
            continue

        lines = fm_text.splitlines()
        insert_idx = -1

        # Tìm dòng next_job_step
        for i, line in enumerate(lines):
            if re.match(r"^next_job_step:", line.strip()):
                insert_idx = i
                # Nếu là block array xuống dòng, quét hết các item con (- ...)
                j = i + 1
                while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                    insert_idx = j
                    j += 1
                break

        # Nếu không có next_job_step, tìm parent_audience
        if insert_idx == -1:
            for i, line in enumerate(lines):
                if re.match(r"^parent_audience:", line.strip()):
                    insert_idx = i
                    j = i + 1
                    while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                        insert_idx = j
                        j += 1
                    break

        if insert_idx == -1:
            # Nếu cả 2 đều không có, chèn vào cuối frontmatter
            lines.append("is_buyer_job:")
        else:
            lines.insert(insert_idx + 1, "is_buyer_job:")

        # Tái cấu trúc lại file
        new_fm = "\n".join(lines)
        # Giữ nguyên cấu trúc xuống dòng ban đầu của frontmatter
        if not new_fm.endswith("\n"):
            new_fm += "\n"
        new_content = f"---{new_fm}---{body}"

        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)

        patched_count += 1
        print(f"  ✅ Đã bổ sung is_buyer_job: {filename}")

    print(f"📊 Kết quả cập nhật Audience .md: {patched_count} file đã cập nhật, {skipped_count} file bỏ qua.")
    return patched_count

# Nhóm 4: Xử lý cập nhật file _audience_index.yaml
def patch_audience_index():
    if not os.path.exists(INDEX_FILE):
        print(f"❌ Không tìm thấy file index: {INDEX_FILE}")
        return False

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    patched_entries = 0
    in_parent_block = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Phát hiện bắt đầu khối parent_audience trong entry
        if re.match(r"^\s+parent_audience:", line):
            if "[]" in line:
                # Dạng inline: parent_audience: []
                # Kiểm tra dòng tiếp theo xem đã có is_buyer_job chưa
                if i + 1 < len(lines) and "is_buyer_job:" in lines[i + 1]:
                    continue
                new_lines.append("  is_buyer_job:")
                patched_entries += 1
            else:
                # Dạng block array, bật cờ theo dõi
                in_parent_block = True
            continue

        if in_parent_block:
            # Kiểm tra xem dòng hiện tại còn là item con của parent_audience hay không
            next_line_is_sub = (i + 1 < len(lines)) and re.match(r"^\s+-\s+", lines[i + 1])
            if not next_line_is_sub:
                # Hết block parent_audience
                in_parent_block = False
                if i + 1 < len(lines) and "is_buyer_job:" in lines[i + 1]:
                    continue
                new_lines.append("  is_buyer_job:")
                patched_entries += 1

    new_content = "\n".join(new_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    with open(INDEX_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)

    print(f"📊 Kết quả cập nhật _audience_index.yaml: {patched_entries} entry đã được bổ sung is_buyer_job.")
    return True

# Nhóm 5: Hàm main thực thi
def main():
    print("🚀 Bắt đầu cập nhật schema Data Contract (is_buyer_job)...")
    patch_audience_md_files()
    patch_audience_index()
    print("✨ Hoàn tất cập nhật schema!")

if __name__ == "__main__":
    main()
