# unvibecode-impact-prototype

[![Tests](https://github.com/aaranarc/unvibecode-impact-prototype/actions/workflows/test.yml/badge.svg)](https://github.com/aaranarc/unvibecode-impact-prototype/actions/workflows/test.yml)

A ~140-line prototype of a proposed `unvibecode impact <file>` command: **before you change a file, see who depends on it, and how far to trust that answer.**

Built for the UnvibeCode Engineering Challenge 2026 (Cohort 3, Track 2). It is a standalone script that only **reads output files UnvibeCode already writes**. It contains no UnvibeCode source code, does not modify the tool, and makes no network calls.

## What it prints

- direct dependents (files that import this file) and 2-hop dependents
- fan-in rank, and a "heavily depended-on" flag for the top 10% (repos with 10+ such files)
- unresolved non-stdlib imports inside the file
- low-confidence links (`stem_fallback` or confidence not `high`)
- a warning when `import <this module>` was left unresolved or linked to a different file, so the count may be too low (for example the src/ layout problem in UnvibeCode issue #308)
- estimated tokens and file count for the existing radius-1 AI context selection, compared with the whole repo (ZIP input with `selections.jsonl`)
- a Markdown block to paste into a pull request ("Impact checked with UnvibeCode")

## Run it

Requires Python 3.10+ (standard library only) and one UnvibeCode run.

```bash
pip install unvibecode            # tested with 0.3.15
python -m unvibecode review --repository ./flask

# Input A: the context ZIP, which stays in ./unvibecode_results
python impact_prototype.py unvibecode_results/flask-unvibecode-analysis-*/flask-repository-context.zip src/flask/app.py

# Input B: the resolved graph (more detail: has resolution strategy). Its temp path is printed in
# unvibecode_results/<run>/technical-logs/connected_code_map.log ("Resolved JSON ..."). UnvibeCode
# deletes it after a COMPLETE run, so copy it first if you want it.
python impact_prototype.py shipreadyv2_resolved_graph.json src/flask/app.py
```

Tests (synthetic fixture graph, no UnvibeCode needed):

```bash
python -m unittest -v
```

## Sample output (pallets/flask 3.1.2, UnvibeCode 0.3.15)

Full files are in [`sample_output/`](sample_output/). About 0.03 s per query on a 2.2 MB graph (MacBook Air, macOS 26).

`src/flask/app.py` (from a fresh local fast-lane context ZIP, Flask 3.1.2, checked 2026-11-05):

```text
impact: src/flask/app.py   (module `flask.app`; input: shipready_complete_repository_context.zip flask-3.1.2)
AI context: radius 1 = 44,995 est. tokens (10 files) vs 238,974 for the whole repo (UnvibeCode's estimates)

Direct dependents: 25   fan-in rank 2 of 32 files with any dependents  << heavily depended-on
  examples/celery/src/task_app/__init__.py
  examples/javascript/js_example/__init__.py
  examples/tutorial/flaskr/__init__.py
  src/flask/__init__.py
  src/flask/cli.py
  src/flask/ctx.py
  src/flask/globals.py
  src/flask/sessions.py
  src/flask/templating.py
  src/flask/testing.py
  tests/conftest.py
  tests/test_apps/blueprintapp/__init__.py
  tests/test_apps/cliapp/app.py
  tests/test_apps/cliapp/factory.py
  tests/test_apps/cliapp/importerrorapp.py
  tests/test_apps/cliapp/inner1/__init__.py
  tests/test_apps/cliapp/inner1/inner2/flask.py
  tests/test_apps/cliapp/multiapp.py
  tests/test_apps/helloworld/hello.py
  tests/test_async.py
  tests/test_cli.py
  tests/test_request.py
  tests/type_check/typing_app_decorators.py
  tests/type_check/typing_error_handler.py
  tests/type_check/typing_route.py

Indirect dependents (2 hops): 37
  examples/celery/src/task_app/views.py
  examples/javascript/js_example/views.py
  examples/javascript/tests/test_js_example.py
  examples/tutorial/flaskr/auth.py
  examples/tutorial/flaskr/blog.py
  examples/tutorial/flaskr/db.py
  examples/tutorial/tests/test_auth.py
  src/flask/__main__.py
  src/flask/blueprints.py
  src/flask/debughelpers.py
  src/flask/helpers.py
  src/flask/json/__init__.py
  src/flask/logging.py
  src/flask/sansio/app.py
  src/flask/sansio/scaffold.py
  src/flask/views.py
  src/flask/wrappers.py
  tests/test_appctx.py
  tests/test_apps/blueprintapp/apps/admin/__init__.py
  tests/test_apps/blueprintapp/apps/frontend/__init__.py
  tests/test_apps/helloworld/wsgi.py
  tests/test_apps/subdomaintestmodule/__init__.py
  tests/test_basic.py
  tests/test_blueprints.py
  tests/test_config.py
  tests/test_converters.py
  tests/test_helpers.py
  tests/test_instance_config.py
  tests/test_json.py
  tests/test_regression.py
  tests/test_reqctx.py
  tests/test_session_interface.py
  tests/test_signals.py
  tests/test_subclassing.py
  tests/test_templating.py
  tests/test_testing.py
  tests/test_user_error_handler.py

Unresolved imports inside this file: 13  ., .globals, .sansio.scaffold, .signals, .typing, _typeshed.wsgi, asgiref.sync, click, werkzeug.datastructures, werkzeug.exceptions, werkzeug.routing, werkzeug.serving, werkzeug.wsgi

Low-confidence links touching this file (stem_fallback or not 'high'): 22
  tests/type_check/typing_error_handler.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  examples/javascript/js_example/__init__.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_apps/helloworld/hello.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  src/flask/app.py -> src/flask/wrappers.py  [file_import, medium, strategy n/a in ZIP]
  src/flask/app.py -> src/flask/typing.py  [imports_module, medium, strategy n/a in ZIP]
  src/flask/app.py -> src/flask/typing.py  [file_import, medium, strategy n/a in ZIP]
  src/flask/app.py -> tests/test_apps/helloworld/wsgi.py  [file_import, medium, strategy n/a in ZIP]
  tests/test_apps/cliapp/multiapp.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_cli.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_apps/cliapp/importerrorapp.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_apps/blueprintapp/__init__.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/conftest.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  examples/tutorial/flaskr/__init__.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_apps/cliapp/inner1/inner2/flask.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]
  tests/test_apps/cliapp/inner1/__init__.py -> src/flask/app.py  [imports_symbol, medium, strategy n/a in ZIP]

--- PR description block ---
### Impact checked with UnvibeCode

`src/flask/app.py`: **25 direct** / **37 indirect (2-hop)** dependents.

- examples/celery/src/task_app/__init__.py
- examples/javascript/js_example/__init__.py
- examples/tutorial/flaskr/__init__.py
- src/flask/__init__.py
- src/flask/cli.py
- src/flask/ctx.py
- src/flask/globals.py
- src/flask/sessions.py
- src/flask/templating.py
- src/flask/testing.py
- ... and 15 more

**Check before merging:** heavily depended-on (fan-in rank 2/32); 22 low-confidence link(s); 13 unresolved import(s) inside the file.

<sub>Generated by `unvibecode impact` (prototype) from the local Connected Code Map. Static imports only; not a test result.</sub>
```

`src/flask/__init__.py` shows how the tool reports a weak answer instead of a silent 0:

```text
impact: src/flask/__init__.py   (module `flask`; input: flask_shipreadyv2_resolved_graph.json 2026-11-01T10:42:14)
Direct dependents: 0
Indirect dependents (2 hops): 0
WARNING: dependents may be undercounted. `import flask` appears 0x unresolved and 78x linked to other files (tests/test_apps/cliapp/inner1/inner2/flask.py).
```

## Limits (honest)

- Static imports only. Dynamic imports, string-based loading, templates and runtime wiring are not counted.
- The answer is only as good as UnvibeCode's graph: in this Flask graph 171 of 352 file edges are `stem_fallback` name guesses. The tool flags them but does not fix them.
- Reads internal file formats (`schema_version` of the resolved graph) that may change between UnvibeCode versions.
- The proposed `--copy` and `--pr` flags and graph caching are not implemented here. The PR block is printed only.
- Tested on Python repositories up to 105 files on one Mac.

## License

MIT. See [LICENSE](LICENSE).
