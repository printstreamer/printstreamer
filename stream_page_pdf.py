""" pdf printstream file page. """

import stream_pdf


class StreamPagePDF:
    """ pdf printstream page. """
    
    def __init__(self, segment, offset=None):
        self.segment = segment
        self.offset = offset
        self.length = 0
        self.data = None
        self.text = []
        self.images = []
        self.attributes = {}

    def parse(self):
        """ Parse a pdf printstream page. """
        # Parse pdf page.
        self.data = self.segment.file_obj.load_page(self.offset)
        # # Extract text with position and font.
        # text_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]
        # Extract text and bounding boxes.
        for block in self.data.get_text("dict")["blocks"]:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        x0, y0, x1, y1 = span["bbox"]
                        self.text.append({
                            "text": span["text"],
                            "font_name": span["font"],
                            "font_size": span["size"],
                            "color": span["color"],
                            "color_rgb": stream_pdf.decode_color(span["color"]),
                            "x": x0,
                            "y": y0,
                            "bbox": (x0, y0, x1, y1),
                        })
                        # # Update overall text bounding box
                        # text_bbox[0] = min(text_bbox[0], x0)
                        # text_bbox[1] = min(text_bbox[1], y0)
                        # text_bbox[2] = max(text_bbox[2], x1)
                        # text_bbox[3] = max(text_bbox[3], y1)
