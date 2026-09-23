# Edgrapi MCP — stdio bridge to https://api.edgrapi.com/mcp
#
# The bridge has no dependencies, so this is just Node plus two files.
#
#   docker run -i --rm -e EDGRAPI_API_KEY=edgr_... ghcr.io/paperandbeyond23-gif/edgrapi-mcp
#
# -i matters: MCP stdio clients talk over stdin/stdout, so the container must
# keep stdin open. There is no port and no server to expose.

FROM node:22-alpine

LABEL org.opencontainers.image.title="Edgrapi MCP"
LABEL org.opencontainers.image.description="US government data for AI agents as clean JSON: SAM.gov contract opportunities, USAspending awards, Grants.gov grants, congressional trades and SEC EDGAR filings."
LABEL org.opencontainers.image.url="https://edgrapi.com"
LABEL org.opencontainers.image.source="https://github.com/paperandbeyond23-gif/edgrapi-mcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY package.json ./
COPY bin/ ./bin/

# Nothing to install — the bridge is dependency-free — but this keeps the
# package metadata honest and fails the build if package.json ever grows deps
# that were not vendored.
RUN npm install --omit=dev --no-audit --no-fund

USER node

ENTRYPOINT ["node", "/app/bin/edgrapi-mcp.js"]
