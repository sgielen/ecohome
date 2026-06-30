import argparse
import json as json_module
import os
import sys

from ecohome.client import EcoHomeClient


def _get_client(args: argparse.Namespace) -> EcoHomeClient:
    username = args.username or os.environ.get("ECOHOME_USER")
    password = args.password or os.environ.get("ECOHOME_PASSWORD")
    if not username or not password:
        print(
            "Error: provide --username/--password or set ECOHOME_USER/ECOHOME_PASSWORD",
            file=sys.stderr,
        )
        sys.exit(1)
    return EcoHomeClient.login(username, password)


def _auto_device_code(client: EcoHomeClient, args: argparse.Namespace) -> str:
    if args.device:
        return args.device
    devices = client.list_devices()
    if not devices:
        print("Error: no devices found", file=sys.stderr)
        sys.exit(1)
    if len(devices) > 1:
        lines = "\n".join(f"  {d['device_code']}  {d['device_nick_name']}" for d in devices)
        print(f"Error: multiple devices found, use --device:\n{lines}", file=sys.stderr)
        sys.exit(1)
    return devices[0]["device_code"]


def _find_card(card_list: list, *, has_modes: bool) -> dict | None:
    for card in card_list:
        if (card.get("modeList") is not None) == has_modes:
            return card
    return None


def cmd_status(client: EcoHomeClient, args: argparse.Namespace) -> int:
    device_code = _auto_device_code(client, args)
    detail = client.get_device_detail(device_code)
    unit = detail.get("curUnit", "°C")

    heating = _find_card(detail["cardList"], has_modes=True)
    hot_water = _find_card(detail["cardList"], has_modes=False)

    if args.json:
        output: dict = {}
        if heating:
            output["heating"] = {
                "on": heating["curSwitch"],
                "current_temp_main": float(heating["curTempMain"]) if heating.get("curTempMain") else None,
                "current_temp_minor": float(heating["curTempMinor"]) if heating.get("curTempMinor") else None,
                "target_temp": float(heating["settingTemp"]) if heating.get("settingTemp") else None,
                "mode": heating["modeList"][0]["modeMeaning"] if heating.get("modeList") else None,
            }
        if hot_water:
            output["hot_water"] = {
                "on": hot_water["curSwitch"],
                "current_temp": float(hot_water["curTempMain"]) if hot_water.get("curTempMain") else None,
                "target_temp": float(hot_water["settingTemp"]) if hot_water.get("settingTemp") else None,
            }
        print(json_module.dumps(output, indent=2))
    else:
        if heating:
            state = "on" if heating["curSwitch"] else "off"
            mode = heating["modeList"][0]["modeMeaning"] if heating.get("modeList") else "unknown"
            t_main = heating.get("curTempMain", "?")
            t_minor = heating.get("curTempMinor")
            t_set = heating.get("settingTemp", "?")
            temps = f"{t_main}{unit} / {t_minor}{unit}" if t_minor else f"{t_main}{unit}"
            print(f"Heating:   {state:<3}  {temps}  →  {t_set}{unit}  ({mode})")
        if hot_water:
            state = "on" if hot_water["curSwitch"] else "off"
            t_main = hot_water.get("curTempMain", "?")
            t_set = hot_water.get("settingTemp", "?")
            print(f"Hot water: {state:<3}  {t_main}{unit}  →  {t_set}{unit}")

    return 0


def cmd_hot_water(client: EcoHomeClient, args: argparse.Namespace) -> int:
    device_code = _auto_device_code(client, args)
    detail = client.get_device_detail(device_code)
    card = _find_card(detail["cardList"], has_modes=False)
    if card is None:
        print("Error: no hot water card found on this device", file=sys.stderr)
        sys.exit(1)
    value = args.state == "on"
    client.update_switch_state(device_code, card["switchAddress"], value, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"Hot water {'enabled' if value else 'disabled'}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pyecohome",
        description="Control your Eco-Home heat pump from the command line.",
    )
    parser.add_argument("--username", default=None, help="Login username (or set ECOHOME_USER)")
    parser.add_argument("--password", default=None, help="Login password (or set ECOHOME_PASSWORD)")
    parser.add_argument("--device", default=None, help="Device code (auto-selected if only one exists)")
    parser.add_argument("--dry-run", action="store_true", help="Print the request instead of sending it")

    subparsers = parser.add_subparsers(dest="command", required=True)

    status_p = subparsers.add_parser("status", help="Show current temperatures and state")
    status_p.add_argument("--json", action="store_true", help="Output as JSON")

    hw_p = subparsers.add_parser("hot-water", help="Enable or disable hot water")
    hw_p.add_argument("state", choices=["on", "off"])

    args = parser.parse_args()
    client = _get_client(args)

    if args.command == "status":
        return cmd_status(client, args)
    if args.command == "hot-water":
        return cmd_hot_water(client, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
