# YAML file structure for `boxes_cli generate` / `boxes_cli build`

This project supports a YAML configuration format to describe one or more box generator runs.

There are **two** YAML styles in use:

- The **full format** with `Defaults:` and `Boxes:` (recommended for generating one or many boxes).
- The **single-box export format** (produced by YAML export from the server / CLI export). The loader treats it as a one-item `Boxes:` list.

## Full format (recommended)

```yaml
Defaults:
  # Default arguments applied to every entry in Boxes (can be overridden per box)
  thickness: 3.0
  burn: 0.1
  format: svg

Boxes:
  - box_type: ABox
    name: "abox_example"
    generate: true
    args:
      x: 100
      y: 80
      h: 50
      output: abox.svg

  - box_type: UniversalBox
    name: "uni_1"
    generate: true
    args:
      x: 120
      y: 90
      h: 60
      output: uni.lbrn2
```

### `Defaults:` section

- `Defaults:` is a mapping of **argument defaults** that are applied to **every** entry in `Boxes:`.
- Each box entry then overrides these defaults with its own `args:`.

In other words, for each item in `Boxes:` the effective arguments are:

- Start with `Defaults`
- Overwrite with that box's `Boxes[i].args`

### `Boxes:` section

- `Boxes:` must be a YAML list.
- Each list item describes one generator run.

Each box entry contain:

- `box_type` (required)
- `name` (optional but recommended)
- `generate` (required if you want it generated)
- `args` (optional mapping)

## `box_type`

`box_type` selects which generator class is instantiated.

### How to list valid `box_type` values

Run:

```bash
boxes_cli list generators
```

This prints all available generators. The `box_type` for YAML is the generator class name shown there (for example `ABox`, `UniversalBox`, etc.).

## `name`

`name` is metadata attached to the box instance.

- In `boxes_cli build`, `name` is typically used to build a default output filename when you do not provide `args.output`.
- In the single-box export YAML, `name` is included so the configuration can be identified and reused.

If you want `name` to control output file naming, you should also set `args.output` explicitly.

## `generate`

`generate` controls whether that entry in `Boxes:` should be generated.

- If `generate: false`, the entry is skipped.
- If `generate: true`, the entry is processed.

If you omit `generate` you risk inconsistent behavior depending on the command or loader. For predictable results, **always set**:

```yaml
generate: true
```

for any entry you want to generate.

## `args`

`args:` is a mapping of generator parameters.

Example:

```yaml
args:
  thickness: 3.0
  burn: 0.1
  format: svg
  output: mybox.svg
  x: 100
  y: 80
  h: 50
```

### Output file (`args.output`)

If `args.output` is present, it is used as the output filename.

In `boxes_cli generate`, the output resolution order is:

- If you pass `--output`, it overrides everything (only valid when the YAML produces exactly one box)
- Else if YAML contains `args.output`, that is used
- Else the tool derives a filename from the YAML file name + the chosen format extension

## Single-box export format

Some tools export a single-box YAML in this shape:

```yaml
box_type: ABox
name: "abox_example"
generate: true
args:
  thickness: 3.0
  burn: 0.1
  format: svg
  output: abox.svg
  x: 100
  y: 80
  h: 50
```

The loader accepts this and treats it as if it were:

```yaml
Defaults: {}
Boxes:
  - box_type: ABox
    name: "abox_example"
    generate: true
    args:
      ...
```

## How to discover valid `args` for a given `box_type`

There are two common ways:

### 1) Generate a parameter template file

Use the `parameters` command for a specific generator:

```bash
boxes_cli parameters ABox
```

You can also generate templates for all generators:

```bash
boxes_cli parameters --all
```

These templates show the supported parameters and their default values.

### 2) Export current parameters (commenting defaults)

You can export a YAML file for a generator (optionally after overriding parameters):

```bash
boxes_cli build ABox --export exported.yaml
boxes_cli build ABox --thickness=4 --x=120 --export exported.yaml
```

That exported YAML is suitable input to `boxes_cli generate`.
