"""Collection of classes and methods used by various hvac test cases."""
import base64
import json
import logging
import operator
import os
import re
import socket
import subprocess
import sys
import time
import warnings
from distutils.version import StrictVersion

from mock import patch

from hvac import Client

try:
    # Python 2.7
    from http.server import BaseHTTPRequestHandler
except ImportError:
    # Python 3.x
    from BaseHTTPServer import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

VERSION_REGEX = re.compile(r'Vault v([0-9.]+)')
LATEST_VAULT_VERSION = '0.11.4'


def get_installed_vault_version():
    command = ['vault', '-version']
    process = subprocess.Popen(**get_popen_kwargs(args=command, stdout=subprocess.PIPE))
    output, _ = process.communicate()
    version = output.strip().split()[1].lstrip('v')
    # replace any '-beta1' type substrings with a StrictVersion parsable version. E.g., 1.0.0-beta1 => 1.0.0b1
    version = version.replace('-', '').replace('beta', 'b')
    return version


def skip_if_vault_version(supported_version, comparison=operator.lt):
    current_version = os.getenv('HVAC_VAULT_VERSION')
    if current_version is None or current_version.lower() == 'head':
        current_version = get_installed_vault_version()

    return comparison(StrictVersion(current_version), StrictVersion(supported_version))


def skip_if_vault_version_lt(supported_version):
    return skip_if_vault_version(supported_version, comparison=operator.lt)


def skip_if_vault_version_ge(supported_version):
    return skip_if_vault_version(supported_version, comparison=operator.ge)


def create_client(**kwargs):
    """Small helper to instantiate a :py:class:`hvac.v1.Client` class with the appropriate parameters for the test env.

    :param kwargs: Dictionary of additional keyword arguments to pass through to the Client instance being created.
    :type kwargs: dict
    :return: Instantiated :py:class:`hvac.v1.Client` class.
    :rtype: hvac.v1.Client
    """
    client_cert_path = get_test_data_path('client-cert.pem')
    client_key_path = get_test_data_path('client-key.pem')
    server_cert_path = get_test_data_path('server-cert.pem')

    return Client(
        url='https://localhost:8200',
        cert=(client_cert_path, client_key_path),
        verify=server_cert_path,
        **kwargs
    )


def get_free_port():
    """Small helper method used to discover an open port to use by mock API HTTP servers.

    :return: An available port number.
    :rtype: int
    """
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def load_test_data(filename):
    """Load test data for use by various test cases.

    :param filename: Name of the test data file.
    :type filename: str | unicode
    :return: Test data contents
    :rtype: str | unicode
    """
    test_data_path = get_test_data_path(filename)
    with open(test_data_path, 'r') as f:
        test_data = f.read()
    return test_data


def get_test_data_path(filename):
    """Get the path to a file under the "test data" directory. I.e., the directory containing self-signed certificates,
        configuration files, etc. that are used for various tests.

    :param filename: Name of the test data file.
    :type filename: str | unicode
    :return: The absolute path to the test data directory.
    :rtype: str | unicode
    """
    # Use __file__ to derive a path relative to this module's location which points to the test data directory.
    relative_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'test')
    return os.path.join(os.path.abspath(relative_path), filename)


def decode_generated_root_token(encoded_token, otp):
    """Decode a newly generated root token via Vault CLI.

    :param encoded_token: The token to decode.
    :type encoded_token: str | unicode
    :param otp: OTP code to use when decoding the token.
    :type otp: str | unicode
    :return: The decoded root token.
    :rtype: str | unicode
    """
    command = ['vault']
    if skip_if_vault_version_ge('0.9.6'):
        # before Vault ~0.9.6, the generate-root command was the first positional argument
        # afterwards, it was moved under the "operator" category
        command.append('operator')

    command.extend(
        [
            'generate-root',
            '-address', 'https://127.0.0.1:8200',
            '-tls-skip-verify',
            '-decode', encoded_token,
            '-otp', otp,
        ]
    )
    process = subprocess.Popen(**get_popen_kwargs(
        args=command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ))

    stdout, stderr = process.communicate()
    logging.debug('decode_generated_root_token stdout: "%s"' % str(stdout))
    if stderr != '':
        logging.error('decode_generated_root_token stderr: %s' % stderr)

    new_token = stdout.replace('Root token:', '')
    new_token = new_token.strip()
    return new_token


