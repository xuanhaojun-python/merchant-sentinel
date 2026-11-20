import re


class DemoPage:
    PATH = "/demo"
    SUBMIT = "button[type=submit]"
    TITLE_TEXT = "Demo Title"
    ROW_XPATH = "//table//tr"
    URL_PATTERN = re.compile(r"/demo/\d+")
    timeout = 3000  # 非大写常量，忽略
    RETRIES = 3     # 非字符串，忽略

    def submit(self):
        return self.SUBMIT, self.SUBMIT
