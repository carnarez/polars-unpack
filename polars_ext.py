import polars as pl
from unpack import JSON_PATH_SEPARATOR


class UnpackFrame:
    def __init__(self, ldf: pl.LazyFrame):
        self._ldf = ldf

    def unpack(
        self,
        dtype: pl.DataType,
        json_path: str = "",
        column: str | None = None,
    ) -> pl.DataFrame | pl.LazyFrame:
        # if we are dealing with a nesting column
        if column is not None:
            if dtype in (pl.Array, pl.List):
                # rename column to json path
                jp = f"{json_path}{JSON_PATH_SEPARATOR}{column}".lstrip(JSON_PATH_SEPARATOR)
                if column in self._ldf.columns:
                    self._ldf = self._ldf.rename({column: jp})
                # unpack
                self._ldf = self.unpack(self._ldf.explode(jp), dtype.inner, jp, jp)
            elif dtype == pl.Struct:
                self._ldf = self.unpack(self._ldf.unnest(column), dtype, json_path)

        # unpack nested children columns when encountered
        elif hasattr(dtype, "fields"):
            for f in dtype.fields:
                # rename column to json path
                jp = f"{json_path}{JSON_PATH_SEPARATOR}{f.name}".lstrip(JSON_PATH_SEPARATOR)
                if f.name in self._ldf.columns:
                    self._ldf = self._ldf.rename({f.name: jp})
                # unpack
                if type(f.dtype) in (pl.Array, pl.List):
                    self._ldf = self.unpack(self._ldf.explode(jp), f.dtype.inner, jp, jp)
                elif type(f.dtype) == pl.Struct:
                    self._ldf = self.unpack(self._ldf.unnest(jp), f.dtype, jp)

        return self._ldf
    

pl.api.register_lazyframe_namespace("json")(UnpackFrame)
pl.api.register_dataframe_namespace("json")(UnpackFrame)