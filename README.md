# Module `flatten_json`

Automatic JSON unpacking to [`Polars`](https://pola.rs) `DataFrame`.

The use case is as follows:

- Provide a schema written in plain text describing the JSON content, to be converted
  into a `Polars` `Struct` (see samples in this repo for examples).
- Read the JSON content (as plain text using `scan_csv()` for instance, or directly as
  JSON via `scan_ndjson()`) and automagically unpack the nested content by processing
  the schema.

A few extra points:

- The schema should be dominant and we should rename columns on the fly as they are
  being unpacked to avoid identical names for different columns (which is forbidden by
  `Polars`).
- _Why not using the inferred schema?_ Because at times we need to provide _more_ fields
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

**Functions**

- [`parse_schema()`](#flatten_jsonparse_schema): Parse a plain text JSON schema into a
  `Polars` `Struct`.
- [`flatten()`](#flatten_jsonflatten): Flatten a \[nested\] JSON into a `Polars`
  `DataFrame` given a schema.

**Classes**

- [`SchemaParsingError`](#flatten_jsonschemaparsingerror): When unexpected content is
  encountered and cannot be parsed.

## Functions

### `flatten_json.parse_schema`

```python
parse_schema(schema: str) -> pl.Struct:
```

Parse a plain text JSON schema into a `Polars` `Struct`.

**Parameters**

- `schema` \[`str`\]: Content of the plain text file describing the JSON schema.

**Returns**

- \[`polars.Struct`\]: JSON schema translated into `Polars` datatypes.

**Raises**

- \[`SchemaParsingError`\]: When unexpected content is encountered and cannot be parsed.

**Notes**

A nested field may not have a name! To be kept in mind when unpacking using the
`.explode()` and `.unnest()` methods.

### `flatten_json.flatten`

```python
flatten(
    df: pl.DataFrame | pl.LazyFrame,
    dtype: pl.DataType,
    column: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
```

Flatten a \[nested\] JSON into a `Polars` `DataFrame` given a schema.

**Parameters**

- `df` \[`polars.DataFrame | polars.LazyFrame`\]: Current `Polars` `DataFrame` (or
  `LazyFrame`) object.
- `dtype` \[`polars.DataType`\]: Datatype of the current object (`polars.List` or
  `polars.Struct`).
- `column` \[`str | None`\]: Column to apply the unpacking on. Defaults to `None`.

**Returns**

- \[`polars.DataFrame | polars.LazyFrame`\]: Updated \[unpacked\] `Polars` `DataFrame`
  (or `LazyFrame`) object.

## Classes

### `flatten_json.SchemaParsingError`

When unexpected content is encountered and cannot be parsed.

#### Constructor

```python
SchemaParsingError()
```

# Module `test_flattener`

Assert capabilities of the `DataFrame` / `LazyFrame` flattener.

**Functions**

- [`test_standalone_datatype()`](#test_flattenertest_standalone_datatype): Test a
  standalone datatype.
- [`test_simple_list()`](#test_flattenertest_simple_list): Test a simple `polars.List`
  containing a standalone datatype.
- [`test_list_nested_in_list_nested_in_list()`](#test_flattenertest_list_nested_in_list_nested_in_list):
  Test a `polars.List` nested in parent `polars.List`s.
- [`test_list_nested_in_struct()`](#test_flattenertest_list_nested_in_struct): Test a
  `polars.List` nested in a `polars.Struct`.
- [`test_struct_nested_in_list()`](#test_flattenertest_struct_nested_in_list): Test a
  `polars.Struct` nested in a `polars.List`.
- [`test_simple_struct()`](#test_flattenertest_simple_struct): Test a simple
  `polars.Struct` containing a few fields.
- [`test_struct_nested_in_struct()`](#test_flattenertest_struct_nested_in_struct): Test
  a `polars.Struct` nested within another `polars.Struct`.
- [`test_real_life()`](#test_flattenertest_real_life): Test complex real life-like
  parsing and flattening.

## Functions

### `test_flattener.test_standalone_datatype`

```python
test_standalone_datatype() -> None:
```

Test a standalone datatype.

Test the following JSON content:

```json
1
```

as described by the following schema:

```
Int64
```

### `test_flattener.test_simple_list`

```python
test_simple_list() -> None:
```

Test a simple `polars.List` containing a standalone datatype.

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

### `test_flattener.test_list_nested_in_list_nested_in_list`

```python
test_list_nested_in_list_nested_in_list() -> None:
```

Test a `polars.List` nested in parent `polars.List`s.

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

### `test_flattener.test_list_nested_in_struct`

```python
test_list_nested_in_struct() -> None:
```

Test a `polars.List` nested in a `polars.Struct`.

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

### `test_flattener.test_struct_nested_in_list`

```python
test_struct_nested_in_list() -> None:
```

Test a `polars.Struct` nested in a `polars.List`.

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

### `test_flattener.test_simple_struct`

```python
test_simple_struct() -> None:
```

Test a simple `polars.Struct` containing a few fields.

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

### `test_flattener.test_struct_nested_in_struct`

```python
test_struct_nested_in_struct() -> None:
```

Test a `polars.Struct` nested within another `polars.Struct`.

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

### `test_flattener.test_real_life`

```python
test_real_life() -> None:
```

Test complex real life-like parsing and flattening.

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

# Module `test_parser`

Assert capabilities of the schema parser.

**Functions**

- [`test_unexpected_syntax()`](#test_parsertest_unexpected_syntax): Test for failure to
  parse the schema due to unknown/unexpected syntax.
- [`test_simple_datatypes()`](#test_parsertest_simple_datatypes): Test all supported
  standalone non-nesting datatypes and associated shorthands.
- [`test_simple_nested_datatypes()`](#test_parsertest_simple_nested_datatypes): Test
  nesting datatypes.
- [`test_delimiters()`](#test_parsertest_delimiters): Test nested structure delimiters:
  `()`, `[]`, `{}` or `<>`.
- [`test_list_nested_in_list()`](#test_parsertest_list_nested_in_list): Test the parsing
  of a `polars.List` within a `polars.List`.
- [`test_list_nested_in_struct()`](#test_parsertest_list_nested_in_struct): Test the
  parsing of a `polars.List` within a `polars.Struct`.
- [`test_struct_nested_in_list()`](#test_parsertest_struct_nested_in_list): Test the
  parsing of a `polars.Struct` within a `polars.List`.
- [`test_struct_nested_in_struct()`](#test_parsertest_struct_nested_in_struct): Test the
  parsing of a `polars.Struct` within a `polars.Struct`.
- [`test_complex_nested_schema()`](#test_parsertest_complex_nested_schema): Test complex
  schema.

## Functions

### `test_parser.test_unexpected_syntax`

```python
test_unexpected_syntax() -> None:
```

Test for failure to parse the schema due to unknown/unexpected syntax.

### `test_parser.test_simple_datatypes`

```python
test_simple_datatypes(text: str, struct: pl.Struct) -> None:
```

Test all supported standalone non-nesting datatypes and associated shorthands.

**Parameters**

- `text` \[`str`\]: Schema in plain text.
- `struct` \[`polars.Struct`\]: Expected datatype.

**Decoration** via `@pytest.mark.parametrize()`.

### `test_parser.test_simple_nested_datatypes`

```python
test_simple_nested_datatypes(text: str, struct: pl.Struct) -> None:
```

Test nesting datatypes.

**Parameters**

- `text` \[`str`\]: Schema in plain text.
- `struct` \[`polars.Struct`\]: Expected datatype.

**Decoration** via `@pytest.mark.parametrize()`.

### `test_parser.test_delimiters`

```python
test_delimiters(text: str, struct: pl.Struct) -> None:
```

Test nested structure delimiters: `()`, `[]`, `{}` or `<>`.

**Parameters**

- `text` \[`str`\]: Schema in plain text.
- `struct` \[`polars.Struct`\]: Expected datatype.

**Decoration** via `@pytest.mark.parametrize()`.

### `test_parser.test_list_nested_in_list`

```python
test_list_nested_in_list() -> None:
```

Test the parsing of a `polars.List` within a `polars.List`.

Test the generation of the following schema:

```
List(List(Int8))
```

### `test_parser.test_list_nested_in_struct`

```python
test_list_nested_in_struct() -> None:
```

Test the parsing of a `polars.List` within a `polars.Struct`.

Test the generation of the following schema:

```
Struct(
    foo: List(Int8)
)
```

### `test_parser.test_struct_nested_in_list`

```python
test_struct_nested_in_list() -> None:
```

Test the parsing of a `polars.Struct` within a `polars.List`.

Test the generation of the following schema:

```
List(
    Struct(
        foo: Int8,
        bar: Int8
    )
)
```

### `test_parser.test_struct_nested_in_struct`

```python
test_struct_nested_in_struct() -> None:
```

Test the parsing of a `polars.Struct` within a `polars.Struct`.

Test the generation of the following schema:

```
Struct(
    foo: Struct(
        bar: Int8
    )
)
```

### `test_parser.test_complex_nested_schema`

```python
test_complex_nested_schema() -> None:
```

Test complex schema.

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

**Notes**

This complex example actively tests most capabilities of the parser:

- Nesting of various datatypes
- Different delimiters
- Missing fields
- Extra fields
