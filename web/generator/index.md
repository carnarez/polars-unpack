Paste and edit JSON content in the field below to get a _rough_ guess at what the
associated schema would look like. If a key is found twice in the JSON content a
suggestion for renaming is provided (based on the complete path to the key; syntax is
`attribute=renamed_attribute: datatype`).

_Quick note about JSON lists:_ `Polars` _expects the_ same _datatype for the entirety of
the latter, and only its_ first _item is checked; guessing the right datatype can be
hazarduous then, floats can be interpreted as integers for instance (if the first float
of the list is truncated from its null decimal place)._

%[unpack](/generator/script.js)
