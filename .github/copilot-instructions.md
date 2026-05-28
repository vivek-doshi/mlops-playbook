# Copilot Instructions

Use the repository intelligence in `.ai/` as the primary source of truth for architecture, standards, and routing.

Required behavior:

1. Read relevant files in `.ai/context/`, `.ai/instructions/`, and `.ai/retrieval/` before proposing structural changes.
2. Preserve the Integration Bridge principle:
   The two repos are not islands. You create a deliberate, documented dependency.
3. Record every substantial chat outcome as a dated summary in `.ai/session/`.
4. Reuse and keep existing skills in `.ai/skills/` intact.
5. Prefer repository golden paths before introducing new conventions.
