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
* It seems `Polars` only accepts input starting with `{`, but not `[` (such as a JSON
  list); although it _is_ valid in a JSON sense...

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


def infer_schema(path_data: str) -> str:
    """Lazily scan newline-delimited JSON data and print the `Polars`-inferred schema.

    We expect the following example JSON:

    ```json
    { "attribute": "test", "nested": { "foo": 1.23, "bar": -8, "vector": [ 0, 1, 2 ] } }
    ```

    to translate into the given `Polars` schema:

    ```
    attribute: Utf8
    nested: Struct(
        foo: Float32
        bar: Int16
        vector: List(UInt8)
    )
    ```

    Although this merely started as a test for the output of the schema parser defined
    somewhere below in this very script, it became quite useful to get a head start when
    writing a schema by hand.

    Parameters
    ----------
    path_data : str
        Path to a JSON file for `Polars` to infer its own schema (_e.g._, `Struct`
        object).

    Returns
    -------
    : str
        Pretty-printed `Polars` JSON schema.
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
            String used to indent (a number of spaces?); defaults to empty string
            (`""`).

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


def parse_schema(path_schema: str) -> pl.Struct:
    """Parse a plain text JSON schema into a `Polars` `Struct`.

    Parameters
    ----------
    path_schema : str
        Path to the plain text file describing the JSON schema.

    Returns
    -------
    : polars.Struct
        JSON schema translated into `Polars` datatypes.
    """
    with pathlib.Path(path_schema).open() as f:
        return SchemaParser(f.read()).struct


# TODO rename fields according to schema
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
                    df.unnest(column if column is not None else f.name),
                    f.dtype,
                )

    return df


def unpack_ndjson(path_schema: str, path_data: str) -> pl.LazyFrame:
    """Lazily scan and unpack newline-delimited JSON file given a `Polars` schema.

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
    return unpack_frame(pl.scan_ndjson(path_data), parse_schema(path_schema))


