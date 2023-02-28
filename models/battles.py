from odoo import fields, models, api
import random
import string
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import math

class battle(models.Model):
    _name = 'empires_of_legends.battle'
    _description = 'Battles'

    name = fields.Char()
    date_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    date_end = fields.Datetime(compute='_get_time')
    time = fields.Float(compute='_get_time')
    distance = fields.Float(compute='_get_time')
    progress = fields.Float()
    state = fields.Selection([('1', 'Preparation'), ('2', 'Launched'), ('3', 'Finished')], default='1')
    player1 = fields.Many2one('res.partner')
    player2 = fields.Many2one('res.partner')
    village1 = fields.Many2one('empires_of_legends.village')
    village2 = fields.Many2one('empires_of_legends.village')
    troop1_list = fields.One2many('empires_of_legends.battle_troop_rel', 'battle_id')
    troop1_available = fields.Many2many('empires_of_legends.village_troop_rel', compute='_get_troops_available')
    total_power = fields.Float()
    winner = fields.Many2one()
    draft = fields.Boolean()

    @api.onchange('player1')
    def onchange_player1(self):
        self.name = self.player1.name
        return {
            'domain': {
                'village1': [('id', 'in', self.player1.villages.ids)],
                'player2': [('id', '!=', self.player1.id)],
            }
        }

    @api.onchange('player2')
    def onchange_player2(self):
        return {
            'domain': {
                'village2': [('id', 'in', self.player2.villages.ids)],
                'player1': [('id', '!=', self.player2.id)],
            }
        }

    @api.depends('village1')
    def _get_troops_available(self):
        for b in self:
            b.troop1_available = b.village1.troops.ids

    @api.depends('troop1_list', 'village2', 'village1')
    def _get_time(self):
        for b in self:
            b.time = 0
            b.distance = 0
            b.date_end = fields.Datetime.now()
            if len(b.village1) > 0 and len(b.village2) > 0 and len(b.troop1_list) > 0 and len(b.troop1_list.troop_id) > 0:
                b.distance = b.village1.territory.distance(b.village2.territory)
                min_speed = b.troop1_list.troop_id.sorted(lambda s: s.speed).mapped('speed')[0]
                b.time = b.distance / min_speed
                b.date_end = fields.Datetime.to_string(
                    fields.Datetime.from_string(b.date_start) + timedelta(minutes=b.time))

    def launch_battle(self):
        for b in self:
            if len(b.village1) == 1 and len(b.village2) == 1 and len(b.troop1_list) > 0 and b.state == '1':

                b.date_start = fields.Datetime.now()
                b.progress = 0
                for s in b.troop1_list:
                    troop_available = \
                        b.troop1_available.filtered(lambda s_a: s_a.troop_id.id == s.troop_id.id)[0]
                    troop_available.qty -= s.qty
                b.state = '2'

    def back(self):
        for b in self:
            if b.state == '2':
                b.state = '1'

    def execute_battle(self):
        for b in self:
            result = b.simulate_battle()

    def simulate_battle(self):
            b = self
            winner = False
            draft = False
            troops1 = b.troop1_list.mapped(lambda s: [s.troop_id.read(['id','damage','armor','capacity'])] * s.qty)
            troops1 = [troop for sublist in troops1 for troop in sublist]

            troops2 = b.village2.troops.mapped(lambda s: [s.troop_id.read(['id','damage','armor','capacity'])] * s.qty)
            troops2 = [troop for sublist in troops2 for troop in sublist]

            for i in range(0, 6):
                if len(troops1) > 0 and len(troops2) > 0:
                    print("ROUND",i,troops1, troops2)
                    for attacker in troops1:
                        target = random.choice(troops2)
                        if attacker['damage'] > target['armor'] / 100 or random.random() > 0.90:
                            target['armor'] -= random.random() * attacker['damage']

                    for defender in troops2:
                        target = random.choice(troops1)
                        if defender['damage'] > target['armor'] / 100 or random.random() > 0.90:
                            target['armor'] -= random.random() * defender['damage']

                    troops1 = list(filter(lambda s: s['armor'] > 0, troops1))
                    troops2 = list(filter(lambda s: s['armor'] > 0, troops2))
            if len(troops1) == 0 and len(troops2) > 0:
                winner = b.player2.id
            if len(troops1) > 0 and len(troops2) == 0:
                winner = b.player1.id
            if len(troops1) > 0 and len(troops2) > 0:
                draft = True

            return {"winner": winner, "draft": draft}


