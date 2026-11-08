"""Public valuation parameters, PV/risk reports, and HW6 cashflow reports."""

from fixedincomelib.model import Model
from fixedincomelib.product import Product
from fixedincomelib.valuation.utilities import create_value_report

from fixedincomelib.valuation import (
    ValuationParameters, ValuationParametersBuilderRegistry,
    ValuationParametersCollection, ValuationRequest, ValuationEngineProductRegistry,
)
# Import the implementation to register its (model, product, method) key.
from fixedincomelib.yield_curve.valuation_engine import ValuationEngineProductFixedAccrued

__all__ = [
    "qfCreateValuationParameters", "qfCreateValuationParametersCollection", "qfCreateValueReport",
]


def qfCreateValuationParameters(vp_type: str, content: list | dict) -> ValuationParameters:
    parameter_cls = ValuationParametersBuilderRegistry().get(vp_type)
    return parameter_cls(content)


def qfCreateValuationParametersCollection(
    valuation_parameters: list[ValuationParameters],
) -> ValuationParametersCollection:
    return ValuationParametersCollection(valuation_parameters)


def qfCreateValueReport(
    model: Model,
    product: Product,
    valuation_parameters_collection: ValuationParametersCollection,
    request: str,
):

    this_report = create_value_report(
        model, product, valuation_parameters_collection, ValuationRequest.from_string(request)
    )

    return this_report


def qfCreateCashflowsReport(model, product, valuation_parameters_collection):
    """Return a cashflow snapshot for an interest-rate stream or composite product."""
    engine = ValuationEngineProductRegistry.new_valuation_engine(
        model, product, valuation_parameters_collection, ValuationRequest.PV)
    return engine.create_cash_flows_report()


__all__ += ["qfCreateCashflowsReport"]
