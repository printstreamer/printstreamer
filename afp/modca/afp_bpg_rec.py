""" AFP BPG Record """

from struct import pack, unpack

from stream_field_afp import StreamFieldAFP


afp_bpg_fields_list = [
    StreamFieldAFP(name="PageName", offset=0, length=8, type="CHAR", optional=True, exception='\x02', range_values=['', ''], meaning=['Name of the page', '']),
    StreamFieldAFP(name="Triplets", offset=8, length=32753, type="", optional=True, exception='\x10', range_values=['', '', ''], meaning=['See "BPG Semantics" for', 'triplet applicability.', '']),
    ]
afp_bpg_fields = {}
for field in afp_bpg_fields_list:
    afp_bpg_fields[field.name] = field


class AFP_BPG:

    def __init__(self, segment):
        self.segment = segment
        self.page = self.segment.cur_page
        self.page_width = None
        self.page_height = None
        # Offset: Length: Type: Optional: Exception: Range:                Meaning:
        self.PageName = None            #      0       8  CHAR  y         X'02'                            Name of the page
        self.Triplets = None            #      8   32753        y         X'10'                            See "BPG Semantics" for
                                        #                                                                  triplet applicability.

    def parse(self, data):
        """ Parse the Begin Page record: page name and triplets.

        Page geometry comes from the Page Descriptor (PGD); BPG only carries the page
        name (and optional triplets), which we surface on the model page.

        :param bytes data: Record data
        """
        if len(data) >= 8:
            self.PageName, self.Triplets = unpack(f">8s{len(data) - 8}s", data)
        else:
            self.PageName = b""
            self.Triplets = b""
        if self.page is not None:
            name = self.PageName.decode("cp500", "replace").strip()
            if name:
                self.page.attributes["name"] = name

    def format(self):
        """ Format the data from the record class fields into a record.

        :returns: Record data
        """
        data = pack(f">8s{len(self.Triplets)}s", self.PageName, self.Triplets)
        return data
