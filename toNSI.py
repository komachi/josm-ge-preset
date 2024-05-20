import xml.etree.ElementTree as ET
import sys
import fileinput
import os
import json
import warnings

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

def generate_tag_type_map(nsiTree):
    m = {}
    for type in nsiTree:
        for key in nsiTree[type]:
            for value in nsiTree[type][key]:
                if not (key, value) in m:
                    m[(key, value)] = type
                else:
                    m[(key, value)] = "both"
    return m

def handle_group(nsiTree, group, parent_fallback_type=None, tag_type_cache=None):
    if tag_type_cache == None: tag_type_cache = generate_tag_type_map(nsiTree)

    # Type to fall back to if other detection algorithms fail
    this_fallback_type = parent_fallback_type
    if group.attrib["name"] in type_by_group:
        this_fallback_type = type_by_group[group.attrib["name"]]

    for item in group.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}item'):
        tags = {}
        for key in item.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}key'):
            tags[key.attrib["key"]] = key.attrib["value"]

        keys = list(item.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}key'))
        
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
            print("No matching tags in NSI tree: %s, skipping" % tags)
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
            print("%s is decided to be in the %s type, but lacks the tag, skipping" % (tags, type))
            continue

        if nsiTree[type][kv[0]][kv[1]]["properties"].get("skipCollection"):
            continue

        written = False
        displayName = item.attrib["name"]
        # Check if we already have this in the file, update tags if found
        for item_ in nsiTree[type][kv[0]][kv[1]]["items"]:
            # Ewwwww
            if (("locationSet" in item_ and item_["locationSet"] == {"include": "ge"})
                    and (("displayName" in item_ and item_["displayName"] == item.attrib["name"])
                        or (type == "brands" and "tags" in item_ and "brand" in item_["tags"] and item_["tags"]["brand"] == tags["brand"])
                        or (type == "operators" and "tags" in item_ and "operator" in item_["tags"] and item_["tags"]["operator"] == tags["operator"])
                        or (type == "brands" and "brand:wikidata" in tags and "tags" in item_ and "brand:wikidata" in item_["tags"] and item_["tags"]["brand:wikidata"] == tags["brand:wikidata"])
                        or (type == "operators" and "operator:wikidata" in tags and "tags" in item_ and "operator:wikidata" in item_["tags"] and item_["tags"]["operator:wikidata"] == tags["operator:wikidata"]))):
                item_["tags"] = tags
                written = True
                break
            elif "displayName" in item_ and item_["displayName"] == item.attrib["name"]:
                displayName = displayName + " (Georgia)"

        # Otherwise, append
        if not written:
            nsiTree[type][kv[0]][kv[1]]["items"].append({ "displayName": item.attrib["name"], "tags": tags } | commonEntryKeys)

    
    for subgroup in group.findall('{http://josm.openstreetmap.de/tagging-preset-1.0}group'):
        handle_group(nsiTree, subgroup, this_fallback_type, tag_type_cache)

def __main__():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise RuntimeError(f"Incorrect number of arguments\n{sys.argv[0]} <name-suggestion-index path> [preset xml path]")

    nsiPath = sys.argv[1]
    inputFile = sys.stdin
    if len(sys.argv) > 2:
        inputFile = open(sys.argv[2])

    nsiData = nsiPath + "/data"
    nsiTree = read_dir_tree(nsiData)

    xml = ET.parse(inputFile)
    root = xml.getroot()

    handle_group(nsiTree, root.find('{http://josm.openstreetmap.de/tagging-preset-1.0}group'))

    write_dir_tree(nsiData, nsiTree)

    print("Don't forget to `npm run build` in the `name-suggestion-index`!")

__main__()
