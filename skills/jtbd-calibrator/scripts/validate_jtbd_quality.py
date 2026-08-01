"""
Ten file: validate_jtbd_quality.py
Last update: 28/07/2026 17:20 (GMT+7)
Vai tro: Script kiem tra chat luong JTBD sau khi LLM calibrate.
Su dung khi: Duoc goi tu dong boi prepare_calibration_batches.py khi submit.
  Co the chay doc lap de debug: python validate_jtbd_quality.py <path_to_json>
Output: Console report voi vi pham. Exit code 0 = CLEAN, 1 = co vi pham.
Tom tat logic: Doc JSON (co structure {"password":"...", "entries":[...]}),
  quet tung entry theo danh sach keyword cam, xuat bao cao theo tung uid.
"""

import json
import sys
import re
import os

# === DANH SACH TU KHOA CAM (xuat hien = vi pham, submit BI TU CHOI) ===

# -- Main Job: compound, menh de muc dich, cam xuc, qualifying adj, ongoing verbs --
BANNED_MAIN_JOB = [
    # #2 Compound (phai don tri)
    (r"\bvà\b", "#2 Compound: chua 'va'"),
    (r"\bhoặc\b", "#2 Compound: chua 'hoac'"),
    (r"\band\b", "#2 Compound: chua 'and'"),
    (r"\bor\b", "#2 Compound: chua 'or'"),
    # Menh de muc dich (Need/Why — 4.3, #12)
    (r"\bđể\b", "#12 Need/Why: Tu 'de' phat hien. Kiem tra noi dung sau 'de': neu la hoat dong phang (xem Luu y 4.3.2) thi hop le — giu lai; neu chua Need/Why thi xoa menh de muc dich"),
    (r"\bnhằm\b", "#12 Need/Why: Menh de muc dich 'nham'"),
    (r"\bsao cho\b", "#12 Need/Why: Menh de muc dich 'sao cho'"),
    (r"\bin order to\b", "#12 Need/Why: Menh de muc dich 'in order to'"),
    (r"\bso that\b", "#12 Need/Why: Menh de muc dich 'so that'"),
    # #1 Prefix cam
    (r"^giúp\b", "#1 Prefix: bat dau bang 'giup'"),
    (r"\bhelp me\b", "#1 Prefix: chua 'help me'"),
    # Cam xuc / menh de phu cam xuc (Need/Why — 4.3, #11)
    (r"\bmà không\b", "#11 Need/Why: Menh de cam xuc 'ma khong...'"),
    (r"\btận hưởng\b", "#11 Need/Why: Emotional outcome 'tan huong'"),
    (r"\byêu thích\b", "#11 Need/Why: Emotional outcome 'yeu thich'"),
    # Qualifying adjectives (Need/Why — 4.3, #10)
    (r"\bmột cách\b", "#10 Need/Why: Trang tu chi chat luong 'mot cach...'"),
    (r"\btoàn diện\b", "#10 Need/Why: Qualifying adj 'toan dien'"),
    (r"\bhiệu quả\b", "#10 Need/Why: Qualifying adj 'hieu qua'"),
    (r"\ban toàn\b", "#10 Need/Why: Qualifying adj 'an toan'"),
    (r"\blành mạnh\b", "#10 Need/Why: Qualifying adj 'lanh manh'"),
    (r"\bchính xác\b", "#10 Need/Why: Qualifying adj 'chinh xac'"),
    (r"\bbền vững\b", "#10 Need/Why: Qualifying adj 'ben vung'"),
    (r"\btối ưu\b", "#10 Need/Why: Qualifying adj 'toi uu'"),
    (r"\bnhanh\b", "#10 Need/Why: Qualifying adj 'nhanh'"),
    (r"\bdễ dàng\b", "#10 Need/Why: Qualifying adj 'de dang'"),
    (r"\bthành công\b", "#10 Need/Why: Qualifying adj 'thanh cong'"),
    # #4 Dong tu ongoing (khong co trang thai ket thuc)
    (r"\bquản lý\b", "#4 Ongoing verb: 'quan ly'"),
    (r"\bduy trì\b", "#4 Ongoing verb: 'duy tri'"),
    (r"\bhọc hỏi\b", "#4 Ongoing verb: 'hoc hoi'"),
    (r"\btheo kịp\b", "#4 Ongoing verb: 'theo kip'"),
    (r"\bchăm sóc\b", "#4 Ongoing verb: 'cham soc'"),
    (r"\bnuôi dưỡng\b", "#4 Ongoing verb: 'nuoi duong'"),
    (r"\bkiểm soát\b", "#4 Ongoing verb: 'kiem soat'"),
    (r"\bdạy\b", "#4 Ongoing verb: 'day'"),
    (r"\bnuôi dạy\b", "#4 Ongoing verb: 'nuoi day'"),
    (r"\bkhuyến khích\b", "#4 Ongoing verb: 'khuyen khich'"),
    (r"\bkỷ luật\b", "#4 Ongoing verb: 'ky luat'"),
]

