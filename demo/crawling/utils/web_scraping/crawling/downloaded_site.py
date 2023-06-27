"""Module containing the DownloadedSite class"""


class DownloadedSite:
    """Class representing a tuple with url and path to file"""

    url: str
    path_to_file: str

    def __init__(self, url: str, path_to_file: str):
        self.url = url
        self.path_to_file = path_to_file

    def __str__(self) -> str:
        return "{url: " + self.url + ", path_to_file: " + self.path_to_file + "}"
