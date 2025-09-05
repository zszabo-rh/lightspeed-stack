"""Unit tests for functions defined in src/models/config.py."""

# pylint: disable=too-many-lines

import json
from pathlib import Path

import pytest

from pydantic import ValidationError

from constants import (
    AUTH_MOD_NOOP,
    AUTH_MOD_K8S,
    AUTH_MOD_JWK_TOKEN,
    POSTGRES_DEFAULT_SSL_MODE,
    POSTGRES_DEFAULT_GSS_ENCMODE,
)

from utils.checks import InvalidConfigurationError

from models.config import (
    AuthenticationConfiguration,
    Configuration,
    JwkConfiguration,
    JwtRoleRule,
    JsonPathOperator,
    LlamaStackConfiguration,
    ServiceConfiguration,
    UserDataCollection,
    TLSConfiguration,
    CORSConfiguration,
    ModelContextProtocolServer,
    InferenceConfiguration,
    PostgreSQLDatabaseConfiguration,
    SQLiteDatabaseConfiguration,
    DatabaseConfiguration,
    Customization,
)


def test_service_configuration_constructor() -> None:
    """
    Verify that the ServiceConfiguration constructor sets default
    values for all fields.
    """
    s = ServiceConfiguration()
    assert s is not None

    assert s.host == "localhost"
    assert s.port == 8080
    assert s.auth_enabled is False
    assert s.workers == 1
    assert s.color_log is True
    assert s.access_log is True
    assert s.tls_config == TLSConfiguration()


def test_service_configuration_port_value() -> None:
    """Test the ServiceConfiguration port value validation."""
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        ServiceConfiguration(port=-1)

    with pytest.raises(ValueError, match="Port value should be less than 65536"):
        ServiceConfiguration(port=100000)


def test_service_configuration_workers_value() -> None:
    """Test the ServiceConfiguration workers value validation."""
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        ServiceConfiguration(workers=-1)


def test_llama_stack_configuration_constructor() -> None:
    """
    Verify that the LlamaStackConfiguration constructor accepts
    valid combinations of parameters and creates instances
    successfully.
    """
    llama_stack_configuration = LlamaStackConfiguration(
        use_as_library_client=True,
        library_client_config_path="tests/configuration/run.yaml",
    )
    assert llama_stack_configuration is not None

    llama_stack_configuration = LlamaStackConfiguration(
        use_as_library_client=False, url="http://localhost"
    )
    assert llama_stack_configuration is not None

    llama_stack_configuration = LlamaStackConfiguration(url="http://localhost")
    assert llama_stack_configuration is not None

    llama_stack_configuration = LlamaStackConfiguration(
        use_as_library_client=False, url="http://localhost", api_key="foo"
    )
    assert llama_stack_configuration is not None


def test_llama_stack_configuration_no_run_yaml() -> None:
    """
    Verify that constructing a LlamaStackConfiguration with a
    non-existent or invalid library_client_config_path raises
    InvalidConfigurationError.
    """
    with pytest.raises(
        InvalidConfigurationError,
        match="Llama Stack configuration file 'not a file' is not a file",
    ):
        LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="not a file",
        )


def test_llama_stack_wrong_configuration_constructor_no_url() -> None:
    """
    Verify that constructing a LlamaStackConfiguration without
    specifying either a URL or enabling library client mode raises
    a ValueError.
    """
    with pytest.raises(
        ValueError,
        match="Llama stack URL is not specified and library client mode is not specified",
    ):
        LlamaStackConfiguration()


def test_llama_stack_wrong_configuration_constructor_library_mode_off() -> None:
    """Test the LlamaStackConfiguration constructor."""
    with pytest.raises(
        ValueError,
        match="Llama stack URL is not specified and library client mode is not enabled",
    ):
        LlamaStackConfiguration(use_as_library_client=False)


def test_llama_stack_wrong_configuration_no_config_file() -> None:
    """Test the LlamaStackConfiguration constructor."""
    m = "Llama stack library client mode is enabled but a configuration file path is not specified"
    with pytest.raises(ValueError, match=m):
        LlamaStackConfiguration(use_as_library_client=True)


def test_inference_constructor() -> None:
    """
    Test the InferenceConfiguration constructor with valid
    parameters.
    """
    # Test with no default provider or model, as they are optional
    inference_config = InferenceConfiguration()
    assert inference_config is not None
    assert inference_config.default_provider is None
    assert inference_config.default_model is None

    # Test with default provider and model
    inference_config = InferenceConfiguration(
        default_provider="default_provider",
        default_model="default_model",
    )
    assert inference_config is not None
    assert inference_config.default_provider == "default_provider"
    assert inference_config.default_model == "default_model"


