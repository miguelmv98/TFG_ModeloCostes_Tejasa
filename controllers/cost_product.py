import json

from odoo import http
from odoo.http import request


class CostProduct(http.Controller):

    @http.route(['/costproduct/timerecord/'],auth="public")
    def index(self, **kwargs):
        return "Hello, world"
