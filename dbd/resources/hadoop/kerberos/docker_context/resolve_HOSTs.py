#!/usr/bin/env python3

import argparse
import itertools

from pathlib import Path

import socket
import sys
import subprocess

from typing import Iterable, Optional

import xml.etree.ElementTree as ET

def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve _HOST variables in XML files.")
    parser.add_argument("xml_files", nargs="*", help="the XML files in which to resolve _HOST variables")
    parser.add_argument("--hadoop", action="store_true", help="in addition to other files, add the Hadoop config files")
    parser.add_argument("--oozie", action="store_true", help="in addition to other files, add the Oozie config files")

    return parser

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

def get_host_from_property_name(name: str) -> Optional[str]:
    hosts = ["namenode", "nodemanager", "resourcemanager", "datanode"]

    for host in hosts:
        if host in name:
            return host

    if "jobhistory" in name:
        return "historyserver"
        
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

def resolve_HOSTs_in_files(files: Iterable[Path]):
    for xml_file in files:
        resolve_in_file(xml_file)

def get_hadoop_files() -> Iterable[Path]:
    return Path("/opt/hadoop/etc/hadoop").glob("*-site.xml")

def get_oozie_files() -> Iterable[Path]:
    filenames = ["/opt/oozie/conf/oozie-site.xml",
                 "/opt/oozie/conf/hadoop-config.xml",
                 "/opt/oozie/conf/hadoop-conf/core-site.xml"]
    return map(Path, filenames)

def main() -> None:
    args = get_argument_parser().parse_args()

    file_paths = map(Path, args.xml_files)

    if args.hadoop:
        print("Hadoop files added.") # TODO
        file_paths = itertools.chain(file_paths, get_hadoop_files())

    if args.oozie:
        print("Oozie file added.") # TODO
        file_paths = itertools.chain(file_paths, get_oozie_files())

    resolve_HOSTs_in_files(file_paths)

if __name__ == "__main__":
    print("Resolving _HOST variables.")
    main()
