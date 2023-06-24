# Module `flatten_json`

Testing grounds for automatic JSON unpacking.

**Functions**

- [`build_dtype()`](#flatten_jsonbuild_dtype): Parse a plain text JSON schema into a
  Polars datatypes.
- [`flatten()`](#flatten_jsonflatten): Flatten a \[nested\] JSON into a Polars dataframe
  given a schema.

## Functions

### `flatten_json.build_dtype`

```python
build_dtype(schema: str) -> pl.Struct:
```

Parse a plain text JSON schema into a Polars datatypes.

**Parameters**

- `schema` \[`str`\]: Content of the

**Returns**

- \[`polars.Struct`\]: JSON schema translated into Polars datatypes.

**Raises**

- \[`ValueError`\]: When unexpected content is encountered and cannot be parsed.

### `flatten_json.flatten`

```python
flatten(df: pl.LazyFrame, dtype: pl.DataType) -> pl.LazyFrame:
```

Flatten a \[nested\] JSON into a Polars dataframe given a schema.

**Parameters**

- `df` \[`polars.LazyFrame`\]: Current dataframe.
- `dtype` \[`polars.DataType`\]: Datatype of the current object (polars.List or
  polars.Struct).

**Returns**

- \[`polars.LazyFrame`\]: Updated \[unpacked\] dataframe.
