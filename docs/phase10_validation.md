# Phase 10 — clean-room validation and cleanup

Validation date: 2026-08-16.

## Completed checks

- All Python unit and API integration tests pass.
- The real local frontend-to-API query path was validated in Phase 9.
- Python dependency, build-tool, and frontend dependency versions are pinned.
- A fresh Python 3.12 virtual environment successfully built and installed the local `raabta-ir` wheel without relying on the existing `.venv` package installation.
- The installed clean-room package imported as `raabta` and all source/backend/script files compiled.
- `pnpm install --frozen-lockfile` and the TypeScript/Vite production build pass.
- Seven standard notebooks execute top-to-bottom with fixed seed `20250816`, visible outputs, and no error outputs.
- The main Phase 6 report/figure command regenerates successfully from measured artifacts.
- The default passage and E5 embedding checksums match their manifests.
- No source, configuration, backend, or frontend file contains a machine-specific Windows workspace path.
- Every inspected provisional evaluation report records zero test queries used.

## Clean-environment issue found and fixed

The first fresh-environment package build correctly failed because Python 3.12 does not include the declared build backend by default. Build requirements are now exactly pinned to `setuptools==84.0.0` and `wheel==0.46.3`. `setup.ps1` installs these through `requirements-dev.txt` and then installs the project itself in editable mode.

The temporary verification environment is located at `work/cleanroom_venv`, is Git-ignored, contains no global installation, and can be deleted safely. Automated deletion was blocked by the workspace sandbox, so it was left visibly contained rather than removed through an unsafe workaround.

## Portable copy contract

Copy the complete project folder except `.venv`, `frontend/node_modules`, `frontend/dist`, and `work/cleanroom_venv`. Preserve the generated `data`, `artifacts`, and `reports` folders if the main PC should reuse the validated corpus, models, embeddings, and results. On the main PC:

1. Install Python 3.11 or 3.12 and Node.js with pnpm.
2. Run `setup.ps1` from the project root.
3. Run `pnpm install --frozen-lockfile` inside `frontend`.
4. Run `scripts/audit_portability.py` before experiments or demonstration.

## Remaining research limitations

- Independent native-speaker review of the diagnostic set and failure categories is still required.
- The six retrieval-component controls have not each been rerun with the CPU-heavy reranker retained.
- The locked test split remains intentionally unevaluated until annotations and the final protocol are approved.
