from django_xworkflows import models as xwf_models

class BookingWorkflow(xwf_models.Workflow):
    states = (
        ('creating', u"Creating"),
        ('pending_approval', u"Pending Approval"),
        ('approved', u"Approved"),
        ('completed', u"Complete"),
        ('cancelled', u"Cancelled"),
    )

    transitions = (
        ('submit', 'creating', 'pending_approval'),
        ('approve', 'pending_approval', 'approved'),
        ('complete', 'approved', 'completed'),
        ('cancel', ('pending_approval', 'approved', 'creating'), 'cancelled'),
    )

    initial_state = 'creating'

class BookingPartWorkflow(xwf_models.Workflow):
    states = (
        ('creating', u"Creating"),
        ('pending_approval', u"Pending Approval"),
        ('approved', u"Approved"),
        ('equipment_out', u"In Use"),
        ('equipment_checked', u"Equipment Checked"),
        ('completed', u"Complete"),
        ('cancelled', u"Cancelled"),
    )

    transitions = (
        ('submit', 'creating', 'pending_approval'),
        ('approve', 'pending_approval', 'approved'),
        ('equipment_out', 'approved', 'equipment_out'),
        ('equipment_checked', 'equipment_out', 'equipment_checked'),
        ('complete', ('approved', 'equipment_out', 'equipment_checked'), 'completed'),
        ('cancel', ('pending_approval', 'approved', 'equipment_out', 'equipment_checked', 'creating'), 'cancelled'),
    )

    initial_state = 'creating'