def get_popen_kwargs(**popen_kwargs):
    """Helper method to add `encoding='utf-8'` to subprocess.Popen when we're in Python 3.x.

    :param popen_kwargs: List of keyword arguments to conditionally mutate
    :type popen_kwargs: **kwargs
    :return: Conditionally updated list of keyword arguments
    :rtype: dict
    """
    if sys.version_info[0] >= 3:
        popen_kwargs['encoding'] = 'utf-8'
    return popen_kwargs


def base64ify(bytes_or_str):
    """Helper method to perform base64 encoding across Python 2.7 and Python 3.X

    :param bytes_or_str:
    :type bytes_or_str:
    :return:
    :rtype:
    """
    if sys.version_info[0] >= 3 and isinstance(bytes_or_str, str):
        input_bytes = bytes_or_str.encode('utf8')
    else:
        input_bytes = bytes_or_str

    output_bytes = base64.urlsafe_b64encode(input_bytes)
    if sys.version_info[0] >= 3:
        return output_bytes.decode('ascii')
    else:
        return output_bytes


class ServerManager(object):
    """Runs vault process running with test configuration and associates a hvac Client instance with this process."""

    def __init__(self, config_path, client):
        """Set up class attributes for managing a vault server process.

        :param config_path: Full path to the Vault config to use when launching `vault server`.
        :type config_path: str
        :param client: Hvac Client that is used to initialize the vault server process.
        :type client: hvac.v1.Client
        """
        self.config_path = config_path
        self.client = client

        self.keys = None
        self.root_token = None

        self._process = None

    def start(self):
        """Launch the vault server process and wait until its online and initialized."""
        command = ['vault', 'server', '-config=' + self.config_path]

        self._process = subprocess.Popen(command,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)

        attempts_left = 20
        last_exception = None
        while attempts_left > 0:
            try:
                self.client.sys.is_initialized()
                return
            except Exception as ex:
                logger.debug('Waiting for Vault to start')

                time.sleep(0.5)

                attempts_left -= 1
                last_exception = ex

        raise Exception('Unable to start Vault in background: {0}'.format(last_exception))

    def stop(self):
        """Stop the vault server process being managed by this class."""
        self._process.kill()
        if os.getenv('HVAC_OUTPUT_VAULT_STDERR', False):
            _, stderr_lines = self._process.communicate()
            with open(get_test_data_path('vault_stderr.log'), 'w') as f:
                f.writelines(stderr_lines)

    def initialize(self):
        """Perform initialization of the vault server process and record the provided unseal keys and root token."""
        assert not self.client.sys.is_initialized()

        result = self.client.sys.initialize()

        self.root_token = result['root_token']
        self.keys = result['keys']

    def unseal(self):
        """Unseal the vault server process."""
        self.client.sys.submit_unseal_keys(self.keys)


