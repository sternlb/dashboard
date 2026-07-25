# BUILD_FROM setzt der HA-Supervisor je Architektur aus build.yaml.
# Default nur für manuelle Builds (docker build) auf dem Pi.
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-debian:trixie-2026.03.0
FROM ${BUILD_FROM}

# Debian trixie: python3 = 3.13.5 (wie auf Leos Dev-PC), gh = 2.46.
# git   -> Repos klonen/pullen, Kanban-Rückschreiben
# gh    -> Repo-Kacheln im Command Center (gh repo list), Auth über GH_TOKEN
# jq    -> /data/options.json in run.sh lesen
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        git \
        gh \
        jq \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# Eigenes venv: Debians python3 ist externally-managed (PEP 668), ein direktes
# pip install ins System würde abgelehnt.
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "${VIRTUAL_ENV}"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# HOME setzt der Add-on-Container nicht selbst (init: false). Ohne HOME
# scheitern git config --global, ~/.streamlit und ~/.config/gh.
ENV HOME=/root \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
