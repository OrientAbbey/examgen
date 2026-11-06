import os

import uvicorn

from .main import create_app

if __name__ == "__main__":
    trust = os.environ.get("EXAMGEN_TRUST_PROXY") == "1"   # derrière Caddy / un PaaS : fait confiance à X-Forwarded-*
    uvicorn.run(create_app(), host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")),
                proxy_headers=True, forwarded_allow_ips="*" if trust else "127.0.0.1")
