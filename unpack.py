"""Automatic JSON unpacking to [`Polars`](https://pola.rs) `DataFrame`.

The use case is as follows:

* Provide a schema written in plain text describing the JSON content, to be converted
  into a `Polars` `Struct` (see samples in this repo for examples).
* Read the JSON content (as plain text using `scan_csv()` for instance, or directly as
  JSON via `scan_ndjson()`) and automagically unpack the nested content by processing
  the schema.

A few extra points:

* The schema should be dominant and we should rename fields as they are being unpacked
  to avoid identical names for different columns (which is forbidden by `Polars` for
  obvious reasons).
* _Why not using the inferred schema?_ Because at times we need to provide fields that
  might _not_ be in the JSON file to fit a certain data structure, or simply ignore
  part of the JSON data when unpacking to avoid wasting resources. Oh, and to rename
  fields too.

The current ~~working~~ state of this little DIY can be checked (in `Docker`) via:

```shell
$ make env
> python unpack.py samples/complex.schema samples/complex.ndjson
```

Note that a call of the same script _without_ providing a schema returns a
representation of the latter as _inferred_ by `Polars` (works as an example of the
syntax used to describe things in plain text):

```shell
$ make env
> python unpack.py samples/complex.ndjson
```

A thorough(-ish) battery of tests can be performed (in `Docker`) via:

```shell
$ make test
```

Although testing various functionalities, these tests are pretty independent. But the
`test_real_life()` functions working on a common example
([schema](/samples/complex.schema) & [data](/samples/complex.ndjson)) are there to check
if this is only fantasy. Running is convincing!

Feel free to extend the functionalities to your own use case.
"""

import pathlib
import re
import sys

import polars as pl

POLARS_DATATYPES: dict[str, pl.DataType] = {
    "array": pl.List,
    "list": pl.List,
    "struct": pl.Struct,
    "float32": pl.Float32,
    "float64": pl.Float64,
    "int8": pl.Int8,
    "int16": pl.Int16,
    "int32": pl.Int32,
    "int64": pl.Int64,
    "uint8": pl.UInt8,
    "uint16": pl.UInt16,
    "uint32": pl.UInt32,
    "uint64": pl.UInt64,
    "utf8": pl.Utf8,
    # shorthands
    "float": pl.Float64,
    "real": pl.Float64,
    "int": pl.Int64,
    "integer": pl.Int64,
    "string": pl.Utf8,
}


class SchemaParsingError(Exception):
    # TODO tune this output
    """When unexpected content is encountered and cannot be parsed."""


def infer_schema(path_data: str) -> str:
    """Lazily scan JSON data and output the `Polars`-inferred schema in plain text.

    Parameters
    ----------
    path_data : str
        Path to a JSON file for `Polars` to infer its own schema (_e.g._, `Struct`
        object).

    Returns
    -------
    : str
        Pretty-printed `Polars` JSON schema.

    Notes
    -----
    This is merely to test the output of the schema parser defined in this very script.
    """

    # quick work
    def _pprint(field: str, dtype: pl.DataType, indent: str = "") -> str:
        """Recursively loop over the inferred schema and pretty print its structure.

        Parameters
        ----------
        field : str
            Name of the current field, including `:` separator.
        dtype : polars.DataType
            Datatype of the current field; nested or not.
        indent : str
            String used to indent (a number of spaces).

        Returns
        -------
        : str
            Pretty-printed field name and datatype of the current field.
        """
        schema = ""

        # nested datatype: Struct
        if hasattr(dtype, "fields"):
            schema += f"{indent}{field}{dtype.__class__.__name__}(\n"
            for f, d in dtype.to_schema().items():
                schema += _pprint(f"{f}: ", d, f"{indent}    ")
            schema += f"{indent})\n"

        # nested datatypes: Array, List
        elif hasattr(dtype, "inner"):
            schema += f"{indent}{field}{dtype.__class__.__name__}(\n"
            schema += _pprint("", dtype.inner, f"{indent}    ")
            schema += f"{indent})\n"

        # non-nested datatypes
        else:
            schema += f"{indent}{field}{dtype}\n"

        return schema

    # generate the pretty-printed schema
    schema = ""
    for field, dtype in pl.scan_ndjson(path_data).schema.items():
        schema += _pprint(f"{field}: ", dtype)

    return schema.strip()


