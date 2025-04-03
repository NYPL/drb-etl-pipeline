import hashlib
import io
import os

import PIL
import pypdf
import requests
import requests.exceptions

from logger import create_log
from managers.coverFetchers.abstractFetcher import AbstractFetcher

logger = create_log(__name__)


class PublisherBacklistCoverFetcher(AbstractFetcher):

    def __init__(self, *args):
        super().__init__(*args)

        self.session = requests.Session()
        self.bucket = os.environ["FILE_BUCKET"]
        self.pdf_url: str | None = None


    def hasCover(self):
        for value, source in self.identifiers:
            if source != "hathi":
                continue

            url = (
                f"https://{self.bucket}.s3.us-east-1.amazonaws.com"
                f"/titles/publisher_backlist/Schomburg/{value}/{value}.pdf"
            )

            response = self.session.head(url)

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                continue
            except Exception as e:
                logger.exception("Unexpected error when fetching PDF")
                continue
            else:
                self.pdf_url = url
                return True

        return False

    def downloadCoverFile(self) -> bytes:
        with io.BytesIO() as stream:
            response = self.session.get(self.pdf_url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                stream.write(chunk)

            with pypdf.PdfReader(stream) as pdf:
                image = PublisherBacklistCoverFetcher.find_cover_in_pdf(pdf)

        with io.BytesIO() as outstream:
            # image.tobytes() returns Pillow's internal image representation, which appears
            # to not be a file type that is generally readable by a browser or Preview.
            # Instead, write to a stream using the`save` method, and read the bytes off the
            # stream
            image.save(outstream, format="PNG")
            return outstream.getvalue()


    @staticmethod
    def find_cover_in_pdf(pdf: pypdf.PdfReader) -> PIL.Image:
        for page in pdf.pages:
            image = page.images[0].image
            if page.extract_text():
                return image

            if image.entropy() < 0.001:
                continue

            return image
