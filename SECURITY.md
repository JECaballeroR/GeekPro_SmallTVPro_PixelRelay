# Security

## Calendar URLs

A Google Calendar private ICS URL is a bearer secret. Anyone who has it
may read the calendar feed.

- Keep it only in `.env` or an operating-system environment variable.
- Never paste it into source code, screenshots, issues or logs.
- Revoke and regenerate it if exposed.

## Device network

Stock GeekMagic HTTP endpoints are intended for a trusted local network.
Do not expose the device directly to the public Internet.

## Reporting

Remove IP addresses, calendar URLs and personal event details before
attaching logs or configuration files to a GitHub issue.
