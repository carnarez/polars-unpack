"""Assert capabilities of the `DataFrame` / `LazyFrame` flattener."""

import json

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
