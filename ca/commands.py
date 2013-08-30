import os

from pycli_tools.parsers import get_argparser

from ca import __version__

from ca.store import SslStore
from ca.store import OPENSSL_BIN

from ca.exceptions import SslStoreExistsError
from ca.exceptions import SslStoreNotInitializedError
from ca.exceptions import AuthorityExistsError
from ca.exceptions import AuthorityCertificateError
from ca.exceptions import AuthorityKeyError


def handle_init(args, store, parser):
    try:
        store.initialize(force=args.force)
    except SslStoreExistsError as e:
        parser.error('%s\nUse --force to overwrite' % e)
    else:
        parser.exit(message='Store initialized\n')


def handle_domain(args, store, parser):
    try:
        store.add_domain(args.domain)
    except SslStoreNotInitializedError:
        parser.error('No store in %s. Maybe you should bootstrap it first?'
                     % args.base_dir)


def handle_generate_ca(args, store, parser):
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


def handle_view_cert(args, store, parser):
    print store.view_info(args.cert_file)


#####################################################################
#####################################################################


def add_parser_for_init(subparsers):
    parser = subparsers.add_parser(
        'init',
        help='bootstrap a new CA SslStore in the given directory.'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='if the current directory already exists and is not '
             'empty: do not ask for confirmation and overwrite '
             'its contents.'
    )
    parser.set_defaults(func=handle_init)
    return parser


def add_parser_for_domain(subparsers):
    parser = subparsers.add_parser(
        'domain',
        help='create a server certificate for a FQDN'
    )
    parser.add_argument(
        'domain',
        help='domain name to generate the certificate for'
    )
    parser.set_defaults(func=handle_domain)
    return parser


def add_parser_for_generate_ca(subparsers):
    parser = subparsers.add_parser(
        'generate-ca',
        help='create the root certificate authority'
    )
    parser.add_argument(
        '--days', default="3650",
        help='the amount of days the ca certificate is valid'
    )
    parser.set_defaults(func=handle_generate_ca)
    return parser


def add_parser_for_view_cert(subparsers):
    parser = subparsers.add_parser(
        'view-cert',
        help='view the subject of a generated certificate'
    )
    parser.add_argument(
        'cert_file',
        help='the certificate file'
    )
    parser.set_defaults(func=handle_view_cert)
    return parser


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
    subparsers = parser.add_subparsers()

    add_parser_for_init(subparsers)
    add_parser_for_domain(subparsers)
    add_parser_for_generate_ca(subparsers)
    add_parser_for_view_cert(subparsers)

    # parse command line arguments
    args = parser.parse_args()

    # Initialize the SslStore
    store = SslStore(
        args.base_dir,
        openssl_bin=args.openssl_bin,
    )

    # call the subcommand handler function
    parser.exit(args.func(args, store=store, parser=parser))
