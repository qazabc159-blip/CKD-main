FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY infra/lambda_inference/requirements-lambda.txt ./requirements-lambda.txt

ENV CC=gcc10-gcc
ENV CXX=gcc10-g++
ENV AR=gcc10-gcc-ar
ENV RANLIB=gcc10-gcc-ranlib
ENV PIP_NO_CACHE_DIR=1
ENV PIP_PREFER_BINARY=1

RUN yum install -y gcc10 gcc10-c++ make binutils && \
    yum clean all && \
    rm -rf /var/cache/yum

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --only-binary=:all: \
        numpy==2.2.6 \
        scipy==1.16.3 \
        pandas==2.3.3 \
        cython==3.2.4 \
        meson-python==0.18.0 \
        ninja \
        boto3 && \
    python -m pip install --no-build-isolation scikit-learn==1.8.0 && \
    python -m pip install -r requirements-lambda.txt

COPY backend ./backend
COPY infra/__init__.py ./infra/__init__.py
COPY infra/lambda_inference ./infra/lambda_inference
COPY artifacts/autoprognosis_336 ./artifacts/autoprognosis_336

CMD ["infra.lambda_inference.handler.lambda_handler"]