def parse_schema(source: str) -> pl.Struct:
    """Parse a plain text JSON schema into a `Polars` `Struct`.

    Parameters
    ----------
    source : str
        Content of the plain text file describing the JSON schema.

    Returns
    -------
    : polars.Struct
        JSON schema translated into `Polars` datatypes.

    Raises
    ------
    : SchemaParsingError
        When unexpected content is encountered and cannot be parsed.

    Notes
    -----
    A nested field may not have a name! To be kept in mind when unpacking using the
    `.explode()` and `.unnest()` methods.
    """
    schema = source  # keep the initial source untouched for clear exception output

    struct: list = []  # highest level list of fields

    nested_names: list[str | None] = []  # names of nested objects
    nested_dtypes: list[pl.List | pl.Struct] = []  # datatypes of nested objects

    fields_of_lists: list[list[pl.DataType]] = []  # fields of encountered lists
    fields_of_structs: list[list[pl.DataType]] = []  # fields of encountered structs

    # continue until everything is parsed
    while len(schema):
        # new field
        if (
            m := re.match(r"([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_]+)", schema)
        ) is not None:
            name = m.group(1)
            dtype = m.group(2).lower()

            # keep track of the last nested object encountered
            if dtype in ("list", "struct"):
                nested_names.append(name)
                nested_dtypes.append(dtype)

            # add the non-nested field to the current object
            else:
                field = pl.Field(name, POLARS_DATATYPES[dtype])
                if nested_dtypes:
                    fields_of_structs[-1].append(field)
                else:
                    struct.append(field)  # not sure this happens...

            schema = schema.replace(m.group(0), "", 1)

        # within nested field
        if (m := re.match(r"([A-Za-z0-9_]+)", schema)) is not None:
            dtype = m.group(1).lower()

            # keep track of the last nested object encountered
            if dtype in ("list", "struct"):
                nested_names.append("")
                nested_dtypes.append(dtype)

            # add the non-nested field to the current object
            else:
                field = pl.Field("", POLARS_DATATYPES[dtype])
                if nested_dtypes:
                    fields_of_lists.append(POLARS_DATATYPES[dtype])
                else:
                    struct.append(field)

            schema = schema.replace(m.group(0), "", 1)

        # start of nested field
        elif (m := re.match(r"([(\[{<])", schema)) is not None:
            if nested_dtypes[-1] == "struct":
                fields_of_structs.append([])

            schema = schema.replace(m.group(0), "", 1)

        # end of nested field
        elif (m := re.match(r"([)\]}>])", schema)) is not None:
            name = nested_names.pop()
            dtype = nested_dtypes.pop()

            # generate the field
            if dtype == "list":
                if name:
                    field = pl.Field(name, pl.List(fields_of_lists.pop()))
                else:
                    field = pl.List(fields_of_lists.pop())
            else:
                field = pl.Field(name, pl.Struct(fields_of_structs.pop()))

            # add the nested field to the current object
            if nested_dtypes:
                if nested_dtypes[-1] == "list":
                    fields_of_lists.append(field)
                else:
                    fields_of_structs[-1].append(field)
            else:
                struct.append(field)

            schema = schema.replace(m.group(0), "", 1)

        # expected but ignored
        elif (m := re.match(r"[,\n\s]+", schema)) is not None:
            schema = schema.replace(m.group(0), "", 1)
            continue

        # unexpected content, raise an exception
        else:
            e = f"{schema[:50]}..."
            raise SchemaParsingError(e)

    return pl.Struct(struct)


