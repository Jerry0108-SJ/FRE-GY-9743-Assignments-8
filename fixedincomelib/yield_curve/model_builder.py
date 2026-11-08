"""Template build-method grouping, instrument preparation, and sequential bootstrap."""
import numpy as np
import pandas as pd
from typing import List, Tuple
from fixedincomelib.date import Date, Period, add_period, accrued
from fixedincomelib.date.basics import TermOrDate as TermOrTerminationDate
from fixedincomelib.data import Data1D, DataCollection, DataGeneric
from fixedincomelib.market import Currency, DataConventionIFR
from fixedincomelib.model import BuildMethod, BuildMethodCollection, Model, ModelComponent, ModelBuilderRegistry
from fixedincomelib.product import Product, ProductFactory
from fixedincomelib.valuation import FundingIndexParameter, ValuationParametersCollection, ValuationEngineProductRegistry, ValuationRequest
from fixedincomelib.yield_curve.build_method import YieldCurveIndexBuildMethod, YieldCurveFundingBuildMethod, YieldCurveBuildMethodCommon
from fixedincomelib.yield_curve.calibration_utils import YieldCurveCalibration
from fixedincomelib.yield_curve.yield_curve_model import YieldCurve, YieldCurveModelComponent

__all__ = ["YieldCurveBuilder"]

