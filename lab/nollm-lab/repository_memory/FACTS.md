# Committed structural facts

`python facts.py --repo REPO --rev REV --out NEW_DIRECTORY` compiles the selected Git commit without executing the target. Python 3.11+ and Git are required. Matching immutable output directories can be reused. Existing directories containing a different build are preserved.

Every JSONL object represents a structural observation. `manifest.json` supplies the format version, compiler revision, commit, counts and table digests. Git paths and identifiers use JSON escapes including surrogate escape for non-UTF-8 path bytes. Reconstruct any citation from `git cat-file blob <blob>` and its recorded path. Physical lines are one-based. The inventory includes symlinks and Git links with their tree mode and object id. Git links have a commit object id and null byte count.

| Table | Identity, fields and scope |
|---|---|
| files.jsonl | One path per tracked Git tree entry. `parent` gives containment. `lang` is a filename hint. `parse` distinguishes inventory-only, Python AST, C-family lexical scanning, CMake literal scanning and syntax errors. |
| symbols.jsonl | A declaration key is the tuple `(path,line,kind,qualname)`. Python class/function nodes include end lines. C-family candidate records report only the header line or type line. The scanner recognizes explicit CMake target names. |
| edges.jsonl | `src,dst,src_blob,dst_blob,line,rel,token,confidence` describe a syntactic relation and evidence. Relative Python base imports are resolved from the owning file. Explicit absolute names match the repository root and its conventional src-layout projection. Multiple local matches remain candidates. Member imports remain candidates because a package may instead supply an attribute or re-export. |
| diagnostics.jsonl | Syntax error types and unresolved static import/include tokens. They leave known node and edge tables usable for other files. |

An exact edge means that the construct and a unique matching file occur under the declared static resolution rules. A quoted direct local header include and an unambiguous Python module import are examples. Build flags, conditional branches, dependency injection, module initialization, dynamically generated paths, environment-specific include/search roots and runtime object identity require further evidence. Include suffix matches remain candidates even when only one suffix matches. CMake literal source edges in direct target declarations refer to the directory of the committed CMakeLists.txt; target_sources or imported CMake fragments remain candidates. Unparsed languages retain path and blob identity. The compiler emits identifiers and structured path evidence, omitting code bodies, comments and documentation prose.

## Additional language profiles in compiler revision 5

Each witness is anchored by Git blob and physical line. The file's `parse` value selects the parser profile. Candidate declaration kinds end in `_candidate`. Asset edges carry an explicit candidate confidence.

| Profile | Witness and scope | Confidence |
|---|---|---|
| js_lexical | Named JavaScript function/class declaration at a statement boundary, including exported, async and generator forms. Shields comments, strings, regex contexts and nested templates. Direct arrow initializers of ASCII-identifier const/let/var declarators have their own js_arrow_binding_candidate predicate, including comma-separated lists and async arrows. Class members, assignments to existing names, wrapped initializer expressions and callback arguments are outside this predicate. | lexical candidate |
| ps_lexical | PowerShell function/filter/workflow/class/enum name followed by a parameter list, base class or body. Skips comments, nested block comments, strings and here-strings. | lexical candidate |
| sql_lexical | Object identifier in a top-level CREATE statement, including schema-qualified and conventional quoted names. Masks comments, string literals and dollar-quoted bodies. The profile recognizes common DDL syntax without selecting a database engine. | lexical candidate |
| html_parser | HTMLParser start-tag ID attributes with simple names and physical attribute lines. Script src / stylesheet href edges require a directly resolvable relative file and no document base override. | attribute or path candidate |
| css_lexical | A named custom property declaration, @property or @keyframes, after shielding comments and literals. | lexical candidate |

A parsed file may contribute zero declarations. In particular, an entrypoint can consist entirely of executable statements or imported/anonymous callbacks. Remaining tracked files always retain path, object ID and parse status.
