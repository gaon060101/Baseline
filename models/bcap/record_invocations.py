"""Record actual current-task tool-invoked commands after runs have finished."""
from pathlib import Path
import json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[2];AN=ROOT/'columns/001-ball-count/analysis'
EXE='C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
DATA='columns/001-ball-count/data/processed/bcap_dev_v010_20260909_r01.pkl'
SEAL='models/bcap/external_seal_20260909_r01.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
    out=AN/'bcap_execution_commands_20260909.json';assert not out.exists()
    commands=[]
    for model,dev,boot in [('pitch','r02','r03'),('swing','r01','r02')]:
        dev_id=f'bcap_{model}__mlb_2024_2025__20260909__{dev}'
        commands.append((dev_id,[EXE,'models/bcap/run.py','develop','--model',model,'--data',DATA,'--run-id',dev_id]))
        boot_id=f'bcap_{model}__mlb_2024_2025__20260909__{boot}'
        commands.append((boot_id,[EXE,'models/bcap/refit_stability.py','--model',model,'--data',DATA,'--development-run',dev_id,'--run-id',boot_id,'--replicates','8']))
        for year,period in [(2023,'2023'),(2026,'2026_ytd_20260907')]:
            rid=f'bcap_{model}__mlb_{period}__20260909__r01'
            commands.append((rid,[EXE,'models/bcap/run.py','external','--model',model,'--year',str(year),'--run-id',rid,'--seal',SEAL]))
    failed='bcap_pitch__mlb_2024_2025__20260909__r01';commands.append((failed,[EXE,'models/bcap/run.py','develop','--model','pitch','--data',DATA,'--run-id',failed]))
    records=[]
    for rid,argv in commands:
        path=AN/'runs'/rid/'manifest.json';m=json.loads(path.read_text(encoding='utf-8'));assert m['status'] in ['COMPLETE','FAILED','WITHHELD']
        records.append(dict(run_id=rid,argv=argv,shell_command="& '"+argv[0]+"' "+' '.join(argv[1:]),source='Recorded after execution from actual functions.exec tool invocations in this BCAP task; not shell history recovered independently',manifest={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)},status=m['status'],started_at_utc=m['started_at_utc'],finished_at_utc=m['finished_at_utc']))
    # These auxiliary commands are recoverable from saved parameters and the
    # inspected CLI, not asserted to be an independently captured shell log.
    auxiliary=[
        dict(role='development_preparation',argv=[EXE,'models/bcap/data.py','--years','2024','2025','--output',DATA,'--audit-dir','columns/001-ball-count/analysis/bcap_preparation_20260909_r01'],source='columns/001-ball-count/analysis/bcap_preparation_20260909_r01/preparation_audit.json'),
        dict(role='core_seal',argv=[EXE,'models/bcap/run.py','seal','--pitch-run','bcap_pitch__mlb_2024_2025__20260909__r02','--swing-run','bcap_swing__mlb_2024_2025__20260909__r01','--output','models/bcap/external_seal_core_20260909_r01.json'],source='models/bcap/external_seal_core_20260909_r01.json'),
        dict(role='final_seal',argv=[EXE,'models/bcap/finalize_seal.py','--core','models/bcap/external_seal_core_20260909_r01.json','--output',SEAL],source=SEAL)
    ]
    for item in auxiliary:
        item['kind']='reconstructed_from_saved_parameters_and_inspected_CLI_not_captured_shell_history'
        item['source_sha256']=sha(ROOT/item['source'])
        item['warning']='Historical parameters only. Existing outputs must be preserved; reruns require new output names and, for fitted models, new run IDs and a new seal.'
    out.write_text(json.dumps(dict(recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cwd=ROOT.as_posix(),commands=records,auxiliary_pipeline_reconstruction=auxiliary,reproduction='Original IDs intentionally cannot be rerun/overwritten. Select unused current-date IDs and record newly selected development IDs in a new seal. Existing fixed-score verification can be rerun to a new audit path.'),ensure_ascii=False,indent=2),encoding='utf-8')
