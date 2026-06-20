""" Collect statistics as pages stream past (bounded memory) for the analyze process. """

from collections import Counter

from parse_options import PageSink


class StatsSink(PageSink):
    """ Tally documents, pages, and element/resource counts without retaining pages. """

    def __init__(self):
        self.documents = 0
        self.pages = 0
        self.elements = 0
        self.element_kinds = Counter()
        self.resources = Counter()

    def on_document_start(self, document):
        self.documents += 1

    def on_page(self, document, page):
        self.pages += 1
        for element in page.elements:
            self.elements += 1
            self.element_kinds[element.kind.value] += 1

    def on_document_end(self, document):
        if document is not None:
            for res in document.resource_library:
                self.resources[res.kind.value] += 1

    def report(self) -> str:
        lines = [
            "Analyze report:",
            f"  Documents:   {self.documents}",
            f"  Pages:       {self.pages}",
            f"  Elements:    {self.elements}",
        ]
        for kind, count in sorted(self.element_kinds.items()):
            lines.append(f"    {kind:<10} {count}")
        if self.resources:
            lines.append("  Resources:")
            for kind, count in sorted(self.resources.items()):
                lines.append(f"    {kind:<12} {count}")
        return "\n".join(lines)
