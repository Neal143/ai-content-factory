import os
import argparse
import yaml
import json
import re

def parse_args():
    parser = argparse.ArgumentParser(description="Extract existing audiences for re-calibration")
    parser.add_argument('--audience-index', required=True, help="Path to _audience_index.yaml")
    parser.add_argument('--vault-root', required=True, help="Path to vault root")
    parser.add_argument('--output-json', required=True, help="Path to output JSON")
    return parser.parse_args()

def extract_context(vault_root, source_path):
    if not source_path:
        return "", "Khong co source_path"
        
    if '#^' in source_path:
        file_path, block_id = source_path.split('#^', 1)
    else:
        file_path, block_id = source_path, None
        
    full_path = os.path.normpath(os.path.join(vault_root, file_path))
    
    if not os.path.exists(full_path):
        return "", f"File khong ton tai: {file_path}"
        
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if block_id:
            # Tim trong data_chunk
            chunks = re.findall(r'<data_chunk>(.*?)</data_chunk>', content, re.DOTALL)
            for chunk in chunks:
                if f'^{block_id}' in chunk:
                    return chunk.strip(), ""
            
            # Khong tim thay trong data_chunk, tim heading
            lines = content.split('\n')
            start_idx = -1
            for i, line in enumerate(lines):
                if line.startswith('#') and f'^{block_id}' in line:
                    start_idx = i
                    break
            
            if start_idx != -1:
                end_idx = len(lines)
                for i in range(start_idx + 1, len(lines)):
                    if lines[i].startswith('#'):
                        end_idx = i
                        break
                return '\n'.join(lines[start_idx:end_idx]).strip(), ""
                
            return "", f"Block ID ^{block_id} khong tim thay trong {file_path}"
        else:
            return content[:5000].strip(), ""
    except Exception as e:
        return "", f"Loi doc file {file_path}: {e}"

def main():
    args = parse_args()
    
    if not os.path.exists(args.audience_index):
        print(f"Lỗi: Không tìm thấy file {args.audience_index}")
        exit(1)
        
    with open(args.audience_index, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Bo qua header
    lines = content.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('#') or line.strip() == '':
            body_start = i + 1
        else:
            break
            
    body = '\n'.join(lines[body_start:])
    index_data = yaml.safe_load(body) or {}
        
    audiences = index_data.get('audiences', [])
    entries = []
    
    for aud in audiences:
        file_ref = aud.get('file_ref', '')
        # Extract filename tu [[filename]]
        match = re.search(r'\[\[(.*?)\]\]', file_ref)
        if not match:
            continue
        original_filename = match.group(1)
        
        md_path = os.path.join(args.vault_root, '01-Atomic', 'Audiences', f"{original_filename}.md")
        if not os.path.exists(md_path):
            print(f"Warning: File {md_path} khong ton tai")
            continue
            
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        fm_match = re.match(r'^---\n(.*?)\n---', md_content, re.DOTALL)
        if not fm_match:
            print(f"Warning: Khong tim thay frontmatter trong {original_filename}")
            continue
            
        fm_text = fm_match.group(1)
        fm_data = yaml.safe_load(fm_text) or {}
        
        source_type = fm_data.get('source_type', '')
        source_path = fm_data.get('source_path', '')
        source_link = fm_data.get('source_link', '')
        
        context_text, context_warning = extract_context(args.vault_root, source_path)
        
        # Tao jtbd_raw = "performer muốn main_job circumstance"
        performer = fm_data.get('audience_Job_performer', '')
        main_job = fm_data.get('audience_main_job', '')
        circumstance = fm_data.get('audience_circumstance', '')
        jtbd_raw = f"{performer} muốn {main_job} {circumstance}"
        
        entry = {
            "original_filename": original_filename,
            "jtbd_raw": jtbd_raw,
            "audience_main_job": main_job,
            "audience_circumstance": circumstance,
            "audience_Job_performer": performer,
            "audience_level": fm_data.get('audience_level', ''),
            "parent_audience": fm_data.get('parent_audience', []),
            "source_type": source_type,
            "source_path": source_path,
            "source_link": source_link,
            "context_text": context_text,
            "context_warning": context_warning
        }
        entries.append(entry)
        
    output_data = {
        "mode": "re-calibrate",
        "entries": entries
    }
    
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Extracted {len(entries)} audiences to {args.output_json}")

if __name__ == '__main__':
    main()
