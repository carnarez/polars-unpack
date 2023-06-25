"""Automatic JSON unpacking to [`Polars`](https://pola.rs) `DataFrame`.

The use case is as follows:

* Provide a schema written in plain text describing the JSON content, to be converted
  into a `Polars` `Struct` (see samples in this repo for examples).
* Read the JSON content (as plain text using `scan_csv()` for instance, or directly as
  JSON via `scan_ndjson()`) and automagically unpack the nested content by processing
  the schema.

A few extra points:

* The schema should be dominant and we should rename columns on the fly as they are
  being unpacked to avoid identical names for different columns (which is forbidden by
  `Polars`).
* _Why not using the inferred schema?_ Because at times we need to provide _more_ fields
  that might not be in the JSON file to fit a certain data structure, or simply ignore
  part of the JSON data when unpacking to avoid wasting resources.

The current ~~working~~ state of this little DIY can be checked via:

```shell
$ make env
> python flatten_json.py samples/complex.schema samples/complex.ndjson
```

A "thorough" (-ish!) battery of tests can be performed via:

```shell
$ make test
```
"""

import pathlib
import re
import sys

import polars as pl

POLARS_DATATYPES: dict[str, pl.DataType] = {
    "list": pl.List,
    "struct": pl.Struct,
    "float32": pl.Float32,
    "float64": pl.Float64,
    "int8": pl.Int8,
    "int16": pl.Int16,
    "int32": pl.Int32,
    "int64": pl.Int64,
    "utf8": pl.Utf8,
    # shorthands
    "float": pl.Float64,
    "real": pl.Float64,
    "int": pl.Int64,
    "integer": pl.Int64,
    "string": pl.Utf8,
}


class SchemaParsingError(Exception):
    """When unexpected content is encountered and cannot be parsed."""


def parse_schema(schema: str) -> pl.Struct:
    """Parse a plain text JSON schema into a `Polars` `Struct`.

    Parameters
    ----------
    schema : str
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


def flatten(
    df: pl.DataFrame | pl.LazyFrame,
    dtype: pl.DataType,
    column: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
    """Flatten a [nested] JSON into a `Polars` `DataFrame` given a schema.

    Parameters
    ----------
    df : polars.DataFrame | polars.LazyFrame
        Current `Polars` `DataFrame` (or `LazyFrame`) object.
    dtype : polars.DataType
        Datatype of the current object (`polars.List` or `polars.Struct`).
    column : str | None
        Column to apply the unpacking on. Defaults to `None`.

    Returns
    -------
    : polars.DataFrame | polars.LazyFrame
        Updated [unpacked] `Polars` `DataFrame` (or `LazyFrame`) object.
    """
    # if we are dealing with the nested column itself
    if column is not None:
        if dtype == pl.List:
            df = flatten(df.explode(column), dtype.inner, column)
        elif dtype == pl.Struct:
            df = flatten(df.unnest(column), dtype)

    # unpack nested children columns when encountered
    elif hasattr(dtype, "fields") and any(
        d in (pl.List, pl.Struct) for d in [f.dtype for f in dtype.fields]
    ):
        for f in dtype.fields:
            if type(f.dtype) == pl.List:
                df = flatten(
                    df.explode(column if column else f.name),
                    f.dtype.inner,
                    f.name,
                )
            elif type(f.dtype) == pl.Struct:
                df = flatten(df.unnest(column if column else f.name), f.dtype)

    return df


if __name__ == "__main__":
    with pathlib.Path(sys.argv[1]).open() as f:
        print("---")

        # parse schema
        dtype = parse_schema(f.read())
        print(dtype.to_schema())

        print("---")

        # read as plain text
        df = pl.scan_csv(
            sys.argv[2],
            new_columns=["json"],
            has_header=False,
            separator="|",
        ).select(pl.col("json").str.json_extract(dtype))
        print(df.collect())
        print(df.select("json").dtypes[0].to_schema())
        print(flatten(df, dtype, "json").collect())

        print("---")

        # read as newline-delimited json
        df = pl.scan_ndjson(sys.argv[2])
        print(df.collect())
        print(df.schema)
        print(flatten(df, dtype).collect())

        print("---")
