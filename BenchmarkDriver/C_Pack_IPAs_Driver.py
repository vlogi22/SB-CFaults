import os
import sys
import subprocess
import shutil
import re
from typing import List, Tuple

from BenchmarkDriver.BenchmarkDriver import BenchmarkDriver
from SBFL.SBFL import SBFL, SpectrumCoefficient

class C_Pack_IPAs_Driver(BenchmarkDriver):
    """Driver for the C-Pack-IPAs benchmark with its specific folder structure."""

    def __init__(self, base_path: str, debug: bool = False):
        super().__init__(base_path, debug)
        self._submissions_dir = os.path.join(self._base_path, "semantically_incorrect_submissions")
        self._tests_dir = os.path.join(self._base_path, "tests")

        self._results_dir = "./C-Pack-IPAs_faulty_programs_results"
        os.makedirs(self._results_dir, exist_ok=True)

        self._debug = debug

    def compile_source(self) -> str:
        """Compile the source code and return the path to the compiled executable.
        
        Returns:
            The path to the compiled executable
        """

        total_compiled = 0
        total_failed = 0

        # Process year directories
        years = [d for d in os.listdir(self._submissions_dir) if d.startswith('year')]
        for year in years:
            year_dir = os.path.join(self._submissions_dir, year)

            # Process lab directories
            labs = [d for d in os.listdir(year_dir) if d.startswith('lab')]
            for lab in labs:
                lab_dir = os.path.join(year_dir, lab)

                self._logger.info(f"Compiling [ year: {year} | lab: {lab} ]")

                # Process exercise directories
                exercises = [d for d in os.listdir(lab_dir) if d.startswith('ex')]
                for ex in exercises:
                    ex_dir = os.path.join(lab_dir, ex)

                    # Process submission directories
                    submissions = [d for d in os.listdir(ex_dir) if d.startswith('ex') and not d.endswith('.c')]
                    for sub in submissions:
                        sub_dir = os.path.join(ex_dir, sub)

                        # Process C files
                        c_files = [f for f in os.listdir(sub_dir) if f.endswith('.c')]
                        for c_file in c_files:
                            c_file_path = os.path.join(sub_dir, c_file)

                            compiled_program_folder = sub_dir.replace(self._submissions_dir, self._results_dir)
                            os.makedirs(compiled_program_folder, exist_ok=True)

                            if self._coverage_calculator.compile_source(c_file_path, compiled_program_folder):
                                total_compiled += 1
                            else:
                                total_failed += 1
        

        print(f"Compiled: {total_compiled}, Failed: {total_failed}", file=sys.stdout)

    def cleanup(self) -> None:
        # Remove the entire results directory
        if os.path.exists(self._results_dir):
            shutil.rmtree(self._results_dir)
    
    def run_tests(self):
        tests = self.get_test_files()
        sbfl = SBFL()

        # Process year directories
        years = [d for d in os.listdir(self._results_dir) if d.startswith('year')]
        for year in years:
            year_dir = os.path.join(self._results_dir, year)

            # Process lab directories
            labs = [d for d in os.listdir(year_dir) if d.startswith('lab')]
            for lab in labs:
                lab_dir = os.path.join(year_dir, lab)

                self._logger.info(f"Running tests for [ year: {year} | lab: {lab} ]")

                # Process exercise directories
                exercises = [d for d in os.listdir(lab_dir) if d.startswith('ex')]
                for ex in exercises:
                    ex_dir = os.path.join(lab_dir, ex)

                    self._logger.debug(f"exercise: {ex} | Path: {ex_dir}")

                    # Process submission directories
                    submissions = [d for d in os.listdir(ex_dir) if d.startswith('ex')]
                    for sub in submissions:
                        sub_dir = os.path.join(ex_dir, sub)

                        self._logger.debug(f"submission: {sub} | Path: {sub_dir}")

                        object_name = next(f for f in os.listdir(sub_dir) if f.endswith(".o"))
                        object = os.path.join(sub_dir, object_name)

                        # Create a results folder for this version
                        outputs_folder = os.path.join(sub_dir, "outputs")
                        os.makedirs(outputs_folder, exist_ok=True)

                        n_passed, n_failed, line_freq = self._coverage_calculator.run_tests(object, tests[f'{lab}_{ex}'], output_folder=outputs_folder)

                        # Remove the entire output directory
                        if os.path.exists(outputs_folder):
                            shutil.rmtree(outputs_folder)

                        # Set up the SBFL instance with the results
                        ranks_folder = os.path.join(sub_dir, "ranks")
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
        tests = {}

        labs = [f for f in os.listdir(self._tests_dir) if f.startswith('lab')]
        for lab in labs:
            lab_dir = os.path.join(self._tests_dir, lab)
            
            exs = [f for f in os.listdir(lab_dir) if f.startswith('ex')]
            for ex in exs:
                ex_dir = os.path.join(lab_dir, ex)
                
                tests[f'{lab}_{ex}'] = []
                
                input_files = [f for f in os.listdir(ex_dir) if f.endswith('.in')]
                for input_file in input_files:
                    input_path = os.path.join(ex_dir, input_file)
                    output_path = input_path.replace('.in', '.out')

                    tests[f'{lab}_{ex}'].append((input_path, output_path))

                    self._logger.debug(f"Test case recorded: {lab}_{ex} | {input_path} | {output_path}")

        self._logger.info(f"Total test cases found: {len(tests)}")
        return tests
