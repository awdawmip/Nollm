# Packaging

Release archives must use POSIX-style `/` path separators.

Valid archive entry:

```text
nollm/reference/python/nollm/cli.py
```

Invalid archive entry:

```text
nollm\reference\python\nollm\cli.py
```

Recommended packaging paths:

- Use the GitHub source zip.
- Use `git archive`.
- Use a Python zip creation script that writes archive names with `Path.as_posix()`.

If a helper script is added later, it must use only the Python standard library unless the project explicitly accepts a packaging dependency.

