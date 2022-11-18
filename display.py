import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def id_label(context, input):
    if input == "type":
        return ["a", None]
    elif input in context["ids"]:
        curie = context["ids"][input]
        if curie.startswith(":"):
            return [curie, None]
        elif curie.startswith("unit:"):
            return [curie, None]
        return [curie, input]
    else:
        return [":" + input, None]


def turtle(context, input, depth=0, last=True):
    if not isinstance(input, dict):
        raise Exception(f"Not a dict: {input}")
    lines = []
    indent = " " * depth * 2
    if "subject" in input:
        subject = input["subject"]
        if subject in context["ids"]:
            label = subject
            curie = context["ids"][subject]
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
            kid, label = id_label(context, key)
            line = f"  {kid} ["
            if label:
                line += f" # '{label}'"
            lines.append(indent + line)
            for item in value:
                lines += turtle(context, item, depth+1)
            lines.append(indent + "  ] ;")
        else:
            labels = []
            kid, label = id_label(context, key)
            if label:
                labels.append(label)
            if isinstance(value, str):
                vid, label = id_label(context, value)
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


def dot(context, input):
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
        elif p in context["data properties"]:
            if o not in literals:
                literals.append(o)
    for c in classes:
        if c in context["short"]:
            line = f'    "{c}" [label="{context["short"][c]}"] ;'
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
        if l in context["ids"]:
            line = f'    "{l}" [label="{context["ids"][l]}"] ;'
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
        elif p in context["data properties"]:
            line = f'  "{o}" -> "{s}" [label="{p}", dir="back", style="dotted"];'
        else:
            line = f'  "{s}" -> "{o}" [label="{p}"] ;'
        lines.append(line)
    lines.append("}")
    return lines


def load_context(context_yaml):
    context = yaml.load(context_yaml, Loader=Loader)
    ids = {}
    for key in ["classes", "object properties", "data properties"]:
        ids.update(context[key])
    context["ids"] = ids
    return context


def display(context_yaml, input_yaml):
    context = load_context(context_yaml)
    data = yaml.load(input_yaml, Loader=Loader)
    lines = [
        "::: {.panel-tabset}",
        "### Diagram",
        "```{dot}",
    ]
    lines += dot(context, data)
    lines += [
        "```",
        "",
        "### YAML",
        "```yaml",
        input_yaml.strip(),
        "```",
        "",
        "### Turtle",
        "```turtle",
    ]
    lines += turtle(context, data)
    lines += [
        "```",
        ":::",
    ]
    # print(context["ids"])
    print("\n".join(lines))


example_context = """
classes:
  Adelie Penguin (Pygoscelis adeliae): "NCBITaxon:9238"
  g: "unit:g"
  mass: "PATO:0000125"
object properties:
  has characteristic: "RO:0000053"
  has unit: ":hasUnit"
  has value: ":hasValue"
data properties:
  has quantity: ":hasQuantity"
short:
  Adelie Penguin (Pygoscelis adeliae): Adelie Penguin
"""

example_input = """
subject: N1A1
type: Adelie Penguin (Pygoscelis adeliae)
has characteristic:
  - type: mass
    has value:
      - type: mass
        has quantity: 3750
        has unit: g
"""


if __name__ == "__main__":
    # example = yaml.load(example_input, Loader=Loader)
    # lines = dot(example_context, example)
    # print("\n".join(lines))
    display(example_context, example_input)
