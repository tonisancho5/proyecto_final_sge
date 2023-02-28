# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
import string
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import math


class player(models.Model):
    _name = 'res.partner'
    _description = 'Players'
    _inherit = 'res.partner'

    #name = fields.Char(required=True, default="Player Name")

    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)
    villages = fields.One2many('empires_of_legends.village', 'player')
    is_player = fields.Boolean(default=False)

    @api.depends('villages')
    def get_villages_qty(self):
        for p in self:
            p.villages_qty = len(p.villages)

    @api.depends('villages')
    def _get_troops(self):
        for p in self:
            p.troops = p.villages.troops

class territory(models.Model):
    _name = 'empires_of_legends.territory'
    _description = 'Territories'

    name = fields.Char(required=True)
    villages = fields.One2many('empires_of_legends.village', 'territory')
    
    
class village(models.Model):
    _name = 'empires_of_legends.village'
    _description = 'Villages'

    name = fields.Char(required=True)
    civilization = fields.Selection([('1', 'Bizantinos'), ('2', 'Britanos'), ('3', 'Celtas'),
                                     ('4', 'Chinos'), ('5', 'Francos'), ('6', 'Godos'), ('7', 'Japoneses')])
    food = fields.Integer(string='Total comida')
    wood = fields.Integer(string='Total madera')
    stone = fields.Integer(string='Total piedra')
    iron = fields.Integer(string='Total hierro')
    gold = fields.Integer(string='Total oro')  # de pago
    infantry_qty = fields.Integer(string='Total caballeros')
    archery_qty = fields.Integer(string='Total arqueros')
    cavalry_qty = fields.Integer(string='Total jinetes')
    siege_qty = fields.Integer(string='Total asedio')
    troops_qty = fields.Integer(compute ='_get_troops_qty', string='Total ejercito', default=0)
    troop = fields.Char()

    player = fields.Many2one('res.partner', domain="[('is_player','=',True)]", ondelete="cascade")
    territory = fields.Many2one('empires_of_legends.territory',ondelete="cascade")
    buildings = fields.One2many('empires_of_legends.building', 'village', ondelete="restrict")
    troops = fields.One2many('empires_of_legends.village_troop_rel', 'village')
    available_troops = fields.Many2many('empires_of_legends.troop', compute="_get_available_troops")
    
    def _get_troops_qty(self):
        for village in self:
            village.troops_qty = village.infantry_qty + village.archery_qty + village.cavalry_qty + village.siege_qty

    def _get_available_troops(self):  # ORM
        for c in self:
            c.available_troops = self.env['empires_of_legends.troop'].search([])
    

class building(models.Model):
    _name = 'empires_of_legends.building'
    _description = 'Building'

    name = fields.Char(required=True)
    avatar = fields.Image(related='type.avatar')

    produce_food = fields.Integer(related='type.produce_food')
    produce_wood = fields.Integer(related='type.produce_wood')
    produce_stone = fields.Integer(related='type.produce_stone')
    produce_iron = fields.Integer(related='type.produce_iron')

    consume_food = fields.Integer(related='type.consume_food')
    consume_wood = fields.Integer(related='type.consume_wood')
    consume_stone = fields.Integer(related='type.consume_stone')
    consume_iron = fields.Integer(related='type.consume_iron')

    train_infantry = fields.Integer(related='type.train_infantry')
    train_cavalry = fields.Integer(related='type.train_cavalry')
    train_archery = fields.Integer(related='type.train_archery')
    train_siege = fields.Integer(related='type.train_siege')

    type = fields.Many2one('empires_of_legends.building_type')
    village = fields.Many2one('empires_of_legends.village')

    @api.model
    def produce(self):
        for building in self.search([]):
            village = building.village
            food = village.food + building.produce_food
            wood = village.wood + building.produce_wood
            stone = village.stone + building.produce_stone
            iron = village.iron + building.produce_iron
            
            village.write({
                "food":food,
                "wood":wood,
                "stone":stone,
                "iron":iron
            })
    
    def train(self):
        for building in self:
            village = building.village
            food = village.food - building.consume_food
            wood = village.wood - building.consume_wood
            stone = village.stone - building.consume_stone
            iron = village.iron - building.consume_iron
            infantry_qty = village.infantry_qty + building.train_infantry
            archery_qty = village.archery_qty + building.train_cavalry
            cavalry_qty = village.cavalry_qty + building.train_archery
            siege_qty = village.siege_qty + building.train_siege


