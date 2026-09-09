# Reproducible test entry and admission rules (Milestone 49J.3A)

**Status:** Verification complete; awaiting Fernando's review  
**Implementation baseline:** `fd0b262`  
**Runtime effect:** None  
**Test behavior effect:** None

## 1. Purpose

49J.3A installs the first accepted 49J.2 policies in current contributor
documentation:

1. Wenu test commands disable ambient pytest-plugin autoload;
2. every new test must identify its distinct contract or fault model and its
   closest existing coverage; and
3. current architecture text accurately describes the fixture topology.

This slice changes no test selection, marker, fixture, assertion, runtime code,
cache, output, or timing. It cannot claim a performance improvement.

## 2. Reproducible entry

The documented routine, integration, visual, and complete gates all use:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
```

Selections and options follow that prefix. Ambient plugins are therefore not
part of Wenu's test environment. Any future required plugin must be explicitly
loaded, version constrained, documented, and accepted in a separate milestone.

The rule responds directly to the accepted 49J.1 observation: pytest 9.1.1
failed before collection when it automatically loaded the incompatible
environmental `pytest_filter_subpackage` plugin. Disabling autoload produced
six successful measurement runs.

## 3. New-test admission

Before adding a test, its author and reviewer must answer:

1. What new contract, boundary, or fault does this test protect?
2. Which existing test is closest, and why is extending or parametrizing it
   insufficient?
3. Does the new capability change lower-level behavior, or merely compose
   functionality that is already tested?
4. Can a new assertion inspect an existing immutable generated artifact
   without obscuring ownership or independence?
5. Which marker and gate describe the work actually performed?

A capability that merely uses accepted functionality does not repeat all
lower-level tests. It normally adds evidence for the new request mapping,
integration seam, composition or ordering, provenance, state isolation,
boundary conditions, and failures newly possible at that seam.

Repeating a lower-level or complete-path test requires one explicit reason:

- the new context changes inputs, invariants, numerical tolerance, ownership,
  or failure modes;
- a distinct public entry route must remain independently exercised;
- a scientific result must be independently recomputed against its oracle;
- cold state or order independence is the contract; or
- the repeated path detects another named fault that existing coverage cannot.

If none applies, extend or parameterize the closest existing contract instead
of adding another full path.

## 4. Documentation corrections

The current suite has module-scoped reusable-sphere fixtures but no
session-scoped fixture and no `tests/conftest.py`. Earlier source-tree language
claiming an implemented session registry was corrected in 49J.2. Current
architecture now records that correction rather than describing it as pending.

The accepted 49J.2 policy permits a future narrowly keyed session registry
only after the required immutability, teardown, order, isolation, and retained
cold-builder proofs. 49J.3A does not implement it.

## 5. Acceptance

Acceptance requires:

- every current non-historical test command to use the isolated prefix;
- contribution instructions to contain the five admission questions and the
  lower-level reuse rule;
- current architecture and source-tree descriptions to agree with committed
  fixtures;
- developer-root inventory and documentation-contract tests to pass; and
- confirmation that no test or runtime file changed except the documentation
  contract protecting these rules.

The coordinate-system guide was reviewed. This milestone changes no scientific
meaning, provenance, ownership, or public coordinate explanation, so the guide
remains current.

Final focused Mac verification passed all 83 current-documentation tests in
2.12 seconds.
