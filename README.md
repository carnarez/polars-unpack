# Module `unpack`

Automatic JSON unpacking to [`Polars`](https://pola.rs) `DataFrame`.

The use case is as follows:

- Provide a schema written in plain text describing the JSON content, to be converted
  into a `Polars` `Struct` (see samples in this repo for examples).
- Read the JSON content (as plain text using `scan_csv()` for instance, or directly as
  JSON via `scan_ndjson()`) and automagically unpack the nested content by processing
  the schema.

A few extra points:

- The schema should be dominant and we should rename fields as they are being unpacked
  to avoid identical names for different columns (which is forbidden by `Polars` for
  obvious reasons).
- _Why not using the inferred schema?_ Because at times we need to provide fields that
  might _not_ be in the JSON file to fit a certain data structure, or simply ignore part
  of the JSON data when unpacking to avoid wasting resources. Oh, and to rename fields
  too.

Limitations encountered so far:

- It seems `Polars` only accepts input starting with `{`, but not `[` (such as a JSON
  list); although valid in a JSON sense...

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

**Functions**

- [`infer_schema()`](#unpackinfer_schema): Lazily scan JSON data and output the
  `Polars`-inferred schema in plain text.
- [`parse_schema()`](#unpackparse_schema): Parse a plain text JSON schema into a
  `Polars` `Struct`.
- [`unpack_frame()`](#unpackunpack_frame): Unpack a \[nested\] JSON into a `Polars`
  `DataFrame` or `LazyFrame` given a schema.
- [`unpack_ndjson()`](#unpackunpack_ndjson): Read (scan) and unpack a newline-delimited
  JSON file given a schema.
- [`unpack_text()`](#unpackunpack_text): Read (scan) and unpack a JSON file read as
  plain text, given a schema.

**Classes**

- [`SchemaParsingError`](#unpackschemaparsingerror): When unexpected content is
  encountered and cannot be parsed.

## Functions

### `unpack.infer_schema`

```python
infer_schema(path_data: str) -> str:
```

Lazily scan JSON data and output the `Polars`-inferred schema in plain text.

**Parameters**

- `path_data` \[`str`\]: Path to a JSON file for `Polars` to infer its own schema
  (_e.g._, `Struct` object).

**Returns**

- \[`str`\]: Pretty-printed `Polars` JSON schema.

**Notes**

This is merely to test the output of the schema parser defined in this very script.

### `unpack.parse_schema`

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

### `unpack.unpack_frame`

```python
unpack_frame(
    df: pl.DataFrame | pl.LazyFrame,
    dtype: pl.DataType,
    column: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
```

Unpack a \[nested\] JSON into a `Polars` `DataFrame` or `LazyFrame` given a schema.

**Parameters**

- `df` \[`polars.DataFrame | polars.LazyFrame`\]: Current `Polars` `DataFrame` (or
  `LazyFrame`) object.
- `dtype` \[`polars.DataType`\]: Datatype of the current object (`polars.Array`,
  `polars.List` or `polars.Struct`).
- `column` \[`str | None`\]: Column to apply the unpacking on; defaults to `None`. This
  is used when the current object has children but no field name; this is the case for
  convoluted `polars.List` within a `polars.List` for instance.

**Returns**

- \[`polars.DataFrame | polars.LazyFrame`\]: Updated \[unpacked\] `Polars` `DataFrame`
  (or `LazyFrame`) object.

**Notes**

The `polars.Array` is considered the \[obsolete\] ancestor of `polars.List` and expected
to behave identically.

### `unpack.unpack_ndjson`

```python
unpack_ndjson(path_schema: str, path_data: str) -> pl.LazyFrame:
```

Read (scan) and unpack a newline-delimited JSON file given a schema.

**Parameters**

- `path_schema` \[`str`\]: Path to the plain text schema describing the JSON content.
- `path_data` \[`str`\]: Path to the JSON file (or multiple files via glob patterns).

**Returns**

- \[`polars.LazyFrame`\]: Unpacked JSON content, lazy style.

### `unpack.unpack_text`

```python
unpack_text(path_schema: str, path_data: str, delimiter: str = "|") -> pl.LazyFrame:
```

Read (scan) and unpack a JSON file read as plain text, given a schema.

**Parameters**

- `path_schema` \[`str`\]: Path to the plain text schema describing the JSON content.
- `path_data` \[`str`\]: Path to the JSON file (or multiple files via glob patterns).
- `delimiter` \[`str`\]: Delimiter to use when parsing the JSON file as a CSV; defaults
  to `|` but `#` or `$` could be good candidates too. Note this delimiter should \*NOT\*
  be present in the file at all (`,` or `:` are thus out of scope given the JSON
  context).

**Returns**

- \[`polars.LazyFrame`\]: Unpacked JSON content, lazy style.

**Notes**

This is mostly a test, to verify the output would be identical, as this unpacking use
case could be applied on a CSV column containing some JSON content for isntance. The
preferred way for native JSON content remains to use the `unpack_ndjson()` function
defined in this same script.

## Classes

### `unpack.SchemaParsingError`

When unexpected content is encountered and cannot be parsed.

#### Constructor

```python
SchemaParsingError()
```
