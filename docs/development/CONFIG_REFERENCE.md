# Configuration Reference

The `sim-retire` CLI is configured through a YAML file. By default it reads
`~/.sim-retire/config.yaml`; use `--config FILE` to select another file.

## File structure

```yaml
database:
  path: ~/.sim-retire/studies.db

output:
  default_format: csv
  default_directory: ./results/

execution:
  default_workers: 4

logging:
  level: INFO
```

## Sections

### `database`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | `~/.sim-retire/studies.db` | SQLite database path |

### `output`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_format` | string | `csv` | Default output format for `run` |
| `default_directory` | string | `./results/` | Default output directory for `run` |

### `execution`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_workers` | integer | `1` | Default parallel workers for `run` |

### `logging`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `level` | string | `INFO` | Logging verbosity |

## Validation

Validate the effective configuration without running a study:

```bash
sim-retire config validate
```

Validate a specific file:

```bash
sim-retire config validate --file /path/to/config.yaml
```

## Reading and writing values

View the full effective configuration:

```bash
sim-retire config list
```

Read a single key:

```bash
sim-retire config get output.directory
```

Set a key and persist it to the active configuration file:

```bash
sim-retire config set execution.default_workers 8
```

## See also

- [CONFIG_PRECEDENCE.md](CONFIG_PRECEDENCE.md) — how CLI flags, config, and
  defaults combine.
- [CLI_USAGE.md](CLI_USAGE.md) — every command and its options.
- [`examples/configs/config.yaml`](../../examples/configs/config.yaml) — a
  runnable example configuration.