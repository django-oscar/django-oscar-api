from os.path import splitext
import shutil
import tempfile
from urllib.request import urlopen
from urllib.parse import urlsplit

from django.conf import settings


def download_binary_file(request):
    response = urlopen(request)
    return response_to_temporary_file(response)


def determine_extension(response):
    try:
        url = response.geturl()
        parsed_url = urlsplit(url)
        path = parsed_url.path
    except AttributeError:
        path = response.name

    _, ext = splitext(path)
    return ext


def response_to_temporary_file(response):
    # Try to keep file in memory, but do not exceed FILE_UPLOAD_MAX_MEMORY_SIZE
    result_file = tempfile.SpooledTemporaryFile(
        max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
        mode="w+b",
        suffix=".upload%s" % determine_extension(response),
        dir=settings.FILE_UPLOAD_TEMP_DIR,
    )
    # copy the response into a file so it can be read multiple times
    shutil.copyfileobj(response, result_file)

    result_file.seek(0)
    return result_file
