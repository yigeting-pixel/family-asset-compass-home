from __future__ import annotations

from pathlib import Path
import pandas as pd


class BaseFundDataProvider:
    """正式数据接入抽象层。

    生产环境建议在这里接入授权数据源，例如 Wind、聚源、天相、同花顺 iFinD、
    基金公司直连、托管行数据、内部产品库等。
    """

    def fund_master(self) -> pd.DataFrame:
        raise NotImplementedError

    def nav(self) -> pd.DataFrame:
        raise NotImplementedError

    def holdings(self) -> pd.DataFrame:
        raise NotImplementedError

    def managers(self) -> pd.DataFrame:
        raise NotImplementedError

    def peer_rank(self) -> pd.DataFrame:
        raise NotImplementedError


class LocalCSVFundDataProvider(BaseFundDataProvider):
    def __init__(self, data_dir: str | Path = "data"):
        self.data_dir = Path(data_dir)

    def _read(self, filename: str) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / filename)

    def fund_master(self) -> pd.DataFrame:
        return self._read("fund_master.csv")

    def nav(self) -> pd.DataFrame:
        df = self._read("nav.csv")
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values(["code", "date"])

    def holdings(self) -> pd.DataFrame:
        return self._read("holdings.csv")

    def managers(self) -> pd.DataFrame:
        return self._read("manager.csv")

    def peer_rank(self) -> pd.DataFrame:
        return self._read("rank.csv")


class VendorFundDataProvider(BaseFundDataProvider):
    """正式数据供应商适配器占位。

    你只需要把下面 5 个方法替换为正式接口或数据库查询，前端和推荐引擎不用改。
    推荐返回字段与 data/*.csv 保持一致。
    """

    def __init__(self, config: dict):
        self.config = config

    def fund_master(self) -> pd.DataFrame:
        raise NotImplementedError("请接入正式基金基本资料接口")

    def nav(self) -> pd.DataFrame:
        raise NotImplementedError("请接入正式净值接口")

    def holdings(self) -> pd.DataFrame:
        raise NotImplementedError("请接入正式持仓接口")

    def managers(self) -> pd.DataFrame:
        raise NotImplementedError("请接入正式基金经理接口")

    def peer_rank(self) -> pd.DataFrame:
        raise NotImplementedError("请接入正式同类排名接口")
