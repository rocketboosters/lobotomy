import copy
import typing
import datetime


def parse_definition_item(shapes: dict, value: dict) -> dict:
    """
    Unwraps the value object by placing its shape data within a copy of
    the object itself and returning that copied object. This works
    recursively to unwrap results hierarchically.

    :param shapes:
        Shape definitions from the service spec in which this value
        definition resides.
    :param value:
        A definition object value to unwrap shape data within, or potentially
        a value object that has no shape and is already a leaf definition
        value as this function is called recursively.
    :return:
        An unwrapped, deep-copied version of the value dictionary where
        the shape(s) have been injected into the object hierarchically to
        remove the need for shape lookups to understand the properties,
        including types, of the value and potentially its member(s) if
        represents a list or dictionary.
    """
    output = copy.deepcopy(value)

    if value.get("type") == "map":
        # Maps are terminal but have key and value shapes.
        output["key"] = parse_definition_item(shapes, value["key"])
        output["value"] = parse_definition_item(shapes, value["value"])

    if "member" in output:
        # Types like lists have a member definition for the items in the
        # list. That needs to be parsed and then the shape is complete.
        output["member"] = parse_definition_item(shapes, output["member"])

    if "members" in output:
        output["members"] = {
            k: parse_definition_item(shapes, v)
            for k, v in (output["members"] or {}).items()
        }

    if "shape" in output:
        shape = copy.deepcopy(shapes[output["shape"]])
        output.update(parse_definition_item(shapes, shape))

    return output


def flat_cast(output: dict) -> typing.Any:
    """
    Creates a flat version of the output with default values for inclusion
    as a skeleton in a configuration response file.
    """
    o = output
    data_type = o.get("type", "structure")
    type_casts = {
        "blob": lambda: "...",
        "string": lambda: "...",
        "integer": lambda: 1,
        "long": lambda: 1,
        "float": lambda: 1.0,
        "timestamp": lambda: f'{datetime.datetime.utcnow().isoformat("T")}Z',
        "list": lambda: [flat_cast(o["member"])],
        "structure": lambda: {k: flat_cast(v) for k, v in o["members"].items()},
    }
    caster = type_casts.get(data_type, lambda: None)
    return caster()
