#!/usr/bin/python

class version:
    def __init__(self, str_version: str) -> None:
        try:
            arr_version = [int(_) for _ in str_version.split('.')]
        except ValueError:
            raise ValueError("version string cannot be empty")

        self.major  = arr_version[0]
        self.minor  = arr_version[1] if len(arr_version) > 1 else 0
        self.hotfix = arr_version[2] if len(arr_version) > 2 else 0

"""# testing framework
case_alpha = version("1.2.3")
case_beta  = version("3.4")
case_gamma = version("")
"""
