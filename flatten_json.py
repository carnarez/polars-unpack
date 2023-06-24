"""Testing grounds for automatic JSON unpacking."""

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
    "float": pl.Float32,
    "real": pl.Float32,
    "int": pl.Int32,
    "integer": pl.Int32,
    "string": pl.Utf8,
}


def build_dtype(schema: str) -> pl.Struct:
    """Parse a plain text JSON schema into a Polars datatypes.

    Parameters
    ----------
    schema : str
        Content of the

    Returns
    -------
    : polars.Struct
        JSON schema translated into Polars datatypes.

    Raises
    ------
    : ValueError
        When unexpected content is encountered and cannot be parsed.
    """
    struct: list = []

    nested_names: list[str | None] = []
    nested_dtypes: list[pl.List | pl.Struct] = []

    fields_of_lists: list[list[pl.DataType]] = []
    fields_of_structs: list[list[pl.DataType]] = []

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
                if len(nested_dtypes):
                    if nested_dtypes[-1] == "list":
                        fields_of_lists[-1].append(field)
                    else:
                        fields_of_structs[-1].append(field)
                else:
                    struct.append(field)

            schema = schema.replace(m.group(0), "", 1)

        # within nested field
        if (m := re.match(r"([A-Za-z0-9_]+)", schema)) is not None:
            dtype = m.group(1).lower()

            # keep track of the last nested object encountered
            if dtype in ("list", "struct"):
                nested_names.append("")
                nested_dtypes.append(dtype)
            else:
                e = f"{schema[:50]}..."
                raise ValueError(e)

            schema = schema.replace(m.group(0), "", 1)

        # start of nested field
        elif (m := re.match(r"([(\[{<])", schema)) is not None:
            if nested_dtypes[-1] == "list":
                fields_of_lists.append([])
            else:
                fields_of_structs.append([])

            schema = schema.replace(m.group(0), "", 1)

        # end of nested field
        elif (m := re.match(r"([)\]}>])", schema)) is not None:
            name = nested_names.pop()
            dtype = nested_dtypes.pop()

            # generate the field
            if dtype == "list":
                field = pl.Field(name, pl.List(pl.Struct(fields_of_lists.pop())))
            else:
                field = pl.Field(name, pl.Struct(fields_of_structs.pop()))

            # add the nested field to the current object
            if len(nested_dtypes):
                if nested_dtypes[-1] == "list":
                    fields_of_lists[-1].append(field)
                else:
                    fields_of_structs[-1].append(field)
            else:
                struct.append(field)

            schema = schema.replace(m.group(0), "", 1)

        # expected but ignored
        elif (m := re.match(r"[,\n\s]+", schema)) is not None:
            schema = schema.replace(m.group(0), "", 1)
            continue

        # unexpected content
        else:
            e = f"{schema[:50]}..."
            raise ValueError(e)

    return pl.Struct(struct)


def flatten(df: pl.LazyFrame, dtype: pl.DataType) -> pl.LazyFrame:
    """Flatten a [nested] JSON into a Polars dataframe given a schema.

    Parameters
    ----------
    df : polars.LazyFrame
        Current dataframe.
    dtype : polars.DataType
        Datatype of the current object (polars.List or polars.Struct).

    Returns
    -------
    : polars.LazyFrame
        Updated [unpacked] dataframe.
    """
    # list of fields
    fields = dtype.fields if hasattr(dtype, "fields") else dtype

    # unpack nested objects when encountered
    if any(d in (pl.List, pl.Struct) for d in [f.dtype for f in fields]):
        for f in fields:
            if type(f.dtype) == pl.List:
                df = flatten(df.explode(f.name), f.dtype.inner)
            elif type(f.dtype) == pl.Struct:
                df = flatten(df.unnest(f.name), f.dtype)

    return df


if __name__ == "__main__":
    with pathlib.Path(sys.argv[1]).open() as f:
        dtype = build_dtype(f.read())

        # read as plain text
        df = (
            pl.scan_csv(
                sys.argv[2],
                new_columns=["raw"],
                has_header=False,
                separator="|",
            ).select(pl.col("raw").str.json_extract(dtype=dtype))
            # .unnest("raw")
        )
        print(flatten(df, dtype).collect())

        # read as newline-delimited json
        df = pl.scan_ndjson(sys.argv[2])
        print(flatten(df, dtype).collect())
