import papermill as pm
from pathlib import Path
import logging
import subprocess
import yaml
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("-f", "--parameters_file", action="store",
                    help="Path to the YAML parameters file")
args = parser.parse_args()


logger = logging.getLogger()

def print_notebooks_to_build(workflow_stages):
    """
    pretty-print the list of notebooks that will be considered

    Parameters
    ----------
    workflow_stages: Dict[str, List[Path]]
        dictionary of workflow stage name mapped to list of notebooks within it. 
    """
    print("======== BUILDING: ===========")
    for directory, files in workflow_stages.items():
        print(directory, ":")
        for nb in files:
            print(" - ", nb)

def build_notebooks(stage, notebook_paths, build_dir, parameters={}):
    """ 
    Build a list of notebooks

    Parameters
    ----------
    stage: str
        name of stage (just for identification purposes)
    notebook_paths: List[Path]
        list of paths to notebooks
    build_dir: Path
        path to top-level of output directory
    """
    logger.info("Building Stage '%s'", stage)
    for path in notebook_paths:
        output_path = build_dir/path
        output_path.parents[0].mkdir(parents=True, exist_ok=True)
        logger.debug("Created %s", path.parents[0])
        try:
            pm.execute_notebook(
                str(path),
                str(output_path),
                parameters = parameters,
            )
        except:
            logging.debug("Notebook {} not run".format(path))

def convert_notebooks(stage, notebook_paths, build_dir, fmt='html'):
    """
    Convert notebooks into another format using nbconvert

    Parameters
    ----------
    stage: str
        name of stage (just for identification purposes)
    notebook_paths: List[Path]
        list of paths to notebooks
    build_dir: Path
        path to top-level of output directory
    fmt: str
        output format supported by nbconvert
    """
    logger.info("Converting notebooks in stage {} into {}".format(stage, fmt))
    for path in notebook_paths:
        cmd = "jupyter nbconvert --to {} {}".format(fmt, build_dir/path)
        try:
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            logger.info("Converted {} in {}".format(path.parents[0], fmt))
        except:
            logger.debug(("{} not converted in {}".format(path.parents[0], fmt)))


def read_parameters_file(filename):
    """
    Read a YAML file with parameters for the notebooks

    Parameters
    ----------
    filename: str
        path to the file

    Returns
    -------
    dictionnary of the parameters
    """
    with open(filename) as file:
        parameters = yaml.load(file, Loader=yaml.SafeLoader)
    return parameters

            
if __name__ == '__main__':

    build_dir = Path("BUILD")
    build_dir.mkdir(exist_ok=True)

    logging_filename = build_dir/"logs.txt"
    logging.basicConfig(level=logging.DEBUG,
                        filename=logging_filename,
                        filemode="w",
                        )

    logging.info("Build directory:", build_dir.resolve())
    
    dirs_to_build = ['Preparation', 'Benchmarks', 'Summaries']

    workflow_stages = {x: [path for path in Path(f'./{x}').rglob("*.ipynb")
                           if '.ipynb_checkpoints' not in path.parts]
                       for x in dirs_to_build}
    print_notebooks_to_build(workflow_stages)

    if args.parameters_file is not None:
        parameters = read_parameters_file(args.parameters_file)
    else:
        parameters = {}

    for stage, paths in workflow_stages.items():
        build_notebooks(stage, paths, build_dir, parameters=parameters)
        convert_notebooks(stage, paths, build_dir)
