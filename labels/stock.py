""" Common label stock templates. All geometry in printer points (1/72 inch). """

from dataclasses import dataclass

from model.geometry import Rect


@dataclass
class LabelStock:
    name: str
    page_width: float
    page_height: float
    rows: int
    cols: int
    label_width: float
    label_height: float
    margin_top: float
    margin_left: float
    h_pitch: float          # left-to-left distance between columns
    v_pitch: float          # top-to-top distance between rows

    @property
    def page_size(self) -> Rect:
        return Rect(0, 0, self.page_width, self.page_height)

    @property
    def per_sheet(self) -> int:
        return self.rows * self.cols


def _in(v):
    return v * 72.0


# A few common stocks (US Letter = 612x792 pt).
STOCKS = {
    # Avery 5160 address labels: 3 x 10, 2.625" x 1".
    "avery-5160": LabelStock("avery-5160", 612, 792, 10, 3, _in(2.625), _in(1.0),
                             margin_top=_in(0.5), margin_left=_in(0.1875),
                             h_pitch=_in(2.75), v_pitch=_in(1.0)),
    # Avery 5163 shipping labels: 2 x 5, 4" x 2".
    "avery-5163": LabelStock("avery-5163", 612, 792, 5, 2, _in(4.0), _in(2.0),
                             margin_top=_in(0.5), margin_left=_in(0.15625),
                             h_pitch=_in(4.1875), v_pitch=_in(2.0)),
    # Avery 5167 return-address labels: 4 x 20, 1.75" x 0.5".
    "avery-5167": LabelStock("avery-5167", 612, 792, 20, 4, _in(1.75), _in(0.5),
                             margin_top=_in(0.5), margin_left=_in(0.28125),
                             h_pitch=_in(2.0625), v_pitch=_in(0.5)),
}


def get_stock(name) -> LabelStock:
    try:
        return STOCKS[name]
    except KeyError:
        raise ValueError(f"Unknown label stock {name!r}; known: {', '.join(STOCKS)}")
