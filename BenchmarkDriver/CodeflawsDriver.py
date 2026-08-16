import os
import sys
import subprocess
import shutil
import re
from typing import List, Tuple

from BenchmarkDriver.BenchmarkDriver import BenchmarkDriver
from SBFL.SBFL import SBFL, SpectrumCoefficient

class CodeflawsDriver(BenchmarkDriver):
    """Driver for the Codeflaws benchmark with its specific folder structure."""

    def __init__(self, base_path: str, debug: bool = False):
        super().__init__(base_path, debug)
        self._codeflaws_dir = os.path.join(self._base_path, "codeflaws")
        self._tests_dir = os.path.join(self._base_path, "tests")

        self._results_dir = "./Codeflaws_faulty_programs_results"
        os.makedirs(self._results_dir, exist_ok=True)

        self._debug = debug

    def compile_source(self) -> str:
        """Compile the source code and return the path to the compiled executable.
        
        Args:
            coverage (bool): Whether to compile with coverage instrumentation. Defaults to False.
            
        Returns:
            The path to the compiled executable
        """

        total_compiled = 0
        total_failed = 0

        # Process bug directories
        bugs = sorted([d for d in os.listdir(self._codeflaws_dir) if 'bug' in d and os.path.isdir(os.path.join(self._codeflaws_dir, d))])
        for bug in bugs:
            bug_dir = os.path.join(self._codeflaws_dir, bug)
            
            folder_parts = bug.split('-')
            buggy_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[3] + ".c"
            golden_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[4] + ".c"

            # Process C files
            c_files = [f for f in os.listdir(bug_dir) if f.endswith('.c') and f == buggy_version]
            for c_file in c_files:
                c_file_path = os.path.join(bug_dir, c_file)
                
                compiled_program_folder = bug_dir.replace(self._codeflaws_dir, self._results_dir)
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
        
        # Process bug directories
        bugs = sorted([d for d in os.listdir(self._results_dir)])
        for bug in bugs:
            bug_dir = os.path.join(self._results_dir, bug)
            
            folder_parts = bug.split('-')
            buggy_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[3]
            golden_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[4]

            # Process C files
            object_files = [f for f in os.listdir(bug_dir) if f == f"{buggy_version}.o"]
            for object_file in object_files:
                object_file_path = os.path.join(bug_dir, object_file)

                self._logger.info(f"Running tests for {object_file}")
                
                # Create a results folder for this version
                outputs_folder = os.path.join(bug_dir, "outputs")
                os.makedirs(outputs_folder, exist_ok=True)
                
                n_passed, n_failed, line_freq = self._coverage_calculator.run_tests(object_file_path, tests[f'{buggy_version}'], output_folder=outputs_folder)

                # Set up the SBFL instance with the results
                ranks_folder = os.path.join(bug_dir, "ranks")
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

        # Process bug directories
        bugs = [d for d in os.listdir(self._codeflaws_dir) if 'bug' in d and os.path.isdir(os.path.join(self._codeflaws_dir, d))]
        for bug in bugs:
            bug_dir = os.path.join(self._codeflaws_dir, bug)
            
            folder_parts = bug.split('-')
            buggy_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[3]
            golden_version = folder_parts[0] + "-" + folder_parts[1] + "-" + folder_parts[4]

            tests[f'{buggy_version}'] = []
            
            input_files = [f for f in os.listdir(bug_dir) if f.startswith('heldout-input')]
            for input_file in input_files:
                input_path = os.path.join(bug_dir, input_file)
                output_path = input_path.replace('heldout-input', 'heldout-output')

                tests[f'{buggy_version}'].append((input_path, output_path))

                self._logger.debug(f"Test case recorded: f'{buggy_version}' | {input_path} | {output_path}")
                

        self._logger.info(f"Total test cases found: {len(tests)}")
        return tests
