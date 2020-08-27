# This script is intended for use in intermediate doc repos generated from docs.ms CI.
# Given a reference ToC and a set of namespaces, limit the reference to ToC entries that contain
# namespaces in our set.

import argparse
import pdb
import os
import fnmatch
import re
import json

# by default, yaml does not maintain insertion order of the dicts
# given that this is intended to generate TABLE OF CONTENTS values,
# maintaining this order is important.
# The drop-in replacement oyaml is a handy solution for us.
import oyaml as yaml
import re
import pdb

## template
# for each file/member found in HOME.md
created_name = "{}" # name
created_uid = "azure.swift.sdk.landingPage.services.{}.{}" # service, member name
created_href = "~/docs-ref-services/swift-gen/{}/{}.md" # service, member name

root_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), ".."))
source_md = os.path.join(root_dir, "seed_reference.yml")
target_reference = os.path.join(root_dir, "docs-ref-mapping", "reference.yml")

type_parse = r"^# [^#]+?(?=#)"
header_row = r"^#.*"
header_row_pattern = re.compile(header_row)
id_extract = r"\[(.*)\]"

targeted_services = ["core","storage"]
categories = ["Operators","Protocols", "Types", "Global Typealiases"]

index_members = {}

# def get_indexed_members(target_home, target_index):
#     with open(target_home, "r", encoding="utf-8") as f:
#         content = f.read()

#     print(content)
#     matches = re.split(type_parse, content, flags = re.MULTILINE)

#     import pdb
#     pdb.set_trace()
#     print(matches)

def get_id_from_line(line):
    match = re.search(id_extract, line).groups()[0]
    return match

def get_formatted_name_items(service, target_dict):
    returned_dict_array = []

    member_names = target_dict.keys()

    for member_name in member_names:
        addition = { 
            "href": created_href.format(service, member_name),
            "name": member_name,
            "uid": created_uid.format(service, member_name)
        }
        returned_dict_array.append(addition)

    return returned_dict_array

# regex is going insane for some reason. ignoring the first 3. it's not an encoding issue but I'll go after this later
def get_indexed_members(target_home):
    with open(target_home, "r", encoding="utf-8") as f:
        content = f.readlines()

    parsed = {}
    active_member = ""
    active_category = ""

    for line in content:
        if line.startswith("# ") and not str.isspace(line):
            category = line.replace("# ","").rstrip()
            if category not in parsed:
                parsed[category] = {}
            active_category = category
        else:
            if line.lstrip().startswith("-"):
                member_id = get_id_from_line(line)
                active_member = member_id
                parsed[active_category][active_member] = line
            elif not str.isspace(line):
                parsed[active_category][active_member] += line

    return parsed

def get_service_from_master(service, target_dict):
    for item in target_dict:
        if item["name"].lower().strip() == service:
            return item

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
      Creates a reference.yml from swift-generated markdown documentation.
      """
    )


    # load seed YML
    try:
        with open(source_md, "r") as reference_yml:
            base_reference_toc = yaml.safe_load(reference_yml)
        # with open(target_md, "r") as target_autogenerated_toc_yml:
        #     target_autogenerated_toc = yaml.safe_load(target_autogenerated_toc_yml)
    except Exception as f:
        print(f)
        exit(1)

    toc = base_reference_toc[0]["items"]
    
    for target_service in targeted_services:
        target_home = os.path.join(root_dir, "docs-ref-services/swift-gen", target_service, "Home.md")
        indexed_members = get_indexed_members(target_home)
        service_toc = get_service_from_master(target_service, toc)

        if service_toc:
            for category in service_toc["items"]:
                category["items"] = get_formatted_name_items(target_service, indexed_members.get(category["name"], {}))

    updated_content = yaml.dump(base_reference_toc, default_flow_style=False)

    with open(target_reference, "w") as f:
        f.write(updated_content)