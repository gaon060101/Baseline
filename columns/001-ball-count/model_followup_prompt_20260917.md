# BCAI / BCAP Development Prompt

Copy the prompt below into the task responsible for model development. Preparing this prompt does not authorize model execution in the current documentation task.

---

Develop BCAI and BCAP for the ball-count column in the Baseline project. The objective is to explain general relationships across counts, pitch locations, and actions, rather than grade individual players' moment-to-moment decisions.

Before implementing anything, inspect the existing artifacts and reuse completed work where appropriate. Work in the priority order below. Keep user-facing explanations and reports in Korean; this handoff prompt is in English.

## Execution mode: implement first, perform a quick review, then report

The user has limited time. This pass is for applying the proposed changes and completing only a lightweight review. This instruction takes precedence over any broader validation or analysis requests later in this prompt.

- Make the feasible code, configuration, documentation, and reporting changes now. Reuse the existing design review instead of repeating the literature research.
- Keep review brief: inspect the changes, check syntax/imports and basic arithmetic where applicable, and run one small smoke test if it can finish quickly with available inputs.
- Do not start full-data training, expensive model fitting, long simulations, full validation suites, broad parameter searches, or repeated tuning in this pass. Run new calculations only when they are small and quick; otherwise implement the necessary entry points and document how to run them later.
- For exploratory components whose implementation requires substantial unresolved design work, record the concrete design and remaining decisions rather than making unsupported assumptions to force completion.
- Preserve existing versions and completed results. Mark new work as implemented but not fully validated where appropriate; do not promote model status or present unexecuted analyses as results.
- Once the feasible changes and quick checks are complete, report back immediately. Summarize what was applied, which quick checks passed or failed, and what execution or deeper validation remains. Do not continue into those follow-up steps during this pass.

## Required reading

- `AGENTS.md`
- `guides/analysis.md`
- `models/registry.md`
- `columns/001-ball-count/column.md`
- `columns/001-ball-count/sources.md`
- `columns/001-ball-count/model_research_followup_20260917.md`
- `models/bcai/observed/v1.0.0/model_card.md`
- `models/bcap/pitch_sb/v0.1.0/model_card.md` and its `specification.yaml`
- `models/bcap/swing/v0.2.0/model_card.md` and its `specification.yaml`
- `columns/001-ball-count/analysis/bcap_external_20260914__r01/final_report.html`

Check the registry for subsequent changes before treating these versions as current.

## Priority 1: Reuse the existing S/B results

BCAP's S/B labels describe the pitch's observed geometric location inside or outside the defined strike zone. They do not represent called strikes/balls or the pitcher's intended target.

The existing 2024–2025 artifact already contains Q0(B), Q1(S), and their difference:

`columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv`

Produce a readable table for all 12 counts, including both action values, the difference, sample sizes, coverage, existing adjusted uncertainty intervals, classification, and units. Explain that lower allowed W favors the pitcher.

Keep the 2023 pattern reproduction separate from development results. Preserve the 2026 measurement hold. Label this as presentation of existing results, not a new model estimate.

## Priority 2: Add a ball/strike state-transition value table

Inspect the existing season-specific BCAI values in their original W units, V(c), and verify their denominators. For each count, calculate:

- Value of the next ball state minus the current state.
- Value of the next strike state minus the current state.
- Difference between the next-ball and next-strike state values.

Describe these as differences between observed state averages, not causal effects of adding a ball or strike.

Explicitly handle terminal walks on three balls, strikeouts on two strikes, ordinary two-strike fouls that leave the count unchanged, and relevant exceptions such as bunts, hit-by-pitches, uncaught third strikes, and errors. Follow the existing valid-PA and outcome definitions; document exclusions or separate categories rather than silently forcing exceptions into ordinary transitions.

Distinguish the state-average difference table from any table of final W conditional on an actually observed transition event. Do not mix BCAI's deduplicated count-reaching plate appearances with pitch-row aggregation. Report occurrence frequency separately from per-event value differences. Do not add transition rewards to final W in a way that counts the same value twice.

