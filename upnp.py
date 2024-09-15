#!/usr/bin/env python
# UPnP-Tool Released under the MIT license on Github: https://github.com/bytequill/UPnP-Tool
import os

try:
    import upnpclient
    import click
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print("Could not find package: " + e.name + "\nPlease install it or the requirements.txt file included with the program")
    exit(1)

console = Console()
d: upnpclient.Device

FILE_SIGNATURE = "UPnP-Tool Released under the MIT license on Github: https://github.com/bytequill/UPnP-Tool" # This string is included in the config file
CONFIG_FILE = ".upnpDevice"
# compute the full path of ~/.config/{CONFIG_FILE} on *nix systems and an equivalent on Windows
CONFIG_FILE = f"{os.path.expanduser('~')}/.config/{CONFIG_FILE}" if os.name != 'nt' else f"{os.environ['USERPROFILE']}/{CONFIG_FILE}"

def device_selected_get() -> None:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            selected_device = f.readline().strip()
    else:
        selected_device = os.getenv('UPNP_DEVICE', None)

    if not selected_device:
        console.print("[red] No device selected.")
        return None

    try:
        d = upnpclient.Device(selected_device)
        console.print("[green] Selected device \"" + selected_device + "\" successfully.")
        return d
    except Exception as e:
        console.print(f"[red] Failed to get the selected device: {e}")
        return None

def device_selected_set(device_str) -> None:
    with open(CONFIG_FILE, 'w') as f:
        f.write(device_str)

        f.write("\n" + FILE_SIGNATURE)
    
    console.print("[green] Selected device \"" + device_str + "\" set successfully.")

def protocol_check_valid(Protocol: str) -> bool:
    if Protocol.upper() != "TCP" and Protocol.upper() != "UDP":
        console.print("[bold red] Protocol must be TCP or UDP, not " + Protocol)
        return False
    return True

@click.command(help="List all port mappings on selected device")
def list():
    i = 0
    table = Table(title="Current UPnP forwards")

    table.add_column("#", style="cyan", justify="center")
    table.add_column("Proto", style="bold", justify="center")
    table.add_column("ExPort", style="bold green", justify="center")
    table.add_column("InPort", style="red", justify="center")
    table.add_column("InHost", style="yellow")
    table.add_column("Description", no_wrap=True)
    table.add_column("Duration", justify="right")
    while True:
        try:
            service = d.WANIPConn1.GetGenericPortMappingEntry(NewPortMappingIndex=i)

            table.add_row(
                str(i),
                str(service["NewProtocol"]),
                str(service["NewExternalPort"]),
                str(service["NewInternalPort"]),
                str(service["NewInternalClient"]),
                str(service["NewPortMappingDescription"]),
                str(service["NewLeaseDuration"])
            )
            i += 1
        except Exception as e:
            break

    console.print(table)

@click.command(help="Look for compatible UPnP devices on the network")
def discover():
    console.print("[green] Initiated search for network devices, please note that error messages are expected during this process.")
    devices = upnpclient.discover(timeout=1)
    table = Table(title="Discovered UPnP Devices")
    table.add_column("#")
    table.add_column("URL", style="bold green")
    table.add_column("Name", style="cyan")
    table.add_column("# of forwards", style="bold blue")

    i = 0
    found_devices = []
    for device in devices:
        device: upnpclient.Device = device
        found = False
        for service in device.services:
            service: upnpclient.Service = service
            # We are ingoring other uses of the ssdp protocol in our script
            if service.service_id == "urn:upnp-org:serviceId:WANIPConn1":
                found = True
                found_devices.append(device)
                ii = 0
                while True:
                    try:
                        # This errors out when there are no more entries, and we don't care about the error message anyway
                        # Not the perfect interface but we shall manage
                        device.WANIPConn1.GetGenericPortMappingEntry(NewPortMappingIndex=ii)
                        ii += 1
                    except:
                        break
                table.add_row(str(i), device.location, device.friendly_name, str(ii))
                break
        if not found:
            continue
        i += 1
    console.print(table)
    
    if len(devices) == 0:
        console.print("[red] Could not find a compatible device")
    # If there is only possible device, select it automatically
    elif len(devices) == 1:
        device_selected_set(found_devices[0].location)
    else:
        while True:
            try:
                x = int(input("Select device index: "))
                device_selected_set(found_devices[x].location)
            # Exception does not catch KeyboardInterrupt
            except Exception:
                console.print("[red] Please select a correct device")
                continue
            break

@click.command(help="Create a new UPnP port mapping")
@click.option("--eport", "ExtPort", required=True, prompt="External port", help="External port")
@click.option("--proto", "Protocol", required=True, help="Protocol. Either TCP or UDP", prompt="Protocol. TCP or UDP")
@click.option("--iport", "IntPort", required=True, prompt="Internal port", help="Internal port")
@click.option("--ihost", "IntHost", required=True, prompt="Internal host(IP)", help="Internal host(IP)")
@click.option("--description", "Description", default="")
@click.option("--lifetime", "Lifetime", default=0, type=int, help="Lifetime of the mapping (in seconds) [default=0(infinite)]")
def add(ExtPort, Protocol: str, IntPort, IntHost, Description, Lifetime):
    if not protocol_check_valid(Protocol):
        return
    
    # ? Possibly allow setting `RemoteHost` and `Enabled` with options ?
    d.WANIPConn1.AddPortMapping(
        NewRemoteHost="",
        NewExternalPort=ExtPort,
        NewProtocol=Protocol.upper(),
        NewInternalPort=IntPort,
        NewInternalClient=IntHost,
        NewEnabled="1",
        NewPortMappingDescription=Description,
        NewLeaseDuration=Lifetime
    )
@click.command(help="Delete a UPnP port mapping")
@click.option("--eport", "ExtPort", required=True, prompt="External port")
@click.option("--proto", "Protocol", required=True, help="Protocol. Either TCP or UDP", prompt="Protocol. TCP or UDP")
def delete(ExtPort, Protocol: str):
    if not protocol_check_valid(Protocol):
        return
    
    d.WANIPConn1.DeletePortMapping(
        ExtPort=ExtPort,
        Proto=Protocol.upper()
    )

@click.group(help="UPnP CLI for stubborn networks by bytequill@codebased.xyz")
@click.option("--device", "device", help="Override the selected device URL")
def main(device):
    global d

    if device:
        d = upnpclient.Device(device)
    else:
        d = device_selected_get()

main.add_command(list)
main.add_command(discover)
main.add_command(add)
main.add_command(delete)

if __name__ == "__main__":
    main()