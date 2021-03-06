# coding: utf-8
# !/usr/bin/env python
"""
@Author: zhirui zhou
@Contact: evilpsycho42@gmail.com
@Time: 2019/11/9 下午12:20
"""

from setuptools import setup


setup(
    name='deepseries',
    version='0.4',
    description='deep learning library for time series prediction.',
    author='zhirui zhou',
    author_email='evilpsycho42@gmail.com',
    license="Apache 2.0",
    url='https://github.com/EvilPsyCHo/Deep-Time-Series-Prediction',
    packages={'deepseries', 'deepseries.nn', 'deepseries.models'},
    package_data={'deepseries': ['dataset/*.csv']},
)
