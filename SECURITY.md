# Security Policy

## Threat model

This app accepts file uploads from anonymous (or bearer-token-authenticated)
users and runs similarity analysis against a user-supplied reference corpus.

| Trust boundary | What crosses it | Mitigation |
| --- | --- | --- |
| Network → API | Multipart file uploads, JSON requests | TLS termination at proxy; input validation in `services/security.py` |
| API → Filesystem | Uploaded documents stored on disk | UUID-named files; `Path.resolve().is_relative_to(UPLOADS_DIR)` enforced on every I/O |
| API → ML models | Persisted scikit-learn models loaded with `joblib` | Models loaded only from `app/ml_models/` (project-controlled path); never from user input |
| API → External | None at MVP | No external API calls beyond model inference; no third-party telemetry |

## Input validation

* **MIME sniff** via `python-magic` on the first 2048 bytes (not the file extension).
* **Allowlist**: `.pdf`, `.txt`, `.docx` only.
* **Size cap**: 10 MB per file.
* **Filename**: the original filename is never used as a filesystem path.
* **Path traversal**: every read/write path is resolved and asserted to be
  inside the uploads directory.

## Authentication

MVP supports an optional `X-API-Key` bearer token. When unset, the API is
**anonymous but rate-limited**. Production deployments MUST set the key and
front the API with a reverse proxy that enforces authn.

## Rate limiting

* 60 requests/minute/IP on `POST /analyses/detect` and `POST /predict`.
* 10 uploads/hour/IP on `POST /documents` and `POST /corpus`.

Enforced by `slowapi` middleware in `app/main.py`.

## Output handling

* Reports never include raw uploaded bytes — only extracted plain-text
  snippets.
* All snippets are HTML-escaped (`<>"'&` → entities) before they leave the
  API; the frontend uses `<mark>` spans without `dangerouslySetInnerHTML`.
* Logs contain only `sha256(file) + length`, never raw text.

## Dependency auditing

CI runs `pip-audit` (Python) and `npm audit --audit-level=high` (Node) on
every push. Dependabot opens weekly rollup PRs.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems. Email
the maintainer or use [GitHub Security Advisories][adv] to report privately.

[adv]: https://github.com/ALPHAMAN-0/Plagiarism_Detected/security/advisories/new

We aim to acknowledge reports within 3 business days.
