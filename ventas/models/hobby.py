from odoo import fields, models

class Hobby(models.Model):
    _name = 'hobby'

    name = fields.Char(string='Nombre')
