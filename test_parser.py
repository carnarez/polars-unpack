"""Assert capabilities of the schema parser."""

import polars as pl
import pytest

from flatten_json import POLARS_DATATYPES, SchemaParsingError, parse_schema


def test_unexpected_syntax() -> None:
    """Test for failure to parse the schema due to unknown/unexpected syntax."""
    with pytest.raises(SchemaParsingError):
        parse_schema("!@#$%^&*")


@pytest.mark.parametrize(
    ("text", "struct"),
    [
        (text.capitalize(), pl.Struct([pl.Field("", dtype)]))
        for text, dtype in POLARS_DATATYPES.items()
        if text not in ("list", "struct")
    ],
)
def test_simple_datatypes(text: str, struct: pl.Struct) -> None:
    """Test all supported standalone non-nesting datatypes and associated shorthands.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert parse_schema(text) == struct


@pytest.mark.parametrize(
    ("text", "struct"),
    [
        (
            "List(Int8)",
            pl.Struct([pl.List(pl.Int8)]),
        ),
        (
            "Struct(foo: Int8, bar: Int8)",
            pl.Struct(
                [
                    pl.Field(
                        "",
                        pl.Struct([pl.Field("foo", pl.Int8), pl.Field("bar", pl.Int8)]),
                    ),
                ],
            ),
        ),
    ],
)
def test_simple_nested_datatypes(text: str, struct: pl.Struct) -> None:
    """Test nesting datatypes.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert parse_schema(text) == struct


@pytest.mark.parametrize(
    ("text", "struct"),
    [
        (
            "Struct(foo: Int8)",
            pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.Int8)]))]),
        ),
        (
            "Struct[foo: Int8]",
            pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.Int8)]))]),
        ),
        (
            "Struct{foo: Int8}",
            pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.Int8)]))]),
        ),
        (
            "Struct<foo: Int8>",
            pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.Int8)]))]),
        ),
        (
            "Struct(foo: Utf8]",  # mixed!?
            pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.Utf8)]))]),
        ),
    ],
)
def test_delimiters(text: str, struct: pl.Struct) -> None:
    """Test nested structure delimiters: `()`, `[]`, `{}` or `<>`.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert parse_schema(text) == struct


def test_list_nested_in_list() -> None:
    """Test the parsing of a `polars.List` within a `polars.List`."""
    struct = pl.Struct([pl.List(pl.List(pl.Int8))])

    assert parse_schema("List(List(Int8))") == struct


def test_list_nested_in_struct() -> None:
    """Test the parsing of a `polars.List` within a `polars.Struct`."""
    struct = pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.List(pl.Int8))]))])

    assert parse_schema("Struct(foo: List(Int8))") == struct


def test_struct_nested_in_list() -> None:
    """Test the parsing of a `polars.Struct` within a `polars.List`."""
    struct = pl.Struct(
        [pl.List(pl.Struct([pl.Field("foo", pl.Int8), pl.Field("bar", pl.Int8)]))],
    )

    assert parse_schema("List(Struct(foo: Int8, bar: Int8))") == struct


def test_struct_nested_in_struct() -> None:
    """Test the parsing of a `polars.Struct` within a `polars.Struct`."""
    struct = pl.Struct(
        [
            pl.Field(
                "",
                pl.Struct([pl.Field("foo", pl.Struct([pl.Field("bar", pl.Int8)]))]),
            ),
        ],
    )

    assert parse_schema("Struct(foo: Struct(bar: Int8))") == struct


def test_complex_nested_schema() -> None:
    """Test complexed schema.

    Test the following nested JSON content:

    ```json
    ```

    as described by the following schema:

    ```
    ```

    Notes
    -----
    This complex example actively tests most capabilities of the parser:
    * Nesting
    """
