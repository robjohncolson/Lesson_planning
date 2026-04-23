FROM python:3.12-slim

# TeXLive packages that cover amsmath, tcolorbox, beamer, tikz, pgfplots.
# texlive-full is ~5 GB; this subset is ~600 MB and covers everything preamble.sty
# and beamer_preamble.sty require.
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-pictures \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build context must be the repo root (not railway/).
# railway/railway.toml sets dockerfilePath = "railway/Dockerfile" accordingly.
COPY railway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Server entry point
COPY railway/server.py .

# YAML→tex generator — lives at repo root. It reads registry.jsonl relative
# to its own location, so the file must sit at /app/questionbank/registry.jsonl.
COPY build_lesson_from_yaml.py .
COPY questionbank/registry.jsonl questionbank/registry.jsonl
COPY questionbank/assessment_shells.jsonl questionbank/assessment_shells.jsonl

# Shared LaTeX style packages — copied into each temp build dir at runtime
COPY tex/preamble.sty .
COPY tex/beamer_preamble.sty .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
