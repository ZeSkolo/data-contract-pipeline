# Data Contract Pipeline

**Data engineering** · A CSV-to-SQLite ingestion pipeline with contracts, quarantine and lineage.

## Run locally

Python 3.11+; no third-party packages required. From the standalone repository checkout root:

```bash
python main.py demo
python main.py run example.json
python -m unittest discover -s tests -v
```

`example.json` is the input contract and contains only synthetic or fictional data. `core.run(payload)` returns a JSON-serializable result. Invalid inputs produce an error and a nonzero CLI exit code.

## What it implements

- Declarative column types, required values, uniqueness, ranges and allowed values.
- Invalid records are quarantined with row-level reasons; valid rows are ingested transactionally.
- Content-addressed batch IDs make repeated input ingestion idempotent.
- Batch lineage records accepted/rejected counts; previews and SQL row counts are returned.

## Design and limitations

Single-file educational ETL, not an orchestrator or warehouse service. Contract column names are validated, values are parameterized and identifiers are quoted. All rows are held in memory, capped at 10000; CSV inputs are limited to 500 KB. Contract changes intentionally create separate batches. No external databases or personal datasets are bundled.

## Suggested next step

Add your own data and domain-specific acceptance tests. Read and understand the implementation before presenting it in interviews. No live deployment is implied.

<!-- AH-INDEPTH-DOCS:START -->
## In-depth engineering guide

### Problem and scope

A CSV-to-SQLite ingestion pipeline with contracts, quarantine and lineage.

This is an independent runnable reference implementation, with synthetic sample input and explicit limits. It is not a deployed service or independently validated business result.

### Architecture and end-to-end flow

```text
CSV and contract → validate schema/rows → quarantine invalid records → transactionally store accepted rows and batch identity → summary
```

| File | Responsibility |
|---|---|
| core.py | Domain validation and project-specific algorithm/state transitions |
| main.py | Bounded JSON CLI input, demo dispatch and JSON output |
| example.json | Exact reproducible sample input |
| tests/test_core.py | Unit and edge-case coverage |

### Design decisions and trade-offs

1. Contracts support str/int/float conversion, required/unique fields, numeric ranges and allowed values. Invalid rows receive explicit quarantine reasons instead of silent coercion.

2. Batch identity is SHA-256 over content and canonicalized contract. Re-running a previously committed batch is idempotent in serial ingestion. Concurrent duplicate-ingest orchestration is not a supported guarantee.

3. Headers and row width must match the contract. Non-finite numbers are rejected. Inputs are bounded to 500 KB and 10,000 rows. SQLite value inserts are parameterized.

### Reproducible setup

Requires Python 3.11+ and no third-party Python packages. Run from the standalone repository checkout root:

```bash
python main.py demo
python main.py run example.json
python -m unittest discover -s tests -v
```

CLI inputs are JSON objects, bounded to 1 MB. Supported domain errors produce a JSON error on stderr and a nonzero exit; inspect the message rather than treating a failed run as a result. The demo does not require a model key, network access or production data.

### Exact example input

```json
{
  "csv": "id,amount,status\nA1,120,paid\nA2,-5,paid\nA1,30,pending\nA3,45,pending\n",
  "contract": {
    "id": {
      "type": "str",
      "required": true,
      "unique": true
    },
    "amount": {
      "type": "float",
      "required": true,
      "min": 0
    },
    "status": {
      "type": "str",
      "allowed": [
        "paid",
        "pending"
      ]
    }
  }
}
```

### Core implementation interfaces

| Callable | Boundary |
|---|---|
| `validate(csv_text, contract)` | Implementation boundary; see source for validation and return structure. |
| `run(p, db_path=None)` | Implementation boundary; see source for validation and return structure. |

The Python `run` result is JSON-serializable. Inspect the source and `main.py run example.json` output for the exact return keys; do not assume another project’s result schema.

### Test coverage and reproducibility

- `tests/test_core.py::test_quarantine`
- `tests/test_core.py::test_idempotent`
- `tests/test_core.py::test_schema`
- `tests/test_core.py::test_nonfinite`
- `tests/test_core.py::test_bad_names`

5 named tests are present in this repository. Run the standalone unittest command above; it includes local HTTP tests where present. The GitHub Actions workflow supports pull requests and manual dispatch; remote CI has not been run as part of this preparation. Docker build/run was not executed; no real cloud/model/production-cluster validation is claimed.

### Security and failure boundaries

Single-file educational ETL, not an orchestrator or warehouse service. Contract column names are validated, values are parameterized and identifiers are quoted. All rows are held in memory, capped at 10000; CSV inputs are limited to 500 KB. Contract changes intentionally create separate batches. No external databases or personal datasets are bundled.

Never commit .env, real API keys, runtime databases, approval material or customer data. See SECURITY.md. A successful example demonstrates the included workflow, not safe internet deployment.

### Troubleshooting

- **Import error:** run from this project’s own folder; each project intentionally has its own core.py.
- **Invalid sample/schema:** start from example.json, then change one field at a time and read the returned validation message.
- **Port already in use:** stop the previous process or select another --port where server.py exists.
- **SQLite lock/state surprise:** close duplicate processes, confirm PROJECT_DB and back up before deliberate resets. Do not delete unrelated project data.
- **External dependency unavailable:** default demos run offline; live provider calls and container pulls require your own working access and may incur external costs.

### Known limitations

Single-file educational ETL, not an orchestrator or warehouse service. Contract column names are validated, values are parameterized and identifiers are quoted. All rows are held in memory, capped at 10000; CSV inputs are limited to 500 KB. Contract changes intentionally create separate batches. No external databases or personal datasets are bundled.

### Extension roadmap — not implemented

Add schema evolution, column-level privacy classifications, serial/concurrent orchestration controls, recovery checkpoints and lineage retention for production ingestion.
<!-- AH-INDEPTH-DOCS:END -->


## Provenance and standalone layout

Extracted from `applied-ai-engineering-lab/projects/09-data-contract-pipeline`. The algorithms, CLI, tests, examples and any server/UI/worker/Docker files are retained byte-for-byte. Only documentation, repository hygiene and CI configuration were adapted for standalone use. This checkout needs neither the parent collection catalog nor its runner/publisher. It is a reference implementation, not evidence of a historical production deployment or measured business outcome.
