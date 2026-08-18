# Operators

This page deliberately contains only safe operational entry points.

## Service endpoints

| Service | Address |
| --- | --- |
| Hosted documentation | `https://nancy.rges-pit.com` |
| MCP and HTTP API | `https://mcp.rges-pit.com` |
| Health check | `https://mcp.rges-pit.com/health` |
| Administrative interface | `https://nancy-admin.rges-pit.com` |

The administrative interface requires operator authentication and is not part
of the public user workflow.

## Traffic controls

The hosted service defaults to 600 requests per minute per API key, 1,200
requests per minute per source IP, and five API-key issuances per hour per
source IP. Health checks are exempt. Personal API keys cannot trigger index
rebuilds.

## Package and deployment sources

- [Nancy Brain package](https://github.com/AmberLee2427/nancy-brain)
- [Package documentation](https://nancy-docs.malpas.nz/)
- [Report a package issue](https://github.com/AmberLee2427/nancy-brain/issues)

Hosted-service access, account, or corpus questions should go to the Nancy
administrators rather than the package issue tracker.
