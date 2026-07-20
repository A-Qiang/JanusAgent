"""JanusAgent inference service — unified model serving over SGLang / vLLM."""

__version__ = "0.1.0"


def hello() -> str:
    return f"Hello from inference-service v{__version__}"


def main() -> None:
    print(hello())
