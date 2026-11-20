from pages.demo_page import DemoPage


class ChildPage(DemoPage):
    def title(self):
        return self.TITLE_TEXT
