from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import mail

from . import workflows
from django_xworkflows import models as xwf_models
import xworkflows

from django.utils.deconstruct import deconstructible
xwf_models.Workflow = deconstructible(xwf_models.Workflow)
xwf_models.WorkflowEnabled = xwf_models.WorkflowEnabledMeta(str('WorkflowEnabled'), (xwf_models.BaseWorkflowEnabled,), {'__module__':'django_xworkflows.models'})
class StateField(xwf_models.StateField):
    def deconstruct(self):
        name, path, args, kwargs = super(StateField, self).deconstruct()
        kwargs['workflow'] = self.workflow
        return name, path, args, kwargs

class LendablesOwner(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    slug = models.SlugField(null=False, blank=False)
    owning_group = models.ForeignKey(Group, null=False)

    def __unicode__(self):
        return self.name

class LendableType(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    slug = models.SlugField(null=False, blank=False)

    def __unicode__(self):
        return self.name

class Lendable(models.Model):
    name = models.CharField(max_length=256, null=False, blank=False)
    slug = models.SlugField(null=False, blank=False)

    description = models.TextField(null=False, blank=False)

    type = models.ForeignKey(LendableType)
    owners = models.ManyToManyField(LendablesOwner)

    warning_message = models.TextField(null=False, blank=True)
    unavailable_message = models.TextField(null=False, blank=True)
    available = models.BooleanField(null=False, blank=False, default=True)

    created_date = models.DateTimeField(auto_now_add=True, null=False)

    inventory_id = models.CharField(max_length=64, null=False, blank=False)

    def __unicode__(self):
        return self.name

class Booking(xwf_models.WorkflowEnabled, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, related_name='bookings')
    created_date = models.DateTimeField(auto_now_add=True, null=False)
    notes = models.TextField(null=False, blank=True, default='')

    state = StateField(workflows.BookingWorkflow)

    @xworkflows.transition()
    def submit(self, user, *args, **kwargs):
        for child in self.booking_parts.all():
            if child.submit.is_available():
                child.submit(user=user, *args, **kwargs)

        if not kwargs.get('silent', False):
            subject = 'Booking #{} requires your attention'.format(self.id)
            interested_parties = [(subject, x) for x in set(self.booking_parts.values_list('lendable__owners__owning_group__user__email', flat=True))]
            from_email = 'mediatec@imperial.ac.uk'
            message = """
Hello,

{} has just created a booking #{} which requires your attention.

Regards,
The Media Booking System
""".format(user, self.id)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    @xworkflows.transition()
    def cancel(self, user, *args, **kwargs):
        new_kwargs = dict(kwargs)
        new_kwargs['silent'] = True
        new_kwargs['user'] = user
        new_kwargs['cancel_children'] = False
        did_cancel = []
        if kwargs.get('cancel_children', True):
            for child in self.booking_parts.all():
                if child.cancel.is_available():
                    did_cancel.append(child)
                    child.cancel(*args, **new_kwargs)

        if not kwargs.get('silent', False):
            interested_parties = [('Your booking #{} has been cancelled'.format(self.id), self.user.email)]
            from_email = 'mediatec@imperial.ac.uk'
            this_also = """
This also resulted in the cancellation of the parts:"""
            for things in did_cancel:
                this_also += "\n * {} (booked from {} to {})".format(things.lendable.name, things.start_date, things.end_date)
            if not did_cancel:
                this_also = ""
            message = """
Hello,

Your booking number #{} has been cancelled by {}.
{}

Regards,
The Media Booking System
""".format(self.id, user, this_also)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    @xworkflows.transition()
    def approve(self, user, *args, **kwargs):
        if not kwargs.get('silent', False):
            interested_parties = [('Your booking #{} has been approved'.format(self.id), self.user.email)]
            from_email = 'mediatec@imperial.ac.uk'
            message = """
Hello,

Your booking number #{} has now been fully approved.

Regards,
The Media Booking System
""".format(self.id)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    @xworkflows.transition()
    def complete(self, user, *args, **kwargs):
        if not kwargs.get('silent', False):
            interested_parties = [('Your booking #{} has been marked as complete'.format(self.id), self.user.email)]
            from_email = 'mediatec@imperial.ac.uk'
            message = """
Hello,

Your booking number #{} has now been marked as complete.

Thank you for using the Media Booking System.
""".format(self.id)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    def __unicode__(self):
        return "Booking by {} on {} ({})".format(self.user, self.created_date, self.state.name)

class BookingPart(xwf_models.WorkflowEnabled, models.Model):
    booking = models.ForeignKey(Booking, related_name='booking_parts')
    lendable = models.ForeignKey(Lendable, related_name='booking_parts')
    start_date = models.DateTimeField(null=False, blank=False)
    end_date = models.DateTimeField(null=False, blank=False)
    notes = models.TextField(null=False, blank=True, default='')

    state = StateField(workflows.BookingPartWorkflow)

    @xworkflows.transition()
    def cancel(self, user, *args, **kwargs):
        extra_note = ''
        part_of_your = 'Part of your'
        if self.booking.booking_parts.exclude(state='cancelled').exclude(id=self.id).count() == 0 and self.booking.cancel.is_available() and kwargs.get('cancel_children', True):
            self.booking.cancel(silent=True, user=user, cancel_children=False)
            extra_note += "\nThis resulted in the cancellation of the booking, as there were no more active parts remaining."
            part_of_your = 'Your'

        if not kwargs.get('silent', False):
            interested_parties = [('{} booking #{} has been cancelled'.format(part_of_your, self.booking.id), self.booking.user.email)]
            from_email = 'mediatec@imperial.ac.uk'
            message = """
Hello,

Part of your booking number #{} has been cancelled by {}.

Your booking of {}, which was booked from {} to {} was cancelled.{}

Regards,
The Media Booking System
""".format(self.booking.id, user, self.lendable.name, self.start_date, self.end_date, extra_note)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    @xworkflows.transition()
    def approve(self, user, *args, **kwargs):
        part_of_your = 'Part of your'
        if self.booking.booking_parts.exclude(state='approved').exclude(id=self.id).count() == 0 and self.booking.approve.is_available() and kwargs.get('approve_children', True):
            self.booking.approve(silent=False, user=user)
            kwargs['silent'] = True

        if not kwargs.get('silent', False):
            interested_parties = [('Part of your booking #{} has been approved'.format(self.booking.id), self.booking.user.email)]
            from_email = 'mediatec@imperial.ac.uk'
            message = """
Hello,

Part of your booking number #{} has been approved by {}:

Your booking of {}, which was booked from {} to {} has now been approved.

Regards,
The Media Booking System
""".format(self.booking.id, user, self.lendable.name, self.start_date, self.end_date)

            datatuple = [(subject, message, from_email, [recipient]) for (subject, recipient) in interested_parties]

            mail.send_mass_mail(datatuple, fail_silently=True)

    @xworkflows.transition()
    def complete(self, user, *args, **kwargs):
        if self.booking.booking_parts.exclude(state='completed').exclude(id=self.id).count() == 0 and self.booking.complete.is_available() and kwargs.get('complete_children', True):
            self.booking.complete(silent=False, user=user)
            kwargs['silent'] = True

    def __unicode__(self):
        return "BookingPart of {} part of {}".format(self.lendable, self.booking)
