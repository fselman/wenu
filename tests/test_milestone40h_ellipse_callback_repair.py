import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

from wenu.charts.legend import _legend_ellipse


def test_ellipse_factory_accepts_matplotlib_keyword_contract():
    figure, ax = plt.subplots()
    try:
        original = Ellipse(
            (0.0, 0.0),
            width=1.0,
            height=0.5,
            facecolor="red",
        )
        result = _legend_ellipse(
            legend=ax.legend([], []),
            orig_handle=original,
            xdescent=0.0,
            ydescent=0.0,
            width=20.0,
            height=7.0,
            fontsize=10.0,
        )
        assert isinstance(result, Ellipse)
        assert result.width > result.height
    finally:
        plt.close(figure)