class HvacIntegrationTestCase(object):
    """Base class intended to be used by all hvac integration test cases."""

    manager = None
    client = None
    mock_warnings = None

    @classmethod
    def setUpClass(cls):
        """Use the ServerManager class to launch a vault server process."""
        cls.manager = ServerManager(
            config_path=get_test_data_path('vault-tls.hcl'),
            client=create_client()
        )
        cls.manager.start()
        cls.manager.initialize()
        cls.manager.unseal()

    @classmethod
    def tearDownClass(cls):
        """Stop the vault server process at the conclusion of a test class."""
        cls.manager.stop()

    def setUp(self):
        """Set the client attribute to an authenticated hvac Client instance."""
        self.client = create_client(token=self.manager.root_token)

        # Squelch deprecating warnings during tests as we may want to deliberately call deprecated methods and/or verify
        # warnings invocations.
        warnings_patcher = patch('hvac.utils.warnings', spec=warnings)
        self.mock_warnings = warnings_patcher.start()

    def tearDown(self):
        """Ensure the hvac Client instance's root token is reset after any auth method tests that may have modified it.

        This allows subclass's to include additional tearDown logic to reset the state of the vault server when needed.
        """
        self.client.token = self.manager.root_token

    @staticmethod
    def convert_python_ttl_value_to_expected_vault_response(ttl_value):
        """Convert any acceptable Vault TTL *input* to the expected value that Vault would return.

        Vault accepts TTL values in the form r'^(?P<duration>[0-9]+)(?P<unit>[smh])?$ (number of seconds/minutes/hours).
            However it returns those values as integers corresponding to seconds when retrieving configuration.
            This method converts the "go duration format" arguments Vault accepts into the number (integer) of seconds
            corresponding to what Vault returns.

        :param ttl_value: A TTL string accepted by vault; number of seconds/minutes/hours
        :type ttl_value: string
        :return: The provided TTL value in the form returned by the Vault API.
        :rtype: int
        """
        expected_ttl = ttl_value
        if not isinstance(ttl_value, int) and ttl_value != '':
            regexp_matches = re.match(r'^(?P<duration>[0-9]+)(?P<unit>[smh])?$', ttl_value)
            if regexp_matches:
                fields = regexp_matches.groupdict()
                expected_ttl = int(fields['duration'])
                if fields['unit'] == 'm':
                    # convert minutes to seconds
                    expected_ttl = expected_ttl * 60
                elif fields['unit'] == 'h':
                    # convert hours to seconds
                    expected_ttl = expected_ttl * 60 * 60
        elif ttl_value == '':
            expected_ttl = 0
        return expected_ttl

    def prep_policy(self, name):
        """Add a common policy used by a subset of integration test cases."""
        text = """
        path "sys" {
            policy = "deny"
        }
            path "secret" {
        policy = "write"
        }
        """
        obj = {
            'path': {
                'sys': {
                    'policy': 'deny'},
                'secret': {
                    'policy': 'write'}
            }
        }
        self.client.set_policy(name, text)
        return text, obj

    def configure_pki(self, common_name='hvac.com', role_name='my-role', mount_point='pki'):
        """Helper function to configure a pki backend for integration tests that need to work with lease IDs.

        :param common_name: Common name to configure in the pki backend
        :type common_name: str
        :param role_name: Name of the test role to configure.
        :type role_name: str
        :param mount_point: The path the pki backend is mounted under.
        :type mount_point: str
        :return: Nothing.
        :rtype: None.
        """
        if '{path}/'.format(path=mount_point) in self.client.list_secret_backends():
            self.client.disable_secret_backend(mount_point)

        self.client.enable_secret_backend(backend_type='pki', mount_point=mount_point)

        self.client.write(
            path='{path}/root/generate/internal'.format(path=mount_point),
            common_name=common_name,
            ttl='8760h',
        )
        self.client.write(
            path='{path}/config/urls'.format(path=mount_point),
            issuing_certificates="http://127.0.0.1:8200/v1/pki/ca",
            crl_distribution_points="http://127.0.0.1:8200/v1/pki/crl",
        )
        self.client.write(
            path='{path}/roles/{name}'.format(path=mount_point, name=role_name),
            allowed_domains=common_name,
            allow_subdomains=True,
            generate_lease=True,
            max_ttl='72h',
        )

    def disable_pki(self, mount_point='pki'):
        """Disable a previously configured pki backend.

        :param mount_point: The path the pki backend is mounted under.
        :type mount_point: str
        """
        self.client.disable_secret_backend(mount_point)


class MockGithubRequestHandler(BaseHTTPRequestHandler):
    """Small HTTP server used to mock out certain GitHub API routes that vault requests in the github auth method."""

    def do_GET(self):
        """Dispatch GET requests to associated mock GitHub 'handlers'."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if self.path == '/user':
            self.do_user()
        elif self.path == '/user/orgs?per_page=100':
            self.do_organizations_list()
        elif self.path == '/user/teams?per_page=100':
            self.do_team_list()
        return

    def log_message(self, format, *args):
        """Squelch any HTTP logging."""
        return

    def do_user(self):
        """Return the bare minimum GitHub user data needed for Vault's github auth method."""
        response = {
            "login": "hvac-dude",
            "id": 1,
        }

        self.wfile.write(json.dumps(response).encode())

    def do_organizations_list(self):
        """Return the bare minimum GitHub organization data needed for Vault's github auth method.

        Only returns data if the request Authorization header has a contrived github token value of "valid-token".
        """
        response = []
        if self.headers.get('Authorization') == 'Bearer valid-token':
            response.append(
                {
                    "login": "hvac",
                    "id": 1,
                }
            )

            self.wfile.write(json.dumps(response).encode())

    def do_team_list(self):
        """Return the bare minimum GitHub team data needed for Vault's github auth method.

        Only returns data if the request Authorization header has a contrived github token value of "valid-token".
        """
        response = []
        if self.headers.get('Authorization') == 'Bearer valid-token':
            response.append(
                {
                    "name": "hvac-team",
                    "slug": "hvac-team",
                    "organization": {
                        "id": 1,
                    }
                }
            )
        self.wfile.write(json.dumps(response).encode())
