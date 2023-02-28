# -*- coding: utf-8 -*-
# from odoo import http


# class EmpiresOfLegends(http.Controller):
#     @http.route('/empires_of_legends/empires_of_legends', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/empires_of_legends/empires_of_legends/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('empires_of_legends.listing', {
#             'root': '/empires_of_legends/empires_of_legends',
#             'objects': http.request.env['empires_of_legends.empires_of_legends'].search([]),
#         })

#     @http.route('/empires_of_legends/empires_of_legends/objects/<model("empires_of_legends.empires_of_legends"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('empires_of_legends.object', {
#             'object': obj
#         })
