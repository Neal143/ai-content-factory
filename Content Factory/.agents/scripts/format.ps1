$ErrorActionPreference = "Stop"
$draft = Get-Content "output/runs/2026-05-25_dieu_hoa_cam_xuc/05-draft.md" -Raw -Encoding UTF8

$fm = "---`r`ntitle: `"Không Dùng Logic Khi Con Đang Hoảng Loạn`"`r`ndate: 2026-05-26`r`npillar: `"Cửa sổ vàng phát triển trẻ 0-7 tuổi`"`r`ntopic: `"dieu_hoa_cam_xuc`"`r`nhook_formula: `"F15`"`r`nword_count: 1691`r`nqa_score: 130/130`r`nstatus: published`r`n---`r`n`r`n"

$finalContent = $fm + $draft + "`r`n<!-- execution_key: 031642eb -->"
Set-Content -Path "output/runs/2026-05-25_dieu_hoa_cam_xuc/07-final.md" -Value $finalContent -Encoding UTF8 -NoNewline

$post = $draft -replace '(?m)^<!--\s*(execution_key|bundle_key|ref_keys|TITLE|SECTION|SECTION_HEADING|PARAGRAPH|PARAGRAPH_HEADING).*-->\r?\n?', ''
$post = $post -replace $([char]0x2042), '.'


$finalPost = $fm + $post.Trim() + "`r`n"
Set-Content -Path "output/posts/2026-05-26-dieu_hoa_cam_xuc.md" -Value $finalPost -Encoding UTF8 -NoNewline
