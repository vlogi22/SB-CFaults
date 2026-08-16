import os
import shutil
from typing import List, Tuple

from BenchmarkDriver.BenchmarkDriver import BenchmarkDriver
from CoverageCalculator.GcovLineCoverageCalculator import GcovLineCoverageCalculator
from SBFL.SBFL import SBFL, SpectrumCoefficient

class TCASDriver(BenchmarkDriver):
    """Driver for the TCAS benchmark with its specific folder structure."""

    def __init__(self, base_path: str, debug: bool = False):
        super().__init__(base_path, debug)
        self._versions_dir = os.path.join(self._base_path, "versions")
        self._tests_dir = os.path.join(self._base_path, "tests")

        self._results_dir = "./tcas_faulty_programs_results"
        os.makedirs(self._results_dir, exist_ok=True)

        self._debug = debug

    def compile_source(self) -> str:
        """Compile the source code and return the path to the compiled executable.

        Returns:
            The path to the compiled executable
        """

        total_compiled = 0
        total_failed = 0

        # Process version directories
        version_dirs = sorted([d for d in os.listdir(self._versions_dir) if d.startswith('v')])
        for version in version_dirs:
            version_path = os.path.join(self._versions_dir, version)
            # if not os.path.isdir(version_path):
            #     continue

            # Process C files
            version_dirs = [f for f in os.listdir(version_path) if f.endswith('.c')]
            for faulty_program in version_dirs:
                faulty_program_path = os.path.join(version_path, faulty_program)
                compiled_program_folder = os.path.join(self._results_dir, version)
                os.makedirs(compiled_program_folder, exist_ok=True)

                if self._coverage_calculator.compile_source(faulty_program_path, compiled_program_folder):
                    total_compiled += 1
                else:
                    total_failed += 1
    
    def cleanup(self) -> None:
        # Remove the entire results directory
        if os.path.exists(self._results_dir):
            shutil.rmtree(self._results_dir)

    def run_tests(self):
        tests = self.get_test_files()
        sbfl = SBFL()

        version_dirs = sorted([d for d in os.listdir(self._results_dir) if d.startswith('v')])
        total_versions = len(version_dirs)

        for version_idx, version_dir in enumerate(version_dirs, start=1):
            self._logger.info(f"Processing version: {version_dir} ({version_idx}/{total_versions})")

            version_path = os.path.join(self._results_dir, version_dir)

            # Find the .o file in the version directory
            tcas_object_name = next(f for f in os.listdir(version_path) if f.endswith(".o"))
            tcas_object = os.path.join(version_path, tcas_object_name)

            # Create a results folder for this version
            outputs_folder = os.path.join(version_path, "outputs")
            os.makedirs(outputs_folder, exist_ok=True)

            n_passed, n_failed, line_freq = self._coverage_calculator.run_tests(tcas_object, tests['tcas'], output_folder=outputs_folder)

            # Set up the SBFL instance with the results
            ranks_folder = os.path.join(version_path, "ranks")
            os.makedirs(ranks_folder, exist_ok=True)
            sbfl.set_parameters(line_freq, n_passed, n_failed)
            rank_list = sbfl.get_rank(
                            coefficient_list = [
                                SpectrumCoefficient.TARANTULA,
                                SpectrumCoefficient.OCHIAI,
                                SpectrumCoefficient.DSTAR
                            ], 
                            export_folder = ranks_folder)

    def get_test_files(self) -> dict[str, List[Tuple[str, str]]]:
        tests = {'tcas': []}

        for file_name in os.listdir(self._tests_dir):
            if file_name.endswith('.in'):
                input_path = os.path.join(self._tests_dir, file_name)
                output_path = input_path.replace('.in', '.out')
                
                tests['tcas'].append((input_path, output_path))

                self._logger.debug(f"Test case recorded: tcas | {input_path} | {output_path}")

        self._logger.info(f"Total test cases found: {len(tests)}")
        return tests
