# 팀원용 이어가기 프롬프트

아래 영어 본문 전체를 Baseline 저장소가 연결된 새 작업에 입력한다. 팀원 이름이 해당 대화에서 확인되지 않았다면 도구가 한 번 확인한다. 결과 설명·질문·검토 보고는 한국어로 받는다. 구체적인 추가 업무는 프롬프트 아래에 덧붙이면 된다.

```text
Continue collaboration on the Baseline repository, specifically column 001-ball-count, from the September 28, 2026 shared handoff. Follow AGENTS.md. Write all user-facing explanations, questions, progress updates, and reports in Korean.

Read collaboration/pending/20260928-210719-gaon-daily-share/changes.md and continuation_prompt.md, guides/collaboration.md, collaboration/README.md, and the pending handoffs. Read README.md, the current-status section of columns/001-ball-count/column.md, guides/codex_workflow.md, and guides/github_sharing.md. Treat older status sections and the setup handoff as historical context. Do not mistake an old STARTED/FAILED progress record for current execution; consult completion records and the actual manifests.

Check the local branch, uncommitted changes, and remote shared main before modifying anything. Preserve local work; do not reset, force-push, or silently merge conflicts. Resolve the content commit C from the handoff after transmission is recorded. If the current teammate has not identified themselves in this conversation, ask whether they are 백가온 or 박민수 while continuing read-only review. Do not infer identity from Git configuration or the operating-system account.

Use these entry points:
- columns/001-ball-count/analysis/r_history_20260928/completion.md
- columns/001-ball-count/analysis/r_history_20260928/report.html
- columns/001-ball-count/analysis/r_bcap_history_20260928/report.html
- columns/001-ball-count/analysis/r_supplement_20260928/report.html
- columns/001-ball-count/analysis/history_comparison_20260928_r01/report.md and audit/final_review.md
- columns/001-ball-count/publish/naver_20260918/index.html and README.md
- columns/001-ball-count/publish/naver_20260918/revision_v15.md and models_v15/ for the model explanations
- columns/001-ball-count/publish/naver_20260918/main_v15/ for the main article's reference-results revision
- guides/r_setup.md, models/bcai/observed/v1.0.0/r/README.md, models/bcap/r/README.md, and models/registry.md when implementation context is needed.

Current scope: BCAI and the four BCAP modules have completed 2015–2025 calculations; the historical comparison and revised manuscripts are available. The main article's editing is finished pending further requests; the BCAI/BCAP explanations are calculation-focused revision 15 and await user feedback. Existing ZIP files are older snapshots. Preserve approved originals and revision archives.

Retain BCAP EXPERIMENTAL, 2026 S/B and SWING WITHHELD_MEASUREMENT, KBO not started, and paused follow-up automation. The 2026 supplement ends September 7 and uses fixed 2025 weights. Distinguish BCAI OBS from Ridge, historical per-year fitting from the shared 2024–2025 fit, conditional intervals from full refitting uncertainty, and observational contrasts from causal recommendations. Read guides/analysis.md and relevant sources.md entries before analytical interpretation; read guides/writing.md before editorial changes.

First deliver a concise Korean summary of completed work, current deliverables, unresolved limitations, and the next review steps, with links. Then conduct a read-only handoff review for actionable inconsistencies in the current documents, distinguishing stale historical notes from genuine current defects. If a concrete task is appended by the user, proceed within that scope; otherwise present specific findings and proposed next work without editing manuscripts or restarting analyses. Do not download excluded inputs merely to read reports. Do not rerun one-time revision scripts or overwrite completed or failed runs. Consult guides/data_setup.md and guides/excluded_files.json if reproduction is explicitly requested.

Keep teammate comments separate. Save text explicitly designated for the collaboration folder under the identified person's 사용자 전달 코멘트, preserving exact wording, attribution, date, and category. Do not fabricate either person's opinions, agreement, or read receipt. Record proxy reading only when explicitly requested and label it as tool-assisted, not human reading. Do not delete a pending handoff before both latest-version acknowledgments and remote preservation requirements are met. This prompt does not authorize publishing, new Git pushes, Drive/Docs synchronization, new data acquisition, model reruns, or restarting paused work.
```
