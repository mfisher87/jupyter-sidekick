"""
Live Step 0 validation.

Question: when an ACP harness edits a notebook on disk, does that reflect into
the live YDoc that connected JupyterLab clients are viewing -- and does it
happen via the autonomous background watcher (not a manual poke)?

Faithful simulation: a harness's entire effect on a notebook is an on-disk
file write. So we drive the REAL jupyter-server-documents document layer
(AsyncFileContentsManager + ArbitraryFileIdManager + OutputsManager +
YRoomFileAPI), load a notebook into a live YDoc, then write a modified .ipynb
to disk out-of-band and WAIT -- letting the real _watch_file() poll loop detect
and reload it. We observe the underlying pycrdt Doc to confirm a diff (the thing
broadcast to connected clients) is actually produced.
"""
import asyncio
import os
import tempfile

import pycrdt
import nbformat
from nbformat.v4 import new_notebook, new_code_cell
from jupyter_server.services.contents.filemanager import AsyncFileContentsManager
from jupyter_server_fileid.manager import ArbitraryFileIdManager
from jupyter_ydoc import YNotebook
from traitlets.config import LoggingConfigurable

from jupyter_server_documents.rooms import YRoomFileAPI
from jupyter_server_documents.outputs.manager import OutputsManager


def cell_sources(ydoc: YNotebook):
    return [c.get("source", "") for c in ydoc.source.get("cells", [])]


async def main():
    results = []
    tmp = tempfile.mkdtemp(prefix="step0_")
    nb_path = os.path.join(tmp, "analysis.ipynb")

    # --- initial notebook on disk (the "before" state) ---
    nbformat.write(new_notebook(cells=[new_code_cell('print("before")')]), nb_path)

    cm = AsyncFileContentsManager(root_dir=tmp, use_atomic_writing=False)
    fim = ArbitraryFileIdManager(db_path=os.path.join(tmp, "fileid.db"))
    om = OutputsManager()

    file_id = fim.index("analysis.ipynb")
    room_id = f"json:notebook:{file_id}"

    class MockYRoom(LoggingConfigurable):
        @property
        def fileid_manager(self): return fim
        @property
        def contents_manager(self): return cm
        @property
        def outputs_manager(self): return om
        @property
        def room_id(self): return room_id

    file_api = YRoomFileAPI(parent=MockYRoom())

    # live YDoc that "connected clients" share; observe the underlying Doc so we
    # can count the diffs that would be broadcast over the websocket.
    doc = pycrdt.Doc()
    awareness = pycrdt.Awareness(ydoc=doc)
    ydoc = YNotebook(doc, awareness)

    updates = {"n": 0}
    sub = doc.observe(lambda event: updates.__setitem__("n", updates["n"] + 1))

    try:
        # --- load: client opens the notebook ---
        file_api.load_content_into(ydoc)
        await file_api.until_content_loaded
        before = cell_sources(ydoc)
        results.append(("notebook loaded into live YDoc", before == ['print("before")'], before))
        updates_after_load = updates["n"]

        # --- simulate the harness: write a 2nd cell to the .ipynb on disk ---
        edited = new_notebook(cells=[
            new_code_cell('print("before")'),
            new_code_cell('print("after -- added by simulated harness")'),
        ])
        nbformat.write(edited, nb_path)
        # guarantee last_modified strictly advances regardless of fs mtime resolution
        bump = os.path.getmtime(nb_path) + 10
        os.utime(nb_path, (bump, bump))
        results.append(("harness wrote out-of-band edit to disk", True, "2 cells on disk"))

        # --- DO NOT poke the file_api. Wait for the autonomous _watch_file loop. ---
        deadline = 6.0
        waited = 0.0
        while waited < deadline:
            await asyncio.sleep(0.25)
            waited += 0.25
            if len(cell_sources(ydoc)) >= 2:
                break

        after = cell_sources(ydoc)
        diffs = updates["n"] - updates_after_load
        results.append((f"live YDoc reflected the edit within {waited:.2f}s (autonomous poll)",
                        len(after) == 2, after))
        results.append(("a broadcast-worthy diff was produced (Doc update fired)",
                        diffs >= 1, f"{diffs} doc update(s) after edit"))
        results.append(("added cell content is present",
                        any("added by simulated harness" in s for s in after), None))
    finally:
        file_api.stop()
        try:
            doc.unobserve(sub)
        except Exception:
            pass

    print("\n=== Live Step 0 results ===")
    ok = True
    for name, passed, detail in results:
        ok = ok and passed
        line = f"[{'PASS' if passed else 'FAIL'}] {name}"
        if detail is not None:
            line += f"\n        -> {detail}"
        print(line)
    print("\nOVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
