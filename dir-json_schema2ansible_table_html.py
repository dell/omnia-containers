"""
Convert JSON Schema in dir to html ansible table format.

Usage:
    python dir-json_schema2ansible_table_html.py <input_dir> <output.html>

Example:
    python dir-json_schema2ansible_table_html.py ./schemas/*.json ./output/*.html
"""

import sys
import os
import json
import yaml
import re
from html import escape
from pprint import pprint

# ---------- JSON Schema type -> Ansible short type ----------
TYPE_MAP_JSON2ANSIBLE = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}

TYPE_MAP_ANSIBLE2DISPLAY = {
    "str": "string",
    "int": "integer",
    "float": "float",
    "bool": "boolean",
    "list": "list",
    "dict": "dict",
    "raw": "raw",
    "path": "path",
    "jsonarg": "json",
    "json": "json",
    "bytes": "bytes",
    "bits": "bits",
    "sid": "sid",
}

def map_json_type_to_ansible(json_type):
    """Map JSON Schema type to Ansible doc type."""
    print(json_type)
    if isinstance(json_type, list):
        # e.g. ["string", "null"] -> pick the non-null type
        types = [t for t in json_type if t != "null"]
        # return comma separated convertion of types
        return  ",".join([TYPE_MAP_JSON2ANSIBLE.get(t, t) for t in types]) if types else "raw"
    return TYPE_MAP_JSON2ANSIBLE.get(json_type, json_type) if json_type else None


def build_description(schema):
    """
    Build a description string from the schema,
    appending constraint info (enum, pattern, min/max, default, etc.).
    """
    parts = []

    desc = schema.get("description")
    if desc:
        parts.append(desc)

    # # Pattern constraint
    # pattern = schema.get("pattern")
    # if pattern:
    #     parts.append(f"Pattern: C({pattern})")

    # Min/max for integers/numbers
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if minimum is not None and maximum is not None:
        parts.append(f"Range: {minimum}-{maximum}.")
    elif minimum is not None:
        parts.append(f"Minimum: {minimum}.")
    elif maximum is not None:
        parts.append(f"Maximum: {maximum}.")

    # MinLength / MaxLength for strings
    min_len = schema.get("minLength")
    max_len = schema.get("maxLength")
    if min_len is not None and min_len > 0:
        parts.append(f"Minimum length: {min_len}.")

    # Default value
    default = schema.get("default")
    if default is not None:
        parts.append(f"Default: C({default}).")

    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return parts


def convert_property(name, schema, required_list=None):
    """
    Convert a single JSON Schema property to an Ansible doc option dict.
    """
    if schema is None:
        schema = {}

    option = {}

    # Description
    desc = build_description(schema)
    if desc:
        option["description"] = desc
    print(schema)
    json_type = schema.get("type")
    print("JSON Type:", json_type)
    ansible_type = map_json_type_to_ansible(json_type)

    # Choices from enum
    choices = schema.get("enum")
    if choices:
        option["choices"] = choices

    # Required
    if required_list and name in required_list:
        option["required"] = True

    # Handle array type
    if json_type == "array":
        option["type"] = "list"
        items = schema.get("items", {})
        items_type = items.get("type")
        if items_type:
            option["elements"] = map_json_type_to_ansible(items_type)

        # If items is an object with properties, convert to suboptions
        if items_type == "object" and items.get("properties"):
            sub_required = items.get("required", [])
            suboptions = {}
            for prop_name, prop_schema in items["properties"].items():
                suboptions[prop_name] = convert_property(
                    prop_name, prop_schema, sub_required
                )
            option["suboptions"] = suboptions

    # Handle object type
    elif json_type == "object":
        option["type"] = "dict"

        # Regular properties
        if schema.get("properties"):
            sub_required = schema.get("required", [])
            suboptions = {}
            for prop_name, prop_schema in schema["properties"].items():
                suboptions[prop_name] = convert_property(
                    prop_name, prop_schema, sub_required
                )
            option["suboptions"] = suboptions

        # patternProperties -> convert each pattern's schema as a suboption
        # with a descriptive name
        elif schema.get("patternProperties"):
            suboptions = {}
            for pattern, pat_schema in schema["patternProperties"].items():
                # Use the pattern as a key hint
                key_name = f"<{name}_key>"
                pat_option = convert_property(key_name, pat_schema)
                pat_desc = pat_option.get("description", "")
                if isinstance(pat_desc, list):
                    pat_desc.insert(0, f"Dynamic key matching pattern: C({pattern})")
                elif pat_desc:
                    pat_option["description"] = [
                        f"Dynamic key matching pattern: C({pattern})",
                        pat_desc,
                    ]
                else:
                    pat_option["description"] = (
                        f"Dynamic key matching pattern: C({pattern})"
                    )
                suboptions[key_name] = pat_option
            option["suboptions"] = suboptions

        # additionalProperties with schema
        elif schema.get("additionalProperties") and isinstance(
            schema["additionalProperties"], dict
        ):
            add_props = schema["additionalProperties"]
            # Handle oneOf
            if add_props.get("oneOf"):
                type_descs = []
                for variant in add_props["oneOf"]:
                    vtype = map_json_type_to_ansible(variant.get("type"))
                    vdesc = variant.get("description", "")
                    type_descs.append(f"{vtype} ({vdesc})" if vdesc else vtype)
                extra = f"Value can be: {' or '.join(type_descs)}."
                if isinstance(option.get("description"), list):
                    option["description"].append(extra)
                elif option.get("description"):
                    option["description"] = [option["description"], extra]
                else:
                    option["description"] = extra
            else:
                val_type = map_json_type_to_ansible(add_props.get("type"))
                if val_type:
                    extra = f"Values are of type {val_type}."
                    if isinstance(option.get("description"), list):
                        option["description"].append(extra)
                    elif option.get("description"):
                        option["description"] = [option["description"], extra]

    # Simple types
    elif ansible_type:
        option["type"] = ansible_type

    # If no type was set from enum-only fields
    if "type" not in option and choices:
        option["type"] = "str"

    return option


