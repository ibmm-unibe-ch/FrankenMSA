# FrankenMSA Feature Index

This document is the canonical inventory of functional capabilities currently present across the `frankenmsa` library and the Dash app. Its purpose is to keep migration work visible while the library becomes the source of truth for reusable domain logic.

## Status Legend

| Status | Meaning |
| --- | --- |
| `library-backed` | Capability already exists in `frankenmsa` and the app should call it rather than reimplement it. |
| `app-only` | Capability exists only in the app or app helpers and needs extraction if it is reusable business logic. |
| `duplicated` | Similar capability exists in both places but the implementation is split or inconsistent. |
| `ui-only` | Capability belongs to Dash presentation or interaction flow and should remain in the app. |

## Migration Labels

| Label | Meaning |
| --- | --- |
| `keep` | Stay where it is. |
| `extract` | Move reusable logic from app code into the library. |
| `refactor` | Keep in library but normalize API, environment handling, or exports. |
| `adopt` | App should switch to an existing library API instead of page-local logic. |

## Feature Matrix

| Domain | Capability | Current Location | Current Entry Points | Status | Migration | Proposed Library Home | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| file-io | Read and write A3M/FASTA-style MSA files | `frankenmsa/utils/fileio.py` | `read_a3m`, `write_a3m`, `encode_a3m`, `decode_a3m` | `library-backed` | `keep` | `frankenmsa.utils.fileio` | Core file API already exists and should anchor app import/export work. |
| file-io | Multimer A3M parsing and assembly | `frankenmsa/utils/fileio.py` | `parse_a3m`, `combine_unpaired_a3m`, `read_a3m_with_chains`, `split_multimer_a3m_file` | `library-backed` | `adopt` | `frankenmsa.utils.fileio` | Multimer helpers now live with the rest of the file I/O surface. |
| file-io | Upload format detection for A3M, FASTA, CSV | `app/pages/file.py` | upload callback | `app-only` | `extract` | `frankenmsa.utils.fileio` | Reusable parser/dispatcher logic should not live in Dash callbacks. |
| file-io | Multimer A3M splitting into per-chain MSAs | `frankenmsa/utils/fileio.py`, `app/pages/file.py` | `split_multimer_a3m_file`, file upload callback | `library-backed` | `adopt` | `frankenmsa.utils.fileio` | Extracted into the library; the app now consumes the shared helper. |
| file-io | CSV chain-column splitting and multimer CSV assembly | `frankenmsa/utils/fileio.py`, `app/pages/file.py` | `split_dataframe_by_chain`, `build_multimer_csv`, file callbacks | `library-backed` | `adopt` | `frankenmsa.utils.fileio` | Extracted into the library; app-side duplication removed. |
| file-io | Download/export orchestration | `app/pages/file.py`, `app/app.py` | download callback, `/colab/download` route | `ui-only` | `keep` | n/a | Route wiring and browser delivery stay app-side. |
| msa-edit | Length normalization, slicing, insertion, replacement, merge/split chains | `frankenmsa/utils/msatools.py` | `unify_length`, `slice_sequences`, `insert_at`, `remove_at`, `replace_at`, `split_chains`, `merge_chains` | `library-backed` | `keep` | `frankenmsa.utils.msatools` | Existing core edit surface. |
| msa-edit | Gap filtering, identity filtering, deduplication, sorting | `frankenmsa/utils/msatools.py` | `filter_gaps`, `filter_identity`, `drop_duplicates`, `sort_gaps`, `sort_identity` | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | App should consistently call these helpers. |
| msa-edit | Regex-based sequence filtering | `frankenmsa/utils/msatools.py`, `app/pages/edit.py` | `filter_by_regex`, regex filter callback | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | Extracted into the library and wired into the app callback. |
| msa-edit | Free-form DataFrame query filtering | `frankenmsa/utils/msatools.py`, `app/pages/edit.py` | `filter_by_query`, free query callback | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | Query filtering now has a reusable library API. |
| msa-edit | Row cropping and column cropping | `frankenmsa/utils/msatools.py`, `app/pages/edit.py` | `crop_to_depth`, `slice_sequences`, crop callbacks | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | Both crop directions are already represented in the library; remaining work is mainly callback cleanup. |
| msa-edit | Character removal and replacement | `frankenmsa/utils/msatools.py` | `replace_characters`, `replace_insertions_with_gaps`, `replace_unknown_with_gaps` | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | Generic replacement and the current app-used gap conversions now live in the library. |
| msa-edit | Uppercase and lowercase sequence transforms | `app/pages/edit.py` | case conversion callbacks | `app-only` | `extract` | `frankenmsa.utils.msatools` | Small but should live with other sequence transforms. |
| msa-edit | Shuffle MSA rows | `frankenmsa/utils/msatools.py`, `app/pages/edit.py` | `shuffle_rows`, shuffle callback | `library-backed` | `adopt` | `frankenmsa.utils.msatools` | Row shuffling with the query preserved is now implemented in the library and consumed by the app. |
| filter | HH-suite wrapper filtering | `frankenmsa/filter/hhsuite.py`, `app/pages/edit.py` | `hhfilter`, HHFilter callback | `library-backed` | `refactor` | `frankenmsa.filter.hhsuite` | Existing backend should stay in library; improve environment and error handling. |
| combine | Horizontal MSA concatenation with optional slicing | `app/pages/combine.py` | combine callback | `app-only` | `extract` | `frankenmsa.utils.msatools` | Reusable composition logic belongs in the library. |
| combine | Vertical stacking with depth and length normalization | `app/pages/combine.py`, `frankenmsa/utils/msatools.py` | combine callback, `adjust_depth`, `unify_length` | `duplicated` | `refactor` | `frankenmsa.utils.msatools` | App orchestration should be thinned down to API calls. |
| align | MMseqs2 alignment via ColabFold API | `frankenmsa/align/mmseqs_colab.py` | `MMSeqs2Colab.align` | `library-backed` | `refactor` | `frankenmsa.align` | Keep backend but normalize incomplete and Colab-oriented assumptions. |
| align | Local multimer MMseqs2 workflow | `frankenmsa/align/mmseqs_local.py`, `frankenmsa/align/workflows.py`, `app/pages/align.py` | `LocalMMSeqs2Colab.align`, workflow helpers, MMseqs page callback | `duplicated` | `refactor` | `frankenmsa.align` | Input normalization and result registration moved into library workflow helpers; backend/result splitting cleanup remains. |
| align | PLM-Search remote lookup | `frankenmsa/align/plm_search.py`, `frankenmsa/align/workflows.py`, `app/pages/align.py` | `PLMSearch.align`, workflow helpers, PLM page callback | `library-backed` | `adopt` | `frankenmsa.align` | The app now uses shared workflow helpers for validation, parsing, and result registration around the backend. |
| align | Sequence text parsing and multimer input validation | `frankenmsa/align/workflows.py`, `app/pages/align.py` | `normalize_mmseqs_input`, `validate_mmseqs_request`, `parse_plm_input` | `library-backed` | `adopt` | `frankenmsa.align.workflows` | Reusable input normalization and validation have been extracted from Dash callbacks into the library. |
| augment | GhostFold augmentation backend | `frankenmsa/augment/ghostfold.py` | `GhostFoldAugmentation.augment` | `library-backed` | `refactor` | `frankenmsa.augment.ghostfold` | Hardcoded Colab paths must be removed. |
| augment | GhostFold input cleanup and multimer result splitting | `app/pages/augment.py` | augmentation callback | `app-only` | `extract` | `frankenmsa.augment` or `frankenmsa.utils.fileio` | App-only orchestration currently hides reusable behavior. |
| cluster | AFCluster sequence clustering | `frankenmsa/cluster/af_cluster.py`, `app/pages/cluster.py` | `AFCluster`, clustering callback | `library-backed` | `adopt` | `frankenmsa.cluster.af_cluster` | Core compute already belongs in the library. |
| cluster | KMeans clustering | `frankenmsa/cluster/kmeans.py` | `KMeans` | `library-backed` | `refactor` | `frankenmsa.cluster.kmeans` | Present in library but not clearly exposed in the UI. |
| cluster | Size-weighted Ward centroid merge after AFCluster | `frankenmsa/cluster/ward.py`, `frankenmsa/cluster/workflows.py`, `app/pages/cluster.py` | `ward_merge_cluster_centroids`, `run_ward_centroid_merge`, ward callback | `library-backed` | `adopt` | `frankenmsa.cluster.ward` and `frankenmsa.cluster.workflows` | Library now exposes this as a weighted centroid merge over existing AFCluster groups; `ward_linking` remains as a compatibility alias. |
| cluster | PCA preparation for cluster visualization | `frankenmsa/visual/dimension_reduction.py`, `app/pages/cluster.py` | `compute_PCA`, plot callbacks | `library-backed` | `keep` | `frankenmsa.visual.dimension_reduction` | Data prep can stay in library; plotting stays app-side. |
| cluster | Scatter plot rendering, interactive cluster selection, settings persistence | `app/pages/cluster.py`, `frankenmsa/cluster/workflows.py` | visualization callbacks, save helpers, dropdown helpers | `duplicated` | `refactor` | `frankenmsa.cluster.workflows` plus app UI | Plot rendering stays app-side; reusable option/save logic moved to library workflows. |
| inverse-fold | Public sequence generation API | `frankenmsa/inverse_fold/api.py` | `generate_sequences`, backend selection helpers | `library-backed` | `refactor` | `frankenmsa.inverse_fold.api` | Should become the single stable entry point for app and notebooks. |
| inverse-fold | Local ProteinMPNN backend | `frankenmsa/inverse_fold/protein_mpnn.py` | `LocalProteinMPNN` | `library-backed` | `refactor` | `frankenmsa.inverse_fold.protein_mpnn` | Resolves an existing checkout and no longer owns installation. |
| inverse-fold | Remote ProteinMPNN backend via Biolib | `frankenmsa/inverse_fold/remote_protein_mpnn.py` | `BiolibProteinMPNN` | `library-backed` | `refactor` | `frankenmsa.inverse_fold.remote_protein_mpnn` | Record limitations such as heteromer support. |
| inverse-fold | ProteinMPNN chain JSONL writing and output packaging | `frankenmsa/inverse_fold/protein_mpnn_workflow.py` | helper functions | `library-backed` | `adopt` | `frankenmsa.inverse_fold` | Shared workflow and packaging helpers now live in the library. |
| inverse-fold | Local ProteinMPNN runner orchestration | `frankenmsa/inverse_fold/protein_mpnn_workflow.py`, `app/pages/inversefold.py` | `run_proteinmpnn`, page callback | `library-backed` | `adopt` | `frankenmsa.inverse_fold` | App page calls the library workflow directly; app helper runner removed. |
| inverse-fold | Colab-specific ProteinMPNN runner orchestration | `frankenmsa/inverse_fold/protein_mpnn_workflow.py`, notebooks | workflow function | `library-backed` | `adopt` | `frankenmsa.inverse_fold` plus thin notebook adapter | Colab setup remains an explicit installer call, but the run workflow is now shared. |
| install | Optional heavyweight dependency installers | `scripts/installers/` | installer scripts | `library-backed` | `keep` | `scripts/installers/` | Reusable pattern for external tool provisioning outside the base package install. |
| inverse-fold | PDB upload, download by code, advanced chain options UI | `app/pages/inversefold.py` | page callbacks | `ui-only` | `keep` | n/a | Dash input flow should remain app-side. |
| visualization | MSA alignment chart data generation | `frankenmsa/visual/alignment_chart.py`, `app/pages/visualize.py` | `visualise_msa`, visualization callbacks | `library-backed` | `refactor` | `frankenmsa.visual.alignment_chart` | Clarify whether the library returns figure data or renders directly. |
| visualization | Gap, conservation, and identity summaries | `app/pages/visualize.py`, `frankenmsa/utils` helpers | visualization callbacks | `duplicated` | `extract` | `frankenmsa.visual` or `frankenmsa.utils.msatools` | Data computations are reusable; charts are UI-only. |
| runtime | Runtime detection, upload directories, branch-aware Colab links | `app/helpers/constants.py` | constants module | `app-only` | `extract` | `frankenmsa.config` or `frankenmsa.utils` | Split reusable path/config logic from app presentation. |
| runtime | Dash page registration, routing, navbar, stores, injected MSA flow | `app/app.py` | app bootstrap | `ui-only` | `keep` | n/a | App integration only. |
| notebooks | Local notebook launch and render mode selection | `FrankenMSA_app_local.ipynb` | notebook cells | `ui-only` | `keep` | n/a | Notebook remains a launcher surface over shared APIs. |
| notebooks | Colab notebook install and app launch flow | `FrankenMSA_app_colab.ipynb` | notebook cells | `ui-only` | `keep` | n/a | Colab-specific runtime flow should call extracted library helpers where applicable. |

