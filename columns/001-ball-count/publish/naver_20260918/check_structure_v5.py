from pathlib import Path
import re,json
D=Path(__file__).resolve().parent
s=(D/'01_ball_count.md').read_text(encoding='utf-8')
old=(D/'revisions/v4_before_structure_v5/01_ball_count.md').read_text(encoding='utf-8')
tables=lambda x: re.findall(r'^\|.*(?:\n\|.*)+',x,re.M)
chapters=re.split(r'^## \d+\.',s,flags=re.M)[1:6]
checks={
 'five_chapters_same_order':all(re.search(r'### .*간단 설명[\s\S]*### .*결과 한눈에 보기[\s\S]*### .*상세 설명',c) for c in chapters) and len(chapters)==5,
 'six_new_tables':len(tables(s))==6 and not(set(tables(s))&set(tables(old))),
 'same_five_images':set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)',s))==set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)',old)),
 'same_external_references':set(re.findall(r'https:[^)]+',s))==set(re.findall(r'https:[^)]+',old)),
 'chapter_links':all(f'id="chapter-{a}"' in s and f'](#chapter-{a})' in s for a in ['bcai','location','swing','three','pitch','game']),
 'visual_check':json.loads((D/'visual_check.json').read_text(encoding='utf-8'))['pass'],
}
report={'pass':all(checks.values()),'checks':checks}
(D/'revision_v5_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert report['pass']
