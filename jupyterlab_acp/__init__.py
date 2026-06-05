"""jupyterlab-acp: Jupyter-native access to coding agents over the Agent Client Protocol."""

__version__ = "0.0.1"


def _jupyter_server_extension_points():
    from .extension import AcpExtension

    return [{"module": "jupyterlab_acp.extension", "app": AcpExtension}]


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "jupyterlab-acp"}]
