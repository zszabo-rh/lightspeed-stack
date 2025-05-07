from fastapi import FastAPI
from app import routers
import version

app = FastAPI(
    title="Swagger service - OpenAPI",
    description=f" service API specification.",
    version=version.__version__,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

routers.include_routers(app)
