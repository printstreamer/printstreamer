""" AFP PGD Record (Page Descriptor) """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP
from model.geometry import Rect
from units import POINTS_PER_INCH


afp_pgd_fields_list = [
    StreamFieldAFP(name="PTOCAdes", offset=0, length=32761, type="UNDF", optional=True, exception='\x00', range_values=['', '', '', ''], meaning=['Up to 32,759 bytes of', 'PTOCA-defined descriptor', 'data', '']),
    ]
afp_pgd_fields = {}
for field in afp_pgd_fields_list:
    afp_pgd_fields[field.name] = field


class AFP_PGD:
    """ Page Descriptor: declares the measurement units and extent of the page. """

    def __init__(self, segment):
        self.segment = segment
        self.document = self.segment.cur_document
        self.page = self.segment.cur_page
        self.x_unit_base = None
        self.y_unit_base = None
        self.x_units = None              # L-units per unit base in X
        self.y_units = None              # L-units per unit base in Y
        self.x_size = None               # page extent in X (L-units)
        self.y_size = None               # page extent in Y (L-units)

    def parse(self, data):
        """ Parse page geometry and apply it to the current model page.

        PGD layout: XpUnitBase(1) YpUnitBase(1) XpUnits(2) YpUnits(2)
                    XpSize(3) YpSize(3) [triplets...]
        Unit base 0x00 means the units count is "per 10 inches"; resolution in
        units/inch is therefore XpUnits / 10.
        """
        if len(data) < 12:
            return
        self.x_unit_base = data[0]
        self.y_unit_base = data[1]
        self.x_units = unpack(">H", data[2:4])[0]
        self.y_units = unpack(">H", data[4:6])[0]
        self.x_size = int.from_bytes(data[6:9], "big")
        self.y_size = int.from_bytes(data[9:12], "big")

        res_x = (self.x_units / 10.0) or 1440.0      # L-units per inch
        res_y = (self.y_units / 10.0) or 1440.0
        if self.page is not None:
            width_pts = self.x_size / res_x * POINTS_PER_INCH
            height_pts = self.y_size / res_y * POINTS_PER_INCH
            self.page.size = Rect(0, 0, width_pts, height_pts)
            # Stash resolution so PTOCA positioning can convert L-units to points.
            self.page.attributes["res_x"] = res_x
            self.page.attributes["res_y"] = res_y

    def format(self):
        """ Format the page geometry back into PGD record data. """
        return pack(">BBHHI", self.x_unit_base or 0, self.y_unit_base or 0,
                    self.x_units or 0, self.y_units or 0, 0)[:6] + \
            (self.x_size or 0).to_bytes(3, "big") + (self.y_size or 0).to_bytes(3, "big")
