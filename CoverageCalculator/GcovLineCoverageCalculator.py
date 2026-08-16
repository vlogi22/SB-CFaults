import os
import sys
import subprocess
import shutil
import re
from typing import List, Tuple, Set, Dict, Optional, Any

from CoverageCalculator.NoCoverageCalculator import NoCoverageCalculator

class GcovLineCoverageCalculator(NoCoverageCalculator):
    """
        
    """

    def __init__(self, debug: bool = False):
        super().__init__(debug)

    def compile_source(self, program_file: str, output_folder: str) -> bool:
        """Compile the source code and return the path to the compiled executable.
        
        Args:
            program_file: The path to the source file to compile
            output_folder: The folder where the compiled executable will be placed
        
        Returns:
            True if compilation is successful, False otherwise
        """

        gcc_flags = "-fno-optimize-sibling-calls -fno-strict-aliasing -fno-asm -g -O0 -std=c17"
        gcov_flags = "-fprofile-arcs -ftest-coverage"

        # GCC Compile
        program_object = os.path.basename(program_file).replace('.c', '.o')
        program_object_path = os.path.join(output_folder, program_object)
        
        compile_cmd = f"gcc {gcc_flags} {gcov_flags} {program_file} -o {program_object_path}"
        
        try:
            subprocess.run(compile_cmd, shell=True, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Compilation failed for {program_file}: {e.stderr.decode()}")
            return False

        self._logger.debug(f"Compiled {program_file} -> {program_object_path}")
            
        return True
    
    def run_tests(self, program_object: str, tests: List[Tuple[str, str]], output_folder: str) -> Tuple[int, int, dict[int, list[int, int]]]:
        """Run the compiled executable with the provided tests and generate coverage data.

        Args:
            program_object: The path to the compiled executable
            tests: A list of tuples where each tuple contains the path to an input file and the path to the expected output file
            output_folder: The folder where the coverage results will be stored
            
        Returns:
            A tuple containing the number of passed tests, the number of failed tests, 
            and a dictionary mapping line numbers to their execution frequency in passed and failed tests.
        """
        
        self._logger.debug(f"Running tests for {program_object} with {tests} test cases. Output folder: {output_folder}")
        
        total_tests = len(tests)
        n_passed_tests = 0
        n_failed_tests = 0
        line_freq = {}
        
        # Run the compiled binary with a test input
        for input_file, expected_output_file in tests:
            test_name = os.path.basename(input_file).split('.')[0]
            my_output_file = os.path.join(output_folder, f"{test_name}.out")
            diff_file = os.path.join(output_folder, f'{test_name}.diff')
            line_coverage_file = ""
            
            try:
                #result = subprocess.run(f"{program_object} $(cat {input_file}) > {my_output_file}", shell=True, capture_output=True, text=True, timeout=3, check=False)
                print(f"{program_object} < {input_file} > {my_output_file}")
                result = subprocess.run(f"{program_object} < {input_file} > {my_output_file}", shell=True, capture_output=True, text=True, timeout=3, check=False)
                
                # Get the diff result to determine if the test passed or failed
                diff_result = subprocess.run(f"diff {expected_output_file} {my_output_file} > {diff_file}", shell=True, capture_output=True, text=True)
                if diff_result.returncode == 0:
                    subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.passed.diff')}", shell=True, capture_output=True, text=True)
                    line_coverage_file = os.path.join(output_folder, f'{test_name}.passed.cov')
                    n_passed_tests += 1
                elif diff_result.returncode == 1:
                    subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.failed.diff')}", shell=True, capture_output=True, text=True)
                    line_coverage_file = os.path.join(output_folder, f'{test_name}.failed.cov')
                    n_failed_tests += 1
                    
                # At this point, .gcno and .gcda files should be generated in the same directory as the program_object.
                line_coverage_list = self.get_coverage(program_object, line_coverage_file)
                
                for line in line_coverage_list:
                    if line not in line_freq:
                        line_freq[line] = [0, 0]  # (passed, failed)
                    
                    line_freq[line][0 if diff_result.returncode == 0 else 1] += 1

            except subprocess.CalledProcessError:
                subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.error_failed.diff')}", shell=True, capture_output=True, text=True)
                n_failed_tests += 1
            except subprocess.TimeoutExpired:
                subprocess.run(f"mv {diff_file} {os.path.join(output_folder, f'{test_name}.timeout_failed.diff')}", shell=True, capture_output=True, text=True)
                n_failed_tests += 1
                
        
        self._logger.info(f"Finished processing: {program_object} | Total: {n_passed_tests + n_failed_tests} | Pass: {n_passed_tests} | Fail: {n_failed_tests}")
        
        # Runtime assertion to ensure total equals sum of passed and failed
        assert n_passed_tests + n_failed_tests == total_tests, f"Test count mismatch: total={total_tests}, passed={n_passed_tests}, failed={n_failed_tests}"
                
        return (n_passed_tests, n_failed_tests, line_freq)
    
    def get_coverage(self, program_object: str, line_coverage_file: str) -> List[int]:
        """

        Args:
            program

        Returns:
            List[int]: A list of line numbers that were executed during the tests.
        """

        program_object_folder = os.path.dirname(program_object)
        
        program_name = os.path.basename(program_object).replace('.o', '')
        gcno_file = program_object.replace('.o', f'.o-{program_name}.gcno')
        gcov_file = os.path.join(program_object_folder, f"{program_name}.c.gcov")
        
        try:
            subprocess.run(['gcov', gcno_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)            
            subprocess.run(f"mv {program_name}.c.gcov {gcov_file}", shell=True)

        except subprocess.CalledProcessError:
            pass
        except subprocess.TimeoutExpired:
            pass
        
        return self.parse_gcov_file(gcov_file, line_coverage_file)

    def parse_gcov_file(self, gcov_file: str, line_coverage_file: str) -> List[int]:
        """Parse the .gcov file to extract line coverage information.
        
        Args:
            gcov_file (str): The path to the .gcov file generated by gcov.
            line_coverage_file (str): The path to the output file where line coverage information will be written.

        Returns:
            List[int]: A list of line numbers that were executed during the tests.
        """
        line_coverage = []
        
        with open(gcov_file, 'r') as cov_file:
            for line in cov_file:
                parts = line.strip().split(":", 2)
                if len(parts) < 3:
                    continue
                exec_count, lineno, code = parts
                if exec_count not in ["#####", "-", ""]:
                    line_coverage.append(int(lineno.strip()))

        with open(line_coverage_file, 'w') as out_file:
            for line_num in line_coverage:
                out_file.write(f"{line_num}\n")
                
        return line_coverage
