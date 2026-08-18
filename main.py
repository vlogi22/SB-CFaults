
import os
import sys
import argparse


from CoverageCalculator.CoverageCalculatorEnum import CoverageCalculatorEnum
from BenchmarkDriver.CodeflawsDriver import CodeflawsDriver
from BenchmarkDriver.C_Pack_IPAs_Driver import C_Pack_IPAs_Driver
from BenchmarkDriver.TCASDriver import TCASDriver

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--benchmark", help = "Benchmark Subject", required=True)
    parser.add_argument("-p", "--path", help="path to Benchmark folder", required=True)
    parser.add_argument("-d", "--debug", help="Enable Debug", action="store_true")
    args=parser.parse_args()

    benchmark = args.benchmark
    base_path = args.path

    if not os.path.isdir(base_path):
        print(f"Not a directory: {base_path}", file=sys.stderr)
        sys.exit(1)

    if benchmark == "TCAS":
        TCAS_driver = TCASDriver(base_path, debug=args.debug)
        TCAS_driver.SetCoverageCalculator(CoverageCalculatorEnum.LINE)
        TCAS_driver.cleanup()
        TCAS_driver.compile_source()
        TCAS_driver.run_tests()
    elif benchmark == "C-Pack-IPAs":
        C_Pack_IPAs_driver = C_Pack_IPAs_Driver(base_path, debug=args.debug)
        C_Pack_IPAs_driver.SetCoverageCalculator(CoverageCalculatorEnum.LINE)
        C_Pack_IPAs_driver.cleanup()
        C_Pack_IPAs_driver.compile_source()
        C_Pack_IPAs_driver.run_tests()
    elif benchmark == "Codeflaws":
        Codeflaws_driver = CodeflawsDriver(base_path, debug=args.debug)
        Codeflaws_driver.SetCoverageCalculator(CoverageCalculatorEnum.LINE)
        Codeflaws_driver.cleanup()
        Codeflaws_driver.compile_source()
        Codeflaws_driver.run_tests()