def convert_schema(schema):
    """Convert a full JSON Schema to Ansible YAML doc format."""
    result = {"options": {}}

    properties = schema.get("properties", {})
    required_list = schema.get("required", [])

    for prop_name, prop_schema in properties.items():
        result["options"][prop_name] = convert_property(
            prop_name, prop_schema, required_list
        )

    return result


def map_type(t):
    """Map Ansible short type names to display names."""
    return TYPE_MAP_ANSIBLE2DISPLAY.get(t, t) if t else t


# ---------- Ansible markup conversion ----------
def convert_markup(text):
    """Convert Ansible doc markup I(), C(), B(), U(), L(), R() to HTML."""
    if not text:
        return ""
    text = escape(text)
    # I(text) -> <em>text</em>
    text = re.sub(r"I\(([^)]*)\)", r"<em>\1</em>", text)
    # C(text) -> <code>
    text = re.sub(
        r"C\(([^)]*)\)",
        r'<code class="docutils literal notranslate"><span class="pre">\1</span></code>',
        text,
    )
    # B(text) -> <strong>
    text = re.sub(r"B\(([^)]*)\)", r"<strong>\1</strong>", text)
    # U(text) -> link
    text = re.sub(r"U\(([^)]*)\)", r'<a href="\1">\1</a>', text)
    return text


def description_to_paragraphs(desc):
    """Convert a description (string or list) into a list of HTML <p> strings."""
    if desc is None:
        return []
    if isinstance(desc, str):
        return [f"<p>{convert_markup(desc)}</p>"]
    if isinstance(desc, list):
        return [f"<p>{convert_markup(item)}</p>" for item in desc]
    return [f"<p>{escape(str(desc))}</p>"]


# ---------- flatten options tree ----------
def flatten_options(options, parent_path="", depth=0):
    """
    Depth-first flattening of the options tree, preserving the
    original insertion order from the JSON schema.
    Returns a list of (name, option_dict, path, depth) tuples.
    """
    if not options:
        return []

    # Separate options with suboptions from leaf options
    with_sub = []
    without_sub = []
    for name in sorted(options.keys()):
        opt = options[name]
        if opt and opt.get("suboptions"):
            with_sub.append((name, opt))
        else:
            without_sub.append((name, opt))

    # Options with suboptions first, then leaf options
    sorted_items = with_sub + without_sub

    rows = []
    for name, opt in sorted_items:
        path = f"{parent_path}/{name}" if parent_path else name
        rows.append((name, opt or {}, path, depth))
        if opt and opt.get("suboptions"):
            rows.extend(flatten_options(opt["suboptions"], path, depth + 1))
    return rows


