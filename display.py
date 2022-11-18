import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

ids = {
    "Adelie Penguin (Pygoscelis adeliae)": "NCBITaxon:9238",
    "has characteristic": "RO:0000053",
    "mass": "PATO:0000125",
    "has value": ":hasValue",
    "has quantity": ":hasQuantity",
    "has unit": ":hasUnit",
    "g": "unit:g",
    "type": "a",
}
shorten = {
    "Adelie Penguin (Pygoscelis adeliae)": "Adelie Penguin",
}

data_properties = [
    "has quantity",
    "has unit"
]

yaml_example = """
subject: N1A1
type: Adelie Penguin (Pygoscelis adeliae)
has characteristic:
  - type: mass
    has value:
      - type: mass
        has quantity: 3750
        has unit: g
"""


def id_label(input):
    if input == "type":
        return ["a", None]
    elif input in ids:
        curie = ids[input]
        if curie.startswith(":"):
            return [curie, None]
        elif curie.startswith("unit:"):
            return [curie, None]
        return [curie, input]
    else:
        return [":" + input, None]


def turtle(input, depth=0, last=True):
    lines = []
    indent = " " * depth * 2
    if "subject" in input:
        subject = input["subject"]
        if subject in ids:
            label = subject
            curie = ids[subject]
            line = f"{curie} # '{label}'"
            lines.append(indent + line)
        else:
            lines.append(":" + subject)
    for key, value in input.items():
        kid = None
        vid = None
        if key == "subject":
            continue
        if isinstance(value, list):
            kid, label = id_label(key)
            line = f"  {kid} ["
            if label:
                line += f" # '{label}'"
            lines.append(indent + line)
            for item in value:
                lines += turtle(item, depth+1)
            lines.append(indent + "  ] ;")
        else:
            labels = []
            kid, label = id_label(key)
            if label:
                labels.append(label)
            if isinstance(value, str):
                vid, label = id_label(value)
                if label:
                    labels.append(label)
            elif isinstance(value, int):
                vid = f'"{value}"^^xsd:integer'
            elif isinstance(value, float):
                vid = f'"{value}"^^xsd:float'
            line = f"  {kid} {vid} ;"
            if labels:
                line += " # '"
                line += "', '".join(labels)
                line += "'"
            lines.append(indent + line)
    if last:
        if depth == 0:
            lines[-1] = lines[-1].replace(";", ".")
        else:
            lines[-1] = lines[-1].replace(" ;", "")
    return lines


SUBJECTS = 0


def flatten(input):
    global SUBJECTS
    triples = []
    subject = None
    if "subject" in input:
        subject = input["subject"]
    else:
        subject = f"_{SUBJECTS}"
        SUBJECTS += 1
    for key, value in input.items():
        if key == "subject":
            continue
        if isinstance(value, str):
            triples.append([subject, key, value])
        elif isinstance(value, int):
            object = f'"{value}"^^xsd:integer'
            triples.append([subject, key, object])
        elif isinstance(value, float):
            object = f'"{value}"^^xsd:float'
            triples.append([subject, key, object])
        elif isinstance(value, list):
            object = f"_{SUBJECTS}"
            triples.append([subject, key, object])
            for item in value:
                triples += flatten(item)
    return triples


def dot(input):
    # classes = []
    # instances = []
    # edges = []
    triples = flatten(input)
    lines = [
        """digraph G {""",
        """  graph [rankdir="BT"]""",
        """  node [shape="rect"]""",
        """  subgraph classes {""",
        """    rank="same" ;""",
    ]
    classes = []
    instances = []
    literals = []
    for triple in triples:
        s, p, o = triple
        if s not in instances:
            instances.append(s)
        if p == "type":
            if o not in classes:
                classes.append(o)
        elif p in data_properties:
            if o not in literals:
                literals.append(o)
    for c in classes:
        if c in shorten:
            line = f'    "{c}" [label="{shorten[c]}"] ;'
        else:
            line = f'    "{c}" ;'
        lines.append(line)
    lines += [
        "  }",
        """  subgraph instances {""",
        """    rank="same" ;""",
        """    node [style="dashed"] ;""",
    ]
    for i in instances:
        if i.startswith("_"):
            line = f'    "{i}" [label=""] ;'
        else:
            line = f'    "{i}" ;'
        lines.append(line)
    lines += [
        "  }",
        """  subgraph literals {""",
        """    rank="same" ;""",
        """    node [shape="plaintext"] ;""",
    ]
    for l in literals:
        if l in ids:
            line = f'    "{l}" [label="{ids[l]}"] ;'
        else:
            label = l.replace('"', '\\"')
            line = f'    "{label}" ;'
        lines.append(line)
    lines.append("  }")
    for triple in triples:
        s, p, o = triple
        o = o.replace('"', '\\"')
        if p == "type":
            line = f'  "{s}" -> "{o}" [style="dashed"];'
        elif p in data_properties:
            line = f'  "{o}" -> "{s}" [label="{p}", dir="back", style="dotted"];'
        else:
            line = f'  "{s}" -> "{o}" [label="{p}"] ;'
        lines.append(line)
    lines.append("}")
    return lines


def display(input):
    data = yaml.load(input, Loader=Loader)
    lines = [
        "::: {.panel-tabset}",
        "### Diagram",
        "```{dot}",
    ]
    lines += dot(data)
    lines += [
        "```",
        "",
        "### YAML",
        "```yaml",
        input.strip(),
        "```",
        "",
        "### Turtle",
        "```turtle",
    ]
    lines += turtle(data)
    lines += [
        "```",
        ":::",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    example = yaml.load(yaml_example, Loader=Loader)
    lines = dot(example)
    print("\n".join(lines))
    # display(yaml_example)
