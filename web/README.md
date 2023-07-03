# Module `unpack_logo`

Add an unpacking animation to the `Polars` b(e)ar logo.

**Functions**

- [`rect_coordinates()`](#unpack_logorect_coordinates): Fetch the coordinates of all
  `rect` objects.
- [`rect_dimensions()`](#unpack_logorect_dimensions): Fetch the dimensions of all `rect`
  objects.
- [`center()`](#unpack_logocenter): Calculate the center of all `rect` objects.
- [`gap()`](#unpack_logogap): Calculate an average for the gap between `rect` objects.
- [`width()`](#unpack_logowidth): Calculate the maximum width when unpacking the bear.
- [`animate()`](#unpack_logoanimate): Update the dimensions of the SVG object and add
  the animation.

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

### `unpack_logo.center`

```python
center(rect: list[xml.etree.ElementTree.Element]) -> tuple[float, float]:
```

Calculate the center of all `rect` objects.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`tuple[float, float]`\]: Coordinates (x, y) of the center.

**Notes**

We should not need to use the y coordinate of the center in here.

### `unpack_logo.gap`

```python
gap(rect: list[xml.etree.ElementTree.Element]) -> float:
```

Calculate an average for the gap between `rect` objects.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`float`\]: Averaged gap size between `rect` objects, as inferred from the bear.

### `unpack_logo.width`

```python
width(rect: list[xml.etree.ElementTree.Element]) -> float:
```

Calculate the maximum width when unpacking the bear.

**Parameters**

- `rect` \[`list[xml.etree.ElementTree.Element]`\]: List of `Element` objects present in
  the SVG.

**Returns**

- \[`float`\]: Total width of the SVG after unpacking the bear.

### `unpack_logo.animate`

```python
animate(tree: xml.etree.ElementTree.ElementTree) -> xml.etree.ElementTree.ElementTree:
```

Update the dimensions of the SVG object and add the animation.

**Parameters**

- `tree` \[`list[xml.etree.ElementTree.ElementTree]`\]: The XML tree parsed from the SVG
  definition.

**Returns**

- \[`list[xml.etree.ElementTree.ElementTree]`\]: Updated tree.