class battle_troop_rel(models.Model):
    _name = 'empires_of_legends.battle_troop_rel'
    _description = 'battle_troop_rel'

    name = fields.Char(related="troop_id.name")
    troop_id = fields.Many2one('empires_of_legends.troop')
    battle_id = fields.Many2one('empires_of_legends.battle')
    qty = fields.Integer()

class battle_troop_rel_wizard(models.TransientModel):
    _name = 'empires_of_legends.battle_troop_rel_wizard'
    _description = 'battle_troop_rel_wizard'

    name = fields.Char(related="troop_id.name")
    troop_id = fields.Many2one('empires_of_legends.troop')
    battle_id = fields.Many2one('empires_of_legends.battle_wizard')
    qty = fields.Integer()

class battle_wizard(models.TransientModel):
    _name = 'empires_of_legends.battle_wizard'
    _description = 'Battle wizard'

    def _default_player1(self):
        return self.env['res.partner'].browse(self._context.get('active_id'))
    name = fields.Char()
    date_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    date_end = fields.Datetime(compute='_get_time')
    time = fields.Float(compute='_get_time')
    distance = fields.Float(compute='_get_time')
    state = fields.Selection([('1', 'Player1'), ('2', 'Player2'), ('3', 'Resume')], default='1')
    player1 = fields.Many2one('res.partner', default=_default_player1)
    player1_resume = fields.Many2one('res.partner', related='player1')
    player2 = fields.Many2one('res.partner')
    player2_resume = fields.Many2one('res.partner', related='player2')
    village1 = fields.Many2one('empires_of_legends.village')
    village2 = fields.Many2one('empires_of_legends.village')
    troop1_list = fields.One2many('empires_of_legends.battle_troop_rel_wizard', 'battle_id')
    troop1_available = fields.Many2many('empires_of_legends.village_troop_rel', compute='_get_troops_available')
    total_power = fields.Float()

    @api.onchange('player1')
    def onchange_player1(self):
        self.name = self.player1.name
        return {
            'domain': {
                'village1': [('id', 'in', self.player1.villages.ids)],
                'player2': [('id', '!=', self.player1.id)],
            }
        }

    @api.onchange('player2')
    def onchange_player2(self):
        return {
            'domain': {
                'village2': [('id', 'in', self.player2.villages.ids)],
                'player1': [('id', '!=', self.player2.id)],
            }
        }

    @api.depends('village1')
    def _get_troops_available(self):
        for b in self:
            b.troop1_available = b.village1.troops.ids

    @api.depends('troop1_list', 'village2', 'village1')
    def _get_time(self):
        for b in self:
            b.time = 0
            b.distance = 0
            b.date_end = fields.Datetime.now()
            if len(b.village1) > 0 and len(b.village2) > 0 and len(b.troop1_list) > 0 and len(
                    b.troop1_list.troop_id) > 0:
                b.distance = b.village1.territory.distance(b.village2.territory)
                min_speed = b.troop1_list.troop_id.sorted(lambda s: s.speed).mapped('speed')[0]
                b.time = b.distance / min_speed
                b.date_end = fields.Datetime.to_string(
                    fields.Datetime.from_string(b.date_start) + timedelta(minutes=b.time))

    def  action_previous(self):
        if self.state == '2':
            self.state = '1'
        elif self.state == '3':
            self.state = '2'
        return {
            'name': 'Create Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'empires_of_legends.battle_wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id
        }

    def action_next(self):
        if self.state == '1':
            self.state = '2'
        elif self.state == '2':
            if len(self.player2) < 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Player2 has to be choosed',
                        'type': 'danger',
                        'sticky': False,
                    }
                }
            else:
                self.state = '3'
        return {
            'name': 'Create Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'empires_of_legends.battle_wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': dict(self._context, player1_context=self.player1.id),

        }

    def create_battle(self):
        new_battle = self.env['empires_of_legends.battle'].create({
            'name': self.name,
            'player1': self.player1.id,
            'player2': self.player2.id,
            'village1': self.village1.id,
            'village2': self.village2.id,
            'state': '1',
            'date_start': self.date_start,
        })
        for s in self.troop1_list:
            self.env['empires_of_legends.battle_troop_rel'].create({
            'troop_id' : s.troop_id.id,
            'battle_id' : new_battle.id,
            'qty' : s.qty,
            })
        return  {
            'name': 'Created Battle',
            'type': 'ir.actions.act_window',
            'res_model': 'empires_of_legends.battle',
            'view_mode': 'form',
            'target': 'current',
            'res_id': new_battle.id,

        }