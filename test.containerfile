# Custom Red Hat llama-stack image with missing dependencies
FROM quay.io/opendatahub/llama-stack:rhoai-v2.25-latest

# Install missing dependencies
USER root
RUN pip install faiss-cpu==1.11.0 && \
    mkdir -p /app-root && \
    chown -R 1001:0 /app-root && \
    chmod -R 775 /app-root

# Switch back to the original user
USER 1001
