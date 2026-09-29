"""t 分布分位数垫片。

优先使用 scipy.stats；scipy 不可用时通过 t 分布 CDF（正则化不完全 Beta，
数值有递推稳定实现）做二分求逆，df>=1 时对常用置信水平精度优于 1e-6。
计算核心因此只需标准库 + NumPy（NumPy 仅其余模块使用）。
"""

import math

try:  # pragma: no cover - 取决于环境
    from scipy.stats import t  # type: ignore
except Exception:  # pragma: no cover

    def _betacf(a: float, b: float, x: float, itmax: int = 200,
                eps: float = 3e-14) -> float:
        """连分式展开的不完全 beta 函数辅因子（Numerical Recipes, Lentz 法）。"""
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        h = d
        for m in range(1, itmax + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < eps:
                break
        return h

    def _betai(a: float, b: float, x: float) -> float:
        """正则化不完全 beta 函数 I_x(a,b)。"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        bt = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
        if x < (a + 1.0) / (a + b + 2.0):
            return bt * _betacf(a, b, x) / a
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

    def _t_cdf(x: float, df: float) -> float:
        """Student t 分布 CDF。"""
        z = df / (df + x * x)
        ib = _betai(df / 2.0, 0.5, z)
        return 1.0 - 0.5 * ib if x > 0 else 0.5 * ib

    class _T:
        @staticmethod
        def ppf(p, df):
            """对 CDF 二分求逆，df>=1。"""
            df = float(df)
            p = float(p)
            if not 0.0 < p < 1.0:
                raise ValueError("p 必须在 (0,1) 内")
            lo, hi = -1.0, 1.0
            while _t_cdf(hi, df) < p:
                hi *= 2.0
            while _t_cdf(lo, df) > p:
                lo *= 2.0
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if _t_cdf(mid, df) < p:
                    lo = mid
                else:
                    hi = mid
            return 0.5 * (lo + hi)

    t = _T()
