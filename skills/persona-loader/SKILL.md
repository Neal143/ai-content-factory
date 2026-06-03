---
name: Persona Loader
description: Phase 4.5 — Nạp Voice DNA, Profile, Authorities và JTBD (từ blackboard) vào Persona Pack. Validation do validate-persona.ps1 đảm nhận.
last_update: 06/05/2026 22:00 (GMT+7)
required_inputs:
  - blackboard               # 00-blackboard.yaml (Persona_Path, resolved_jtbd)
  - persona_voice_dna        # [Persona_Path]/voice-dna.yaml
  - persona_profile          # [Persona_Path]/profile.yaml
  - persona_authorities      # [Persona_Path]/authorities.yaml
provided_outputs:
  - PERSONA_DNA
---

# Persona Loader (Phase 4.5)

> EXECUTION_KEY: e7d48f9a

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện từ các phase trước đã được biên dịch sẵn trong `.temp/payload.md` (run folder). Đọc file này để lấy input từ phase trước. Các file khác (persona, references, logs) vẫn đọc trực tiếp theo hướng dẫn bên dưới.

Nạp 3 file persona YAML + JTBD từ blackboard, compile thành Persona Pack, ghi vào run folder.

> ⛔ Skill này KHÔNG validate. `validate-persona.ps1` đã chạy ở Bước 3 workflow.
> ⛔ CHỈ load 3 file + JTBD. audience.yaml không còn load ở đây — JTBD đã resolve vào blackboard trước khi Persona Loader chạy.

## Bước 1: Đọc 3 file persona + JTBD từ blackboard

Dùng tool `view_file` đọc lần lượt 3 file tại `[Persona_Path]` (lấy từ Blackboard):

1. `[Persona_Path]/voice-dna.yaml`
2. `[Persona_Path]/profile.yaml`
3. `[Persona_Path]/authorities.yaml`

> ⛔ **FATAL RULE:** PHẢI dùng tool đọc thành công cả 3. File Not Found → DỪNG, BÁO USER.

Sau khi đọc mỗi file, ghi nhận giá trị `FILE_KEY` (dòng `# FILE_KEY: ...`).

Đọc `resolved_jtbd` từ `00-blackboard.yaml` trong run folder → trích `audience_Job_performer`, `audience_main_job`, `audience_circumstance`.

## Bước 2: Compile Persona Pack

Compile thành file `04.5-persona-pack.md` — TOÀN BỘ nội dung pack BẮT BUỘC bọc trong `[BLOCK: PERSONA_DNA]...[/BLOCK: PERSONA_DNA]`:

```
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

## Bước 3: Ghi keys

Append cuối file `04.5-persona-pack.md`:
```
<!-- execution_key: [EXECUTION_KEY từ SKILL.md] -->
<!-- persona_keys: voice-dna=[key1], profile=[key2], authorities=[key3] -->
```
