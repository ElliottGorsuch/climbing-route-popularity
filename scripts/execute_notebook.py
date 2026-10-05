"""Execute the EDA notebook using this Python environment and temporary kernel files."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import AsyncKernelManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "notebooks/02_popularity_eda.ipynb"
    previous = {
        key: os.environ.get(key)
        for key in ["JUPYTER_PATH", "JUPYTER_RUNTIME_DIR", "IPYTHONDIR"]
    }
    with tempfile.TemporaryDirectory(
        prefix="climbing-notebook-", dir="/private/tmp"
    ) as temporary:
        directory = Path(temporary)
        kernel = directory / "kernels/python3"
        kernel.mkdir(parents=True)
        (kernel / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        sys.executable,
                        "-m",
                        "ipykernel_launcher",
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": "Python 3 (project environment)",
                    "language": "python",
                }
            )
        )
        os.environ["JUPYTER_PATH"] = str(directory)
        os.environ["JUPYTER_RUNTIME_DIR"] = str(directory / "runtime")
        os.environ["IPYTHONDIR"] = str(directory / "ipython")
        try:
            notebook = nbformat.read(path, as_version=4)
            manager = AsyncKernelManager(
                kernel_name="python3", transport="ipc", ip=str(directory / "kernel")
            )
            client = NotebookClient(
                notebook,
                km=manager,
                timeout=240,
                kernel_name="python3",
                resources={"metadata": {"path": str(ROOT)}},
            )
            try:
                client.execute()
            finally:
                asyncio.run(manager.shutdown_kernel(now=True))
            nbformat.write(notebook, path)
            for cell in notebook.cells:
                for output in cell.get("outputs", []):
                    if output.output_type == "error":
                        raise RuntimeError(output.evalue)
                    if (
                        output.output_type == "stream"
                        and "warning" in output.get("text", "").lower()
                    ):
                        raise RuntimeError("Notebook emitted a warning: " + output.text)
            print(
                f"Executed {sum(c.cell_type == 'code' for c in notebook.cells)} code cells with no errors or warning output"
            )
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    main()
