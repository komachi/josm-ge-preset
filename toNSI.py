import xml.etree.ElementTree as ET
import sys
import fileinput
import os
import json
# import re

commonEntryKeys = { "locationSet": {"include": ["ge"]} }

# Roughly translated from https://github.com/osmlab/name-suggestion-index/wiki/Contributing
groups_by_type = {
    "brands": ["Pharmacies", "Entertainment", "Cafes and Restaraunts", "Shops", "Finance", "Fuel stations", "Communication", "Insurance companies"],
    "operators": ["Healthcare", "Government services", "Post", "Urban units"]
}


type_by_group = {}

for type in groups_by_type:
    for group in groups_by_type[type]:
        type_by_group[group] = type

def read_dir_tree(path):
    tree = {}
    for subdir in os.listdir(path):
        tree[subdir] = {}
        for subsubdir in os.listdir(os.path.join(path, subdir)):
            if subsubdir == ".gitkeep": continue
            tree[subdir][subsubdir] = {}
            for file in os.listdir(os.path.join(path, subdir, subsubdir)):
                tree[subdir][subsubdir][file.replace(".json", "")] = json.load(open(os.path.join(path, subdir, subsubdir, file)))
    return tree

def write_dir_tree(path, tree):
    for subdir in tree:
        for subsubdir in tree[subdir]:
            for file in tree[subdir][subsubdir]:
                json.dump(tree[subdir][subsubdir][file], open(os.path.join(path, subdir, subsubdir, file + ".json"), "w"), ensure_ascii=False)

def generate_tag_type_map(nsi_tree):
    m = {}
    for type in nsi_tree:
        for key in nsi_tree[type]:
            for value in nsi_tree[type][key]:
                if not (key, value) in m:
                    m[(key, value)] = type
                else:
                    m[(key, value)] = "both"
    return m

# def contains_georgian(text):
#     # Define the regular expression pattern for Georgian script
#     georgian_pattern = re.compile(r'[\u10A0-\u10FF\u2D00-\u2D2F0-9."" -]+')
    
#     # Search for the pattern in the input text
#     return georgian_pattern.match(text)

def good(text):
    sys.stderr.write("\033[0;32m%s\033[0m\n" % text)
def goodnote(text):
    sys.stderr.write("\033[1;32m%s\033[0m\n" % text)
def bad(text):
    sys.stderr.write("\033[1;33m%s\033[0m\n" % text)

