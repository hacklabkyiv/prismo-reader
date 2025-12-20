class UrlParser:
    url = None
    scheme = None
    netloc = None
    hostname = None
    port = None

    def __init__(self, url):
        self.url = url
        self.parse()

    def parse(self):
        if self.url[:7] == "http://":
            self.scheme = "http"
            self.netloc = self.url[7:]
        elif self.url[:8] == "https://":
            self.scheme = "https"
            self.netloc = self.url[8:]
        else:
            self.netloc = self.url

        if "/" in self.netloc:
            self.netloc = self.netloc[:self.netloc.index("/")]

        if ":" in self.netloc:
            self.hostname, self.port = self.netloc.split(":")
        else:
            self.hostname = self.netloc

        return self

    @property
    def get_scheme(self):
        return self.scheme if self.scheme else "http"

    def __str__(self):
        return "scheme: {}, netloc: {}, hostname: {}, port: {}".format(self.scheme, self.netloc, self.hostname, self.port)

    def __repr__(self):
        return self.__str__()
