from pathlib import Path
import re, json, hashlib, zipfile

HERE=Path(__file__).resolve().parent
C=HERE.parent.parent
ROOT=C.parent.parent
FIG=C/'figures/naver_20260918'

# Keep direct source links readable next to the claims they support.
p=HERE/'01_ball_count.md'
text=p.read_text(encoding='utf-8')
text=re.sub(r'(\S)(\[\d+ ·)',r'\1 \2',text)
p.write_text(text,encoding='utf-8')

# Mirror the new historical-status notice without replacing the older outline preview.
p=C/'outline_mlb.html'
text=p.read_text(encoding='utf-8')
if 'data-draft-notice="20260918"' not in text:
    note='<aside data-draft-notice="20260918" style="max-width:1080px;margin:24px auto;padding:22px;background:#e2f0ec;color:#173a3d"><strong>2026-09-18 집필 반영</strong><p>이 개요와 이후 구현·검수를 반영한 <a href="publish/naver_20260918/index.html">본문·BCAI·BCAP 세 글</a>을 작성했습니다. 아래는 9월 17일 설계 기록입니다. 새 상태 평균 차이와 그림 8종을 반영했고, 전문 미확인 문헌은 제외했습니다. 사용자 검토 전으로 외부 발행은 하지 않았습니다.</p></aside>'
    text=text.replace('<main>',note+'<main>',1)
    p.write_text(text,encoding='utf-8')

# A compact attachment bundle; no external paper or proprietary raw data included.
caption='네이버 첨부용 차트·도식 8장\n\n'
caption+='배치: 1편은 01,02,03,04,05,08 순서. 2편은 06,07. 3편은 05,04.\n'
caption+='원고의 그림 캡션을 함께 옮겨 주세요. 기간·단위·표본·출처·불확실성 설명을 유지합니다.\n'
caption+='사용자 검토본이며 게시·업로드하지 않았습니다.\n'
pngs=sorted(FIG.glob('*.png'));assert len(pngs)==8
with zipfile.ZipFile(HERE/'네이버_첨부그림_8장.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in pngs:z.write(p,p.name)
    z.writestr('그림_배치_안내.txt',caption.encode('utf-8-sig'))

mds=['01_ball_count.md','02_bcai.md','03_bcap.md','04_references_ko.md','revision_v3.md','revision_v2.md','README.md','manuscript_source_map.md','reference_audit.md','02_bcai_evidence.md','03_bcap_evidence.md']
missing=[]
for name in mds:
    txt=(HERE/name).read_text(encoding='utf-8')
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',txt):
        if link.startswith(('http','#','C:')):continue
        if not (HERE/link.split('#')[0]).exists():missing.append((name,link))
assert not missing,missing
fm=json.loads((FIG/'figure_manifest.json').read_text(encoding='utf-8'))
for rel,sha in fm['inputs_sha256'].items():assert hashlib.sha256((C/rel).read_bytes()).hexdigest()==sha,rel
for fig in fm['figures']:assert hashlib.sha256((FIG/fig['file']).read_bytes()).hexdigest()==fig['sha256']

receipt={
 'status':'3차 두괄식 수정·결과 영역 분리·문헌 전용 서식·사용자 검토 대기·외부 미게시',
 'model_run':'기존 집계 재사용. 새 모델 학습·원자료 수집·KBO 분석 없음.',
 'md_created':mds,
 'central_md_updated':['README.md','guides/writing.md','columns/001-ball-count/column.md','columns/001-ball-count/sources.md'],
 'figures':8,'local_links_missing':missing,'saved_aggregate_hashes_unchanged':True,
 'manuscript_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in mds},
 'review':'분모·정의·핵심 수치·구간·현재 모델 상태·원문 인용 검토, 8종 그림 시각 확인, 1280/390px HTML 표시 확인. 전체 모델 재검증 아님.'
}
(HERE/'delivery_check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'png_files':len(pngs),'md_links_missing':missing,'aggregate_hashes_match':True},ensure_ascii=False))
