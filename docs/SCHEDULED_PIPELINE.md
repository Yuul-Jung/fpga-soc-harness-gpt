# 1h / 2h / 4h FPGA SoC self-maintaining harness

## Cadence
GitHub Actions `continuous-pipeline.yml` is the sole scheduled orchestrator.

| Schedule | UTC cron | KST time (UTC+9) | Stage |
|---|---|---|---|
| Every hour | `7 * * * *` | every hour :07 | New source exploration **and full existing-material regression/repair** |
| Every 2 hours | `17 */2 * * *` | 09:17, 11:17, 13:17, ... | Verify discoveries and **all prior courseware** |
| Every 4 hours | `27 */4 * * *` | 09:27, 13:27, 17:27, ... | Make/review capstone deliverables and recheck **all older projects** |

Schedules are GitHub-hosted, may execute late or skip during GitHub outages, and are not a guaranteed real-time timer. Jobs serialize via `concurrency`. Failures appear in Actions; results in `catalog/*history.json`.

## Hourly creative research
The search intentionally rotates four complementary lenses: implementation, capstone, integration, and evidence; it combines board/FPGA vendor + application + interfaces and periodically uses board-agnostic anchor queries. It prioritizes underrepresented project categories, retains known projects, deduplicates by repository and tracks source tree SHA. Search results are untrusted; contents of external repositories are never executed.

`catalog/research_history.json` contains each query set, counts and search errors. `config/research_matrix.json` is expandable.

Every hourly research run also executes the existing capstone HTML/SVG/source regression and safely regenerates all derived artifacts. The 2h stage additionally evaluates and improves all collected references and proposals.

## Every 2 hours: verification + safe improvement of old work
1. Audit **every** known reference for source inventory, license, board, application and evidence.
2. Recheck upstream commit tree SHA for a rotating subset of sources; changed upstream revisions are not adopted automatically.
3. Update improvement backlog and human-safe capstone proposals.
4. Regenerate existing generated HTML, SVG, BOM, connection JSON, and source hash manifests.
5. Run the available first-party RTL and C regression tests on **all existing capstones**.
6. Check links, SVG syntax, structure port connections and compiled source results; save a material audit report and history.
7. Correct *derivative outputs* only through canonical Design IR, preserving original hand-authored RTL, XDC, register map and manually verified evidence.

## Every 4 hours: capstone generation + recurrence
1. Only sources marked reviewed and suitably documented are eligible as inspiration for first-party templates.
2. Create **at most one** new real RTL starter per cycle, and only for an already implemented/tested template. At v1 the available starter is pulse-frequency meter; one instance is created and will not be duplicated on later cycles.
3. Require genuine local Verilog + testbench + simple C integration helper; never generate fake working IP/RTL by randomly renaming signal names.
4. Generate HTML, source copies, module diagram SVG, machine-readable connections JSON, BOM CSV, verification JSON.
5. **Recheck and repair all existing published materials** each cycle; regression failures make the workflow fail and preserve audit logs.
6. Physical KiCad netlists, XDC pin assignments, AXI Block Designs and real board test are gated until real hardware metadata and reproducible vendor builds are available.

## Use
Manual: repository Actions → Continuous FPGA SoC research and capstone maintenance → Run workflow → choose `all` or one stage. No local PC required.

Local commands:
```bash
python3 -m harness.research             # internet/GITHUB_TOKEN needed
python3 -m harness.review --offline     # no remote requests
python3 -m harness.refine
python3 -m harness.factory
python3 -m harness.maintenance --stage factory
python3 -m unittest discover -s tests -v
```

## Important limitations
- This is **scheduled deterministic Python automation**, not a continuously reasoning autonomous LLM agent. Creative search uses diversity/feedback heuristics, not LLM generation.
- The 2h stage verifies metadata and first-party working examples; it does not actually synthesize downloaded third-party HDL.
- The initial structured "계통도" is digital module topology, **not KiCad electrical schematic or physical wire proof**. Existing first-party RTL is not rewritten automatically.
- Full SoC outputs require a real Vivado IP Block Design, verified address map, board XDC and tested firmware. Unverified steps are clearly labeled.
- Automatic changes to approved RTL or external source code require explicit human review and new evidence.
