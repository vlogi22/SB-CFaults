import math
from enum import Enum
import os
from unittest import case, result

class SpectrumCoefficient(Enum):
    TARANTULA = "tarantula"
    OCHIAI = "ochiai"
    JACCARD = "jaccard"
    DSTAR = "dstar"

class SBFL:

    def __init__(self, line_freq: dict[int, tuple[int, int]] = None, total_passed: int = 0, total_failed: int = 0):
        """
        Args:
            line_freq (dict[int, tuple[int, int]]): A dictionary mapping line numbers to tuples of (passed, failed) counts.
            total_passed (int): The total number of passed test cases.
            total_failed (int): The total number of failed test cases.
        """
        self.set_parameters(line_freq, total_passed, total_failed)

    def set_parameters(self, line_freq: dict[int, tuple[int, int]], total_passed: int, total_failed: int):
        self.__line_freq = line_freq
        self.__N_S = total_passed
        self.__N_F = total_failed

    def cal_tarantula(self) -> dict[int, float]:
        """ Calculates the Tarantula scores for each line.

            (N_CF/N_F) / ((N_CF/N_F) + (N_CS/N_S))
        Returns:
            dict[int, float]: A dictionary mapping line numbers to their Tarantula scores.
        """
        tarantula_scores = {}
        for line, pf_freq in self.__line_freq.items():
            N_CS = pf_freq[0]
            N_CF = pf_freq[1]

            # Guard against division by zero when there are no failing/passing tests
            cf_ratio = (N_CF / self.__N_F) if self.__N_F > 0 else 0.0
            cs_ratio = (N_CS / self.__N_S) if self.__N_S > 0 else 0.0

            denominator = cf_ratio + cs_ratio
            if denominator == 0:
                tarantula_scores[line] = 0.0
            else:
                tarantula_scores[line] = cf_ratio / denominator

        return tarantula_scores
    
    def cal_ochiai(self) -> dict[int, float]:
        """ Calculates the Ochiai scores for each line.

            (N_CF) / sqrt( (N_F) * (N_C) )
        Returns:
            dict[int, float]: A dictionary mapping line numbers to their Ochiai scores.
        """
        ochiai_scores = {}

        for line, pf_freq in self.__line_freq.items():
            N_CS = pf_freq[0]
            N_CF = pf_freq[1]

            denominator = math.sqrt(self.__N_F * (N_CF + N_CS))
            ochiai_scores[line] = 0.0 if denominator == 0 else N_CF / denominator

        return ochiai_scores

    def cal_jaccard(self) -> dict[int, float]:
        """ Calculates the Jaccard scores for each line.
        
            (N_CF) / (N_CF + N_UF + N_CS)
        Returns:
            dict[int, float]: A dictionary mapping line numbers to their Jaccard scores.
        """
        jaccard_scores = {}
        
        for line, pf_freq in self.__line_freq.items():
            N_CS = pf_freq[0]
            N_CF = pf_freq[1]

            denominator = self.__N_F + N_CS
            jaccard_scores[line] = 0.0 if denominator == 0 else N_CF / denominator
            
        return jaccard_scores

    def cal_dstar(self, power: int = 2, normalize: bool = True) -> dict[int, float]:
        """ Calculates the Dstar scores for each line.

            (N_CF)^power / (N_CS + N_UF)
        Args:
            power (int, optional): The power to which to raise the failed count. Defaults to 2.

        Returns:
            dict[int, float]: A dictionary mapping line numbers to their Dstar scores.
        """
        dstar_scores = {}
        for line, pf_freq in self.__line_freq.items():
            N_CS = pf_freq[0]
            N_CF = pf_freq[1]
            
            denominator = N_CS + self.__N_F - N_CF
            dstar_scores[line] = 0.0 if denominator == 0 else N_CF / denominator

        if normalize:
            max_score = max(dstar_scores.values()) if dstar_scores else 1
            max_score = 1 if max_score == 0 else max_score
            dstar_scores = {line: score / max_score for line, score in dstar_scores.items()}

        return dstar_scores

    def scores_to_rank(self, scores: dict[int, float]) -> dict[int, tuple[int, int]]:
        """ Returns the rank of each line based on their scores.

        Args:
            scores (dict[int, float]): A dictionary mapping line numbers to their scores.
            
        Returns:
            dict[int, tuple[int, int]]: A dictionary mapping line numbers to their rank and score.
        """
        sorted_lines = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        rank_dict = {}
        current_rank = 1
        previous_score = None

        for index, (line, score) in enumerate(sorted_lines):
            if previous_score is not None and score < previous_score:
                current_rank = index + 1
            rank_dict[line] = (current_rank, score)
            previous_score = score

        return rank_dict

    def get_rank(self, coefficient_list: list[SpectrumCoefficient] = [], export_folder: str = None) -> dict[SpectrumCoefficient, dict[int, tuple[int, int]]]:
        """ Returns the rank of each line based on the specified spectrum coefficient.

        Args:
            spectrum_coefficient (SpectrumCoefficient): The spectrum coefficient to use for ranking.

        Returns:
            dict[SpectrumCoefficient, dict[int, tuple[int, int]]]: A dictionary mapping spectrum coefficients to their corresponding rank dictionaries.
                        type              {line_no, (rank, score)}
        """
        if export_folder:
            os.makedirs(export_folder, exist_ok=True)
            export_path = os.path.join(export_folder, "sbfl_parameters.csv")
            with open(export_path, 'w') as f:
                f.write("{")
                comma = False
                for line, (n_suc, n_fail) in self.__line_freq.items():
                    if comma:
                        f.write(",")
                    else:
                        comma = True

                    f.write("{" + f" line: {line} , N_SC: {n_suc} , N_FC: {n_fail} , N_SU: {self.__N_S - n_suc} , N_FU: {self.__N_F - n_fail}" + "}\n")
                f.write("}")
                f.close()

        result = {}

        if not coefficient_list:
            # If no coefficients are specified, calculate ranks for all coefficients
            coefficient_list = list(SpectrumCoefficient)

        for spectrum_coefficient in coefficient_list:
            match spectrum_coefficient:
                case SpectrumCoefficient.TARANTULA:
                    scores = self.cal_tarantula()
                case SpectrumCoefficient.OCHIAI:
                    scores = self.cal_ochiai()
                case SpectrumCoefficient.JACCARD:
                    scores = self.cal_jaccard()
                case SpectrumCoefficient.DSTAR:
                    scores = self.cal_dstar()
                case _:
                    pass # Ignore unknown coefficients

            result[spectrum_coefficient] = self.scores_to_rank(scores)

        if export_folder:
            os.makedirs(export_folder, exist_ok=True)
            for spectrum_coefficient, rank_dict in result.items():
                export_path = os.path.join(export_folder, f"{spectrum_coefficient.value}_rank.csv")
                with open(export_path, 'w') as f:
                    f.write("{")
                    comma = False
                    for line, (rank, score) in sorted(rank_dict.items(), key=lambda item: item[1][0]):
                        if comma:
                            f.write(",")
                        else:
                            comma = True
    
                        f.write("{" + f"line: {line}, rank: {rank}, score: {score:.20f}" + "}\n")
                    f.write("}")
                f.close()
                
        return result

    def print_rank(self, rank_list: dict[SpectrumCoefficient, dict[int, tuple[int, int]]]) -> None:
        """ Prints the rank of each line for each spectrum coefficient.

        Args:
            rank_list (dict[SpectrumCoefficient, dict[int, tuple[int, int]]]): A dictionary mapping
                spectrum coefficients to their corresponding rank dictionaries, as returned by get_rank().
        """
        for coefficient, rank_dict in rank_list.items():
            print(f"=== {coefficient.value.upper()} ===")
            sorted_lines = sorted(rank_dict.items(), key=lambda item: item[1][0])
            for line, (rank, score) in sorted_lines:
                print(f"  Line {line}: rank={rank}, score={score:.10f}")
            print()

if __name__=="__main__":
    line_freq = { 1:[3, 3], 2:[3, 3], 3:[0, 1], 4:[3, 2], 5:[3, 2], 6:[2, 0], 7:[2, 0], 8:[2, 0] }
    sbfl = SBFL(line_freq, 3, 3)

    rank_list = sbfl.get_rank(export_folder="SBFL/ranks") # All
    sbfl.print_rank(rank_list)