# -*- coding: UTF-8 -*-

from importlib import reload
from short_term_solvency_ratio import ratio_calculator
from short_term_solvency_ratio import utils
ratio_calculator = reload(ratio_calculator)
utils = reload(utils)


if __name__ == "__main__":
    config = utils.config
    file_path = config['broker_picked_stock_path']
    calculator = ratio_calculator.ShortTermSolvencyCalculator(config, file_path)
    calculator.calculate()
