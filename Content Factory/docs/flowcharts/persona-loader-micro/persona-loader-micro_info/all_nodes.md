# Giải thích các Node trong Sơ đồ persona-loader

## read_files
Dùng tool `view_file` đọc lần lượt 3 file tại `[Persona_Path]`:
1. `[Persona_Path]/voice-dna.yaml`
2. `[Persona_Path]/profile.yaml`
3. `[Persona_Path]/authorities.yaml`
Sau khi đọc, ghi nhận giá trị `FILE_KEY` (dòng `# FILE_KEY: ...`).

## fail_file_not_found
Quy định: `⛔ FATAL RULE`: Bắt buộc đọc thành công cả 3. Nếu File Not Found → DỪNG, BÁO USER.

## read_bb
Đọc `resolved_jtbd` từ `00-blackboard.yaml` trong run folder.
Trích xuất: `audience_Job_performer`, `audience_main_job`, `audience_circumstance`.

## compile_pack
Compile thành file `04.5-persona-pack.md` trong run folder theo format cấu trúc (Verbatim 100%):
```markdown
[System Context: JTBD Anchor]
Job Performer: {audience_Job_performer}
Main Job: {audience_main_job}
Circumstance: {audience_circumstance}

[Voice DNA]
Pronouns: self={self} | audience={audience} | expert={expert_after_intro} | banned={banned}
Tone: {primary} / {personality}
Language: {language} | Formality: {formality}
Fillers: {library} (min: {min_per_post}, max: {max_per_post})
Parentheticals: enabled={enabled} | {library} (min: {min_per_post}, max: {max_per_post})
Engagement: frequency={frequency} | patterns={patterns} | max_gap={max_gap}
Anti-patterns: no_dash={no_dash} | no_staccato={no_staccato} | no_anaphora={no_anaphora} | no_repetitive={no_repetitive} | language_purity={language_purity} | banned_words={banned_words}
Techniques: killer_statements={killer_statements} | concrete_imagery_min={concrete_imagery_min} | redefinition={redefinition} | narrative_schedule={narrative_schedule}
Extra: sentence_rhythm | analogy_style | closing_style | emotional_register | humor_style | argumentation_style | stance

[Profile]
Name: {name} ({nickname})
Title: {title} | Experience: {experience}
Signature: {signature_phrase}
Authority: {authority_claims}
Approach: {content_approach}

[Authorities]
{experts list với name, field, credentials, cascade, used_count, note}
Citation patterns: {citation_patterns}
Diversity rule: {diversity_rule}
```

## write_keys
Append cuối file `04.5-persona-pack.md` các key:
```markdown
<!-- execution_key: [EXECUTION_KEY từ SKILL.md] -->
<!-- persona_keys: voice-dna=[key1], profile=[key2], authorities=[key3] -->
```

## validate_pack
Script `validate-persona-pack.ps1` kiểm tra tính hợp lệ.
Check 1: File tồn tại và không rỗng.

## fail_pack_missing
Nếu không tồn tại: `[FAIL] 04.5-persona-pack.md not found: $PackPath` (Exit 1).
Nếu file rỗng: `[FAIL] 04.5-persona-pack.md is empty` (Exit 1).

## check_sections
Check 2: 4 section headers bắt buộc phải có mặt (Regex match string): `[Voice DNA]`, `[JTBD Anchor]`, `[Profile]`, `[Authorities]`.

## check_fields
Check 3: Các field cực kỳ quan trọng không được rỗng (Regex match):
- `Pronouns:\s*self=\S+`
- `Job Performer:\s*\S+`
- `Name:\s*\S+`

## check_keys
Check 4: `persona_keys` phải đủ 3 key và khớp với file gốc.
Bảng cấu hình các file mong đợi (Verbatim):
```powershell
$expectedFiles = @(
    @{ Label = "voice-dna";   File = "voice-dna.yaml" },
    @{ Label = "profile";     File = "profile.yaml" },
    @{ Label = "authorities"; File = "authorities.yaml" }
)
```
Regex trích xuất từ pack: `persona_keys:\s*(.+?)-->` và vòng lặp tách key `(\S+)=(\S+)`.
Regex trích xuất từ file gốc: `# FILE_KEY:\s*(\S+)`.

## fail_format
Lỗi tương ứng với từng validation bị fail, đánh cờ `$failed = $true` và gọi `exit 1` ở cuối:
- Missing section: `[FAIL] Missing section: $section`
- Missing field: `[FAIL] Critical field empty or missing: $($cp.Name)`
- Mất file YAML gốc: `[FAIL] Persona file not found: $yamlPath`
- Thiếu key: `[FAIL] Missing key for $($ef.Label): source=$sourceKey pack=$packKey`
- Lệch key: `[FAIL] Key mismatch $($ef.Label): source=$sourceKey pack=$packKey`

## rotate_key
Check 5: Rotate `voice-dna.yaml` FILE_KEY (Idempotent).
Mục đích: Ép Phase 6 (QA Checker) phải đọc lại `voice-dna.yaml` thật sự để lấy key mới.
Chỉ thực thi khi: Phase 6 CHƯA chạy (`06-qa-result.md` chưa tồn tại).
- Generate chuỗi 8 ký tự Hex: `-join (('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f') | Get-Random -Count 8)`
- Cập nhật source yaml: Regex replace `(?m)^# FILE_KEY: .+$` thành `# FILE_KEY: $newKey`.
- Cập nhật file Pack để Sentinel 45 re-run không bị mismatch: Regex replace `voice-dna=[^,\s>]+` thành `voice-dna=$newKey`.
- In kết quả: `[OK] Rotated voice-dna.yaml FILE_KEY -> $newKey`.
Nếu Phase 6 đã chạy: `[INFO] Skip rotation: Phase 6 already started or voice-dna.yaml not found.`
Cuối cùng, báo thành công: `[PASS] Persona Pack validated.` (Exit 0).