# -- Circumstance: menh de muc dich, cam xuc, qualifying adj --
BANNED_CIRCUMSTANCE = [
    (r"\bđể\b", "#12 Need/Why: Tu 'de' phat hien. Kiem tra noi dung sau 'de': neu la hoat dong phang (xem Luu y 4.3.2) thi hop le — giu lai; neu chua Need/Why thi xoa menh de muc dich"),
    (r"\bnhằm\b", "#12 Need/Why: Menh de muc dich 'nham'"),
    (r"\bsao cho\b", "#12 Need/Why: Menh de muc dich 'sao cho'"),
    (r"\bin order to\b", "#12 Need/Why: Menh de muc dich 'in order to'"),
    (r"\bso that\b", "#12 Need/Why: Menh de muc dich 'so that'"),
    (r"\bmà không\b", "#11 Need/Why: Menh de cam xuc 'ma khong...'"),
    (r"\bmột cách\b", "#10 Need/Why: Trang tu chi chat luong 'mot cach...'"),
    (r"\btoàn diện\b", "#10 Need/Why: Qualifying adj 'toan dien'"),
    (r"\bhiệu quả\b", "#10 Need/Why: Qualifying adj 'hieu qua'"),
    (r"\ban toàn\b", "#10 Need/Why: Qualifying adj 'an toan'"),
    (r"\blành mạnh\b", "#10 Need/Why: Qualifying adj 'lanh manh'"),
    (r"\bchính xác\b", "#10 Need/Why: Qualifying adj 'chinh xac'"),
    (r"\bnhanh\b", "#10 Need/Why: Qualifying adj 'nhanh'"),
    (r"\bdễ dàng\b", "#10 Need/Why: Qualifying adj 'de dang'"),
    (r"\btận hưởng\b", "#11 Need/Why: Emotional outcome 'tan huong'"),
]

# === KIEM TRA CAU TRUC CIRCUMSTANCE ===

def check_circumstance_structure(value):
    """Kiem tra Circumstance bat dau bang 'khi'/'trong khi'/'trong luc'/'when'/'while'.
    Tra ve None neu hop le, hoac message loi neu vi pham."""
    if not value or not value.strip():
        return "#8 Circumstance trong (empty) — can dien gia tri."
    v = value.strip().lower()
    if not (v.startswith("khi ") or v.startswith("trong khi ")
            or v.startswith("trong lúc ")
            or v.startswith("when ") or v.startswith("while ")):
        return "#8 Circumstance KHONG bat dau bang 'Khi...'/'Trong khi...'/'Trong luc...'"
    return None

# === HAM QUET ===

def scan_field(value, banned_list):
    """Quet 1 gia tri theo danh sach keyword cam. Tra ve list vi pham."""
    violations = []
    for pattern, msg in banned_list:
        if re.search(pattern, value, re.IGNORECASE):
            violations.append(msg)
    return violations

def validate_file(filepath):
    """Kiem tra chat luong JTBD trong file JSON.
    Tra ve (total_violations, report_text).
    JSON structure: {"password":"...", "entries":[{"uid":"...", "audience_main_job":"...", ...}]}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        return 0, ""

    total_violations = 0
    lines = []

    for entry in entries:
        uid = entry.get("uid", "unknown")
        main_job = entry.get("audience_main_job", "")
        circumstance = entry.get("audience_circumstance", "")

        entry_violations = []

        # -- Quet main_job --
        for v in scan_field(main_job, BANNED_MAIN_JOB):
            entry_violations.append(f"main_job: {v}")

        # -- Quet circumstance --
        for v in scan_field(circumstance, BANNED_CIRCUMSTANCE):
            entry_violations.append(f"circumstance: {v}")

        # -- Kiem tra cau truc circumstance --
        struct_err = check_circumstance_structure(circumstance)
        if struct_err:
            entry_violations.append(f"circumstance: {struct_err}")

        # -- Ghi bao cao --
        if entry_violations:
            lines.append(f"\n--- [{uid}] ---")
            lines.append(f'  main_job: "{main_job}"')
            lines.append(f'  circumstance: "{circumstance}"')
            for v in entry_violations:
                lines.append(f"  \U0001f6d1 {v}")
                total_violations += 1

    return total_violations, "\n".join(lines)

# === MAIN ===

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_jtbd_quality.py <path_to_calib_eval_temp.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File khong ton tai: {filepath}")
        sys.exit(1)

    total_violations, report = validate_file(filepath)

    if report:
        print(report)

    print(f"\n{'='*50}")
    if total_violations == 0:
        print("\u2705 CLEAN — Khong phat hien vi pham.")
        sys.exit(0)
    else:
        print(f"\U0001f6d1 CO {total_violations} VI PHAM — SUBMIT BI TU CHOI. Sua va nop lai.")
        sys.exit(1)

if __name__ == "__main__":
    main()
