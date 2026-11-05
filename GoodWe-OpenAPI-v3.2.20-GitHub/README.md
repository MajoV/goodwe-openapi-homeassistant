# GoodWe OpenAPI by home-co

Monitor selected GoodWe plants in Home Assistant using the official GoodWe OpenAPI.

**Version:** 3.2.20

## Installation

1. Copy `custom_components/goodwe_openapi` into the Home Assistant `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for **GoodWe OpenAPI by home-co**.
4. Add the integration and provide the GoodWe OpenAPI AppID and AppSecret. Configure only the Plant IDs you want to monitor.

## Notes

- Requires an internet connection and an authorized GoodWe account.
- This is a custom integration, not an official GoodWe or Home Assistant integration.
- Do not commit credentials, access tokens, or personal plant records.
- The integration has not been validated through a full automated test suite.
