"""Template identifiers for curve inputs and the funding-parameter table."""

from typing import Tuple
from abc import ABC, abstractmethod

from fixedincomelib.market.data_conventions import DataConvention, DataConventionIFR, DataConventionRFRSwap
from fixedincomelib.market.registries import DataIdentifierRegistry

__all__ = ["DataIdentifier", "DataIdentifierIFR", "DataIdentifierOvernightIndexSwap"]


class DataIdentifier(ABC):

    _data_type = ''

    def __init__(self, data_convention : DataConvention|str) -> None:
        self.data_convention_ = data_convention
        self.data_identifier_ = (self._data_type, data_convention if isinstance(data_convention, str) else data_convention.name)
    
    @property
    def data_type(self) -> str:
        return self._data_type
    
    @property
    def data_convention(self) -> DataConvention|str:
        return self.data_convention_
    
    @property
    def data_identifier(self) -> Tuple[str, str]:
        return self.data_identifier_

    def to_string(self):
        name =  self.data_convention if isinstance(self.data_convention, str) else self.data_convention.name
        return f'{self.data_type}:{name}'
    
    @abstractmethod
    def unit(self):
        pass


class DataIdentifierIFR(DataIdentifier):

    _data_type = 'Instantaneous Forward Rate'

    def __init__(self, data_convention: DataConventionIFR) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001


DataIdentifierRegistry().register(DataIdentifierIFR._data_type.upper(), DataIdentifierIFR)


class DataIdentifierOvernightIndexSwap(DataIdentifier):
    """Par OIS rates in decimals; report a positive one-basis-point rate move."""

    _data_type = 'Overnight Index Swap'

    def __init__(self, data_convention: DataConventionRFRSwap) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001


DataIdentifierRegistry().register(DataIdentifierOvernightIndexSwap._data_type.upper(), DataIdentifierOvernightIndexSwap)


from fixedincomelib.market.data_conventions import DataConventionZeroSpread

class DataIdentifierZeroSpread(DataIdentifier):

    _data_type = 'Spread Zero Rate'

    def __init__(self, data_convention: DataConventionZeroSpread) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001


class DataIdentifierDataGeneric(DataIdentifier):

    _data_type = 'Data Generic'

    def __init__(self, data_label: str) -> None:
        super().__init__(data_label)

    def unit(self):
        pass

__all__ += ["DataIdentifierZeroSpread", "DataIdentifierDataGeneric"]
DataIdentifierRegistry().register(DataIdentifierZeroSpread._data_type.upper(), DataIdentifierZeroSpread)
DataIdentifierRegistry().register(DataIdentifierDataGeneric._data_type.upper(), DataIdentifierDataGeneric)
