class FlaskCustomError(Exception):
    def __init__(self, error_title: str, error_list: list, error_code: str, response_code:int):
        self.error_title = error_title
        self.error_list = error_list
        self.error_code = error_code
        self.response_code = response_code