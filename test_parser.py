"""Assert capabilities of the schema parser."""

import pathlib

import polars as pl
import pytest

from unpack import (
    POLARS_DATATYPES,
    SchemaParser,
    SchemaParsingError,
    UnknownDataTypeError,
    infer_schema,
    parse_schema,
)


@pytest.mark.parametrize(
    ("text", "struct"),
    [
        (text.capitalize(), pl.Struct([pl.Field("", dtype)]))
        for text, dtype in POLARS_DATATYPES.items()
        if text not in ("list", "struct")
    ],
)
def test_datatype(text: str, struct: pl.Struct) -> None:
    """Test all supported standalone non-nesting datatypes and associated shorthands.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert SchemaParser(text).to_struct() == struct


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
def test_datatype_nested(text: str, struct: pl.Struct) -> None:
    """Test nesting datatypes.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert SchemaParser(text).to_struct() == struct


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
def test_delimiter(text: str, struct: pl.Struct) -> None:
    """Test nested structure delimiters: `()`, `[]`, `{}` or `<>`.

    Parameters
    ----------
    text : str
        Schema in plain text.
    struct : polars.Struct
        Expected datatype.
    """
    assert SchemaParser(text).to_struct() == struct


def test_list_nested_in_list() -> None:
    """Test the parsing of a `polars.List` within a `polars.List`.

    Test the generation of the following schema:

    ```
    List(List(Int8))
    ```
    """
    struct = pl.Struct([pl.List(pl.List(pl.Int8))])

    assert SchemaParser("List(List(Int8))").to_struct() == struct


def test_list_nested_in_struct() -> None:
    """Test the parsing of a `polars.List` within a `polars.Struct`.

    Test the generation of the following schema:

    ```
    Struct(
        foo: List(Int8)
    )
    ```
    """
    struct = pl.Struct([pl.Field("", pl.Struct([pl.Field("foo", pl.List(pl.Int8))]))])

    assert SchemaParser("Struct(foo: List(Int8))").to_struct() == struct


def test_pretty_printing() -> None:
    """Test whether an inferred schema is correctly printed."""
    with pathlib.Path("samples/nested-list.schema").open() as f:
        assert infer_schema("samples/nested-list.ndjson") == f.read().strip()


def test_real_life() -> None:
    """Test complex schema.

    Test the following nested JSON content:

    ```json
    {
        "headers": {
            "timestamp": 1372182309,
            "source": "Online.Transactions",
            "offset": 123456789
        },
        "payload": {
            "transaction": "inbound",
            "location": 765,
            "customer": {
                "type": "REGISTERED",
                "customerIdentifier": "a8098c1a-f86e-11da-bd1a-00112444be1e"
            },
            "lines": [
                {
                    "product": 76543,
                    "productDescription": "Toilet plunger",
                    "quantity": 2,
                    "vatRate": 0.21,
                    "lineAmount": {
                        "lineAmountIncludingVat": 10.0,
                        "lineAmountExcludingVat": 8.26,
                        "lineAmountVat": 1.74,
                        "lineAmountCurrency": "EUR"
                    },
                    "discounts": [
                        {
                            "promotion": 100023456000789,
                            "promotionDescription": "Buy one get two",
                            "discountAmount": {
                                "discountAmountIncludingVat": 10.0,
                                "discountAmountExcludingVat": 8.26,
                                "discountAmountVat": 1.74,
                                "discountAmountCurrency": "EUR"
                            }
                        }
                    ]
                },
                {
                    "product": 3456,
                    "productDescription": "Toilet cap",
                    "quantity": 1,
                    "vatRate": 0.21,
                    "lineAmount": {
                        "lineAmountIncludingVat": 30.0,
                        "lineAmountExcludingVat": 24.79,
                        "lineAmountVat": 5.21,
                        "lineAmountCurrency": "EUR"
                    }
                }
            ],
            "payment": {
                "method": "Card",
                "company": "OnlineBanking",
                "identifier": 123456789,
                "totalAmount": {
                    "totalAmountIncludingVat": 40.0,
                    "totalAmountExcludingVat": 33.05,
                    "totalAmountVat": 6.95,
                    "totalAmountCurrency": "EUR"
                }
            }
        }
    }
    ```

    as described by the following schema:

    ```
    headers: Struct<
        timestamp: Int64,
        source: Utf8,
        offset: Int64
    >,
    payload: Struct<
        transaction: Utf8,
        location: Int8,
        customer: Struct{
            type: Utf8,
            registration: Utf8
        },
        lines: List[
            Struct{
                product: Int16,
                productDescription: Utf8,
                quantity: Int8,
                vatRate: Float32,
                lineAmount: Struct(
                    lineAmountIncludingVat: Float32,
                    lineAmountExcludingVat: Float32,
                    lineAmountVat: Float32,
                    lineAmountCurrency: Utf8
                )
                discounts: List[
                    Struct{
                        promotion: Int64,
                        promotionDescription: Utf8,
                        discountAmount: Struct{
                            discountAmountIncludingVat: Float32,
                            discountAmountExcludingVat: Float32,
                            discountAmountVat: Float32,
                            discountAmountCurrency: Utf8
                        }
                    }
                ]
            }
        ],
        payment: Struct{
            method: Utf8,
            company: Utf8,
            transactionIdentifier: Int64,
            totalAmount: Struct{
                totalAmountIncludingVat: Float32,
                totalAmountExcludingVat: Float32,
                totalAmountVat: Float32,
                totalAmountCurrency: Utf8
            }
        }
    >
    ```
    """
    dtype = parse_schema("samples/complex.schema")
    df = pl.scan_ndjson("samples/complex.ndjson").collect()

    assert dtype.to_schema() == df.schema


def test_struct_nested_in_list() -> None:
    """Test the parsing of a `polars.Struct` within a `polars.List`.

    Test the generation of the following schema:

    ```
    List(
        Struct(
            foo: Int8,
            bar: Int8
        )
    )
    ```

    Notes
    -----
    It seems `Polars` only accepts input starting with `{`, but not `[` (such as a JSON
    lists); although the schema described above is valid in a JSON sense, the associated
    data will not be ingested by `Polars`.
    """
    struct = pl.Struct(
        [pl.List(pl.Struct([pl.Field("foo", pl.Int8), pl.Field("bar", pl.Int8)]))],
    )

    assert SchemaParser("List(Struct(foo: Int8, bar: Int8))").to_struct() == struct


def test_struct_nested_in_struct() -> None:
    """Test the parsing of a `polars.Struct` within a `polars.Struct`.

    Test the generation of the following schema:

    ```
    Struct(
        foo: Struct(
            bar: Int8
        )
    )
    ```
    """
    struct = pl.Struct(
        [
            pl.Field(
                "",
                pl.Struct([pl.Field("foo", pl.Struct([pl.Field("bar", pl.Int8)]))]),
            ),
        ],
    )

    assert SchemaParser("Struct(foo: Struct(bar: Int8))").to_struct() == struct


def test_unexpected_syntax() -> None:
    """Test for failure to parse the schema due to unknown/unexpected syntax."""
    with pytest.raises(SchemaParsingError):
        SchemaParser("!@#$%^&*").to_struct()
    with pytest.raises(SchemaParsingError):
        SchemaParser("Struct(!@#$%^&*)").to_struct()


def test_unknown_datatype() -> None:
    """Test for unknown datatype."""
    with pytest.raises(UnknownDataTypeError):
        SchemaParser("Foo").to_struct()
    with pytest.raises(UnknownDataTypeError):
        SchemaParser("Struct(foo: Bar)").to_struct()
