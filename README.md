**Automatic JSON unpacking to [`Polars`](https://pola.rs) `DataFrame` or `LazyFrame`.**
Get it via a simple:

```shell
$ pip install git+https://github.com/carnarez/polars-unpack@master
```

or simply:

```shell
$ wget https://raw.githubusercontent.com/carnarez/polars-unpack/master/polars_unpack/unpack.py
```

for the script itself, whatever you find more appropriate. The story behind the use case
is succintly illustrated below.

By providing a schema written in the following pseudo-code:

```text
column: Utf8
nested: List(
    Struct(
        attr: UInt8
        attr2=renamed: UInt8
    )
)
missing_from_source: Float32
```

the JSON file (rewritten as newline-delimited JSON not to waste resources) below:

```json
{
    "column": "content",
    "nested": [
        {
            "attr": 0,
            "attr2": 2
        },
        {
            "attr": 1,
            "attr2": 3
        }
    ],
    "omitted_in_schema": "ignored"
}
```

gets automatically unpacked:

```text
┌─────────┬──────┬─────────┬─────────────────────┐
│ column  ┆ attr ┆ renamed ┆ missing_from_source │
│ ---     ┆ ---  ┆ ---     ┆ ---                 │
│ str     ┆ ui8  ┆ ui8     ┆ f32                 │
╞═════════╪══════╪═════════╪═════════════════════╡
│ content ┆ 0    ┆ 2       ┆ null                │
│ content ┆ 1    ┆ 3       ┆ null                │
└─────────┴──────┴─────────┴─────────────────────┘
```

Note the missing and extra (but omitted) attributes, and what they mean for the final
`Polars` object.