## Priority 3: Evaluate and implement a separate exploratory action-value decomposition

Read Sections 2.2, 3, and 5.1 of the public v2 manuscript:

**Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees**, Ryan Yee and Sameer K. Deshpande  
https://arxiv.org/html/2305.05752v2

Design a probability-times-conditional-value decomposition while retaining BCAP's final-PA W objective. Cover the relevant outcomes without omissions or overlap: taken balls, called strikes, hit-by-pitches, swinging misses, fouls, balls in play, and any additional categories required by the existing data definitions. Verify that branch probabilities sum to one.

Report count-level and location-level averages and their components using the same common reference distribution. Do not produce individual rankings or individual action recommendations. Player effects may remain as adjustment variables where justified.

Adopting BART is not itself the objective. Separate the decision to decompose outcomes from the choice of estimator. Compare the existing direct estimate and the decomposed estimate on the same sample and W scale. Evaluate predictive calibration, data support, and uncertainty. Do not claim that decomposition establishes new causal identification.

If a component is unsupported, document the limitation and complete the supported components without manufacturing values.

## Priority 4: Assess feasibility before modeling changes in opponent response

Consider assumption-based scenarios in which hitters swing less often at pitches outside the zone. Examine whether the observed outside-zone advantage at 0-2 and 1-2 persists under those scenarios.

Specify what remains fixed when changing the response rate. Do not combine the existing S/B and Swing/Take marginal averages into a 2×2 payoff matrix or a Nash mixture: their conditioning sets and reference populations differ. If jointly conditioned values lack support, defer the calculation and report the missing information and reason.

Review the assumptions in:

**Computing an Optimal Pitching Strategy in a Baseball At-Bat**, Connor Douglas, Everett Witt, Mia Bendy, and Yevgeniy Vorobeychik  
https://arxiv.org/html/2110.04321v1

In particular, examine the assumed target behavior at 3-0, pitch-type-specific Gaussian execution error, and count-invariant execution error. Treat these as modeling assumptions to assess, not established facts. Distinguish solving the assumed game from validating a policy in actual play.

Also consult:

**MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning**, Gagan Sidhu and Brian Caffo  
https://arxiv.org/html/1407.8392v1

Separate the policy-evaluation stage that assumes perfect recognition of the current pitch type from the subsequent simulation involving recognition error. Distinguish information available during the decision from information recorded after the pitch.

## Validation and scope

- Preserve existing model versions, raw data, processed data, and completed runs. Record new artifacts and design changes under appropriate versions and new run IDs, following the registry and analysis guide. Update the relevant model cards, specifications, validation records, and column links when applicable.
- Do not describe previously exposed external data as a fresh unseen validation set.
- Do not resume 2026 S/B or SWING evaluation before resolving the coordinate/strike-zone measurement issue.
- In this pass, perform only the lightweight checks specified above. Document the deeper denominator, split, support, calibration, and uncertainty checks required before the new results can be used in the column. Do not continue repeated tuning or enlarge the dataset automatically.
- If required local inputs are absent from the shared repository, inspect the data setup instructions. Do not automatically download them again.
- Exclude full path-dependent BCAI expansion, individual player recommendations or rankings, deployment of a full at-bat JOINT policy, KBO data collection or execution, the next RE24/runners-and-outs column, and external uploads.
- Treat the earlier token estimates as planning estimates, not an explicit token budget. The stopping point for this pass is implementation plus a quick review and a completion report, not full model validation.

## Deliverables

Produce a concise Korean Markdown implementation report and, if quick to generate using the existing renderer, a matching HTML preview. Clearly distinguish:

1. Existing results reused or reformatted.
2. Newly computed observational results.
3. Assumption-based sensitivity scenarios.
4. Questions that remain unresolved.

Include definitions, units, denominators, source artifact paths, validation outcomes, interpretation limits, and the implications for the column. State which model or documentation files changed and which analyses were deferred, with concrete reasons.
