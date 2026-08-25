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
5. Implement only the smallest current milestone and preserve the canonical
   Wenu pipeline and responsibility boundaries.
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
