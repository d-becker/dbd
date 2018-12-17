#!/usr/bin/env python3

from pathlib import Path

import socket
import subprocess

from typing import Iterable, Optional

import xml.etree.ElementTree as ET

def perform_dns(hostname: str) -> str:
    cmd_ip = ["dig", "+short", hostname]
    process_result_ip = subprocess.run(cmd_ip, stdout=subprocess.PIPE, check=True)
    ip = process_result_ip.stdout.decode().strip()

    return ip

def perform_reverse_dns(ip: str) -> str:
    cmd_rDNS = ["dig", "+short", "-x", ip]
    process_result_rDNS = subprocess.run(cmd_rDNS, stdout=subprocess.PIPE, check=True)

    # Delete the last '.' character that dig adds to the reverse DNS result.
    hostname = process_result_rDNS.stdout.decode().strip()[:-1]

    return hostname

def get_reverse_dns_host_name(normal_hostname: str) -> str:
    ip = perform_dns(normal_hostname)

    return perform_reverse_dns(ip)

def get_site_xml_files(directory: Path) -> Iterable[Path]:
    return directory.glob("*-site.xml")

def get_host_from_property_name(name: str) -> Optional[str]:
    hosts = ["namenode", "nodemanager", "resourcemanager", "datanode"]

    for host in hosts:
        if host in name:
            return host
        
    return None

def resolve_in_property(property: ET.Element) -> bool:
    value_element = property.find("value")
    if value_element is None or value_element.text is None or "_HOST" not in value_element.text:
        return False

    name_element = property.find("name")
    if name_element is None or name_element.text is None:
        return False

    name = name_element.text

    if "principal" not in name:
        return False

    hostname = get_host_from_property_name(name)
    this_host_name = socket.gethostname()
    if hostname is None:
        # If no recognised hostname is found in the name, we fall back to the local host's name.
        hostname = this_host_name

    if hostname == "datanode" and this_host_name != "datanode":
        # If the element specifies the datanode but we are not on the
        # datanode, we should not have it listed, because for example
        # the name node will not accept other datanodes if one is
        # given, which does not let us scale.
        # TODO: Maybe we should get the parent and delete property.
        property.remove(value_element)
        property.remove(name_element)
        return True

    full_hostname = get_reverse_dns_host_name(hostname)
        
    value_element.text = value_element.text.replace("_HOST", full_hostname)
    return True

def resolve_in_file(site_file: Path) -> None:
    print("Processing file: {}.".format(site_file))
    tree = ET.parse(str(site_file))
    root = tree.getroot()

    for property in root.iter("property"):
        resolve_in_property(property)

    tree.write(str(site_file))

def resolve_HOSTs(site_directory: Path) -> None:
    for site_file in get_site_xml_files(site_directory):
        resolve_in_file(site_file)

def main() -> None:
    resolve_HOSTs(Path("/opt/hadoop/etc/hadoop"))

if __name__ == "__main__":
    print("Running python script.")
    main()
else:
    print("NOT running python script.")