class YieldCurveBuilder:
    @staticmethod
    def create_model_yield_curve(value_date: Date, data_collection: DataCollection,
                                 build_method_collection: BuildMethodCollection):
        if not value_date.is_valid():
            raise ValueError("A valid model value date is required.")
        if build_method_collection.num_build_methods == 0:
            raise ValueError("At least one yield-curve build method is required.")
        model_yield_curve = YieldCurve(value_date, data_collection, build_method_collection)
        build_methods_pack, residual_build_methods = YieldCurveBuilder._sort_out_build_method_and_funding(
            build_method_collection, data_collection)
        components_to_be_calibrated = []
        for bm_pack in build_methods_pack.values():
            # Template order: funding components first, then index components.
            for kind in (YieldCurveFundingBuildMethod._build_method_type, YieldCurveIndexBuildMethod._build_method_type):
                for bm in bm_pack.get(kind, []):
                    mkt_data_list = [data_collection.get_data_from_data_collection(data_type, bm[data_type])
                                     for data_type in bm.calibration_instruments() if bm[data_type] != ""]
                    component = YieldCurveBuilder.prepare_calibrate_instruments(
                        value_date, mkt_data_list, bm, bm_pack[DataGeneric._data_shape])
                    model_yield_curve.set_model_component(bm.target_index.name(), component)
                    components_to_be_calibrated.append((component, bm_pack[YieldCurveBuildMethodCommon._build_method_type]))
        # Existing direct-IFR models do not require a common build method.
        for bm in residual_build_methods:
            convention = bm.instantaneous_forward_rate
            if not isinstance(convention, DataConventionIFR):
                raise ValueError(f"{bm.target}: market calibration requires a currency common build method.")
            data = data_collection.get_data_from_data_collection('INSTANTANEOUS FORWARD RATE', convention.name)
            if not isinstance(data, Data1D):
                raise TypeError("IFR inputs must be Data1D.")
            component = YieldCurveBuilder.calibrate_single_component_from_state_data(value_date, convention, data, bm)
            model_yield_curve.set_model_component(bm.target_index.name(), component)
        for component in model_yield_curve.components_.values():
            reference = getattr(component.component_identifier, 'reference_index', None)
            if reference is not None:
                model_yield_curve.retrieve_model_component(reference)
        for component, solver_info in components_to_be_calibrated:
            YieldCurveBuilder.calibrate_single_component_from_mkt_data(model_yield_curve, component, solver_info)
        return model_yield_curve

    @staticmethod
    def calibrate_single_component_from_state_data(
        value_date: Date,
        data_conv: DataConventionIFR,
        state_data: Data1D,
        build_method: YieldCurveIndexBuildMethod | YieldCurveFundingBuildMethod,
    ):

        time_to_anchored_dates = []
        values = []
        market_data = []
        for i in range(len(state_data.axis1)):
            this_x = state_data.axis1[i]
            if TermOrTerminationDate(this_x).is_term():
                # if it is term
                moved_date = add_period(
                    value_date,
                    Period(this_x),
                    data_conv.business_day_convention,
                    data_conv.holiday_convention,
                )
                time = accrued(value_date, moved_date)
            else:
                # if it is date
                time = accrued(value_date, Date(this_x))
            time_to_anchored_dates.append(time)
            values.append(state_data.values[i])
            market_data.append(
                [
                    "INSTANTANEOUS FORWARD RATE",
                    data_conv.conv_name,
                    this_x,
                    "",
                    state_data.values[i],
                    state_data.data_identifier.unit(),
                ]
            )

        combined_data = np.asarray([time_to_anchored_dates, values], dtype=float)
        if combined_data.shape[1] == 0:
            raise ValueError(f"{data_conv.name}: IFR data must contain at least one node.")
        if not np.all(np.isfinite(combined_data)):
            raise ValueError(f"{data_conv.name}: node times and IFR values must be finite.")
        if np.any(combined_data[0] < 0):
            raise ValueError(f"{data_conv.name}: IFR nodes cannot precede the model value date.")
        if not np.all(np.diff(combined_data[0]) > 0):
            raise ValueError(f"{data_conv.name}: IFR node times must be strictly increasing.")

        return YieldCurveModelComponent(
            value_date,
            build_method.target_index,
            combined_data,
            build_method,
            market_data=market_data,
        )


    @staticmethod
    def calibrate_single_component_from_mkt_data(
        model: Model, model_component: ModelComponent, solver_info: YieldCurveBuildMethodCommon
    ):

        calib_prod = model_component.calibration_product
        calib_funding = model_component.calibration_funding
        assert len(calib_prod) == len(calib_funding)
        for id, (prod, funding) in enumerate(zip(calib_prod, calib_funding)):
            fi_vp = FundingIndexParameter({"Funding Index": funding})
            vpc = ValuationParametersCollection([fi_vp])
            engine = ValuationEngineProductRegistry.new_valuation_engine(
                model, prod, vpc, ValuationRequest.PV_DETAILED
            )
            initial_guess = 0.0

            YieldCurveCalibration.calibrate_state_var(
                engine, model_component.component_identifier, id, solver_info, initial_guess
            )


    @staticmethod
    def prepare_calibrate_instruments(
        value_date: Date, mkt_data_list: List[Data1D], build_method: BuildMethod, fpt: pd.DataFrame
    ):

        dt, dconv = "DATA TYPE", "DATA CONVENTION"
        ### create calibration instrument tuples, i.e., (time_to_anchored_time, product)
        valid_count = set()
        calib_instrument_quadruple = []
        for data in mkt_data_list:
            if data.data_type.upper() not in {'OVERNIGHT INDEX SWAP', 'SPREAD ZERO RATE'}:
                raise ValueError("This assignment calibrates OIS and zero funding spread only.")
            if data.data_type.upper() == 'SPREAD ZERO RATE' and any(float(v) != 0.0 for v in data.values):
                raise ValueError("Funding spread quotes must remain zero in this assignment.")
            data_convention = data.data_convention
            v = fpt[
                (fpt[dt].str.upper() == data.data_type.upper())
                & (fpt[dconv].str.upper() == data.data_convention.name.upper())
            ]
            funding_identifier = (
                v["FUNDING IDENTIFIER"].values[0] if len(v) != 0 else build_method.target
            )

            for axis1, value in zip(data.axis1, data.values):


                prod: Product = ProductFactory.create_product_from_data_convention(
                    value_date, axis1, data_convention, value, quote_style='yield'
                )

                tmp_acc = accrued(value_date, prod.last_date)
                if tmp_acc == 0.0:
                    tmp_acc = 1e-4  # not nice solution, but just for the sake of it
                valid_count.add(tmp_acc)
                calib_instrument_quadruple.append(
                    (
                        tmp_acc,
                        prod,
                        funding_identifier,
                        [
                            data.data_type,
                            data.data_convention.conv_name,
                            axis1,
                            "",
                            value,
                            data.data_identifier.unit(),
                        ],
                    )
                )
        assert len(valid_count) == len(calib_instrument_quadruple)
        sorted_calib_instruments = sorted(
            calib_instrument_quadruple,
            key=lambda calib_instrument_tuples: calib_instrument_tuples[0],
        )

        ### initialize state data and calibration product
        calib_instruments = []
        funding_identifiers = []
        time_to_anchored_dates = []
        sorted_mkt_data = []
        for each in sorted_calib_instruments:
            time_to_anchored_dates.append(each[0])
            calib_instruments.append(each[1])
            funding_identifiers.append(each[2])
            sorted_mkt_data.append(each[3])
        state_data = np.asarray([time_to_anchored_dates, [0.0] * len(time_to_anchored_dates)])

        ### initialize model component
        return YieldCurveModelComponent(
            value_date,
            build_method.target_index,
            state_data,
            build_method,
            calib_instruments,
            funding_identifiers,
            sorted_mkt_data,
        )


    @staticmethod
    def _sort_out_build_method_and_funding(build_method_collection: BuildMethodCollection,
                                          data_collection: DataCollection) -> Tuple[dict, List[BuildMethod]]:
        key_common = YieldCurveBuildMethodCommon._build_method_type
        key_index = YieldCurveIndexBuildMethod._build_method_type
        key_funding = YieldCurveFundingBuildMethod._build_method_type
        ordered_bm_list = {}
        other_build_methods = []
        for _, bm in build_method_collection.items:
            if isinstance(bm, YieldCurveBuildMethodCommon):
                funding_table = data_collection.get_data_from_data_collection('DATA GENERIC', bm['FUNDING PARAMETERS'])
                ordered_bm_list[bm.target] = {key_common: bm, DataGeneric._data_shape: funding_table.display()}
            elif isinstance(bm, (YieldCurveIndexBuildMethod, YieldCurveFundingBuildMethod)):
                other_build_methods.append(bm)
            else:
                raise TypeError("Unsupported yield-curve build method.")
        residual_build_methods = []
        for bm in other_build_methods:
            currency = bm.target_index.currency().code()
            if currency in ordered_bm_list and bm.instantaneous_forward_rate is None:
                kind = key_funding if isinstance(bm, YieldCurveFundingBuildMethod) else key_index
                ordered_bm_list[currency].setdefault(kind, []).append(bm)
            else:
                residual_build_methods.append(bm)
        for content in ordered_bm_list.values():
            content[key_index] = YieldCurveBuilder._sort_out_bm_dependency(content.get(key_index, []))
        return ordered_bm_list, residual_build_methods

    @staticmethod
    def _sort_out_bm_dependency(build_methods: List[BuildMethod]):
        bms_sorted = []
        not_stand_alone = []
        for bm in build_methods:
            if bm.reference_index is not None:
                not_stand_alone.append(bm)
            else:
                bms_sorted.append(bm)
        bms_sorted += not_stand_alone
        return bms_sorted


ModelBuilderRegistry().register(YieldCurve._model_type.to_string(), YieldCurveBuilder.create_model_yield_curve)
