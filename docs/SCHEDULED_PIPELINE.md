# 1h / 90m / 150m FPGA SoC self-maintaining harness

## Cadence
GitHub Actions `continuous-pipeline.yml` orchestrates research/review/factory. `sync-site.yml` independently repairs generated artifacts every 30 minutes, and `verify.yml` runs a full independent regression every two hours.

| Schedule | UTC cron | KST time (UTC+9) | Stage |
|---|---|---|---|
| Every 30 minutes | `15,45 * * * *` | every hour :15 and :45 | Independent safe generated-site repair, RTL/C and source/link checks |
| Every 2 hours | `25 */2 * * *` | 09:25, 11:25, ... | Independent Python/RTL and legacy-material regression |
| Every hour | `7 * * * *` | every hour :07 | New source exploration **and full existing-material regression/repair** |
| Every 90 minutes | `17 0-23/3 * * *` + `47 1-23/3 * * *` | 09:17, 10:47, 12:17, ... | Verify discoveries and **all prior courseware** |
| Every 150 minutes | `27 0,5,10,15,20 * * *` + `57 2,7,12,17,22 * * *` | 09:27, 11:57, 14:27, ... | Make/review capstone deliverables and recheck **all older projects** |

Schedules are GitHub-hosted, may execute late or skip during GitHub outages, and are not a guaranteed real-time timer. Jobs serialize via `concurrency`. Failures appear in Actions; results in `catalog/*history.json`.

## Hourly creative research
The search intentionally rotates four complementary lenses: implementation, capstone, integration, and evidence; it combines board/FPGA vendor + application + interfaces and periodically uses board-agnostic anchor queries. It prioritizes underrepresented project categories, retains known projects, deduplicates by repository and tracks source tree SHA. Search results are untrusted; contents of external repositories are never executed.

`catalog/research_history.json` contains each query set, counts and search errors. `config/research_matrix.json` is expandable.

Every hourly research run also executes the existing capstone HTML/SVG/source regression and safely regenerates all derived artifacts. The 90m stage additionally evaluates and improves all collected references and proposals.

## Every 90 minutes: verification + safe improvement of old work
1. Audit **every** known reference for source inventory, license, board, application and evidence.
2. Recheck upstream commit tree SHA for a rotating subset of sources; changed upstream revisions are not adopted automatically.
3. Update improvement backlog and human-safe capstone proposals.
4. Regenerate existing generated HTML, SVG, BOM, connection JSON, and source hash manifests.
5. Run the available first-party RTL and C regression tests on **all existing capstones**.
6. Check links, SVG syntax, structure port connections and compiled source results; save a material audit report and history.
7. Correct *derivative outputs* only through canonical Design IR, preserving original hand-authored RTL, XDC, register map and manually verified evidence.

## Every 150 minutes: capstone generation + recurrence
1. Only sources marked reviewed and suitably documented are eligible as inspiration for first-party templates.
2. **Require at least one new unique capstone per cycle.** Prefer a genuinely new reviewed first-party RTL template. When no new RTL template exists, generate one distinct capstone **design-only brief** from an unused reviewed proposal, explicitly marked unimplemented. If eligible unique proposals run out, fail visibly; never duplicate a project or invent verified RTL.
3. Implemented capstones require genuine Verilog, testbench and C helper. Design-only briefs must not claim any of those are implemented. Never fabricate working IP/RTL by renaming signals.
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
- The 90m stage verifies metadata and first-party working examples; it does not actually synthesize downloaded third-party HDL.
- The initial structured "계통도" is digital module topology, **not KiCad electrical schematic or physical wire proof**. Existing first-party RTL is not rewritten automatically.
- Full SoC outputs require a real Vivado IP Block Design, verified address map, board XDC and tested firmware. Unverified steps are clearly labeled.
- Automatic changes to approved RTL or external source code require explicit human review and new evidence.

## Persistent policy (2026-11-03)
Run indefinitely until the user requests a stop. Every 150-minute factory run must create at least one new unique capstone document, with implementation status explicit. If the vetted candidate pool is exhausted, the run must fail and report the missing prerequisite rather than falsely claim success. Cron runs can be delayed or skipped by GitHub; this is not a real-time guarantee.

## Creative capstone fallback (2026-11-03)
Every factory run must produce at least one new, genuinely distinct capstone. After approved first-party RTL templates, use the curated original scenario bank and then distinct combinations of two inputs, output, controller policy and telemetry. A design brief is a deliverable, **not** verified RTL. Do not block generation waiting for third-party source metadata; continue to run existing RTL/C regression tests and publish HTML. The pool is large but finite; if exhausted, report failure and expand the catalog rather than fabricate a duplicate.
