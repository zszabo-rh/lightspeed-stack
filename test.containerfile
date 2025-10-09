# Custom Red Hat llama-stack image with missing dependencies
FROM quay.io/opendatahub/llama-stack:rhoai-v2.25-latest

# Install missing dependencies
USER root
RUN pip install faiss-cpu==1.11.0 && \
    mkdir -p /opt/app-root/.llama/distributions/ollama && \
    chown -R 1001:0 /opt/app-root/.llama && \
    chmod -R g+rwx /opt/app-root/.llama

# Set working directory
WORKDIR /opt/app-root

# Switch back to the original user
USER 1001
