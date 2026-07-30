import os, re

def update_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    new_content = content
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')

f1 = '.agents/skills/book-parser/references/atom-structure.md'
update_file(f1, [
    (r'source_link:\s*"\[\[<Tên Sách>\]\]"', 'source_link: "[[<Tên Sách>#^chunk-{NN}]]"'),
    (r'source_path:\s*"02-sources/books/<Tên Sách>\.md"', 'source_path: "02-sources/books/<Tên Sách>.md#^chunk-{NN}"')
])

f2 = '.agents/skills/book-audience-matcher/references/audience-structure.md'
update_file(f2, [
    (r'source_link:\s*"\[\[<Display>\]\]"', 'source_link: "[[<Display>#^{fragment}]]"   # book-overview hoặc chunk-{NN}'),
    (r'source_path:\s*"02-sources/books/<Display>\.md"', 'source_path: "02-sources/books/<Display>.md#^{fragment}"')
])

f3 = '.agents/skills/book-parser/SKILL.md'
update_file(f3, [
    (r'(source_link.*?)', r'\1\n  - Lưu ý: Luôn có block ID dạng #^chunk-{NN} tương ứng với chunk chứa atom đó.')
])

f4 = '.agents/skills/book-audience-matcher/SKILL.md'
update_file(f4, [
    (r'(source_link.*?)', r'\1\n  - Lưu ý: Luôn có block ID dạng #^book-overview hoặc #^chunk-{NN} tương ứng với decision map.')
])
