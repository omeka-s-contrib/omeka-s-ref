# omeka-s-ref

The `o-ref` namespace: two terms that identify and link Omeka S resources by a property value
instead of by internal id, so records can move between installations.

**Namespace:** `https://omeka-s-contrib.github.io/omeka-s-ref/ns#` (prefix `o-ref`)

| Term | Where | Meaning |
|---|---|---|
| `o-ref:id` | top level of a record | This record's own identity, used to find an existing copy (duplicate check) |
| `o-ref:ref` | where Omeka puts `{"o:id": …}` (`o:item_set`, a resource value) | A link to another record, resolved to that record's id on import |

Both take one property and one value:

```json
"o-ref:id": {"dcterms:identifier": "obj-1"},
"o:item_set": [{"o-ref:ref": {"dcterms:identifier": "set-paintings"}}]
```

The [namespace page](https://omeka-s-contrib.github.io/omeka-s-ref/ns) explains the matching rules,
with an example. Machine-readable: [Turtle](https://omeka-s-contrib.github.io/omeka-s-ref/ns.ttl),
[JSON-LD](https://omeka-s-contrib.github.io/omeka-s-ref/ns.jsonld),
[RDF/XML](https://omeka-s-contrib.github.io/omeka-s-ref/ns.rdf).

Used by [Omeka-S-Cli](https://github.com/GhentCDH/Omeka-S-Cli) (`item:export`, `item:import`).

## Stability

- The namespace URI never changes. Terms are only added, never removed or redefined.
- Each change bumps `owl:versionInfo` in `ns.ttl` (and the version on `ns.html`) and gets a git tag.

## Repository

- `ns.ttl`: the source of truth.
- `ns.html`: the page served at the namespace URI. Its inlined JSON-LD must say the same as `ns.ttl`;
  after changing `ns.ttl`, regenerate it with
  `python -c "import build, rdflib; print(rdflib.Graph().parse('ns.ttl').serialize(format='json-ld', context=build.CONTEXT, indent=2))"`.
- `index.html`: the landing page.
- `build.py`: writes the site to `_site/` (`ns.jsonld` and `ns.rdf` generated from `ns.ttl`), and
  fails when `ns.html` lacks an anchor for a term or its JSON-LD differs from `ns.ttl`.
- `.github/workflows/pages.yml`: runs `build.py` and deploys to GitHub Pages from `main`.

Run the tests locally:

```bash
python -m venv .venv
.venv/bin/pip install rdflib pyld pytest pyyaml
.venv/bin/pytest
```

## License

[MIT](LICENSE)
