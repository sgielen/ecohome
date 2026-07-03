# ecohome

Open-source Python client and CLI for the [New Energy
Eco-Home](https://ehome.ne01.com/) heat pump API, which is used by Batavia Heat
heat pumps in the Netherlands.

## Installation

Requires Python 3.14+. Older versions probably work fine, YMMV.

```
pip install ecohome
```

Or from source using [uv](https://github.com/astral-sh/uv):

```
uv sync
```

## CLI usage

Credentials can be passed as flags or via environment variables:

```
export ECOHOME_USER=you@example.com
export ECOHOME_PASSWORD=yourpassword
```

After the first successful login, credentials are saved to `~/.ecohome/credentials.json`
(mode 0600) and reused automatically on subsequent calls.

### Show status

```
pyecohome status
```

Example output:

```
Heating:   off  29.2℃ / 27.6℃  →  40.0℃  (Verwarming)
Hot water: off  61.5℃  →  65.0℃
```

Add `--json` for machine-readable output:

```
pyecohome status --json
```

```json
{
  "heating": {
    "on": false,
    "current_temp_main": 29.2,
    "current_temp_minor": 27.6,
    "target_temp": 40.0,
    "mode": "Verwarming"
  },
  "hot_water": {
    "on": false,
    "current_temp": 61.5,
    "target_temp": 65.0
  }
}
```

### Control hot water

```
pyecohome hot-water on
pyecohome hot-water off
```

Use `--dry-run` to print the request that would be sent without actually sending it:

```
pyecohome hot-water on --dry-run
```

### Options

| Flag | Description |
|------|-------------|
| `--username` | Login username (overrides `ECOHOME_USER`) |
| `--password` | Login password (overrides `ECOHOME_PASSWORD`) |
| `--device` | Device code to target (auto-selected when you have only one device) |
| `--dry-run` | Print the outgoing request instead of sending it |

## Python API

```python
from ecohome.client import EcoHomeClient

client = EcoHomeClient.login("you@example.com", "yourpassword")

# List devices
devices = client.list_devices()
device_code = devices[0]["device_code"]

# Current state
detail = client.get_device_detail(device_code)

# Turn hot water on/off
client.update_switch_state(device_code, address="1020", value=True)

# Log out (also removes saved credentials)
client.logout()
```

## Credentials storage

Credentials (username, user ID, token, session cookie) are stored in
`~/.ecohome/credentials.json` after a successful login. Pass
`save_credentials=False` to `EcoHomeClient.login()` to opt out.

## Development

```
uv sync
uv run ruff check src/
```

### Releases

- Update version number in `pyproject.toml`
- Run `uv sync`, commit and push all changes
- Run `uv build`
- Run `git tag v0.1.1` (same version as in `pyproject.toml`)
- Run `git push --tags`
- Run `uvx twine upload dist/*`
