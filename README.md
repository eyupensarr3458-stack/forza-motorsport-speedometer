# Forza Precision Telemetry Announcer (NVDA Add-on)

NVDA global plugin for Forza telemetry announcements over UDP.

For Forza Motorsport, open `Gameplay > Data Out`, enable `Data Out`, set `Data Out IP Address` to your IPv4 address, set the port to `5300`, and set `Data Out Package Format` to `Car Dash`.

## Features

- Announces current vehicle speed with `Alt+A`.
- Listens on UDP port `5300`.
- Includes repair helpers for loopback exemption and firewall rule creation.

## Repository Layout

- `globalPlugins/ForzaGlobal.py`
- `installTasks.py`
- `manifest.ini`
- `scripts/build.ps1`

## Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Build output is written to `dist/` as:

- `forza_precision_telemetry-4.0.3.nvda-addon`

## Distribution

Publish each built `.nvda-addon` as a GitHub Release asset and use the direct `https` asset URL in NVDA add-on datastore submission.

## Publish Automation

If `gh` is installed and authenticated, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish.ps1 -GitHubOwner YOUR_GITHUB_USERNAME
```

This command:

- builds the add-on
- creates/pushes a GitHub repository
- creates or updates a GitHub release asset
- opens the prefilled NVDA add-on datastore registration form
