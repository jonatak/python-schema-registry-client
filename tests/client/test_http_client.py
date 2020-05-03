import pytest

import httpx
from schema_registry.client import SchemaRegistryClient, utils


def test_invalid_cert():
    with pytest.raises(FileNotFoundError):
        SchemaRegistryClient(url="https://127.0.0.1:65534", cert_location="/path/to/cert")


def test_cert_with_key(certificates):
    client = SchemaRegistryClient(
        url="https://127.0.0.1:65534",
        cert_location=certificates["certificate"],
        key_location=certificates["key"],
        key_password=certificates["password"],
    )

    assert client.conf[utils.SSL_CERTIFICATE_LOCATION] == certificates["certificate"]
    assert client.conf[utils.SSL_KEY_LOCATION] == certificates["key"]
    assert client.conf[utils.SSL_KEY_PASSWORD] == certificates["password"]


def test_custom_headers():
    extra_headers = {"custom-serialization": "application/x-avro-json"}

    client = SchemaRegistryClient(url="https://127.0.0.1:65534", extra_headers=extra_headers)
    assert extra_headers == client.extra_headers


def test_override_headers(client, deployment_schema, mocker, response_klass):
    extra_headers = {"custom-serialization": "application/x-avro-json"}
    client = SchemaRegistryClient("https://127.0.0.1:65534", extra_headers=extra_headers)

    assert client.prepare_headers().get("custom-serialization") == "application/x-avro-json"

    subject = "test"
    override_header = {"custom-serialization": "application/avro"}

    request_patch = mocker.patch.object(httpx.Client, "request", return_value=response_klass(200, content={"id": 1}))
    client.register(subject, deployment_schema, headers=override_header)

    prepare_headers = client.prepare_headers(body="1")
    prepare_headers["custom-serialization"] = "application/avro"

    request_patch.assert_called_once_with("POST", mocker.ANY, headers=prepare_headers, json=mocker.ANY)


def test_cert_path():
    client = SchemaRegistryClient(url="https://127.0.0.1:65534", ca_location=True)

    assert client.conf[utils.SSL_CA_LOCATION]


def test_init_with_dict(certificates):
    client = SchemaRegistryClient(
        {
            "url": "https://127.0.0.1:65534",
            "ssl.certificate.location": certificates["certificate"],
            "ssl.key.location": certificates["key"],
            "ssl.key.password": certificates["password"],
        }
    )
    assert "https://127.0.0.1:65534/" == client.url_manager.url


def test_empty_url():
    with pytest.raises(AssertionError):
        SchemaRegistryClient({"url": ""})


def test_invalid_type_url():
    with pytest.raises(AttributeError):
        SchemaRegistryClient(url=1)


def test_invalid_type_url_dict():
    with pytest.raises(AttributeError):
        SchemaRegistryClient({"url": 1})


def test_invalid_url():
    with pytest.raises(AssertionError):
        SchemaRegistryClient({"url": "example.com:65534"})


def test_basic_auth_url():
    client = SchemaRegistryClient({"url": "https://user_url:secret_url@127.0.0.1:65534"})

    assert ("user_url", "secret_url") == client.session.auth


def test_basic_auth_userinfo():
    client = SchemaRegistryClient(
        {
            "url": "https://user_url:secret_url@127.0.0.1:65534",
            "basic.auth.credentials.source": "user_info",
            "basic.auth.user.info": "user_userinfo:secret_userinfo",
        }
    )
    assert ("user_userinfo", "secret_userinfo") == client.session.auth


def test_basic_auth_sasl_inherit():
    client = SchemaRegistryClient(
        {
            "url": "https://user_url:secret_url@127.0.0.1:65534",
            "basic.auth.credentials.source": "SASL_INHERIT",
            "sasl.mechanism": "PLAIN",
            "sasl.username": "user_sasl",
            "sasl.password": "secret_sasl",
        }
    )
    assert ("user_sasl", "secret_sasl") == client.session.auth


def test_basic_auth_invalid():
    with pytest.raises(ValueError):
        SchemaRegistryClient(
            {"url": "https://user_url:secret_url@127.0.0.1:65534", "basic.auth.credentials.source": "VAULT"}
        )
