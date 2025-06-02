from typing import Any, Dict, List, Union
from bidict import bidict
import pandas as pd

class NewsBiHashList:
    def __init__(self) -> None:
        self._list: List[Dict[str, Any]] = []
        self._bD: bidict[Union[str, int], int] = bidict()

    def __getitem__(self, key: Union[str, int]) -> Dict[str, Any]:
        return self._list[self._bD[key]]

    def get_item_by_index(self, index: int) -> Dict[str, Any]:
        return self._list[index]

    def __len__(self) -> int:
        return len(self._list)

    def __setitem__(self, key: Union[str, int], value: Dict[str, Any]) -> None:
        if key in self._bD:
            self._list[self._bD[key]] = value
        else:
            self.append(key, value)

    def append(self, key: Union[str, int], value: Dict[str, Any]) -> None:
        self._list.append(value)
        self._bD[key] = len(self._list) - 1

    def __delitem__(self, key: Union[str, int]) -> None:
        if key not in self._bD:
            raise KeyError(f"Key {key} not in BiHashList")
        index: int = self._bD[key]
        del self._list[index]
        del self._bD[key]
        for k, v in self._bD.items():
            if v > index:
                self._bD[k] -= 1

    def del_item_by_index(self, index: int) -> None:
        if index not in self._bD.inv:
            raise KeyError(f"Index {index} not in BiHashList")
        key: Union[str, int] = self._bD.inv[index]
        del self._list[index]
        del self._bD[key]
        for k, v in self._bD.items():
            if v > index:
                self._bD[k] -= 1

    def __contains__(self, key: Union[str, int]) -> bool:
        return key in self._bD

    def return_ranged_value_list_from_indices(self, start_index: int, end_index: int) -> List[Dict[str, Any]]:
        return self._list[start_index:end_index + 1]

    def return_ranged_value_list_from_keys(self, start_key: Union[str, int], end_key: Union[str, int]) -> List[Dict[str, Any]]:
        start_index: int = self._bD[start_key]
        end_index: int = self._bD[end_key]
        return self._list[start_index:end_index + 1]



# Assuming df_news is already created
# news_store = NewsBiHashList()

# for _, row in df_news.iterrows():
    # print('row: ', row)
    # key = row['datetime']  # Use datetime as key
    # value = row.to_dict()  # Storing the entire row as a dictionary
    # news_store.append(key, value)
