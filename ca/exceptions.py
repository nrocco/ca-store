class SslStoreExistsError(Exception):
    pass


class SslStoreNotInitializedError(Exception):
    pass


class SslStoreError(Exception):
    pass


class AuthorityExistsError(Exception):
    pass


class AuthorityCertificateError(Exception):
    pass


class AuthorityKeyError(Exception):
    pass
