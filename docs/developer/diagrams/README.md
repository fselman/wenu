# UML Diagrams

These diagrams are generated automatically from the source code using
`pyreverse`.

They describe the current implementation and should not be edited manually.

To regenerate:

```bash
cd wenu
pyreverse src/wenu
dot -Tsvg classes.dot -o classes.svg
dot -Tsvg packages.dot -o packages.svg
```

These diagrams complement, but do not replace,

- `current_architecture.md`
- `implementation_reference.md`

because UML shows the static structure but not the runtime execution flow.
