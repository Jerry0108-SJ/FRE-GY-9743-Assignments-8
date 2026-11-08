"""Create data containers from caller-provided tables, using the course APIs.

For qfCreateData1D, the DataFrame index supplies the axis labels and its
``values`` column supplies the market values. IFR, OIS, and zero-spread values
are passed through unchanged; callers provide decimal rates in their notebook.
qfCreateDataGeneric supplies the template's funding-parameter table.
"""

import pandas as pd
from typing import List

from fixedincomelib.data import DataObject, Data1D, DataCollection, DataGeneric
from fixedincomelib.market.registries import DataConventionRegistry

__all__ = ["qfCreateData1D", "qfCreateDataCollection"]


def qfCreateData1D(data_type : str, data_conv : str, df : pd.DataFrame):
    axis1 = df.index.tolist()
    values = df['values'].tolist()
    data_conv_obj = DataConventionRegistry().get(data_conv)
    return Data1D(data_type, data_conv_obj, axis1, values)


def qfCreateDataCollection(data_objects : List[DataObject]):
    return DataCollection(data_objects)


def qfCreateDataGeneric(data_type : str, data_label : str, df : pd.DataFrame):
    columns = df.columns.tolist()
    values = df.values.tolist()
    return DataGeneric(data_type, data_label, columns, values)

__all__ += ["qfCreateDataGeneric"]
