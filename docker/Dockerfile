# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

FROM python:3.11-slim
LABEL maintainer="support@taiga.io"

# Avoid prompting for configuration
ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

# Use a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Get the code
COPY . /taiga-protected
WORKDIR /taiga-protected

RUN set -eux; \
    apt-get update; \
    # install system dependencies
    apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       gosu \
       git; \
    # install Taiga protected dependencies
    python -m pip install --upgrade pip; \
    python -m pip install wheel; \
    python -m pip install -r requirements.txt; \
    chmod +x docker/entrypoint.sh; \
    #  create taiga group and user to use it and give permissions over the code (in entrypoint)
    groupadd --system taiga --gid=999; \
    useradd --system --no-create-home --gid taiga --uid=999 --shell=/bin/bash taiga; \
    chown -R taiga:0 /taiga-protected; \
    chmod -R g+rwX /taiga-protected; \
    # remove unneeded files and packages
    apt-get purge -y \
       build-essential \
       git; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*; \
    rm -rf /root/.cache; \
    # clean taiga protected
    rm requirements.txt; \
    find . -name '__pycache__' -exec rm -r '{}' +; \
    find . -name '*pyc' -exec rm -r '{}' +

EXPOSE 8003
ENTRYPOINT ["./docker/entrypoint.sh"]
