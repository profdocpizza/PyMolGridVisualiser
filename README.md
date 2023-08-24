# PyMolGridVisualizer

PyMolGridVisualizer is a Python tool designed to generate PDF visualizations of PDB files in a grid layout. Utilizing PyMOL, this tool makes it easier to visualize multiple protein structures at once.

## Table of Contents

- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [FAQ](docs/faq.md)

## Quick Start

To quickly get started with PyMolGridVisualizer:

1. Clone this repository:
    ```
    git clone https://github.com/profdocpizza/PyMolGridVisualizer.git
    ```

2. Navigate to the PyMolGridVisualizer directory:
    ```
    cd PyMolGridVisualizer
    ```

3. Install the required packages using Anaconda:
    ```
    conda env create -f environment.yml
    ```

4. Activate the environment:
    ```
    conda activate pymolgrid
    ```

5. Run the tool on sample PDB files:
    ```
    python src/protein_visualiser.py examples/
    ```

For detailed usage instructions, visit the [Usage Guide](docs/usage.md).
