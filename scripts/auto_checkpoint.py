"""
TEN SCRIPT: auto_checkpoint.py
LAST UPDATE: 23/08/2026 00:52 (GMT+7)
VAI TRO: Generic utility - Tu dong checkpoint data cho bat ky workflow/script nao.
SU DUNG KHI NAO: Import boi bat ky script nao can tu dong luu trang thai data
                  (VD: book-extractor exit scripts, content-post, vault-curation...).
OUTPUT: Goi save_progress.ps1 voi Label (auto-timestamp) va Description.

================================================================================
HUONG DAN THIET KE LABEL & DESCRIPTION (BEST PRACTICES):
================================================================================

1. QUY TAC DAT `label`:
   - Cau truc: "<workflow-slug>-<phase-or-step-slug>"
   - Format: Chu thuong (lowercase), dung dau gach ngang (-), khong chua dau cach hoac ky tu dac biet.
   - Luu y: auto_checkpoint() se TU DONG gan them timestamp "-%Y%m%d-%H%M%S" vao sau label
     de dam bao tag trong git (.save-data/) luon DUY NHAT tuyet doi (khong so duplicate).
   - Vi du:
     + "beyond-the-rainbow-bridge_2026-08-22-phase1"
     + "content-post-draft-generation"
     + "vault-curator-atom-dedup"

2. QUY TAC DAT `description`:
   - Cau truc chuan 3 thanh phan:
     "<Ten Workflow> (<Ten Cong Doan / Phase / Step>) - <Dinh Danh Doi Tuong / Run Slug>"
   - Format: Khuyen khich dung tieng Anh hoac tieng Viet khong dau (unaccented) de tuong thich
     an toan 100% giua cac tien trinh PowerShell tren Windows.
   - Vi du mau cho cac he thong khac nhau:
     + Book Extractor: "Book Extractor (Phase 2: Vivid Curation) - beyond-the-rainbow-bridge_2026-08-22"
     + Content Post:   "Content Creator (Step 2: Draft Generation) - post_ai_agent_2026-08-23"
     + Vault Curation: "Vault Curator (Pipeline: Atom Deduplication) - vault_atoms_batch_01"

3. MAU CODE TICH HOP (CODE SNIPPETS):

   A. Neu script nam trong '.agents/scripts/' (cung thu muc):
      try:
          from auto_checkpoint import auto_checkpoint
          auto_checkpoint(label, description)
      except Exception:
          pass

   B. Neu script nam trong '.agents/skills/<skill_name>/scripts/':
      try:
          import sys, os
          _AGENTS_SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))
          sys.path.insert(0, _AGENTS_SCRIPTS)
          from auto_checkpoint import auto_checkpoint
          auto_checkpoint(label, description)
      except Exception:
          pass

================================================================================
TOM TAT LOGIC:
  1. Nhan label va description tu caller.
  2. Sinh Label: "{slug}-{YYYYMMDD-HHMMSS}" (dam bao duy nhat).
  3. Goi subprocess: powershell save_progress.ps1 -Action save.
  4. Fail-safe: Moi loi deu bi bat im lang, khong anh huong script goi.
"""

import os
import subprocess
from datetime import datetime, timezone, timedelta


def auto_checkpoint(label, description=None):
    """
    Generic data checkpoint utility.

    Args:
        label: Base slug identifier (VD: "book-phase2", "content-draft").
               Timestamp tu dong append de dam bao duy nhat.
        description: Mo ta ngan. Mac dinh = label neu khong truyen.

    Usage:
        from auto_checkpoint import auto_checkpoint
        auto_checkpoint("book-phase1", "Book Extractor (Phase 1: Raw Mining) - slug_2026-08-22")
    """
    try:
        # -- Append timestamp de dam bao label duy nhat --
        vn_tz = timezone(timedelta(hours=7))
        ts = datetime.now(vn_tz).strftime("%Y%m%d-%H%M%S")
        full_label = f"{label}-{ts}"

        if not description:
            description = label

        # -- Resolve duong dan save_progress.ps1 (cung thu muc) --
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps1_path = os.path.join(script_dir, "save_progress.ps1")

        if not os.path.exists(ps1_path):
            return

        # -- CWD = Factory root (2 levels up tu .agents/scripts/) --
        factory_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

        # -- Goi save_progress.ps1 --
        subprocess.run(
            [
                "powershell", "-ExecutionPolicy", "Bypass",
                "-File", ps1_path,
                "-Action", "save",
                "-Label", full_label,
                "-Description", description
            ],
            cwd=factory_root,
            capture_output=True,
            timeout=30
        )

    except Exception:
        pass  # Fail-safe: never crash the calling script