def unpack_text(
    path_schema: str,
    path_data: str,
    delimiter: str = "|",
) -> pl.LazyFrame:
    r"""Lazily scan and unpack JSON data read as plain text, given a `Polars` schema.

    Parameters
    ----------
    path_schema : str
        Path to the plain text schema describing the JSON content.
    path_data : str
        Path to the JSON file (or multiple files via glob patterns).
    delimiter : str
        Delimiter to use when parsing the JSON file as a CSV; defaults to `|` but `#` or
        `$` could be good candidates too. Note this delimiter should \*NOT\* be present
        in the file at all (`,` or `:` are thus out of scope given the JSON context).

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
    schema = parse_schema(path_schema)

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


class SchemaParser:
    """Parse a plain text JSON schema into a `Polars` `Struct`."""

    def __init__(self, source: str) -> None:
        """Instantiate the object.

        Parameters
        ----------
        source : str
            JSON schema described in plain text, using `Polars` datatypes.

        Attributes
        ----------
        source : str
            JSON schema described in plain text, using `Polars` datatypes.
        struct : polars.Struct
            Plain text schema parsed as a `Polars` `Struct`.
        """
        self.source = source

    @property
    def struct(self) -> pl.Struct:
        """Return the `Polars` `Struct`.

        Returns
        -------
        : polars.Struct
            Plain text schema parsed as a `Polars` `Struct`.
        """
        return self.to_struct()

    def parse_closing_delimiter(self, struct: pl.Struct) -> pl.Struct:
        """Parse and register the closing of a nested structure.

        Parameters
        ----------
        struct : polars.Struct
            Current state of the `Polars` `Struct`.

        Returns
        -------
        : polars.Struct
            Updated `Polars` `Struct` including the latest parsed addition.
        """
        name, dtype = self.record["parents"].pop()

        # list
        if dtype == "list":
            f = self.record["lists"].pop()
            d = f.dtype if hasattr(f, "dtype") else f

            # list within struct or list within list
            field = pl.Field(name, pl.List(d)) if name else pl.List(d)

        # struct
        else:
            field = pl.Field(name, pl.Struct(self.record["structs"].pop()))

        # add the attribute to the current nested object, or the root struct
        if self.record["parents"]:
            if self.record["parents"][-1][1] == "list":
                self.record["lists"].append(field)
            else:
                self.record["structs"][-1].append(field)
        else:
            struct.append(field)

        return struct

    def parse_opening_delimiter(self) -> None:
        """Parse and register the opening of a nested structure."""
        # create a new list to register new fields
        if self.record["parents"][-1][1] == "struct":
            self.record["structs"].append([])

    def parse_lone_dtype(self, struct: pl.Struct, dtype: str) -> pl.Struct:
        """Parse and register a standalone datatype (found within a list for instance).

        Parameters
        ----------
        struct : polars.Struct
            Current state of the `Polars` `Struct`.
        dtype : str
            Expected `Polars` datatype.

        Returns
        -------
        : polars.Struct
            Updated `Polars` `Struct` including the latest parsed addition.
        """
        # keep track of the nested object encountered, or if non-nested add it to the
        # the current nested object, or the root struct
        if dtype in ("list", "struct"):
            self.record["parents"].append(("", dtype))
        elif self.record["parents"]:
            self.record["lists"].append(POLARS_DATATYPES[dtype])
        else:
            struct.append(pl.Field("", POLARS_DATATYPES[dtype]))

        return struct

    def parse_attr_dtype(self, struct: pl.Struct, name: str, dtype: str) -> pl.Struct:
        """Parse and register an attribute and its associated datatype.

        Parameters
        ----------
        struct : polars.Struct
            Current state of the `Polars` `Struct`.
        name : str
            New attribute name.
        dtype : str
            Expected `Polars` datatype for this attribute.

        Returns
        -------
        : polars.Struct
            Updated `Polars` `Struct` including the latest parsed addition.
        """
        field = pl.Field(name, POLARS_DATATYPES[dtype])

        # keep track of the nested object encountered, or if non-nested add it to the
        # the current nested object, or the root struct
        if dtype in ("list", "struct"):
            self.record["parents"].append((name, dtype))
        elif self.record["parents"]:
            self.record["structs"][-1].append(field)
        else:
            struct.append(field)

        return struct

    def to_struct(self) -> None:
        r"""Parse the plain text schema into a `Polars` `Struct`.

        We expect something as follows:

        ```
        attribute: Utf8
        nested: Struct(
            foo: Float32
            bar: Int16
            vector: List[UInt8]
        )
        ```

        to translate into a `Polars` native `Struct` object:

        ```python
        polars.Struct([
            polars.Field("attribute", polars.Utf8),
            polars.Struct([
                polars.Field("foo", polars.Float32),
                polars.Field("bar", polars.Int16),
                polars.Field("vector", polars.List(polars.UInt8))
            ])
        ])
        ```

        The following patterns (recognised via regular expressions) are supported:

        * `([A-Za-z0-9_]+)\\s*:\\s*([A-Za-z0-9_]+)` for an attribute name, a column
          (`:`) and a datatype; for instance `attribute: Utf8` in the example above.
          Attribute name and datatype must not have spaces and only include
          alphanumerical or underscore (`_`) characters.
        * `([A-Za-z0-9_]+)` for a lone datatype; for instance the inner content of the
          `List()` in the example above. Keep in mind this datatype could be a complex
          structure as much as a canonical datatype.
        * `[(\\[{<]` and its `[)\\]}>]` counterpart for opening and closing of nested
          datatypes. Any of these characters can be used to open or close nested
          structures; mixing also allowed, for the better or the worse.

        Indentation and trailing commas are ignored. The source is parsed until the end
        of the file is reached or a `SchemaParsingError` exception is raised.

        Raises
        ------
        : SchemaParsingError
            When unexpected content is encountered and cannot be parsed.
        """
        s = self.source
        struct: list[pl.Datatype] = []

        # bookkeeping
        self.record: dict = {"parents": [], "lists": [], "structs": []}

        # continue until everything is parsed
        while s:
            if (m := re.match(r"([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_]+)", s)) is not None:
                struct = self.parse_attr_dtype(struct, m.group(1), m.group(2).lower())
            elif (m := re.match(r"([A-Za-z0-9_]+)", s)) is not None:
                struct = self.parse_lone_dtype(struct, m.group(1).lower())
            elif (m := re.match(r"[(\[{<]", s)) is not None:
                self.parse_opening_delimiter()
            elif (m := re.match(r"[)\]}>]", s)) is not None:
                struct = self.parse_closing_delimiter(struct)
            elif (m := re.match(r"[,\n\s]+", s)) is not None:
                pass
            else:
                e = f"{s[:50]}..."
                raise SchemaParsingError(e)

            # clean up the current match
            s = s.replace(m.group(0), "", 1)

        # clean up in case someone checks the object attributes
        delattr(self, "record")

        return pl.Struct(struct)


class SchemaParsingError(Exception):
    """When unexpected content is encountered and cannot be parsed."""


if __name__ == "__main__":
    # infer schema from ndjson
    if len(sys.argv[1:]) == 1 and sys.argv[1].endswith("ndjson"):
        sys.stdout.write(f"{infer_schema(sys.argv[1])}\n")
    # unpack ndjson given a schema
    elif len(sys.argv[1:]) == 2:
        sys.stdout.write(f"{unpack_ndjson(sys.argv[1], sys.argv[2]).fetch(3)}\n")
    # usage
    else:
        sys.stderr.write(f"Usage: python3.1X {sys.argv[0]} <SCHEMA> <NDJSON>\n")
