from unittest.mock import MagicMock, patch

from src.models.registry import get_production_model_uri, promote_model, register_model


@patch("src.models.registry.MlflowClient")
@patch("src.models.registry.mlflow.register_model")
def test_register_model_meets_threshold(mock_register, mock_client):
    mock_register.return_value.version = "1"

    version = register_model(
        run_id="abc", model_artifact_path="model.pkl", model_name="test_model", accuracy=0.9, accuracy_threshold=0.8
    )

    assert version == "1"
    mock_register.assert_called_once_with(model_uri="runs:/abc/model.pkl", name="test_model")


@patch("src.models.registry.MlflowClient")
@patch("src.models.registry.mlflow.register_model")
def test_register_model_below_threshold(mock_register, mock_client):
    version = register_model(
        run_id="abc", model_artifact_path="model.pkl", model_name="test_model", accuracy=0.7, accuracy_threshold=0.8
    )

    assert version is None
    mock_register.assert_not_called()


@patch("src.models.registry.MlflowClient")
def test_promote_model(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    promote_model("test_model", "1", "Production", archive_existing=False)

    mock_client.transition_model_version_stage.assert_called_once_with(name="test_model", version="1", stage="Production")


@patch("src.models.registry.MlflowClient")
@patch("os.getenv")
def test_get_production_model_fallback(mock_getenv, mock_client_class):
    mock_client = MagicMock()
    mock_client.get_latest_versions.return_value = []
    mock_client_class.return_value = mock_client

    mock_getenv.return_value = "models/fallback.pkl"

    uri = get_production_model_uri("test_model")

    assert uri == "models/fallback.pkl"


@patch("src.models.registry.MlflowClient")
def test_get_production_model_found(mock_client_class):
    mock_client = MagicMock()
    mock_client.get_latest_versions.return_value = [MagicMock()]
    mock_client_class.return_value = mock_client

    uri = get_production_model_uri("test_model")

    assert uri == "models:/test_model/Production"