## Extraction Priorities

### Priority 1: Shared Parsing and Conversion

These are low-risk, high-value targets because they are pure functions and easy to test.

| Capability | Source | Destination |
| --- | --- | --- |
| Multimer A3M split logic | `app/pages/file.py` | `frankenmsa/utils/fileio.py` |
| CSV chain split and assembly | `app/pages/file.py` | `frankenmsa/utils/fileio.py` |
| Sequence text parsing for alignment inputs | `app/pages/align.py` | `frankenmsa/utils/seqtools.py` |
| Regex and free-query filters | `app/pages/edit.py` | `frankenmsa/utils/msatools.py` |
| Character transforms | `app/pages/edit.py` | `frankenmsa/utils/msatools.py` |

### Priority 2: ProteinMPNN Consolidation

| Capability | Source | Destination |
| --- | --- | --- |
| Chain JSONL and output packaging helpers | `frankenmsa/inverse_fold/protein_mpnn_workflow.py` | completed |
| Local runner orchestration | `frankenmsa/inverse_fold/protein_mpnn_workflow.py` | completed |
| Shared Colab/local workflow core | `frankenmsa/inverse_fold/protein_mpnn_workflow.py` | completed |

### Priority 3: Normalize Existing Library Backends

| Capability | Action |
| --- | --- |
| GhostFold | Remove hardcoded Colab path assumptions and add explicit configuration. |
| MMseqs2 and PLM-Search | Standardize result handling and public API wrappers. |
| Ward centroid merge | Expose intentionally through the cluster package and document that it merges existing cluster centroids rather than reclustering all sequences. |
| Visualization helpers | Separate reusable data computation from app-specific rendering. |

