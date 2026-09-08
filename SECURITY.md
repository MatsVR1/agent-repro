# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected security vulnerability. Contact the maintainer privately through the GitHub profile or repository security advisory workflow with a description, reproduction steps, affected versions, and a suggested mitigation.

## Data handling

`agent-repro` is designed to process traces locally. It applies pattern-based redaction before writing generated bundles, but no automatic redactor can guarantee that every secret or personal datum is detected. Always review `bundle.json` and `github-issue.md` before sharing them. Do not use the example patterns as a substitute for an organization-specific data classification and privacy review.