def test_inference_default_model_missing() -> None:
    """
    Test case where only default provider is set, should fail
    """
    with pytest.raises(
        ValueError,
        match="Default model must be specified when default provider is set",
    ):
        InferenceConfiguration(
            default_provider="default_provider",
        )


def test_inference_default_provider_missing() -> None:
    """
    Test case where only default model is set, should fail
    """
    with pytest.raises(
        ValueError,
        match="Default provider must be specified when default model is set",
    ):
        InferenceConfiguration(
            default_model="default_model",
        )


def test_user_data_collection_feedback_enabled() -> None:
    """Test the UserDataCollection constructor for feedback."""
    # correct configuration
    cfg = UserDataCollection(feedback_enabled=False, feedback_storage=None)
    assert cfg is not None
    assert cfg.feedback_enabled is False
    assert cfg.feedback_storage is None


def test_user_data_collection_feedback_disabled() -> None:
    """Test the UserDataCollection constructor for feedback."""
    # incorrect configuration
    with pytest.raises(
        ValueError,
        match="feedback_storage is required when feedback is enabled",
    ):
        UserDataCollection(feedback_enabled=True, feedback_storage=None)


def test_user_data_collection_transcripts_enabled() -> None:
    """Test the UserDataCollection constructor for transcripts."""
    # correct configuration
    cfg = UserDataCollection(transcripts_enabled=False, transcripts_storage=None)
    assert cfg is not None


def test_user_data_collection_transcripts_disabled() -> None:
    """Test the UserDataCollection constructor for transcripts."""
    # incorrect configuration
    with pytest.raises(
        ValueError,
        match="transcripts_storage is required when transcripts is enabled",
    ):
        UserDataCollection(transcripts_enabled=True, transcripts_storage=None)


def test_cors_default_configuration() -> None:
    """Test the CORS configuration."""
    cfg = CORSConfiguration()
    assert cfg is not None
    assert cfg.allow_origins == ["*"]
    assert cfg.allow_credentials is False
    assert cfg.allow_methods == ["*"]
    assert cfg.allow_headers == ["*"]


def test_cors_custom_configuration_v1() -> None:
    """Test the CORS configuration."""
    cfg = CORSConfiguration(
        allow_origins=["foo_origin", "bar_origin", "baz_origin"],
        allow_credentials=False,
        allow_methods=["foo_method", "bar_method", "baz_method"],
        allow_headers=["foo_header", "bar_header", "baz_header"],
    )
    assert cfg is not None
    assert cfg.allow_origins == ["foo_origin", "bar_origin", "baz_origin"]
    assert cfg.allow_credentials is False
    assert cfg.allow_methods == ["foo_method", "bar_method", "baz_method"]
    assert cfg.allow_headers == ["foo_header", "bar_header", "baz_header"]


def test_cors_custom_configuration_v2() -> None:
    """Test the CORS configuration."""
    cfg = CORSConfiguration(
        allow_origins=["foo_origin", "bar_origin", "baz_origin"],
        allow_credentials=True,
        allow_methods=["foo_method", "bar_method", "baz_method"],
        allow_headers=["foo_header", "bar_header", "baz_header"],
    )
    assert cfg is not None
    assert cfg.allow_origins == ["foo_origin", "bar_origin", "baz_origin"]
    assert cfg.allow_credentials is True
    assert cfg.allow_methods == ["foo_method", "bar_method", "baz_method"]
    assert cfg.allow_headers == ["foo_header", "bar_header", "baz_header"]


def test_cors_custom_configuration_v3() -> None:
    """Test the CORS configuration."""
    cfg = CORSConfiguration(
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["foo_method", "bar_method", "baz_method"],
        allow_headers=["foo_header", "bar_header", "baz_header"],
    )
    assert cfg is not None
    assert cfg.allow_origins == ["*"]
    assert cfg.allow_credentials is False
    assert cfg.allow_methods == ["foo_method", "bar_method", "baz_method"]
    assert cfg.allow_headers == ["foo_header", "bar_header", "baz_header"]


def test_cors_improper_configuration() -> None:
    """Test the CORS configuration."""
    expected = (
        "Value error, Invalid CORS configuration: "
        + "allow_credentials can not be set to true when allow origins contains '\\*' wildcard."
        + "Use explicit origins or disable credential."
    )

    with pytest.raises(ValueError, match=expected):
        # allow_credentials can not be true when allow_origins contains '*'
        CORSConfiguration(
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["foo_method", "bar_method", "baz_method"],
            allow_headers=["foo_header", "bar_header", "baz_header"],
        )


