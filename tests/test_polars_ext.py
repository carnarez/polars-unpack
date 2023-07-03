import polars as pl
from unpack import SchemaParser
from polars_ext import *  # TODO fix by properly packaging folder structure


def test_datatype() -> None:
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

    # tested in the other module but might as well...
    assert SchemaParser("Int64").to_struct() == dtype
    assert dtype.to_schema() == df.schema
    assert df.json.unpack(dtype).frame_equal(df)
