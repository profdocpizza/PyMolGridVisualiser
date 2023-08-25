# Installation Guidelines

## Prerequisites

- Python 3.x
- pip (Python package manager)
- Anaconda

## Simple installation

1. Ensure you have Python and Anaconda installed on your system.
2. Clone this repository: `git clone https://github.com/yourusername/PyMolGridVisualiser.git`
3. Navigate into the project directory: `cd PyMolGridVisualiser`
4. Install the required Python packages:
    ```
    conda env create -f environment.yml
    ```
    If this step is taking too long, try Alternative Installation below.


## Alternative Installation
1. Clone this repository: `git clone https://github.com/yourusername/PyMolGridVisualiser.git`
2. Navigate into the project directory: `cd PyMolGridVisualiser`
4. Create conda environment:
    ```
    conda create --name pymolgrid python=3.8.17
    ```
5. Activate conda environment:
    ```
    conda activate pymolgrid
    ```
6. Install image and PDF processing libraries from conda-forge channel:
    ```
    conda install -c conda-forge fpdf=1.7.2 pillow=9.4.0 pypdf2=1.26.0
    ```
7. Install pymol from schrodinger channel:
    ```
    conda install -c schrodinger pymol=2.4.1
    ```

That's it! You're now set up and ready to convert PDB files into grid-based PDF visualisations.
