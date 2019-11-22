import hashlib


def file_hash(content):
    """
    file_hash will hash the content of a file.

    >>> from io import BytesIO
    >>> long_text = "Harrie en Henk (Hent)" * 879
    >>> file_hash(BytesIO(long_text.encode()))
    'cf3c7be4778cded29fab4b66622c5e8af91d01a9'
    """
    sha1 = getattr(content, "sha1", None)
    if sha1 is not None:
        return sha1

    hasher = hashlib.sha1()
    buf = content.read(65536)
    while len(buf) > 0:
        hasher.update(buf)
        buf = content.read(65536)

    content.seek(0)
    return hasher.hexdigest()
