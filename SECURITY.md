# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in MCPS, please **do not** open a public GitHub issue.

Instead, please follow responsible disclosure practices:

1. **Email Security Team**: Send a detailed report to `security@your-org.com`
   - Include a description of the vulnerability
   - Provide steps to reproduce (if applicable)
   - Estimate the severity and impact
   - Suggest a potential fix if possible

2. **Timeline**:
   - We will acknowledge your report within 48 hours
   - We aim to release a patch within 7-30 days depending on severity
   - We will credit you in the security advisory (if desired)

3. **Do Not**:
   - Publicly disclose the vulnerability before we've released a patch
   - Access other users' data
   - Perform any testing on accounts you don't own
   - Disrupt services

## Security Considerations

### Database Security

- SQLite databases contain sensitive metadata
- Always use strong, unique API keys
- Keep database files in secure locations with restricted access
- Regularly back up your database

### API Security

- All API keys (GitHub, OpenAI, etc.) must be kept confidential
- Use environment variables, never commit credentials to version control
- Use `.env.example` for documentation, `.env` is in `.gitignore`
- Rotate API keys periodically

### Dependency Security

- We regularly update dependencies to patch known vulnerabilities
- Run `pip check` to identify known security issues in dependencies
- Monitor security advisories for your dependencies

### Input Validation

- All user inputs are validated
- File uploads are scanned for malicious content
- SQL queries use parameterized statements to prevent injection

## Security Best Practices for Users

### Installation

```bash
# Verify package integrity
pip install mcps --require-hashes

# Use virtual environments
python -m venv venv
source venv/bin/activate
```

### Configuration

```bash
# Never commit sensitive data
cp .env.example .env
# Edit .env with YOUR secrets
# .env is in .gitignore

# Use strong, unique secrets
export SECRET_KEY=$(openssl rand -hex 32)
```

### Database

```bash
# Back up your database regularly
bash scripts/backup-db.sh

# Verify database integrity
bash scripts/backup-db.sh --verify
```

## Supported Versions

| Version | Supported | Status |
|---------|-----------|--------|
| 3.0.0   | Yes       | Current |
| 2.5.0   | Yes       | LTS until 2025-06 |
| 2.0.0   | Partial   | Maintenance only |
| < 2.0   | No        | Please upgrade |

## Security Scanning

MCPS includes built-in security scanning features:

### Code Analysis
- AST-based vulnerability detection
- Dangerous pattern identification
- License compliance checking
- Dependency vulnerability scanning

### Harvested Server Security
- Safety assessment of downloaded code
- Binary scanning
- Configuration validation

## Compliance

MCPS follows these security standards:

- OWASP Top 10 mitigations
- CWE most dangerous software weakness prevention
- NIST Cybersecurity Framework alignment
- Data privacy best practices

## Security Roadmap

- [ ] SBOM (Software Bill of Materials) generation
- [ ] Cryptographic signature verification for packages
- [ ] Hardware security key support
- [ ] Audit logging system
- [ ] Penetration testing program
- [ ] Security certification

## Contact

- **Security Email**: security@your-org.com
- **GitHub Security**: https://github.com/your-org/mcps/security
- **Maintainers**: See CONTRIBUTORS file

---

**Last Updated**: 2025-01-15

Thank you for helping keep MCPS secure!