# ---------- generate a single table row ----------
def generate_row(name, opt, path, depth, row_index):
    """Generate one <tr> element for a parameter."""
    row_class = "row-even" if row_index % 2 == 0 else "row-odd"
    indent = depth
    ind = "                    "  # base indentation (20 spaces)

    # --- First <td>: parameter name + type info ---
    indents_html = ""
    for _ in range(indent):
        indents_html += f'{ind}    <div class="omnia-indent"></div>\n'

    # Anchor and IDs
    anchor_id = f"parameter-{path}"
    title_id = "module-parameter-" + path.replace("/", "-").replace("_", "-")

    # Type line
    type_str = map_type(opt.get("type", ""))
    elements_str = map_type(opt.get("elements", ""))
    required = opt.get("required", False)

    type_line_parts = []
    if type_str:
        type_line_parts.append(f'<span class="omnia-type">{type_str}</span>')
    if elements_str:
        type_line_parts.append(
            f' / <span class="omnia-elements">elements={elements_str}</span>'
        )
    if required:
        type_line_parts.append(
            f' / <span class="omnia-required">required</span>'
        )

    type_line = "".join(type_line_parts)

    # Build first <td>
    td1_lines = []
    td1_lines.append(f'{ind}<td>')
    if indents_html:
        td1_lines.append(indents_html.rstrip("\n"))
    td1_lines.append(f'{ind}    <div class="omnia-cell">')
    td1_lines.append(
        f'{ind}        <div class="ansibleOptionAnchor" id="{anchor_id}"></div>'
    )
    td1_lines.append(
        f'{ind}        <p class="omnia-title" id="{title_id}">'
    )
    td1_lines.append(f"{ind}            <strong>{escape(name)}</strong>")
    td1_lines.append(f"{ind}        </p>")
    if type_line:
        td1_lines.append(
            f'{ind}        <p class="omnia-type-line">{type_line}</p>'
        )
    td1_lines.append(f"{ind}    </div>")
    td1_lines.append(f"{ind}</td>")

    # --- Second <td>: description ---
    desc_indents = ""
    for _ in range(indent):
        desc_indents += f'{ind}    <div class="omnia-indent-desc"></div>\n'

    paragraphs = description_to_paragraphs(opt.get("description"))

    td2_lines = []
    td2_lines.append(f"{ind}<td>")
    if desc_indents:
        td2_lines.append(desc_indents.rstrip("\n"))
    td2_lines.append(f'{ind}    <div class="omnia-cell">')
    for p in paragraphs:
        td2_lines.append(f"{ind}        {p}")
    td2_lines.append(f"{ind}    </div>")
    td2_lines.append(f"{ind}</td>")

    # Assemble <tr>
    tr = f'{ind[:-4]}<tr class="{row_class}">\n'
    tr += "\n".join(td1_lines) + "\n"
    tr += "\n".join(td2_lines) + "\n"
    tr += f"{ind[:-4]}</tr>"
    return tr


