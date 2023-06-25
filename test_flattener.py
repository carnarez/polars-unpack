"""Assert capabilities of the `DataFrame` / `LazyFrame` flattener."""

import json
import pathlib

import polars as pl

from flatten_json import flatten, parse_schema


def test_standalone_datatype() -> None:
    """Test a standalone datatype.

    Test the following JSON content:

    ```json
    1
    ```

    as described by the following schema:

    ```
    Int64
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("", pl.Int64),
        ],
    )

    df = pl.DataFrame([0, 1, 2, 3], dtype)

    assert parse_schema("Int64") == dtype
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(df)


def test_simple_list() -> None:
    """Test a simple `polars.List` containing a standalone datatype.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": [
            0,
            1,
            2,
            3
        ]
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: List(Int64)
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field("json", pl.List(pl.Int64)),
        ],
    )

    df = pl.DataFrame(
        {
            "text": "foobar",
            "json": json.loads("[[0, 1, 2, 3]]"),
        },
        dtype,
    )

    assert parse_schema("text:Utf8,json:List(Int64)") == dtype
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(df.explode("json"))


def test_list_nested_in_list_nested_in_list() -> None:
    """Test a `polars.List` nested in parent `polars.List`s.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": [
            [
                [
                    [10, 12],
                    [11, 13]
                ],
                [
                    [30, 32],
                    [31, 33]
                ]
            ],
            [
                [
                    [20, 22],
                    [21, 23]
                ],
                [
                    [40, 42],
                    [41, 43]
                ]
            ]
        ]
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: List(List(List(Int64)))
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field(
                "json",
                pl.List(
                    pl.List(
                        pl.List(pl.Int64),
                    ),
                ),
            ),
        ],
    )

    df = pl.DataFrame(
        {
            "text": "foobar",
            "json": json.loads(
                "[[[[10, 12], [11, 13]], [[30, 32], [31, 33]]],"
                " [[[20, 22], [21, 23]], [[40, 42], [41, 43]]]]",
            ),
        },
        dtype,
    )

    assert parse_schema("text:Utf8,json:List(List(List(Int64)))") == dtype
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(
        df.explode("json").explode("json").explode("json"),
    )


def test_list_nested_in_struct() -> None:
    """Test a `polars.List` nested in a `polars.Struct`.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": {
            "foo": {
                "fox": 0,
                "foz": 2
            },
            "bar": [
                1,
                3
            ]
        }
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: Struct(
        foo: Struct(
            fox: Int64,
            bax: Int64
        ),
        bar: List(Int64)
    )
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field(
                "json",
                pl.Struct(
                    [
                        pl.Field(
                            "foo",
                            pl.Struct(
                                [pl.Field("fox", pl.Int64), pl.Field("foz", pl.Int64)],
                            ),
                        ),
                        pl.Field("bar", pl.List(pl.Int64)),
                    ],
                ),
            ),
        ],
    )

    df = pl.DataFrame(
        {
            "text": ["foobar"],
            "json": [
                json.loads(
                    '{"foo": {"fox": 0, "foz": 2}, "bar": [1, 3]}',
                ),
            ],
        },
        dtype,
    )

    assert (
        parse_schema(
            "text:Utf8,json:Struct(foo:Struct(fox:Int64,foz:Int64),bar:List(Int64))",
        )
        == dtype
    )
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(
        df.unnest("json").unnest("foo").explode("bar"),
    )