def handle_group(nsi_tree, group, parent_fallback_type=None, tag_type_cache=None):
    if tag_type_cache == None: tag_type_cache = generate_tag_type_map(nsi_tree)

    # Type to fall back to if other detection algorithms fail
    this_fallback_type = parent_fallback_type
    if group.attrib["name"] in type_by_group:
        this_fallback_type = type_by_group[group.attrib["name"]]

    for item in group.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}item'):        
        displayName = item.attrib["ka.name"] if "ka.name" in item.attrib else item.attrib["name"]
        tags = {}
        for key in item.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}key'):
            tags[key.attrib["key"]] = key.attrib["value"]

        keys = list(item.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}key'))

        # ==== Used for xml fixup ====
        # This is really really bad, but I'm lazy and it works-ish
        # for key in keys:

        #     some_kartuli_name = None
        #     if contains_georgian(tags.get("name:ka", "")):
        #         some_kartuli_name = tags["name:ka"]
        #     if contains_georgian(tags.get("brand:ka", "")):
        #         some_kartuli_name = tags["brand:ka"]
        #     if contains_georgian(tags.get("operator:ka", "")):
        #         some_kartuli_name = tags["operator:ka"]

        #     if some_kartuli_name is not None:
        #         if key.attrib["key"] == "name" and not contains_georgian(key.attrib["value"]):
        #             if "name:ka" in tags and contains_georgian(tags["name:ka"]):
        #                 tags["name"] = tags["name:ka"]
        #                 key.attrib["value"] = tags["name:ka"]
        #             else:
        #                 tags["name"] = some_kartuli_name
        #                 key.attrib["value"] = some_kartuli_name
        #         if key.attrib["key"] == "brand" and not contains_georgian(key.attrib["value"]):
        #             if "brand:ka" in tags and contains_georgian(tags["brand:ka"]):
        #                 tags["brand"] = tags["brand:ka"]
        #                 key.attrib["value"] = tags["brand:ka"]
        #             else:
        #                 tags["brand"] = some_kartuli_name
        #                 key.attrib["value"] = some_kartuli_name
        #         if key.attrib["key"] == "operator" and not contains_georgian(key.attrib["value"]):
        #             if "operator:ka" in tags and contains_georgian(tags["operator:ka"]):
        #                 tags["operator"] = tags["operator:ka"]
        #                 key.attrib["value"] = tags["operator:ka"]
        #             else:
        #                 tags["operator"] = some_kartuli_name
        #                 key.attrib["value"] = some_kartuli_name

        #     if key.attrib["key"] == "name:ka" and not contains_georgian(key.attrib["value"]) and "name" in tags and contains_georgian(tags["name"]):
        #         tags["name:ka"] = tags["name"]
        #         key.attrib["value"] = tags["name"]
        #     if key.attrib["key"] == "brand:ka" and not contains_georgian(key.attrib["value"]) and "brand" in tags and contains_georgian(tags["brand"]):
        #         tags["brand:ka"] = tags["brand"]
        #         key.attrib["value"] = tags["brand"]
        #     if key.attrib["key"] == "operator:ka" and not contains_georgian(key.attrib["value"]) and "operator" in tags and contains_georgian(tags["operator"]):
        #         tags["operator:ka"] = tags["operator"]
        #         key.attrib["value"] = tags["operator"]
        # for i in range(0, len(keys)):
        #     key = keys[i]
        #     # Hack: add in missing name:ka, brand:ka, operator:ka
        #     if keys[i].attrib["key"] == "name" and not "name:ka" in tags:
        #         tags["name:ka"] = tags["name"]
        #         item.insert(i + 1, ET.Element("{http://josm.openstreetmap.de/tagging-preset-1.0}key", {"key": "name:ka", "value": tags["name"]}))
        #     if keys[i].attrib["key"] == "brand" and not "brand:ka" in tags:
        #         tags["brand:ka"] = tags["brand"]
        #         item.insert(i + 1, ET.Element("{http://josm.openstreetmap.de/tagging-preset-1.0}key", {"key": "brand:ka", "value": tags["brand"]}))
        #     if keys[i].attrib["key"] == "operator" and not "operator:ka" in tags:
        #         tags["operator:ka"] = tags["operator"]
        #         item.insert(i + 1, ET.Element("{http://josm.openstreetmap.de/tagging-preset-1.0}key", {"key": "operator:ka", "value": tags["operator"]}))
        # ============================
        
        # Identify the relevant file ({type}/{key}/{value}.json) to append this to
        type = None # "brands" or "operators"
        kv = None   # (key, value)

        # If there's a matching tag uniquely positioned in an NSI tree, pick that file
        for key in tags:
            value = tags[key]
            if (key, value) in tag_type_cache:
                kv = (key, value)
                if not tag_type_cache[(key, value)] == "both":
                    type = tag_type_cache[(key, value)]

        if kv is None:
            bad("No matching tags in NSI tree for %s, skipping" % displayName)
            continue

        # If there's only one of "operator"/"brand", then choose the corresponding tree
        if type is None:
            if "operator" in tags and "brand" not in tags:
                type = "operators"
            elif "brand" in tags and "operator" not in tags:
                type = "brands"

        # Otherwise, fall back
        if type is None:
            type = this_fallback_type

        # Actually, here it'd only be possible if neither operator nor brand tag exists, but it's kinda clearer this way and makes this easier to add more types in the future
        if (type == "operators" and "operator" not in tags) or (type == "brands" and "brand" not in tags):
            bad("%s is decided to be in the %s type, but lacks the tag, skipping" % (displayName, type))
            continue

        if nsi_tree[type][kv[0]][kv[1]]["properties"].get("skipCollection"):
            continue

        written = False
        # Check if we already have this in the file, update tags if found
        for item_ in nsi_tree[type][kv[0]][kv[1]]["items"]:
            # Ewwwww
            if (("locationSet" in item_ and "include" in item_["locationSet"] and item_["locationSet"]["include"] == ["ge"])
                    and (("displayName" in item_ and item_["displayName"] == displayName)
                        or (type == "brands" and "tags" in item_ and "brand" in item_["tags"] and item_["tags"]["brand"] == tags["brand"])
                        or (type == "operators" and "tags" in item_ and "operator" in item_["tags"] and item_["tags"]["operator"] == tags["operator"])
                        or (type == "brands" and "brand:wikidata" in tags and "tags" in item_ and "brand:wikidata" in item_["tags"] and item_["tags"]["brand:wikidata"] == tags["brand:wikidata"])
                        or (type == "operators" and "operator:wikidata" in tags and "tags" in item_ and "operator:wikidata" in item_["tags"] and item_["tags"]["operator:wikidata"] == tags["operator:wikidata"]))):
                item_["tags"] = tags
                written = True
                goodnote("Replaced %s" % displayName)
                break
            elif "displayName" in item_ and item_["displayName"] == displayName:
                displayName = displayName + " (Georgia)"

        # Otherwise, append
        if not written:
            good("Appended %s" % displayName)
            nsi_tree[type][kv[0]][kv[1]]["items"].append({ "displayName": displayName, "tags": tags } | commonEntryKeys)

    
    for subgroup in group.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}group'):
        handle_group(nsi_tree, subgroup, this_fallback_type, tag_type_cache)

def __main__():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise RuntimeError(f"Incorrect number of arguments\n{sys.argv[0]} <name-suggestion-index path> [preset xml path]")

    nsi_path = sys.argv[1]
    input_file = sys.stdin
    fixup = os.environ.get("FIXUP_XML_FILE", None)
    if len(sys.argv) > 2:
        input_file = open(sys.argv[2], "rw" if fixup else "r")

    nsi_data = nsi_path + "/data"
    nsi_tree = read_dir_tree(nsi_data)

    xml = ET.parse(input_file)
    root = xml.getroot()

    handle_group(nsi_tree, root.find('{http://josm.openstreetmap.de/tagging-preset-1.0}group'))

    write_dir_tree(nsi_data, nsi_tree)

    if fixup: xml.write(fixup, encoding="utf-8")

    sys.stderr.write("\n")
    goodnote("Done! Don't forget to `npm run build` in the `name-suggestion-index`!")

__main__()
