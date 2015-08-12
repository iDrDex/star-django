# coding: utf-8
import pickle
import pytest


@pytest.fixture(autouse=True)
def real_db(_django_cursor_wrapper):
    _django_cursor_wrapper.enable()


# import pandas as pd
from pandas.util.testing import assert_frame_equal
from .analysis import get_analysis_df

# test speed up
from cacheops import file_cache
get_analysis_df = file_cache.cached(get_analysis_df)


@pytest.mark.parametrize("name, case_query, control_query, modifier_query", [
    ('huntington', 'HD=="HD"', 'HD_Control=="HD_Control"', ''),
    ('malaria', 'Malaria=="Malaria"', 'Malaria_Control=="Malaria_Control"', ''),
    ('oldyoung', "old=='old' or age > 60", "young=='young' or age < 40", "ad<>'ad'"),
])
def test_analysis_df(name, case_query, control_query, modifier_query):
    df = get_analysis_df(case_query, control_query, modifier_query)
    saved_df = _load_frame('data/%s.analysis_df.pkl' % name)

    assert_frame_equal(df, saved_df)


import os.path

def _relative(filename):
    return os.path.join(os.path.dirname(__file__), filename)

def _load_frame(filename):
    return pickle.load(open(_relative(filename), 'rb'))

# свести в одну кодовую базу? как?

# разбиение
# кеширование операций, в обеих базах кода
# тулзы для сравнения датафреймов

# тесты отдельных функций с известными входными данными?

# users.set_index('user_id', inplace=True)
# users.ix[99]
# pd.concat([left_frame, right_frame])