def test_struct_nested_in_list() -> None:
    """Test a `polars.Struct` nested in a `polars.List`.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": [
            {
                "foo": 0,
                "bar": 1
            },
            {
                "foo": 2,
                "bar": 3
            }
        ]
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: List(
        Struct(
            foo: Int64,
            bar: Int64
        )
    )
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field(
                "json",
                pl.List(
                    pl.Struct([pl.Field("foo", pl.Int64), pl.Field("bar", pl.Int64)]),
                ),
            ),
        ],
    )

    df = pl.DataFrame(
        {
            "text": "foobar",
            "json": json.loads('[[{"foo": 0, "bar": 1}, {"foo": 2, "bar": 3}]]'),
        },
        dtype,
    )

    assert parse_schema("text:Utf8,json:List(Struct(foo:Int64,bar:Int64))") == dtype
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(df.explode("json").unnest("json"))


def test_simple_struct() -> None:
    """Test a simple `polars.Struct` containing a few fields.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": {
            "foo": 0,
            "bar": 1
        }
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: Struct(
        foo: Int64,
        bar: Int64
    )
    ```
    """
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field(
                "json",
                pl.Struct([pl.Field("foo", pl.Int64), pl.Field("bar", pl.Int64)]),
            ),
        ],
    )

    df = pl.DataFrame(
        {
            "text": ["foobar"],
            "json": [json.loads('{"foo": 0, "bar": 1}')],
        },
        dtype,
    )

    assert parse_schema("text:Utf8,json:Struct(foo:Int64,bar:Int64)") == dtype
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(df.unnest("json"))


def test_struct_nested_in_struct() -> None:
    """Test a `polars.Struct` nested within another `polars.Struct`.

    Test the following nested JSON content:

    ```json
    {
        "text": "foobar",
        "json": {
            "foo": {
                "fox": 0,
                "foz": 2
            },
            "bar": {
                "bax": 1,
                "baz": 3
            }
        }
    }
    ```

    as described by the following schema:

    ```
    text: Utf8,
    json: Struct(
        foo: Struct(
            fox: Int64,
            foz: Int64
        ),
        bar: Struct(
            bax: Int64,
            baz: Int64
        )
    )
    ```
    """
    # yup, this is why we want this to be generated
    dtype = pl.Struct(
        [
            pl.Field("text", pl.Utf8),
            pl.Field(
                "json",
                pl.Struct(
                    [
                        pl.Field(
                            "foo",
                            pl.Struct(
                                [pl.Field("fox", pl.Int64), pl.Field("foz", pl.Int64)],
                            ),
                        ),
                        pl.Field(
                            "bar",
                            pl.Struct(
                                [pl.Field("bax", pl.Int64), pl.Field("baz", pl.Int64)],
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )

    df = pl.DataFrame(
        {
            "text": ["foobar"],
            "json": [
                json.loads(
                    '{"foo": {"fox": 0, "foz": 2}, "bar": {"bax": 1, "baz": 3}}',
                ),
            ],
        },
        dtype,
    )

    assert (
        parse_schema(
            "text:Utf8,"
            "json:Struct(foo:Struct(fox:Int64,foz:Int64),bar:Struct(bax:Int64,baz:Int64))",
        )
        == dtype
    )
    assert dtype.to_schema() == df.schema
    assert flatten(df, dtype).frame_equal(df.unnest("json").unnest("foo", "bar"))


def test_real_life() -> None:
    """Test complex real life-like parsing and flattening.

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
        ]
    >
    ```

    with the last bit of the JSON being ignored during flattening (truncated schema):

    ```
    payload: Struct<
        ...,
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
    with pathlib.Path("samples/complex.schema").open() as f:
        dtype = parse_schema(f.read())

    with pathlib.Path("samples/complex.ndjson") as p:
        df_ndjson = pl.scan_ndjson(p)

    with pathlib.Path("samples/complex.csv") as p:
        df_csv = pl.scan_csv(
            p,
            dtypes={
                "timestamp": pl.Int64,
                "source": pl.Utf8,
                "offset": pl.Int64,
                "transaction": pl.Utf8,
                "location": pl.Int8,
                "type": pl.Utf8,
                "customerIdentifier": pl.Utf8,
                "product": pl.Int16,
                "productDescription": pl.Utf8,
                "quantity": pl.Int8,
                "vatRate": pl.Float32,
                "lineAmountIncludingVat": pl.Float32,
                "lineAmountExcludingVat": pl.Float32,
                "lineAmountVat": pl.Float32,
                "lineAmountCurrency": pl.Utf8,
                "promotion": pl.Int64,
                "promotionDescription": pl.Utf8,
                "discountAmountIncludingVat": pl.Float32,
                "discountAmountExcludingVat": pl.Float32,
                "discountAmountVat": pl.Float32,
                "discountAmountCurrency": pl.Utf8,
            },
        )

    assert (
        flatten(df_ndjson, dtype)
        .drop("payment")
        .collect()
        .frame_equal(df_csv.collect())
    )
