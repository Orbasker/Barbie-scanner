# Define function directory
ARG FUNCTION_DIR="/function"

FROM --platform=linux/amd64 mcr.microsoft.com/playwright:v1.52.0-jammy as build-image

# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
    apt-get install -y \
    g++ \
    make \
    cmake \
    unzip \
    libcurl4-openssl-dev \
    python3-pip

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Copy function code
COPY app/* ${FUNCTION_DIR}

# Install the runtime interface client and FastAPI
RUN pip3 install  \
    --target ${FUNCTION_DIR} \
    awslambdaric playwright boto3

# Multi-stage build: grab a fresh copy of the base image
FROM --platform=linux/amd64 mcr.microsoft.com/playwright:v1.52.0-jammy

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the build image dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Make sure scripts in .local are usable:
ENV PATH="$PATH:/root/.local/bin"

ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]
CMD [ "main.handler" ]