class building_type(models.Model):
    _name = 'empires_of_legends.building_type'
    _description = 'Building Types'

    name = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)

    produce_food = fields.Integer()
    produce_wood = fields.Integer()
    produce_stone = fields.Integer()
    produce_iron = fields.Integer()

    consume_food = fields.Integer()
    consume_wood = fields.Integer()
    consume_stone = fields.Integer()
    consume_iron = fields.Integer()

    train_infantry = fields.Integer()
    train_cavalry = fields.Integer()
    train_archery = fields.Integer()
    train_siege = fields.Integer()

class troop(models.Model):
    _name = 'empires_of_legends.troop'
    _description = 'Troops'

    name = fields.Char()
    image = fields.Image(max_width=200, max_height=200)
    hp = fields.Float(default=1)
    armor = fields.Float(default=1)
    damage = fields.Float(default=1)
    time = fields.Float(compute='_get_train_time')
    speed = fields.Float(compute='_get_train_time')

    def _get_train_time(self):
        for s in self:
            s.time = (s.hp + 3 * s.damage + 2 * s.armor)
            s.speed = 1000 / (9 * s.hp + 15 * s.armor + 5 * s.damage)+1

    def train(self):  # ORM
        for s in self:
            print('fabrica', self.env.context['ctx_village'])
            village = self.env['empires_of_legends.village'].browse(self.env.context['ctx_village'])
            village_troop_rel = village.troop.filtered(lambda c: c.troop_id.id == s.id)
            if (len(village_troop_rel) == 0):
                village_troop_rel = self.env['empires_of_legends.village_troop_rel'].create({
                    "troop_id": s.id,
                    "village_id": village.id,
                    "qty": 0
                })
            self.env['empires_of_legends.village_troop_train'].create({
                "troop_id": village_troop_rel.id,
                "time_remaining": s.time
            })

class village_troop_rel(models.Model):
    _name = 'empires_of_legends.village_troop_rel'
    _description = 'village_troop_rel'

    name = fields.Char(related="troop_id.name")
    troop_id = fields.Many2one('empires_of_legends.troop')
    village = fields.Many2one('empires_of_legends.village')
    qty = fields.Integer()
    trains = fields.One2many('empires_of_legends.village_troop_train', 'troop_id')
    trains_queue = fields.Integer(compute="_get_trains_queue")
    trains_progress = fields.Float(compute="_get_trains_queue")

    def _get_trains_queue(self):
        for c in self:
            c.trains_queue = len(c.trains)
            c.trains_progress = 0
            if (c.trains_queue >= 1):
                c.trains_progress = c.trains[0].progress

class village_troop_train(models.Model):
    _name = 'empires_of_legends.village_troop_train'
    _description = 'Troop train model'

    name = fields.Char(related="troop_id.name")
    troop_id = fields.Many2one('empires_of_legends.village_troop_rel')
    progress = fields.Float()
    time_remaining = fields.Float()

    @api.model
    def update_train(self):
        for s in self.env['empires_of_legends.village_troop_rel'].search([]).filtered(lambda rel: len(rel.trains) > 0):
                print(s.trains)
                troop_in_queue = s.trains[0]
                time = troop_in_queue.time_remaining - 1
                progress = 100 - 100*(time / s.troop_id.time)
                if time <= 0:
                    s.qty += 1
                    troop_in_queue.unlink()

                else:
                    troop_in_queue.write({"time_remaining": time, "progress": progress})
                    print("Updated", troop_in_queue)

class player_wizard(models.TransientModel):
    _name = 'empires_of_legends.player_wizard'
    _description = 'Wizard per crear players'

    def _default_client(self):
        return self.env['res.partner'].browse(self._context.get('active_id'))
    name = fields.Many2one('res.partner',default=_default_client, required=True)
    password = fields.Char()
    avatar = fields.Image(max_width=200, max_height=200)

    def create_player(self):
        self.ensure_one()
        self.name.write({'password': self.password,
                         'avatar': self.avatar,
                         'is_player': True
                         })