## Environment and Dependency Notes

| Area | Current Assumption | Required Direction |
| --- | --- | --- |
| GhostFold | Colab filesystem assumptions | Replace with configured temp/work directories. |
| ProteinMPNN | Mixed local helper logic and library backend logic | Runtime now resolves one shared installation contract; installer logic lives outside the package. |
| ESM encoding | Colab-oriented logging path in utility code | Remove hardcoded paths and make logging optional. |
| HH-suite | System binary availability | Improve dependency checks and error reporting. |
| MMseqs2 and PLM-Search | External service availability | Keep network boundaries explicit in public APIs. |

## App-Only Responsibilities That Should Stay in the App

- Dash layouts, page routing, and callback wiring.
- File upload widgets, dropdowns, sliders, and status messaging.
- Browser download routes and UI-triggered export delivery.
- Visualization rendering components and interactive selection state.
- Notebook launch controls and environment-specific launcher UX.

## Next Implementation Steps

1. Extract multimer split and CSV chain conversion helpers from the file page into `frankenmsa.utils`.
2. Move regex, free-query, and character-transform editing logic into `frankenmsa.utils.msatools`.
3. Normalize notebook callers so they invoke `frankenmsa.inverse_fold.run_proteinmpnn` directly where appropriate.
4. Remove hardcoded Colab path assumptions from existing library modules while extracting the shared helpers.
5. Add focused tests around the extracted pure functions before refactoring the Dash pages to adopt them.