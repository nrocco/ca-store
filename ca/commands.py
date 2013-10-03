import os

from pycli_tools.parsers import get_argparser
from pycli_tools.commands import Command, arg

from ca import __version__

from ca.store import SslStore
from ca.store import OPENSSL_BIN

from ca.exceptions import SslStoreExistsError
from ca.exceptions import SslStoreNotInitializedError
from ca.exceptions import AuthorityExistsError
from ca.exceptions import AuthorityCertificateError
from ca.exceptions import AuthorityKeyError


class InitCommand(Command):
    '''bootstrap a new CA SslStore in the given directory.'''

    args = [
        arg('--force', action='store_true', help=\
            'if the current directory already exists and is not '
            'empty: do not ask for confirmation and overwrite '
            'its contents.')
    ]

    def run(self, args, store, parser):
        try:
            store.initialize(force=args.force)
        except SslStoreExistsError as e:
            parser.error('%s\nUse --force to overwrite' % e)
        else:
            parser.exit(message='Store initialized\n')


class DomainCommand(Command):
    '''create a server certificate for a FQDN'''

    args = [
        arg('domain', help='domain name to generate the certificate for')
    ]

    def run(self, args, store, parser):
        try:
            store.add_domain(args.domain)
        except SslStoreNotInitializedError:
            parser.error('No store in %s. Maybe you should bootstrap it first?'
                         % args.base_dir)


class GenerateCaCommand(Command):
    '''create the root certificate authority'''

    args = [
        arg('--days', default="3650",
            help='the amount of days the ca certificate is valid')
    ]

    def run(self, args, store, parser):
        try:
            store.generate_root_ca_key(args.days)
        except AuthorityExistsError as e:
            parser.error(e)
        except AuthorityCertificateError as e:
            parser.error(e)
        except AuthorityKeyError as e:
            parser.error(e)
        else:
            parser.exit(message='CA key generated in %s\n' % store.ca_key)


class ViewCertCommand(Command):
    '''view the subject of a generated certificate'''

    args = [
        arg('cert_file', help='the certificate file')
    ]

    def run(self, args, store, parser):
        print store.view_info(args.cert_file)



#####################################################################
#####################################################################



def main():
    parser = get_argparser(
        prog='ca',
        logging_format='[%(levelname)s] %(message)s',
        version=__version__,
        default_config='~/.carc',
        description='Certificate Authority Management'
    )
    parser.add_argument(
        '--openssl-bin',
        default=OPENSSL_BIN,
        help='specify an alternate openssl binary. '
             'if not specified defaults to %s' % OPENSSL_BIN
    )
    parser.add_argument(
        '--base-dir',
        default=os.getcwd(),
        help='base directory'
    )

    parser.add_commands([
        InitCommand(),
        DomainCommand(),
        GenerateCaCommand(),
        ViewCertCommand()
    ])

    # parse command line arguments
    args = parser.parse_args()

    # Initialize the SslStore
    store = SslStore(
        args.base_dir,
        openssl_bin=args.openssl_bin,
    )

    # call the subcommand handler function
    args.func(args, store=store, parser=parser)
