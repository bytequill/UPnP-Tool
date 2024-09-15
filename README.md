# UPnP-Tool
```
Usage: upnp.py [OPTIONS] COMMAND [ARGS]...
  UPnP CLI for stubborn networks by bytequill@codebased.xyz

Options:
  --device TEXT  Override the selected device URL
  --help         Show this message and exit.

Commands:
  add       Create a new UPnP port mapping
  delete    Delete a UPnP port mapping
  discover  Look for compatible UPnP devices on the network
  list      List all port mappings on selected device
```
This is a small and simple CLI using the [upnpclient](https://pypi.org/project/upnpclient/) library.  
It was created because all applications I could find did not detect my router.  
After some looking and trying I managed to find this python library, so I wrote a simple CLI wrapper for it.  
Hopefully someone will find some use for it.