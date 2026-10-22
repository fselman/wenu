# Wenu agent instructions

Before inspecting, planning, modifying, reviewing, or packaging any Wenu work,
read `docs/developer/assistant_instructions.md` completely and follow it as the
governing repository procedure.

In particular:

1. Treat the Git repository, not conversational memory, as the source of
   truth.
2. Establish the active branch, exact commit, and working-tree status before
   proposing a modification.
3. Read the active architecture, migration, implementation-reference,
   source-tree, future-roadmap, implementation, and test material required by
   the governing instructions. Documents under `docs/developer/archive/` are
   historical evidence, not routine architectural authority.
4. Perform an as-is assessment before changing anything.
5. Follow the [agreed roadmap](docs/developer/kernel_roadmap_v0.9.5.md) strictly,
   identify the selected intermediate milestone ID, and implement only its
   bounded scope. Preserve the canonical Wenu pipeline and responsibility boundaries.
   Treat the state SDK as one component of the broader shared-service kernel;
   geometry/projection consumers use their appropriate public services, not
   artificial object-state queries. Follow the roadmap’s agreed service boundary.
6. Before remote work begins, confirm with the user that the Mac working tree is
   clean and synchronized with the agreed GitHub base. Treat uncommitted local
   work as invisible until the user reports or publishes it.
7. After the user approves a bounded milestone, use a dedicated GitHub branch,
   commit the verified work there, and open or update a pull request for review.
   Do not merge, delete, force-push, or commit directly to `main` without a
   separate explicit request.
8. Guide the user through synchronizing the Mac and running the relevant local,
   scientific, visual, print, or classroom acceptance checks.
9. Use the Finder-safe Mac ZIP patch handoff in
   `docs/developer/assistant_instructions.md` only when direct GitHub delivery
   is unavailable or the user specifically requests a patch.
10. When direct GitHub delivery is available, inspect repository files and make
    repository changes through that connection. Do not ask the user to paste
    repository files or to execute file-editing commands on the assistant's
    behalf.
11. If direct GitHub access is unavailable, stop and state that access is
    unavailable. Do not silently substitute a manual copy-and-paste workflow.
    Use the documented ZIP fallback only when the user specifically requests it
    or direct GitHub delivery is genuinely unavailable.
12. Whenever Fernando must run local shell commands, provide every command in
    complete, copy-and-paste-ready blocks through the chat. Every Wenu command
    block intended for his Mac must begin with a macOS/Darwin check that stops
    all subsequent commands on failure. Fernando also works on wenu-imaging
    on Linux chapman3 and may paste into the wrong terminal. Retain exact Wenu
    repository path and applicable branch/SHA/clean/upstream checks; follow the
    guard pattern in the governing instructions. Never ask him to edit repository
    files manually or compose an error-prone command himself.
13. Give every downloadable file an explicit version number in its filename.
    Increment it when contents change, never rely on automatic `(counter)`
    suffixes, and make accompanying commands reference the exact versioned
    filename. Follow the versioned-file handoff rule in the governing instructions.

14. Any extra item, unlisted prerequisite, scope expansion or change of agreed
    order must be discussed with Fernando, explicitly agreed, and documented in
    the roadmap before implementation. Do not silently add or activate work.
    Follow [roadmap control](docs/developer/assistant_instructions.md#roadmap-control-mandatory-before-implementation).
