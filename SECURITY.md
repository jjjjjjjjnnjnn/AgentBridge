# Security Policy

## Reporting a Vulnerability

We take the security of RelayOS seriously. If you discover a security vulnerability,
please follow the steps below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the project maintainer (jjjjjjjjnnjnn on GitHub)
or create a private security advisory at:
https://github.com/jjjjjjjjnnjnn/relayos/security/advisories/new

You should receive a response within 48 hours. If for some reason you do not,
please follow up to ensure the message was received.

## What to Include

To help us understand and fix the issue quickly, please include:

- Type of vulnerability
- Full paths of source files related to the issue
- Step-by-step reproduction instructions
- Proof-of-concept or exploit code (if possible)
- Impact description

## Scope

The following are considered in-scope for security reports:

- The `relayos` PyPI package (all versions)
- The source code in the `main` branch
- Configuration and secret handling
- Subprocess execution and command injection
- SQLite injection

## Out of Scope

- Attacks requiring physical access to the victim's machine
- Social engineering attacks
- Theoretical vulnerabilities without practical exploit

## Process

1. Report received → acknowledged within 48 hours
2. Assessment → we determine severity and impact
3. Fix → a patch is prepared
4. Release → new version published to PyPI with fix notes
5. Disclosure → issue is publicly disclosed after the fix is released

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Responsible Disclosure

We kindly request that you give us reasonable time to fix the issue before
making any information public. We will credit you in the release notes
(unless you prefer to remain anonymous).
