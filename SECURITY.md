# SECURITY (MVP Notes)

- This MVP is for demonstration only and is **not** production-ready.
- No real patient data should be used.
- Authentication is stubbed via `X-User-Id` header; in production use OIDC (NHS CIS2) and RBAC.
- Files are stored locally; use encrypted volumes if testing on shared machines.
