import os
import logging
import subprocess

from ca.exceptions import AuthorityCertificateError
from ca.exceptions import AuthorityExistsError
from ca.exceptions import AuthorityKeyError
from ca.exceptions import SslStoreError
from ca.exceptions import SslStoreExistsError
from ca.exceptions import SslStoreNotInitializedError


logger = logging.getLogger(__name__)


OPENSSL_BIN = '/usr/bin/openssl'

OPENSSL_CONFIG_TEMPLATE = """\
prompt = no
distinguished_name = req_distinguished_name

[ req_distinguished_name ]
C                      = NL
ST                     = Noord-Holland
L                      = Amsterdam
O                      = CasaDiRocco
OU                     = CasaDiRocco
CN                     = %s
emailAddress           = dirocco.nico@gmail.com
"""


class OpenSsl(object):
    binary = OPENSSL_BIN

    def __init__(self, binary=OPENSSL_BIN):
        self.binary = binary

    def execute(self, *args):
        cmdline = [self.binary] + list(args)
        logger.debug('> %s', ' '.join(cmdline))
        return subprocess.check_output(cmdline)

    def get_subject_from_crt(self, certificate):
        return self.execute('x509', '-noout', '-in', certificate, '-subject')


class SslStore(object):
    INDEX_ENTRY = "{unkown}\t{id}\t{serial}\t{subject}"

    def __init__(self, dir, openssl_bin=OPENSSL_BIN):
        self.openssl = OpenSsl(binary=openssl_bin)

        self.dir = os.path.abspath(dir)
        self.ca_key = os.path.join(self.dir, 'ca', 'ca.key')
        self.ca_crt = os.path.join(self.dir, 'ca', 'ca.crt')
        self.serials = os.path.join(self.dir, '.serials')

    def initialized(self):
        if not os.path.exists(self.dir):
            return False
        if not os.path.exists(self.ca_key):
            return False
        if not os.path.exists(self.ca_crt):
            return False
        if not os.path.exists(self.serials):
            return False
        return True

    def reset(self):
        logger.debug('Deleting contents of %s', self.dir)
        for root, dirs, files in os.walk(self.dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def initialize(self, force=False):
        logger.debug('Initialize CA SslStore in %s', self.dir)

        if not os.path.exists(self.dir):
            logger.info('Creating directory %s.', self.dir)
            os.makedirs(self.dir)
        elif os.listdir(self.dir) == []:
            pass
        elif force:
            logger.info('Directory %s exists.', self.dir)
            self.reset()
        else:
            raise SslStoreExistsError('Directory %s already exists.' %
                                      self.dir)

        os.makedirs(os.path.join(self.dir, 'ca'))
        os.makedirs(os.path.join(self.dir, 'domains'))

        self.write_serial(serial=1)

    def generate_root_ca_key(self, days=3650):
        has_ca_key = os.path.exists(self.ca_key)
        has_ca_crt = os.path.exists(self.ca_crt)

        if has_ca_key and has_ca_crt:
            raise AuthorityExistsError('CA certificates already exist')
        elif has_ca_key and not has_ca_crt:
            raise AuthorityCertificateError('CA is missing its certificate')
        elif not has_ca_key and has_ca_crt:
            raise AuthorityKeyError('CA is missing its key')

        logger.info('Generating the CA key and certificate.')

        try:
            self.openssl.execute(
                'req', '-new', '-x509',
                '-extensions', 'v3_ca',
                '-keyout', self.ca_key,
                '-out', self.ca_crt,
                '-days', str(days)
            )
        except subprocess.CalledProcessError as e:
            raise SslStoreError(e)

    def get_next_serial(self):
        return open(self.serials, 'r').read()

    def write_serial(self, serial=None):
        if not serial:
            serial = int(self.get_next_serial()) + 1

        logger.debug('Writing serial %d to .serials', serial)
        file = open(self.serials, 'w')
        file.write('%02d' % serial)
        file.close()

    def add_domain(self, domain_name, days=365):
        if not self.initialized():
            raise SslStoreNotInitializedError()

        key = os.path.join(self.dir, 'domains', '%s.key' % domain_name)
        csr = os.path.join(self.dir, 'domains', '%s.csr' % domain_name)
        crt = os.path.join(self.dir, 'domains', '%s.crt' % domain_name)
        cnf = os.path.join(self.dir, 'domains', '%s.cnf' % domain_name)

        config = open(cnf, 'w')
        config.write(OPENSSL_CONFIG_TEMPLATE % domain_name)
        config.close()

        try:
            logger.info('Generating a private key')
            self.openssl.execute('genrsa', '-out', key, '1024')
            logger.info('Generating a certificate signing request')
            self.openssl.execute('req', '-new', '-key', key,
                                 '-out', csr, '-config', cnf)
            logger.info('Generating a certificate and sign with CA')
            self.openssl.execute('x509', '-req', '-days', str(days),
                                 '-CA', self.ca_crt, '-CAkey', self.ca_key,
                                 '-in', csr, '-out', crt,
                                 '-set_serial', self.get_next_serial())
        except Exception as e:
            for f in [key, csr, crt, cnf]:
                try:
                    os.remove(f)
                except OSError:
                    pass
            raise e
        else:
            self.write_serial()

    def view_info(self, file, type='cert'):
        if 'cert' == type:
            return self.openssl.get_subject_from_crt(file)
        else:
            raise SslStoreError('%s type not supported' % type)

    def __str__(self):
        return '<SslStore dir=%s>' % self.dir