# ---------- CSS template ----------
CSS_TEMPLATE = """\
    <style type="text/css">
        :root {
            --table-background-header: #6ab0de;
            --table-background-even: #fff;
            --table-background-odd: #fff;
            --table-border: #000;
            --narrowtable-background: #e7f2fa;
            --option-type: purple;
            --option-elements: purple;
            --option-required: red;
            --option-default: blue;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 40px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
        }

        table.omnia-table {
            border-color: var(--table-border) !important;
            display: table;
            height: 1px;
            width: 100%;
            border-collapse: collapse;
        }

        table.omnia-table tr {
            height: 100%
        }

        table.omnia-table td,
        table.omnia-table th {
            border-color: var(--table-border) !important;
            border-bottom: none !important;
            vertical-align: top !important
        }

        table.omnia-table th>p {
            font-size: medium !important;
            margin: 0;
        }

        table.omnia-table thead tr {
            background-color: var(--table-background-header)
        }

        table.omnia-table tbody .row-odd td {
            background-color: var(--table-background-odd) !important
        }

        table.omnia-table tbody .row-even td {
            background-color: var(--table-background-even) !important
        }

        table.omnia-table ul>li>p {
            margin: 0 !important
        }

        table.omnia-table ul>li>div[class^=highlight] {
            margin-bottom: 4px !important
        }

        table.omnia-table p.omnia-title {
            display: inline;
            font-weight: bold;
        }

        table.omnia-table .omnia-type-line {
            font-size: small;
            margin-bottom: 0;
            margin-top: 4px;
        }

        table.omnia-table .omnia-type {
            color: var(--option-type)
        }

        table.omnia-table .omnia-elements {
            color: var(--option-elements)
        }

        table.omnia-table .omnia-required {
            color: var(--option-required)
        }

        table.omnia-table .omnia-line {
            margin-top: 8px
        }

        table.omnia-table .omnia-default,
        table.omnia-table .omnia-default-bold {
            color: var(--option-default)
        }

        table.omnia-table p {
            margin: 0 0 8px
        }

        table.omnia-table td {
            padding: 0 !important;
            white-space: normal
        }

        table.omnia-table td>div.omnia-cell {
            border-top: 1px solid var(--table-border);
            padding: 8px 8px
        }

        table.omnia-table td:first-child {
            display: flex;
            height: inherit;
            flex-direction: row
        }

        table.omnia-table td:first-child>div.omnia-cell {
            height: inherit;
            flex: 1 0 auto;
            max-width: 100%;
            white-space: nowrap
        }

        table.omnia-table .omnia-indent {
            border-right: 1px solid var(--table-border);
            margin-left: 2em
        }

        .simple {
            list-style: none;
            padding-left: 0;
        }

        .simple li {
            margin: 4px 0;
        }

        code {
            background-color: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        em {
            font-style: italic;
        }

        strong {
            font-weight: bold;
        }

        .docutils.literal {
            background-color: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
        }

        .omnia-indent-desc {
            display: block;
        }

        @media (max-width:1200px) {
            table.omnia-table {
                border: none !important;
                display: block;
                height: unset
            }

            table.omnia-table thead {
                display: none
            }

            table.omnia-table tbody,
            table.omnia-table td,
            table.omnia-table tr {
                border: none !important;
                display: block
            }

            table.omnia-table tbody .row-even td,
            table.omnia-table tbody .row-odd td {
                background-color: unset !important
            }

            table.omnia-table td>div.omnia-cell {
                border-top: none
            }

            table.omnia-table td:first-child>div.omnia-cell {
                background-color: var(--narrowtable-background) !important
            }

            table.omnia-table td:not(:first-child) {
                display: flex;
                flex-direction: row
            }

            table.omnia-table td:not(:first-child)>div.omnia-cell {
                margin-left: 1em
            }

            table.omnia-table .omnia-indent,
            table.omnia-table .omnia-indent-desc {
                border: none;
                margin-left: 1em
            }

        }
    </style>"""


# ---------- main ----------
def convert(yaml_data, html_path):
    options = yaml_data.get("options", {})
    rows = flatten_options(options)

    # Generate table rows
    row_html_parts = []
    for i, (name, opt, path, depth) in enumerate(rows):
        row_html_parts.append(generate_row(name, opt, path, depth, i))

    rows_html = "\n".join(row_html_parts)

    # Assemble full HTML
    html = f"""
<table class="longtable omnia-table docutils align-default" style="width: 100%">
    <thead>
        <tr class="row-odd">
            <th class="head">
                <p>Parameter</p>
            </th>
            <th class="head">
                <p>Details</p>
            </th>
        </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
</table>
"""
    # print(html)

    if(html_path):
      with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
      print(f"Converted to {html_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input_dir> <output_dir>")
        sys.exit(1)

    output_path = None
    input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = input_path + "/" + "html"
        os.makedirs(output_path, exist_ok=True)

    # read all jsons from input_path
    json_files = [f for f in os.listdir(input_path) if f.endswith(".json")]
    for jsx in json_files:
        input_json = os.path.join(input_path, jsx)
        try:
            with open(input_json, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except FileNotFoundError as fnf_err:
            print(f"Error: Input file not found: {input_json}")
            print(f"Details: {fnf_err}")
            sys.exit(1)
        except json.JSONDecodeError as js_err:
            print(f"Error: Invalid JSON in input file: {input_json}")
            print(f"Details: {js_err}")
            sys.exit(1)

        result = convert_schema(schema)
        output_html = os.path.join(output_path, jsx.replace(".json", ".html"))
        convert(result, output_html)
