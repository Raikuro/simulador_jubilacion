# Configuration Precedence

Every setting in `sim-retire` resolves through a three-level precedence
hierarchy:

```
CLI flags  >  Configuration file  >  Built-in defaults
```

Explicit command-line flags always win. If a value is not supplied on the
command line, the configuration file is consulted. If it is absent there,
the built-in default applies.

## Rules

1. **Highest:** CLI flags passed directly to the command, e.g.
   `run --workers 2 --format sqlite`.
2. **Middle:** Values from the active configuration file (the `--config`
   file, or `~/.sim-retire/config.yaml` by default).
3. **Lowest:** Built-in defaults compiled into the CLI.

## Concrete example

Given `examples/configs/config.yaml`:

```yaml
execution:
  default_workers: 4
```

| Invocation | Effective `workers` |
|------------|---------------------|
| `sim-retire run study.yaml` | `4` (from config) |
| `sim-retire --config other.yaml run study.yaml` | whatever `other.yaml` sets, or the default |
| `sim-retire run study.yaml --workers 8` | `8` (CLI wins) |

Only the value that is *not* supplied falls through to the next level — it is
not a complete override. Settings provided on the CLI for one command do not
change the file; they affect only that invocation.

## How it is applied in `run`

`run` resolves its execution defaults before parsing the study:

1. `--workers` given → use it; otherwise read `execution.default_workers`.
2. `--format` given → use it; otherwise read `output.default_format`.
3. `--output-dir` given → use it; otherwise read `output.default_directory`.

If the configuration file is missing or malformed, it degrades to defaults
and the command proceeds — with an appropriate error only from commands that
explicitly validate configuration, such as `config validate`.

## Where the configuration file comes from

The active file is resolved in this order:

1. The `--file FILE` option of `config validate` / subcommands that accept it.
2. The `--config FILE` global option.
3. The default `~/.sim-retire/config.yaml`.

## See also

- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) — every configuration key.
- [CLI_USAGE.md](CLI_USAGE.md) — command arguments.