def test_tls_configuration() -> None:
    """Test the TLS configuration."""
    cfg = TLSConfiguration(
        tls_certificate_path=Path("tests/configuration/server.crt"),
        tls_key_path=Path("tests/configuration/server.key"),
        tls_key_password=Path("tests/configuration/password"),
    )
    assert cfg is not None
    assert cfg.tls_certificate_path == Path("tests/configuration/server.crt")
    assert cfg.tls_key_path == Path("tests/configuration/server.key")
    assert cfg.tls_key_password == Path("tests/configuration/password")


def test_tls_configuration_in_service_configuration() -> None:
    """Test the TLS configuration in service configuration."""
    cfg = ServiceConfiguration(
        tls_config=TLSConfiguration(
            tls_certificate_path=Path("tests/configuration/server.crt"),
            tls_key_path=Path("tests/configuration/server.key"),
            tls_key_password=Path("tests/configuration/password"),
        )
    )
    assert cfg is not None
    assert cfg.tls_config is not None
    assert cfg.tls_config.tls_certificate_path == Path("tests/configuration/server.crt")
    assert cfg.tls_config.tls_key_path == Path("tests/configuration/server.key")
    assert cfg.tls_config.tls_key_password == Path("tests/configuration/password")


def test_tls_configuration_wrong_certificate_path() -> None:
    """Test the TLS configuration loading when some path is broken."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("this-is-wrong"),
            tls_key_path=Path("tests/configuration/server.key"),
            tls_key_password=Path("tests/configuration/password"),
        )


def test_tls_configuration_wrong_key_path() -> None:
    """Test the TLS configuration loading when some path is broken."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("tests/configurationserver.crt"),
            tls_key_path=Path("this-is-wrong"),
            tls_key_password=Path("tests/configuration/password"),
        )


def test_tls_configuration_wrong_password_path() -> None:
    """Test the TLS configuration loading when some path is broken."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("tests/configurationserver.crt"),
            tls_key_path=Path("tests/configuration/server.key"),
            tls_key_password=Path("this-is-wrong"),
        )


def test_tls_configuration_certificate_path_to_directory() -> None:
    """Test the TLS configuration loading when some path points to a directory."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("tests/"),
            tls_key_path=Path("tests/configuration/server.key"),
            tls_key_password=Path("tests/configuration/password"),
        )