def unpack_frame(
    df: pl.DataFrame | pl.LazyFrame,
    dtype: pl.DataType,
    column: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
    """Unpack a [nested] JSON into a `Polars` `DataFrame` or `LazyFrame` given a schema.

    Parameters
    ----------
    df : polars.DataFrame | polars.LazyFrame
        Current `Polars` `DataFrame` (or `LazyFrame`) object.
    dtype : polars.DataType
        Datatype of the current object (`polars.Array`, `polars.List` or
        `polars.Struct`).
    column : str | None
        Column to apply the unpacking on; defaults to `None`. This is used when the
        current object has children but no field name; this is the case for convoluted
        `polars.List` within a `polars.List` for instance.

    Returns
    -------
    : polars.DataFrame | polars.LazyFrame
        Updated [unpacked] `Polars` `DataFrame` (or `LazyFrame`) object.

    Notes
    -----
    The `polars.Array` is considered the [obsolete] ancestor of `polars.List` and
    expected to behave identically.
    """
    # if we are dealing with a nesting column
    if column is not None:
        if dtype in (pl.Array, pl.List):
            df = unpack_frame(df.explode(column), dtype.inner, column)
        elif dtype == pl.Struct:
            df = unpack_frame(df.unnest(column), dtype)

    # unpack nested children columns when encountered
    elif hasattr(dtype, "fields"):
        for f in dtype.fields:
            if type(f.dtype) in (pl.Array, pl.List):
                df = unpack_frame(
                    df.explode(column if column is not None else f.name),
                    f.dtype.inner,
                    f.name,
                )
            elif type(f.dtype) == pl.Struct:
                df = unpack_frame(
                    df.unnest(column if column is not None else f.name), f.dtype,
                )

    return df


def unpack_ndjson(path_schema: str, path_data: str) -> pl.LazyFrame:
    """Read (scan) and unpack a newline-delimited JSON file given a schema.

    Parameters
    ----------
    path_schema : str
        Path to the plain text schema describing the JSON content.
    path_data : str
        Path to the JSON file (or multiple files via glob patterns).

    Returns
    -------
    : polars.LazyFrame
        Unpacked JSON content, lazy style.
    """
    with pathlib.Path(path_schema).open() as f:
        return unpack_frame(pl.scan_ndjson(path_data), parse_schema(f.read()))


def unpack_text(path_schema: str, path_data: str, delimiter: str = "|") -> pl.LazyFrame:
    r"""Read (scan) and unpack a JSON file read a plain text, given a schema.

    Parameters
    ----------
    path_schema : str
        Path to the plain text schema describing the JSON content.
    path_data : str
        Path to the JSON file (or multiple files via glob patterns).
    delimiter : str
        Delimiter to use when parsing the "CSV" file; it should \*NOT\* be present in
        the file at all. Defaults to `|`.

    Returns
    -------
    : polars.LazyFrame
        Unpacked JSON content, lazy style.

    Notes
    -----
    This is mostly a test, to verify the output would be identical, as this unpacking
    use case could be applied on a CSV column containing some JSON content for isntance.
    The preferred way for native JSON content remains to use the `unpack_ndjson()`
    function defined in this same script.
    """
    with pathlib.Path(path_schema).open() as f:
        schema = parse_schema(f.read())

        return unpack_frame(
            (
                pl.scan_csv(
                    path_data,
                    has_header=False,
                    new_columns=["json"],
                    delimiter=delimiter,
                ).select(pl.col("json").str.json_extract(schema))
            ),
            schema,
        )


if __name__ == "__main__":
    # infer schema from ndjson
    if len(sys.argv[1:]) == 1 and sys.argv[1].endswith("ndjson"):
        sys.stdout.write(infer_schema(sys.argv[1]))
    # unpack ndjson given a schema
    elif len(sys.argv[1:]) == 2:
        sys.stdout.write(f"{unpack_ndjson(sys.argv[1], sys.argv[2]).fetch(3)}\n")
    # usage
    else:
        sys.stderr.write(f"Usage: python3.1X {sys.argv[0]} <SCHEMA> <NDJSON>\n")
