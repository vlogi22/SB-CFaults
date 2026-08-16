import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Set, Dict, Optional, Any

from CoverageCalculator.CoverageCalculatorEnum import CoverageCalculatorEnum
from CoverageCalculator.NoCoverageCalculator import NoCoverageCalculator
from CoverageCalculator.GcovLineCoverageCalculator import GcovLineCoverageCalculator

class BenchmarkDriver(ABC):
    """Abstract base class for benchmark drivers with different folder structures."""
    
    def __init__(self, base_path: str, debug: bool = False, log_file: Optional[str] = None):
        self._base_path = base_path
        self._debug = debug

        self.SetCoverageCalculator(CoverageCalculatorEnum.EMPTY)
                
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )
        self._logger.addHandler(console_handler)
        
        # File handler - creates .log file in current folder
        log_filename = f"{self.__class__.__name__}.log"
        file_handler = logging.FileHandler(f"{log_filename}")
        file_handler.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )
        self._logger.addHandler(file_handler)
    
    def get_base_path(self) -> str:
        return self._base_path

    def SetCoverageCalculator(self, coverageType: CoverageCalculatorEnum = CoverageCalculatorEnum.EMPTY):
        if coverageType == CoverageCalculatorEnum.EMPTY:
            self._coverage_calculator = NoCoverageCalculator(self._debug)
        else:
            self._coverage_calculator = GcovLineCoverageCalculator(self._debug)
    # ==========================

    @abstractmethod
    def compile_source(self) -> str:
        """Compile the source code and return the path to the compiled executable.
        
        Returns:
            The path to the compiled executable
        """
        pass

    @abstractmethod
    def run_tests(self) -> str:
        """Run a test case and return the output.
            
        Returns:
            The program output as a string
        """
        pass
    
    @abstractmethod
    def get_test_files(self) -> List[Tuple[str, str]]:
        """Get all test cases files for a bug folder.
            
        Returns:
            List of tuples containing (input_file, expected_output_file)
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Remove non-.c files from the versions directory."""
        pass
