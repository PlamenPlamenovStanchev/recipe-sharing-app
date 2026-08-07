"""Health-check API resource."""

from flask_restful import Resource


class HealthResource(Resource):
    """Report whether the API process is available."""

    def get(self):
        """Return the service health status."""
        return {"status": "ok", "service": "recipe-sharing-api"}, 200