def test_tls_configuration_key_path_to_directory() -> None:
    """Test the TLS configuration loading when some path points to a directory."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("tests/configurationserver.crt"),
            tls_key_path=Path("tests/"),
            tls_key_password=Path("tests/configuration/password"),
        )


def test_tls_configuration_password_path_to_directory() -> None:
    """Test the TLS configuration loading when some path points to a directory."""
    with pytest.raises(ValueError, match="Path does not point to a file"):
        TLSConfiguration(
            tls_certificate_path=Path("tests/configurationserver.crt"),
            tls_key_path=Path("tests/configuration/server.key"),
            tls_key_password=Path("tests/"),
        )


def test_model_context_protocol_server_constructor() -> None:
    """Test the ModelContextProtocolServer constructor."""
    mcp = ModelContextProtocolServer(name="test-server", url="http://localhost:8080")
    assert mcp is not None
    assert mcp.name == "test-server"
    assert mcp.provider_id == "model-context-protocol"
    assert mcp.url == "http://localhost:8080"


def test_model_context_protocol_server_custom_provider() -> None:
    """Test the ModelContextProtocolServer constructor with custom provider."""
    mcp = ModelContextProtocolServer(
        name="custom-server",
        provider_id="custom-provider",
        url="https://api.example.com",
    )
    assert mcp is not None
    assert mcp.name == "custom-server"
    assert mcp.provider_id == "custom-provider"
    assert mcp.url == "https://api.example.com"


def test_model_context_protocol_server_required_fields() -> None:
    """Test that ModelContextProtocolServer requires name and url."""

    with pytest.raises(ValidationError):
        ModelContextProtocolServer()  # pyright: ignore

    with pytest.raises(ValidationError):
        ModelContextProtocolServer(name="test-server")  # pyright: ignore

    with pytest.raises(ValidationError):
        ModelContextProtocolServer(url="http://localhost:8080")  # pyright: ignore


def test_configuration_empty_mcp_servers() -> None:
    """
    Test that a Configuration object can be created with an empty
    list of MCP servers.

    Verifies that the Configuration instance is constructed
    successfully and that the mcp_servers attribute is empty.
    """
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=[],
        customization=None,
    )
    assert cfg is not None
    assert not cfg.mcp_servers


def test_configuration_single_mcp_server() -> None:
    """
    Test that a Configuration object can be created with a single
    MCP server and verifies its properties.
    """
    mcp_server = ModelContextProtocolServer(
        name="test-server", url="http://localhost:8080"
    )
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=[mcp_server],
        customization=None,
    )
    assert cfg is not None
    assert len(cfg.mcp_servers) == 1
    assert cfg.mcp_servers[0].name == "test-server"
    assert cfg.mcp_servers[0].url == "http://localhost:8080"


def test_configuration_multiple_mcp_servers() -> None:
    """
    Verify that the Configuration object correctly handles multiple
    ModelContextProtocolServer instances in its mcp_servers list,
    including custom provider IDs.
    """
    mcp_servers = [
        ModelContextProtocolServer(name="server1", url="http://localhost:8080"),
        ModelContextProtocolServer(
            name="server2", url="http://localhost:8081", provider_id="custom-provider"
        ),
        ModelContextProtocolServer(name="server3", url="https://api.example.com"),
    ]
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=mcp_servers,
        customization=None,
    )
    assert cfg is not None
    assert len(cfg.mcp_servers) == 3
    assert cfg.mcp_servers[0].name == "server1"
    assert cfg.mcp_servers[1].name == "server2"
    assert cfg.mcp_servers[1].provider_id == "custom-provider"
    assert cfg.mcp_servers[2].name == "server3"


def test_dump_configuration(tmp_path) -> None:
    """
    Test that the Configuration object can be serialized to a JSON file and
    that the resulting file contains all expected sections and values.

    Please note that redaction process is not in place.
    """
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(
            tls_config=TLSConfiguration(
                tls_certificate_path=Path("tests/configuration/server.crt"),
                tls_key_path=Path("tests/configuration/server.key"),
                tls_key_password=Path("tests/configuration/password"),
            ),
            cors=CORSConfiguration(
                allow_origins=["foo_origin", "bar_origin", "baz_origin"],
                allow_credentials=False,
                allow_methods=["foo_method", "bar_method", "baz_method"],
                allow_headers=["foo_header", "bar_header", "baz_header"],
            ),
        ),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
            api_key="whatever",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        database=DatabaseConfiguration(
            sqlite=None,
            postgres=PostgreSQLDatabaseConfiguration(
                db="lightspeed_stack",
                user="ls_user",
                password="ls_password",
                port=5432,
                ca_cert_path=None,
                ssl_mode="require",
                gss_encmode="disable",
            ),
        ),
        mcp_servers=[],
        customization=None,
        inference=InferenceConfiguration(
            default_provider="default_provider",
            default_model="default_model",
        ),
    )
    assert cfg is not None
    dump_file = tmp_path / "test.json"
    cfg.dump(dump_file)

    with open(dump_file, "r", encoding="utf-8") as fin:
        content = json.load(fin)
        # content should be loaded
        assert content is not None

        # all sections must exists
        assert "name" in content
        assert "service" in content
        assert "llama_stack" in content
        assert "user_data_collection" in content
        assert "mcp_servers" in content
        assert "authentication" in content
        assert "authorization" in content
        assert "customization" in content
        assert "inference" in content
        assert "database" in content

        # check the whole deserialized JSON file content
        assert content == {
            "name": "test_name",
            "service": {
                "host": "localhost",
                "port": 8080,
                "auth_enabled": False,
                "workers": 1,
                "color_log": True,
                "access_log": True,
                "tls_config": {
                    "tls_certificate_path": "tests/configuration/server.crt",
                    "tls_key_password": "tests/configuration/password",
                    "tls_key_path": "tests/configuration/server.key",
                },
                "cors": {
                    "allow_credentials": False,
                    "allow_headers": [
                        "foo_header",
                        "bar_header",
                        "baz_header",
                    ],
                    "allow_methods": [
                        "foo_method",
                        "bar_method",
                        "baz_method",
                    ],
                    "allow_origins": [
                        "foo_origin",
                        "bar_origin",
                        "baz_origin",
                    ],
                },
            },
            "llama_stack": {
                "url": None,
                "use_as_library_client": True,
                "api_key": "**********",
                "library_client_config_path": "tests/configuration/run.yaml",
            },
            "user_data_collection": {
                "feedback_enabled": False,
                "feedback_storage": None,
                "transcripts_enabled": False,
                "transcripts_storage": None,
            },
            "mcp_servers": [],
            "authentication": {
                "module": "noop",
                "skip_tls_verification": False,
                "k8s_ca_cert_path": None,
                "k8s_cluster_api": None,
                "jwk_config": None,
            },
            "customization": None,
            "inference": {
                "default_provider": "default_provider",
                "default_model": "default_model",
            },
            "database": {
                "sqlite": None,
                "postgres": {
                    "host": "localhost",
                    "port": 5432,
                    "db": "lightspeed_stack",
                    "user": "ls_user",
                    "password": "**********",
                    "ssl_mode": "require",
                    "gss_encmode": "disable",
                    "namespace": "lightspeed-stack",
                    "ca_cert_path": None,
                },
            },
            "authorization": None,
        }


def test_dump_configuration_with_one_mcp_server(tmp_path) -> None:
    """
    Verify that a configuration with a single MCP server can be
    serialized to JSON and that all expected fields and values are
    present in the output.

    Parameters:
        tmp_path: Temporary directory path provided by pytest for file output.
    """
    mcp_servers = [
        ModelContextProtocolServer(name="test-server", url="http://localhost:8080"),
    ]
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=mcp_servers,
        customization=None,
        inference=InferenceConfiguration(),
    )
    dump_file = tmp_path / "test.json"
    cfg.dump(dump_file)

    with open(dump_file, "r", encoding="utf-8") as fin:
        content = json.load(fin)
        assert content is not None
        assert "mcp_servers" in content
        assert len(content["mcp_servers"]) == 1
        assert content["mcp_servers"][0]["name"] == "test-server"
        assert content["mcp_servers"][0]["url"] == "http://localhost:8080"
        assert content["mcp_servers"][0]["provider_id"] == "model-context-protocol"

        # check the MCP server configuration
        assert content["mcp_servers"] == [
            {
                "name": "test-server",
                "url": "http://localhost:8080",
                "provider_id": "model-context-protocol",
            }
        ]


def test_dump_configuration_with_more_mcp_servers(tmp_path) -> None:
    """
    Test that a configuration with multiple MCP servers can be
    serialized to JSON and that all server entries are correctly
    included in the output.

    Verifies that the dumped configuration file contains all
    expected fields and that each MCP server is present with the
    correct name, URL, and provider ID.
    """
    mcp_servers = [
        ModelContextProtocolServer(name="test-server-1", url="http://localhost:8081"),
        ModelContextProtocolServer(name="test-server-2", url="http://localhost:8082"),
        ModelContextProtocolServer(name="test-server-3", url="http://localhost:8083"),
    ]
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=mcp_servers,
        customization=None,
        inference=InferenceConfiguration(),
    )
    dump_file = tmp_path / "test.json"
    cfg.dump(dump_file)

    with open(dump_file, "r", encoding="utf-8") as fin:
        content = json.load(fin)
        assert content is not None
        assert "mcp_servers" in content
        assert len(content["mcp_servers"]) == 3
        assert content["mcp_servers"][0]["name"] == "test-server-1"
        assert content["mcp_servers"][0]["url"] == "http://localhost:8081"
        assert content["mcp_servers"][0]["provider_id"] == "model-context-protocol"
        assert content["mcp_servers"][1]["name"] == "test-server-2"
        assert content["mcp_servers"][1]["url"] == "http://localhost:8082"
        assert content["mcp_servers"][1]["provider_id"] == "model-context-protocol"
        assert content["mcp_servers"][2]["name"] == "test-server-3"
        assert content["mcp_servers"][2]["url"] == "http://localhost:8083"
        assert content["mcp_servers"][2]["provider_id"] == "model-context-protocol"

        # check the MCP server configuration
        assert content["mcp_servers"] == [
            {
                "name": "test-server-1",
                "provider_id": "model-context-protocol",
                "url": "http://localhost:8081",
            },
            {
                "name": "test-server-2",
                "provider_id": "model-context-protocol",
                "url": "http://localhost:8082",
            },
            {
                "name": "test-server-3",
                "provider_id": "model-context-protocol",
                "url": "http://localhost:8083",
            },
        ]


def test_authentication_configuration_in_config() -> None:
    """Test the authentication configuration in main config."""
    cfg = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=[],
    )
    assert cfg.authentication is not None
    assert cfg.authentication.module == AUTH_MOD_NOOP
    assert cfg.authentication.skip_tls_verification is False
    assert cfg.authentication.k8s_ca_cert_path is None
    assert cfg.authentication.k8s_cluster_api is None

    cfg2 = Configuration(
        name="test_name",
        service=ServiceConfiguration(),
        llama_stack=LlamaStackConfiguration(
            use_as_library_client=True,
            library_client_config_path="tests/configuration/run.yaml",
        ),
        user_data_collection=UserDataCollection(
            feedback_enabled=False, feedback_storage=None
        ),
        mcp_servers=[],
        authentication=AuthenticationConfiguration(
            module=AUTH_MOD_K8S,
            skip_tls_verification=True,
            k8s_ca_cert_path="tests/configuration/server.crt",
            k8s_cluster_api=None,
        ),
    )
    assert cfg2.authentication is not None
    assert cfg2.authentication.module == AUTH_MOD_K8S
    assert cfg2.authentication.skip_tls_verification is True
    assert cfg2.authentication.k8s_ca_cert_path == Path(
        "tests/configuration/server.crt"
    )
    assert cfg2.authentication.k8s_cluster_api is None


def test_authentication_configuration() -> None:
    """Test the AuthenticationConfiguration constructor."""

    auth_config = AuthenticationConfiguration(
        module=AUTH_MOD_NOOP,
        skip_tls_verification=False,
        k8s_ca_cert_path=None,
        k8s_cluster_api=None,
    )
    assert auth_config is not None
    assert auth_config.module == AUTH_MOD_NOOP
    assert auth_config.skip_tls_verification is False
    assert auth_config.k8s_ca_cert_path is None
    assert auth_config.k8s_cluster_api is None

    # try to retrieve JWK configuration
    with pytest.raises(
        ValueError,
        match="JWK configuration is only available for JWK token authentication module",
    ):
        _ = auth_config.jwk_configuration


def test_authentication_configuration_jwk_token() -> None:
    """Test the AuthenticationConfiguration with JWK token."""

    auth_config = AuthenticationConfiguration(
        module=AUTH_MOD_JWK_TOKEN,
        skip_tls_verification=False,
        k8s_ca_cert_path=None,
        k8s_cluster_api=None,
        jwk_config=JwkConfiguration(url="http://foo.bar.baz"),
    )
    assert auth_config is not None
    assert auth_config.module == AUTH_MOD_JWK_TOKEN
    assert auth_config.skip_tls_verification is False
    assert auth_config.k8s_ca_cert_path is None
    assert auth_config.k8s_cluster_api is None

    # try to retrieve JWK configuration
    assert auth_config.jwk_configuration is not None


def test_authentication_configuration_jwk_token_but_insufficient_config() -> None:
    """Test the AuthenticationConfiguration with JWK token."""

    with pytest.raises(ValidationError, match="JwkConfiguration"):
        AuthenticationConfiguration(
            module=AUTH_MOD_JWK_TOKEN,
            skip_tls_verification=False,
            k8s_ca_cert_path=None,
            k8s_cluster_api=None,
            jwk_config=JwkConfiguration(),
        )


def test_authentication_configuration_jwk_token_but_not_config() -> None:
    """Test the AuthenticationConfiguration with JWK token."""

    with pytest.raises(
        ValidationError,
        match="Value error, JWK configuration must be specified when using JWK token",
    ):
        AuthenticationConfiguration(
            module=AUTH_MOD_JWK_TOKEN,
            skip_tls_verification=False,
            k8s_ca_cert_path=None,
            k8s_cluster_api=None,
            # no JwkConfiguration
        )


def test_authentication_configuration_jwk_broken_config() -> None:
    """Test the AuthenticationConfiguration with JWK set, but not configured."""

    auth_config = AuthenticationConfiguration(
        module=AUTH_MOD_JWK_TOKEN,
        skip_tls_verification=False,
        k8s_ca_cert_path=None,
        k8s_cluster_api=None,
        jwk_config=JwkConfiguration(url="http://foo.bar.baz"),
    )
    assert auth_config is not None

    # emulate broken config
    auth_config.jwk_config = None
    # try to retrieve JWK configuration

    with pytest.raises(ValueError, match="JWK configuration should not be None"):
        _ = auth_config.jwk_configuration


def test_authentication_configuration_supported() -> None:
    """Test the AuthenticationConfiguration constructor."""
    auth_config = AuthenticationConfiguration(
        module=AUTH_MOD_K8S,
        skip_tls_verification=False,
        k8s_ca_cert_path=None,
        k8s_cluster_api=None,
    )
    assert auth_config is not None
    assert auth_config.module == AUTH_MOD_K8S
    assert auth_config.skip_tls_verification is False
    assert auth_config.k8s_ca_cert_path is None
    assert auth_config.k8s_cluster_api is None


def test_authentication_configuration_module_unsupported() -> None:
    """Test the AuthenticationConfiguration constructor with module as None."""
    with pytest.raises(ValidationError, match="Unsupported authentication module"):
        AuthenticationConfiguration(
            module="non-existing-module",
            skip_tls_verification=False,
            k8s_ca_cert_path=None,
            k8s_cluster_api=None,
        )


def test_database_configuration(subtests) -> None:
    """Test the database configuration handling."""
    with subtests.test(msg="PostgreSQL"):
        d1 = PostgreSQLDatabaseConfiguration(
            db="db",
            user="user",
            password="password",
            port=1234,
            ca_cert_path=Path("tests/configuration/server.crt"),
        )
        d = DatabaseConfiguration(postgres=d1)
        assert d is not None
        assert d.sqlite is None
        assert d.postgres is not None
        assert d.db_type == "postgres"
        assert d.config is d1

    with subtests.test(msg="SQLite"):
        d1 = SQLiteDatabaseConfiguration(
            db_path="/tmp/foo/bar/baz",
        )
        d = DatabaseConfiguration(sqlite=d1)
        assert d is not None
        assert d.sqlite is not None
        assert d.postgres is None
        assert d.db_type == "sqlite"
        assert d.config is d1


def test_no_databases_configuration() -> None:
    """Test if no databases configuration is checked."""
    d = DatabaseConfiguration()
    assert d is not None

    # default should be SQLite when nothing is provided
    assert d.db_type == "sqlite"

    # simulate no DB configuration
    d.sqlite = None
    d.postgres = None

    with pytest.raises(ValueError, match="No database configuration found"):
        # access property to call its getter
        _ = d.db_type

    with pytest.raises(ValueError, match="No database configuration found"):
        # access property to call its getter
        _ = d.config


def test_two_databases_configuration() -> None:
    """Test if two databases configuration is checked."""
    d1 = PostgreSQLDatabaseConfiguration(db="db", user="user", password="password")
    d2 = SQLiteDatabaseConfiguration(db_path="foo_bar_baz")
    with pytest.raises(
        ValidationError, match="Only one database configuration can be provided"
    ):
        DatabaseConfiguration(postgres=d1, sqlite=d2)


def test_postgresql_database_configuration() -> None:
    """Test the PostgreSQLDatabaseConfiguration model."""
    c = PostgreSQLDatabaseConfiguration(db="db", user="user", password="password")
    assert c is not None
    assert c.host == "localhost"
    assert c.port == 5432
    assert c.db == "db"
    assert c.user == "user"
    assert c.password.get_secret_value() == "password"
    assert c.ssl_mode == POSTGRES_DEFAULT_SSL_MODE
    assert c.gss_encmode == POSTGRES_DEFAULT_GSS_ENCMODE
    assert c.namespace == "lightspeed-stack"
    assert c.ca_cert_path is None


def test_postgresql_database_configuration_port_setting(subtests) -> None:
    """Test the PostgreSQLDatabaseConfiguration model."""
    with subtests.test(msg="Correct port value"):
        c = PostgreSQLDatabaseConfiguration(
            db="db", user="user", password="password", port=1234
        )
        assert c is not None
        assert c.port == 1234

    with subtests.test(msg="Negative port value"):
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            PostgreSQLDatabaseConfiguration(
                db="db", user="user", password="password", port=-1
            )

    with subtests.test(msg="Too big port value"):
        with pytest.raises(ValueError, match="Port value should be less than 65536"):
            PostgreSQLDatabaseConfiguration(
                db="db", user="user", password="password", port=100000
            )


def test_postgresql_database_configuration_ca_cert_path(subtests) -> None:
    """Test the PostgreSQLDatabaseConfiguration model."""
    with subtests.test(msg="Path exists"):
        c = PostgreSQLDatabaseConfiguration(
            db="db",
            user="user",
            password="password",
            port=1234,
            ca_cert_path=Path("tests/configuration/server.crt"),
        )
        assert c.ca_cert_path == Path("tests/configuration/server.crt")

    with subtests.test(msg="Path does not exist"):
        with pytest.raises(ValidationError, match="Path does not point to a file"):
            PostgreSQLDatabaseConfiguration(
                db="db",
                user="user",
                password="password",
                port=1234,
                ca_cert_path=Path("not a file"),
            )


def test_jwt_role_rule_missing_attributes() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(ValidationError, match="validation errors"):
        _ = JwtRoleRule()


def test_jwt_role_rule_correct_attributes() -> None:
    """Check the JwtRoleRule config class."""
    r = JwtRoleRule(
        jsonpath="$.id",
        negate=False,
        value="xyz",
        roles=["admin"],
        operator=JsonPathOperator.EQUALS,
    )

    assert r is not None
    assert r.compiled_regex is None


def test_jwt_role_rule_invalid_json_path() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(ValidationError, match="Invalid JSONPath expression"):
        _ = JwtRoleRule(
            jsonpath="this/is/not/valid",
            negate=False,
            value="xyz",
            roles=["admin"],
            operator=JsonPathOperator.EQUALS,
        )


def test_jwt_role_rule_no_roles_specified() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(
        ValidationError, match="At least one role must be specified in the rule"
    ):
        _ = JwtRoleRule(
            jsonpath="$.id",
            negate=False,
            value="xyz",
            roles=[],
            operator=JsonPathOperator.EQUALS,
        )


def test_jwt_role_rule_star_role_specified() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(
        ValidationError, match="The wildcard '\\*' role is not allowed in role rules"
    ):
        _ = JwtRoleRule(
            jsonpath="$.id",
            negate=False,
            value="xyz",
            roles=["*"],
            operator=JsonPathOperator.EQUALS,
        )


def test_jwt_role_rule_same_roles() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(ValidationError, match="Roles must be unique in the rule"):
        _ = JwtRoleRule(
            jsonpath="$.id",
            negate=False,
            value="xyz",
            roles=["admin", "admin", "user"],
            operator=JsonPathOperator.EQUALS,
        )


def test_jwt_role_rule_invalid_value() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(
        ValidationError, match="MATCH operator requires a string pattern"
    ):
        _ = JwtRoleRule(
            jsonpath="$.id",
            negate=False,
            value=True,  # not a string
            roles=["admin", "user"],
            operator=JsonPathOperator.MATCH,
        )


def test_jwt_role_rule_valid_regexp() -> None:
    """Check the JwtRoleRule config class."""
    j = JwtRoleRule(
        jsonpath="$.id",
        negate=False,
        value=".*",  # valid regexp
        roles=["admin", "user"],
        operator=JsonPathOperator.MATCH,
    )
    assert j.compiled_regex is not None


def test_jwt_role_rule_invalid_regexp() -> None:
    """Check the JwtRoleRule config class."""
    with pytest.raises(
        ValidationError, match="Invalid regex pattern for MATCH operator"
    ):
        _ = JwtRoleRule(
            jsonpath="$.id",
            negate=False,
            value="[[[",  # invalid regexp
            roles=["admin", "user"],
            operator=JsonPathOperator.MATCH,
        )


def test_service_customization(subtests) -> None:
    """Check the service customization class."""
    with subtests.test(msg="System prompt is enabled"):
        c = Customization()
        assert c is not None
        assert c.disable_query_system_prompt is False
        assert c.system_prompt_path is None
        assert c.system_prompt is None

    with subtests.test(msg="System prompt is disabled"):
        c = Customization(disable_query_system_prompt=True)
        assert c is not None
        assert c.disable_query_system_prompt is True
        assert c.system_prompt_path is None
        assert c.system_prompt is None

    with subtests.test(
        msg="Disabled overrides provided path, but the prompt is still loaded"
    ):
        c = Customization(
            disable_query_system_prompt=True,
            system_prompt_path="tests/configuration/system_prompt.txt",
        )
        assert c.system_prompt is not None
        # check that the system prompt has been loaded from the provided file
        assert c.system_prompt == "This is system prompt."
        # but it is still disabled
        assert c.disable_query_system_prompt is True


def test_service_customization_wrong_system_prompt_path() -> None:
    """Check the service customization class."""
    with pytest.raises(ValidationError, match="Path does not point to a file"):
        _ = Customization(system_prompt_path="/path/does/not/exists")


def test_service_customization_correct_system_prompt_path(subtests) -> None:
    """Check the service customization class."""
    with subtests.test(msg="One line system prompt"):
        # pass a file containing system prompt
        c = Customization(system_prompt_path="tests/configuration/system_prompt.txt")
        assert c is not None
        # check that the system prompt has been loaded from the provided file
        assert c.system_prompt == "This is system prompt."

    with subtests.test(msg="Multi line system prompt"):
        # pass a file containing system prompt
        c = Customization(
            system_prompt_path="tests/configuration/multiline_system_prompt.txt"
        )
        assert c is not None
        # check that the system prompt has been loaded from the provided file
        assert "You are OpenShift Lightspeed" in c.system_prompt
        assert "Here are your instructions" in c.system_prompt
        assert "Here are some basic facts about OpenShift" in c.system_prompt
