import os
import sys
import logging
import subprocess
from typing import List, Tuple, Set

class NoCoverageCalculator:
    """Driver for the TCAS benchmark with its specific folder structure."""

    def __init__(self, debug: bool = False):
        # self._n_human_labelled = 0
        # self._human_labelled_passing: List[Any] = []
        # self._human_labelled_failing: List[Any] = []

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # # Console handler
        # console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setFormatter(
        #     logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        # )
        # self._logger.addHandler(console_handler)
        
        # File handler - creates .log file in current folder
        log_filename = f"{self.__class__.__name__}.log"
        file_handler = logging.FileHandler(f"{log_filename}")
        file_handler.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )
        self._logger.addHandler(file_handler)

    def compile_source(self, program_file: str, output_folder: str) -> bool:
        gcc_flags = "-fno-optimize-sibling-calls -fno-strict-aliasing -fno-asm -g -O0 -std=c17"
        
        # GCC Compile
        program_object = os.path.basename(program_file).replace('.c', '.o')
        program_object_path = os.path.join(output_folder, program_object)
        
        compile_cmd = f"gcc {gcc_flags} {program_file} -o {program_object_path}"
        
        try:
            subprocess.run(compile_cmd, shell=True, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Compilation failed for {program_file}: {e.stderr.decode()}")
            return False

        self._logger.debug(f"Compiled {program_file} -> {program_object_path}")
            
        return True

    def run_tests(self, program_object: str, tests: List[Tuple[str, str]], output_folder: str, input_from_args: bool = False) -> Tuple[int, int, dict[int, list[int, int]]]:
        """Run the compiled executable with the provided tests and generate coverage data.

        Args:
            program_object: The path to the compiled executable
            tests: A list of tuples where each tuple contains the path to an input file and the path to the expected output file
            output_folder: The folder where the coverage results will be stored
        """
        total_tests = len(tests)
        passed_tests = 0
        failed_tests = 0
        line_freq = {}
        
        # Run the compiled binary with a test input
        for input_file, expected_output_file in tests:
            test_name = os.path.basename(input_file).split('.')[0]
            my_output_file = os.path.join(output_folder, f"{test_name}.out")
            diff_file = os.path.join(output_folder, f'{test_name}.diff')
            
            try:
                if input_from_args:
                    result = subprocess.run(f"{program_object} $(cat {input_file}) > {my_output_file}", shell=True, capture_output=True, text=True, timeout=3, check=False)
                else:
                    result = subprocess.run(f"{program_object} < {input_file} > {my_output_file}", shell=True, capture_output=True, text=True, timeout=3, check=False)
                            
                diff_result = subprocess.run(f"diff {expected_output_file} {my_output_file} > {diff_file}", shell=True, capture_output=True, text=True)
                
                if diff_result.returncode == 0:
                    subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.passed.diff')}", shell=True, capture_output=True, text=True)
                    passed_tests += 1
                else:
                    subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.failed.diff')}", shell=True, capture_output=True, text=True)
                    failed_tests += 1
                    
            except subprocess.CalledProcessError:
                subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.error_failed.diff')}", shell=True, capture_output=True, text=True)
                failed_tests += 1
            except subprocess.TimeoutExpired:
                subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.timeout_failed.diff')}", shell=True, capture_output=True, text=True)
                failed_tests += 1
        
        self._logger.info(f"Finished processing: {program_object} | Total: {total_tests} | Pass: {passed_tests} | Fail: {failed_tests}")
        
        # Runtime assertion to ensure total equals sum of passed and failed
        assert passed_tests + failed_tests == total_tests, f"Test count mismatch: total={total_tests}, passed={passed_tests}, failed={failed_tests}"
        
        return (passed_tests, failed_tests, line_freq)
    
    def get_coverage(self, program_object: str, tests: List[Tuple[str, str]], output_folder: str, diff: bool, export: bool = True) -> Set[int]:
        return set()  # No coverage information is collected in this implementation
