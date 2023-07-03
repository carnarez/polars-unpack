# Module `unpack_logo`

Add an unpacking animation to the `Polars` b(e)ar logo.

**Functions**

- [`rect_coordinates()`](#unpack_logorect_coordinates): Fetch the coordinates of all
  `rect` objects.
- [`rect_dimensions()`](#unpack_logorect_dimensions): Fetch the dimensions of all `rect`
  objects.
- [`calculate_average_gap()`](#unpack_logocalculate_average_gap): Calculate an average
  for the gap between `rect` objects.
- [`calculate_figure_center()`](#unpack_logocalculate_figure_center): Calculate the
  center of the figure.
- [`calculate_unpacked_width()`](#unpack_logocalculate_unpacked_width): Calculate the
  maximum width when unpacking the bear.
- [`animate_svg()`](#unpack_logoanimate_svg): Update the dimensions of the SVG object
  and add the animation.

## Functions

### `unpack_logo.rect_coordinates`

```python
rect_coordinates(rect: list[xml.etree.ElementTree.Element]) -> list[tuple[float, float]]:
```

Fetch the coordinates of all `rect` objects.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`list[tuple[float, float]]`\]: List of (x, y) pairs.

### `unpack_logo.rect_dimensions`

```python
rect_dimensions(rect: list[xml.etree.ElementTree.Element]) -> list[tuple[float, float]]:
```

Fetch the dimensions of all `rect` objects.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`list[tuple[float, float]]`\]: List of (width, height) pairs.

### `unpack_logo.calculate_average_gap`

```python
calculate_average_gap(rect: list[xml.etree.ElementTree.Element]) -> float:
```

Calculate an average for the gap between `rect` objects.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`float`\]: Averaged gap size between `rect` objects, as inferred from the bear.

### `unpack_logo.calculate_figure_center`

```python
calculate_figure_center(
    rect: list[xml.etree.ElementTree.Element],
) -> tuple[float, float]:
```

Calculate the center of the figure.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`tuple[float, float]`\]: Coordinates (x, y) of the center.

**Notes**

We should not need to use the y component of the center down here.

### `unpack_logo.calculate_unpacked_width`

```python
calculate_unpacked_width(rect: list[xml.etree.ElementTree.Element]) -> float:
```

Calculate the maximum width when unpacking the bear.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`float`\]: Total width of the SVG after unpacking the bear.

### `unpack_logo.animate_svg`

```python
animate_svg(
    tree: xml.etree.ElementTree.ElementTree,
) -> xml.etree.ElementTree.ElementTree:
```

Update the dimensions of the SVG object and add the animation.

**Parameters**

- `tree` \[`list[xml.etree.ElementTree.ElementTree]`\]: The XML tree parsed from the SVG
  definition.

**Returns**

- \[`list[xml.etree.ElementTree.ElementTree]`\]: Updated tree.
