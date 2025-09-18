git clone https://github.com/lightspeed-core/lightspeed-stack.git
cd lightspeed-stack

echo "pod started"
echo $E2E_LSC_HOSTNAME

curl -f http://$E2E_LSC_HOSTNAME:8080/v1/models || {
    echo "❌ Basic connectivity failed - showing logs before running full tests"
    exit 1
}

echo "Installing test dependencies..."
pip install uv
uv sync

echo "Running comprehensive e2e test suite..."
make test-e2e