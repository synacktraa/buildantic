from __future__ import annotations

import typing as t
from urllib.parse import quote

from pydantic_core import to_json

if t.TYPE_CHECKING:
    from .types import EncodingMeta, PathEncodingStyle, QueryEncodingStyle

__all__ = ("encode_path_parameter", "encode_query_parameter", "format_path", "format_query")


to_str = lambda v: to_json(v).decode("utf-8") if isinstance(v, (list, dict)) else str(v)

"""
// PATH ENCODING
  [style]   [explode]   [primitive]	    [array]                       [object]
                         (id = 5)   (id = [3, 4, 5])  (id = {“role”: “admin”, “firstName”: “Alex”})
  simple      false          5           3,4,5                role,admin,firstName,Alex
  simple      true           5           3,4,5                role=admin,firstName=Alex
  label       false         .5          .3,4,5               .role,admin,firstName,Alex
  label       true          .5          .3.4.5               .role=admin.firstName=Alex
  matrix      false        ;id=5       ;id=3,4,5            ;id=role,admin,firstName,Alex
  matrix      true         ;id=5    ;id=3;id=4;id=5          ;role=admin;firstName=Alex
"""


def encode_path_parameter(  # noqa: C901
    name: str,
    value: t.Any,
    style: PathEncodingStyle | None = None,
    explode: bool | None = None,
) -> str:
    """
    Encode a path parameter according to the specified style and explode value.

    :param name: The name of the parameter
    :param value: The value of the parameter
    :param style: The encoding style (simple, label, or matrix)
    :param explode: Whether to explode the parameter
    :return: The encoded parameter string
    """
    style, explode = style or "simple", explode or False

    def encode_array(arr: list) -> str:
        if style == "simple":
            return ",".join(map(to_str, arr))
        elif style == "label":
            return ".".join(map(to_str, arr)) if explode else ",".join(map(to_str, arr))
        elif style == "matrix":
            return (
                ";".join(f"{name}={item}" for item in arr)
                if explode
                else f"{name}=" + ",".join(map(to_str, arr))
            )
        raise ValueError(f"Unsupported path encoding style: {style}")

    def encode_object(obj: dict) -> str:
        def _join(sep: str, kv_sep: str) -> str:
            return sep.join(f"{k}{kv_sep}{to_str(v)}" for k, v in obj.items())

        if style == "simple":
            return _join(",", "=") if explode else _join(",", ",")
        elif style == "label":
            return _join(".", "=") if explode else _join(",", ",")
        elif style == "matrix":
            return _join(";", "=") if explode else f"{name}=" + _join(",", ",")
        raise ValueError(f"Unsupported path encoding style: {style}")

    if isinstance(value, list):
        encoded = encode_array(value)
    elif isinstance(value, dict):
        encoded = encode_object(value)
    else:  # Primitive value
        encoded = to_str(value) if style != "matrix" else f"{name}={to_str(value)}"

    if style == "simple":
        return encoded
    elif style == "label":
        return "." + encoded
    elif style == "matrix":
        return ";" + encoded
    raise ValueError(f"Unsupported path encoding style: {style}")


"""
// QUERY ENCODING
  [style]     [explode]   [primitive]	    [array]                       [object]
                            (id = 5)   (id = [3, 4, 5])  (id = {“role”: “admin”, “firstName”: “Alex”})
   form	         true	      id=5	    id=3&id=4&id=5	           role=admin&firstName=Alex
   form	        false		  id=5	       id=3,4,5	              id=role,admin,firstName,Alex
spaceDelimited	 true	       n/a	    id=3&id=4&id=5	                     n/a
spaceDelimited	false	       n/a	     id=3%204%205	                     n/a
pipeDelimited	 true	       n/a	    id=3&id=4&id=5	                     n/a
pipeDelimited	false	       n/a	       id=3|4|5	                         n/a
 deepObject	     true	       n/a	          n/a	            id[role]=admin&id[firstName]=Alex
"""


def encode_query_parameter(  # noqa: C901
    name: str,
    value: t.Any,
    style: QueryEncodingStyle | None = None,
    explode: bool | None = None,
) -> str:
    """
    Encode a query parameter according to the specified style and explode value.

    :param name: The name of the parameter
    :param value: The value of the parameter
    :param style: The encoding style (form, spaceDelimited, pipeDelimited, or deepObject)
    :param explode: Whether to explode the parameter
    :return: The encoded parameter string
    :raises ValueError: If the combination of style, explode, and value type is not supported
    """
    style, explode = style or "form", True if explode is None else explode
    encode_value = lambda v: quote(str(v))

    if style == "form":
        if isinstance(value, list):
            if explode:
                return "&".join(f"{name}={encode_value(v)}" for v in value)
            else:
                return f"{name}={','.join(encode_value(v) for v in value)}"
        elif isinstance(value, dict):
            if explode:
                return "&".join(f"{k}={encode_value(v)}" for k, v in value.items())
            else:
                return f"{name}={','.join(f'{k},{encode_value(v)}' for k, v in value.items())}"
        else:
            return f"{name}={encode_value(value)}"

    elif style in ("spaceDelimited", "pipeDelimited"):
        if not isinstance(value, list):
            raise ValueError(f"{style} style only supports array values")
        if explode:
            return "&".join(f"{name}={encode_value(v)}" for v in value)
        else:
            delimiter = "%20" if style == "spaceDelimited" else "|"
            return f"{name}={delimiter.join(encode_value(v) for v in value)}"

    elif style == "deepObject":
        if not isinstance(value, dict) or not explode:
            raise ValueError("deepObject style only supports object values with explode=True")
        return "&".join(f"{name}[{encode_value(k)}]={encode_value(v)}" for k, v in value.items())

    else:
        raise ValueError(f"Unsupported query encoding style: {style}")


def format_path(
    path: str, params: dict, encodings: t.Dict[str, EncodingMeta[PathEncodingStyle]]
) -> str:
    """
    Format a path string with the given parameters and encodings.

    :param path: The path string with placeholders
    :param params: A dictionary of parameter names and values
    :param encodings: A dictionary of parameter names and their encoding information
    :return: The formatted path string
    """
    formatted_map = {}
    for name, value in params.items():
        style, explode = None, None
        if encoding := encodings.get(name):
            style, explode = encoding.style, encoding.explode
        formatted_map[name] = encode_path_parameter(name, value, style, explode)
    return path.format_map(formatted_map)


def format_query(params: dict, encodings: t.Dict[str, EncodingMeta[QueryEncodingStyle]]) -> str:
    """
    Format a query string with the given parameters and encodings.

    :param params: A dictionary of parameter names and values
    :param encodings: A dictionary of parameter names and their encoding information
    :return: The formatted query string
    """
    query_parts = []
    for name, value in params.items():
        style, explode = None, None
        if encoding := encodings.get(name):
            style, explode = encoding.style, encoding.explode
        query_parts.append(encode_query_parameter(name, value, style, explode))

    return "&".join(query_parts)
