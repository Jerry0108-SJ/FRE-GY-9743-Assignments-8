"""Direct IFR construction and the template's OIS calibration configuration."""

from typing import Union, List
import QuantLib as ql

from fixedincomelib.market.data_conventions import DataConventionIFR, DataConventionRFRSwap
from fixedincomelib.market.registries import (
    DataConventionRegistry, FundingIdentifier, FundingIdentifierRegistry, IndexRegistry,
)
from fixedincomelib.model import BuildMethod, BuildMethodBuilderRregistry
from fixedincomelib.utilities.numerics import ExtrapMethod, InterpMethod

__all__ = ["YieldCurveIndexBuildMethod", "YieldCurveFundingBuildMethod"]


class YieldCurveIndexBuildMethod(BuildMethod):

    _version = 1
    _build_method_type = 'YIELD_CURVE_INDEX'

    def __init__(self, 
                 target : str,
                 content : Union[List, dict]):

        super().__init__(target, 'YIELD_CURVE_INDEX', content)
        if self.bm_dict['INTERPOLATION METHOD'] == '':
            self.bm_dict['INTERPOLATION METHOD'] = 'PIECEWISE_CONSTANT_LEFT_CONTINUOUS'
        if self.bm_dict['EXTRAPOLATION METHOD'] == '':
            self.bm_dict['EXTRAPOLATION METHOD'] = 'FLAT'
        self.target_index_ = IndexRegistry().get(self.target)

    def calibration_instruments(self) -> set:
        return {'INSTANTANEOUS FORWARD RATE', 'OVERNIGHT INDEX SWAP'}

    def additional_entries(self) -> set:
        return {'REFERENCE INDEX', 'INTERPOLATION METHOD', 'EXTRAPOLATION METHOD'}

    @property
    def overnight_index_swap(self) -> DataConventionRFRSwap | None:
        name = self['OVERNIGHT INDEX SWAP']
        return None if name == '' else DataConventionRegistry().get(name)

    @property
    def target_index(self) -> ql.Index:
        return self.target_index_

    @property
    def reference_index(self):
        if 'REFERENCE INDEX' not in self.bm_dict:
            return None
        return self.bm_dict['REFERENCE INDEX']

    @property
    def instantaneous_forward_rate(self) -> DataConventionIFR:
        if self['INSTANTANEOUS FORWARD RATE'] == '':
            return None
        return DataConventionRegistry().get(self['INSTANTANEOUS FORWARD RATE'])

    @property
    def interpolation_method(self) -> InterpMethod:
        return InterpMethod.from_string(self['INTERPOLATION METHOD'])

    @property
    def extrapolation_method(self) -> ExtrapMethod:
        return ExtrapMethod.from_string(self['EXTRAPOLATION METHOD'])


class YieldCurveFundingBuildMethod(BuildMethod):

    _version = 1
    _build_method_type = 'YIELD_CURVE_FUNDING'

    def __init__(self, 
                 target : str,
                 content : Union[List, dict]):

        super().__init__(target, 'YIELD_CURVE_FUNDING', content)
        if self.bm_dict['INTERPOLATION METHOD'] == '':
            self.bm_dict['INTERPOLATION METHOD'] = 'PIECEWISE_CONSTANT_LEFT_CONTINUOUS'
        if self.bm_dict['EXTRAPOLATION METHOD'] == '':
            self.bm_dict['EXTRAPOLATION METHOD'] = 'FLAT'
        self.target_index_ = FundingIdentifierRegistry().get(self.target)

    def calibration_instruments(self) -> set:
        return {'INSTANTANEOUS FORWARD RATE', 'SPREAD ZERO RATE'}

    def additional_entries(self) -> set:
        return {'REFERENCE INDEX', 'INTERPOLATION METHOD', 'EXTRAPOLATION METHOD'}

    @property
    def target_index(self) -> FundingIdentifier:
        return self.target_index_

    @property
    def reference_index(self):
        if 'REFERENCE INDEX' not in self.bm_dict:
            return None
        return self.bm_dict['REFERENCE INDEX']

    @property
    def instantaneous_forward_rate(self) -> DataConventionIFR:
        if self['INSTANTANEOUS FORWARD RATE'] == '':
            return None
        return DataConventionRegistry().get(self['INSTANTANEOUS FORWARD RATE'])

    @property
    def interpolation_method(self) -> InterpMethod:
        return InterpMethod.from_string(self['INTERPOLATION METHOD'])

    @property
    def extrapolation_method(self) -> ExtrapMethod:
        return ExtrapMethod.from_string(self['EXTRAPOLATION METHOD'])


### register
BuildMethodBuilderRregistry().register(YieldCurveIndexBuildMethod._build_method_type, YieldCurveIndexBuildMethod)
BuildMethodBuilderRregistry().register(f'{YieldCurveIndexBuildMethod._build_method_type}_DES', YieldCurveIndexBuildMethod.deserialize)
BuildMethodBuilderRregistry().register(YieldCurveFundingBuildMethod._build_method_type, YieldCurveFundingBuildMethod)
BuildMethodBuilderRregistry().register(f'{YieldCurveFundingBuildMethod._build_method_type}_DES', YieldCurveFundingBuildMethod.deserialize)

from fixedincomelib.market.basics import Currency

class YieldCurveBuildMethodCommon(BuildMethod):

    _version = 1
    _build_method_type = 'YIELD_CURVE_COMMON'

    def __init__(self,
                 currency : str,
                 content : Union[List, dict]):

        super().__init__(currency, 'YIELD_CURVE_COMMON', content)
        assert 'FUNDING PARAMETERS' in self.bm_dict
        if self.bm_dict['SOLVER'] == '':
            self.bm_dict['SOLVER'] = 'BRENT'
        self.target_currency_ = Currency(self.target)

    def calibration_instruments(self) -> set:
        return {}

    def additional_entries(self) -> set:
        return {'FUNDING PARAMETERS', 'SOLVER'}

    @property
    def target_currency(self) -> Currency:
        return self.target_currency_

    @property
    def solver(self) -> str:
        return self['SOLVER']

__all__ += ["YieldCurveBuildMethodCommon"]
BuildMethodBuilderRregistry().register(YieldCurveBuildMethodCommon._build_method_type, YieldCurveBuildMethodCommon)
BuildMethodBuilderRregistry().register(YieldCurveBuildMethodCommon._build_method_type + "_DES", YieldCurveBuildMethodCommon.deserialize)
