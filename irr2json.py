#!/usr/bin/env python3

import_file = "./irr.db"
serial_hash_file = "./IRR.SERIALHASH"
export_file = "./irrdb.json"


import os
import time

tm = int(time.time())

def asdot_to_asplain(str):
    split = str.split(".")
    if len(split) == 2:
        dot = int(split[0] or "0")
        add = int(split[1] or "0")
        return (dot * 65536) + add
    else:
        return None

if not os.path.isfile(f"./{serial_hash_file}"):
    print(f"./{serial_hash_file} does not exist, exiting")
    exit(1)

if not os.path.isfile(f"./{import_file}"):
    print(f"./{import_file} does not exist, exiting")
    exit(1)

irr_serial_hash = ""
with open(serial_hash_file, 'r') as f_serial:
    irr_serial_hash = f_serial.read()

roa_serial_hash = ""
if os.path.isfile(f"./{export_file}"):
    with open(export_file, 'rb') as f:
        f.seek(0, os.SEEK_END)
        newlines = 0
        while newlines < 3:
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            newlines += 1
            f.seek(-2, os.SEEK_CUR)
        ending = f.read()
        # not very error-proof but oh well
        roa_serial_hash = ending.decode('utf-8').translate({ord(i): None for i in ', {}\n'}).split(":")[1]

if irr_serial_hash == roa_serial_hash:
    print(f"{export_file} is up to date. nothing to do.")
    exit()

print(f"{export_file} is out of date, regenerating")

with open(export_file, "w") as f_out:
    f_out.writelines([
        "{\n",
        "    \"roas\": ["
    ])

    with open(import_file, "r") as f_in:
        print(f"{import_file} is properly opened, processing")
        proc_cnt = 0
        line = f_in.readline()
        prefix = None
        asn = None
        source = None
        next_proc_item = "route"
        cnt = 0
        while line:
            variables = line.split(":")

            attrib = variables[0].strip().lower() or ""
            val = (":".join(variables[1:])).strip().split()[0].upper() or ""

            if attrib.startswith(next_proc_item) and len(val) > 0:
                if attrib.startswith("route"):
                    prefix = val.lower()
                    next_proc_item = "origin"

                if attrib.startswith("origin"):
                    val = val.replace("AS", "")
                    if "." not in val:
                        asn = f"AS{val}"
                    else:
                        asn = f"AS{asdot_to_asplain(val)}"
                    next_proc_item = "source"

                if attrib.startswith("source"):
                    source = val.upper()

            if prefix and asn and source:
                if "." in prefix:
                    maxlen = 24
                    prefixlen = 32
                elif ":" in prefix:
                    maxlen = 48
                    prefixlen = 128
                else:
                    maxlen = 1
                    prefixlen = 32

                if "/" in prefix:
                    prefixlen = int(prefix.split("/")[1])

                if prefixlen <= maxlen:
                    f_out.write(f"\n        {{\"asn\": \"{asn}\", \"prefix\": \"{prefix}\", \"maxLength\": {maxlen}, \"ta\": \"{source}\"}},")
                    proc_cnt += 1
                prefix = None
                asn = None
                next_proc_item = "route"

            line = f_in.readline()
        if proc_cnt > 0:
            # remove last comma
            f_out.seek(0, os.SEEK_END)
            pos = f_out.tell() - 1
            f_out.seek(pos, os.SEEK_SET)
            f_out.truncate()

    f_out.writelines([
        "\n    ],\n",
        "    \"metadata\": {\n",
        "        \"builder\": \"irr2json\",\n",
        f"        \"generated\": {tm},\n",
        f"        \"valid\": {tm + 86400},\n",
        f"        \"counts\": {proc_cnt},\n",
        f"        \"serial_hash\": {irr_serial_hash}\n",
        "    }\n",
        "}"
    ])


print(f"{export_file} written")
