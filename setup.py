"""Make `polars_unpack` installable (via `pip install git+https://...`)."""

import setuptools  # type: ignore

setuptools.setup(
    author="carnarez",
    description=("Automated, schema-based JSON unpacking to Polars objects."),
    name="polars_unpack",
    packages=["polars_unpack"],
    package_data={"polars_unpack": ["py.typed"]},
    url="https://github.com/carnarez/polars_unpack",
    version="0.0.1",
)
