import numpy as np, pandas as pd

class FinancialFeatureBuilder:

    @staticmethod
    def divide(a,b):
        result = a / b

        return result.replace([np.inf, -np.inf], np.nan)

    def build(self, df):
        df = df.copy()

        df = df.sort_values(["ticker", "fiscal_year", "fiscal_quarter"]).reset_index(drop=True)

        df["current_ratio"] = self.divide(df["current_assets"], df["current_liabilities"])
        df["cash_to_assets"] = self.divide(df["cash"], df["total_assets"])

        df["operating_margin"] = self.divide(df["operating_income"], df["revenue"])
        df["net_margin"] = self.divide(df["net_income"], df["revenue"])

        df["free_cash_flow"] = (df["operating_cash_flow"] - df["capex"])
        df["ocf_margin"] = self.divide(df["operating_cash_flow"], df["revenue"])
        df["fcf_margin"] = self.divide(df["free_cash_flow"], df["revenue"])


        grouped = df.groupby("ticker")

        previous_revenue = grouped["revenue"].shift(4)

        df["revenue_growth_yoy"] = (
            self.divide(
                df["revenue"] - previous_revenue,
                previous_revenue.abs()
            )
        )

        previous_income = grouped["net_income"].shift(4)

        df["net_income_change_yoy"] = (
            self.divide(
                df["net_income"] - previous_income,
                previous_income.abs()
            )
        )

        return df
