# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability in Solacia, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. **Email**: Send details to [security@solacia.dev](mailto:security@solacia.dev)
2. **GitHub**: Use [private vulnerability reporting](https://github.com/iweb3insight/solacia/security/advisories/new)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

| Action | Timeline |
|--------|----------|
| Acknowledgment | 48 hours |
| Initial assessment | 5 business days |
| Fix or mitigation | 14 business days |
| Public disclosure | After fix is released |

### Scope

The following are in scope:

- Remote code execution
- Authentication/authorization bypass
- SQL injection
- Prompt injection leading to data exfiltration
- API key or secret exposure
- Denial of service via crafted input

### Out of Scope

- Social engineering
- Attacks requiring physical access
- Issues in third-party dependencies (report to the dependency directly)

## Security Best Practices for Deployments

- Always use a reverse proxy (nginx/caddy) in production
- Set `API_HOST=127.0.0.1` and expose via reverse proxy only
- Use environment variables for secrets, never `.env` files in production
- Enable rate limiting at the reverse proxy level
- Regularly update dependencies (`pip-audit`)
