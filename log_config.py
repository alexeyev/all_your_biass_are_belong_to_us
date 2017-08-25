# -*- coding: utf-8 -*-

"""
    Logging configuration: flooding both all_results file and stdout
"""

import logging

logging.basicConfig(filename='all_sessions.log',
                    format='[%(asctime)s] [%(levelname)s] %(message)s',
                    level=logging.DEBUG)

lg = logging.getLogger()
lg.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
lg.addHandler(ch)
