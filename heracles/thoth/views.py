from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from django.views.generic import CreateView, DetailView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from collections import OrderedDict
import datetime

from . import models as m, forms as f, workflows as wf

class ThothMixin(object):
    def user_is_admin(self):
        return bool(self.get_adminable_groups())

    def get_adminable_groups(self, user=None):
        if user is None:
            user = self.request.user
        if user.is_superuser:
            return m.LendablesOwner.objects.all()
        return m.LendablesOwner.objects.filter(owning_group__in=user.groups.all())

    def get_context_data(self, **kwargs):
        data = super(ThothMixin, self).get_context_data(**kwargs)
        data.update({
            'thoth_admin': self.user_is_admin()
        })
        return data

    def get_state_to_label_map(self):
        return {
            'creating': None,
            'cancelled': None,
            'pending_approval': 'warning',
            'approved': 'primary',
            'equipment_out': 'danger',
            'equipment_checked': 'info',
            'completed': 'success',
            None: None,
        }

    def get_state_key(self):
        lmap = self.get_state_to_label_map()

        return [(x[0], x[1], lmap.get(x[0], lmap[None])) for x in [
            ('creating', 'Creating'),
            ('cancelled', 'Cancelled'),
            ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'),
            ('equipment_out', 'On Loan'),
            ('equipment_checked', 'Returned'),
            ('completed', 'Completed'),
        ]]

    def get_transition_to_label_map(self):
        return {
            'submit': 'primary',
            'approve': 'success',
            'cancel': 'danger',
            'equipment_out': 'primary',
            'equipment_checked': 'info',
            'complete': 'success',
            None: None,
        }

    def get_transition_key(self):
        lmap = self.get_transition_to_label_map()

        return [(x[0], x[1], lmap.get(x[0], lmap[None])) for x in [
            ('submit', 'Submit'),
            ('approve', 'Approve'),
            ('cancel', 'Cancel'),
            ('equipment_out', 'Equipment Released'),
            ('equipment_checked', 'Equipment Returned & Checked'),
            ('complete', 'Mark Complete'),
        ]]


class IndexView(ThothMixin, TemplateView):
    template_name = 'thoth/index.html'

def dummy(request):
    return render(request, 'thoth/index.html')

class PublicMakeView(ThothMixin, View):
    http_method_names = [u'get']

    def get(self, request, *args, **kwargs):
        # does this user have any bookings in progress?
        # if so, redirect them to it
        booking, create = m.Booking.objects.get_or_create(user=request.user, state=wf.BookingWorkflow.states.creating)
        return HttpResponseRedirect(reverse('thoth-booking', kwargs={'pk': booking.pk}))

class PublicViewBookingView(ThothMixin, DetailView):
    template_name = 'thoth/public/view.html'
    model = m.Booking

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)

        obj = self.get_object()

        ok_ret, fail_ret = self.get, self.http_method_not_allowed
        ret = fail_ret

        if action == 'cancel_part':
           [x.cancel(user=request.user) for x in obj.booking_parts.filter(id=request.POST.get('part_id'))]
           ret = ok_ret
        elif action == 'cancel':
           obj.cancel(user=request.user)
           ret = ok_ret

        return ret(request, *args, **kwargs)

class AdminHandleBookingView(ThothMixin, DetailView):
    template_name = 'thoth/admin/view.html'
    model = m.Booking

    def get_context_data(self, **kwargs):
        data = super(AdminHandleBookingView, self).get_context_data(**kwargs)

        data.update({
            'label_map': self.get_transition_to_label_map(),
            'key': self.get_transition_key(),
        })

        return data

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)

        obj = self.get_object()

        ok_ret, fail_ret = self.get, self.http_method_not_allowed
        ret = fail_ret

        if action == 'change_state':
           for x in obj.booking_parts.filter(id=request.POST.get('part_id')):
               getattr(x, request.POST.get('transition'))(user=request.user)
           ret = ok_ret
        elif action == 'cancel':
           obj.cancel(user=request.user)
           ret = ok_ret

        return ret(request, *args, **kwargs)


class PublicItemCalendarView(ThothMixin, DetailView):
    template_name = 'thoth/public/item_calendar.html'
    model = m.Lendable

    weekday_names = ['Mon', 'Tues', 'Weds', 'Thurs', 'Fri', 'Sat', 'Sun']
    first_day_of_week = 0
    last_day_of_week = 6

    def get_display_date(self):
        date_str = self.request.GET.get('date', None)
        if date_str is None:
            return timezone.now().date()

        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    def build_calendar(self, qs, date):
        one_day = datetime.timedelta(days=1)

        this_month = date.month
        first_day_of_month = date.replace(day=1)
        last_day_of_month = date.replace(day=28)

        # try to find the last day of the month
        while last_day_of_month.month == this_month:
            last_day_of_month += one_day
        # now back a step so we're actually in the month
        last_day_of_month -= one_day

        start_date, end_date = first_day_of_month, last_day_of_month
        # walk backwards until we get to first_day_of_week
        while start_date.weekday() != self.first_day_of_week:
            start_date -= one_day
        # walk forwards until we get to last_day_of_week
        while end_date.weekday() != self.last_day_of_week:
            end_date += one_day

        # filter the queryset
        qs = qs.filter(Q(start_date__lte=end_date + one_day) & Q(end_date__gte=start_date - one_day)).order_by('start_date')

        flattened_bookings = [[] for _ in range((end_date - start_date).days + 1)]

        state_to_label_map = self.get_state_to_label_map()
 
        for booking_part in qs:
            label_suffix = state_to_label_map.get(booking_part.state.state.name, state_to_label_map[None])
            if label_suffix is None: continue

            b_start, b_end = booking_part.start_date.date(), booking_part.end_date.date()
            b_current = b_start

            while b_current <= b_end and b_current <= end_date:
                if b_current < start_date:
                    b_current += one_day
                    continue

                fb = flattened_bookings[(b_current - start_date).days]

                event_dict = {
                    'title': 'Booking by {}'.format(booking_part.booking.user),
                    'starts_today': b_current == b_start,
                    'ends_today': b_current == b_end,
                    'label_suffix': label_suffix, 
                }
                if event_dict['starts_today']:
                    event_dict['start_time'] = booking_part.start_date.time()
                if event_dict['ends_today']:
                    event_dict['end_time'] = booking_part.end_date.time()
                fb.append(event_dict)

                b_current += one_day

        calendar = []

        current_date = start_date
        while current_date <= end_date:
            if len(calendar) == 0 or len(calendar[-1]) == 7:
                calendar.append([])
            today = {}
            calendar[-1].append(today)

            today['date'] = current_date.day
            today['is_this_month'] = (current_date >= first_day_of_month and current_date <= last_day_of_month)
            today['events'] = flattened_bookings[(current_date - start_date).days]

            current_date += one_day

        return calendar
        

    def get_context_data(self, **kwargs):
        data = super(PublicItemCalendarView, self).get_context_data(**kwargs)

        show_date = self.get_display_date()

        one_day = datetime.timedelta(days=1)

        last_date = show_date
        while last_date.day != 1 or last_date.month == show_date.month:
            last_date -= one_day
        next_date = show_date
        while next_date.day != 1 or next_date.month == show_date.month:
            next_date += one_day

        data.update({
            'date': show_date,
            'weekdays': self.weekday_names,
            'calendar': self.build_calendar(data['lendable'].booking_parts, show_date),
            'last_date': last_date,
            'next_date': next_date,
            'state_key': self.get_state_key(),
        })

        return data

class PublicCreateBookingView(ThothMixin, DetailView):
    template_name = 'thoth/public/create.html'
    model = m.Booking

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)

        obj = self.get_object()

        ok_ret, fail_ret = self.get, self.http_method_not_allowed
        ret = fail_ret

        if action == 'remove_part':
           obj.booking_parts.filter(id=request.POST.get('part_id')).delete()
           ret = ok_ret
        elif action == 'book_item':
           form = f.BookingPartForm(request.POST)
           errors = []
           ret = ok_ret
           if form.is_valid():
               part = m.BookingPart(lendable=form.cleaned_data['item'], start_date=form.cleaned_data['from_date'], end_date=form.cleaned_data['to_date'], booking=obj)
               part.save()
               if not self.validate_booking_part(obj, part):
                   errors = part.failure_messages
                   part.delete()
           for error in errors:
               messages.add_message(request, messages.ERROR, 'Unable to add item to booking: {}'.format(error))
        elif action == 'submit':
           notes = self.get_notes_form()
           parts = obj.booking_parts.all().select_related()
           valid, _ = self.validate_booking(obj, parts)
           if notes.is_valid() and valid:
               obj.notes = notes.cleaned_data['notes']
               obj.submit(user=request.user)
               return HttpResponseRedirect(request.path) # reload
           elif not valid:
               messages.add_message(request, messages.ERROR, 'Your booking is invalid and cannot yet be submitted.')
        return ret(request, *args, **kwargs)
        

    def get_date_range_form(self):
        if self.request.GET.get('from_date', None) is not None and self.request.GET.get('to_date', None) is not None:
            return f.FutureDateRangeForm(self.request.GET)
        return f.FutureDateRangeForm()

    def get_notes_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action', None) == 'submit':
            return f.NotesForm(self.request.POST)
        return f.NotesForm()

    def get_available(self, booking, from_date, to_date):
        # we want all the Lendable objects which aren't booked /at all/ during this time
        # however, we're going to end up displaying the stuff anyway...
        dformat = '%Y-%m-%d %H:%M:%S'
        all_objects = m.Lendable.objects.all().extra(
            select=OrderedDict([
                ('bookings_during_period', 'SELECT COUNT(*) FROM thoth_bookingpart WHERE thoth_bookingpart.lendable_id = thoth_lendable.id AND (thoth_bookingpart.start_date < %s AND thoth_bookingpart.end_date > %s) AND thoth_bookingpart.state NOT IN ("cancelled")'),
                ('firm_bookings_during_period', 'SELECT COUNT(*) FROM thoth_bookingpart WHERE thoth_bookingpart.lendable_id = thoth_lendable.id AND (thoth_bookingpart.start_date < %s AND thoth_bookingpart.end_date > %s) AND thoth_bookingpart.state NOT IN ("creating", "pending_approval", "cancelled")'),
                ('booked_by_me', 'SELECT thoth_bookingpart.id FROM thoth_bookingpart WHERE thoth_bookingpart.booking_id = %s AND thoth_bookingpart.state NOT IN ("cancelled") AND thoth_bookingpart.lendable_id = thoth_lendable.id AND (thoth_bookingpart.start_date < %s AND thoth_bookingpart.end_date > %s)'),
            ]),
            select_params=(to_date.strftime(dformat), from_date.strftime(dformat), to_date.strftime(dformat), from_date.strftime(dformat), booking.id, to_date.strftime(dformat), from_date.strftime(dformat), )
        )
        return list(all_objects)

    def is_booking_complex(self, parts):
        current_owners = None
        if len(parts) <= 1:
            return False
        for part in parts:
            owners = set(part.lendable.owners.all())
            if current_owners is None:
                current_owners = owners
                continue
            if len(current_owners & owners) == 0:
                return True
        return False

    def validate_booking_part(self, booking, part):
        part.failure_messages = []

        # check the booking is in the future
        if part.start_date < timezone.now():
            part.failure_messages.append(u'You can only make bookings for the future.')

        if part.start_date >= part.end_date:
            part.failure_messages.append(u'Your booking must end after it begins.')

        if not part.lendable.available:
            part.failure_messages.append(u'This item is no longer available for booking.')

        bps = m.BookingPart.objects.filter(lendable=part.lendable)
        if part.id:
            bps = bps.exclude(pk=part.id)

        if bps.exclude(state__in=('creating', 'pending_approval', 'cancelled')).count() > 0:
            part.failure_messages.append(u'This item has already been booked.')

        if bps.filter(booking=booking).filter(Q(start_date__lt=part.end_date) & Q(end_date__gt=part.start_date)).count() > 0:
            part.failure_messages.append(u'This item overlaps with a booking period for the same item in this booking.')

        return len(part.failure_messages) == 0

    def validate_booking(self, booking, parts):
        booking_valid = True

        failed_parts = []

        for part in parts:
            if not self.validate_booking_part(booking, part):
                booking_valid = False
                failed_parts.append(part)

        return booking_valid, failed_parts

    def get_context_data(self, **kwargs):
        data = super(PublicCreateBookingView, self).get_context_data(**kwargs)

        if data['booking'].state != 'creating':
            raise Http404('Nope')

        available = None

        date_range_form = self.get_date_range_form()
        if date_range_form.is_valid():
            available = self.get_available(data['booking'], date_range_form.cleaned_data['from_date'], date_range_form.cleaned_data['to_date'])

        notes_form = self.get_notes_form()

        parts = data['booking'].booking_parts.all().select_related()

        booking_valid, failed_parts = False, []
        if parts:
            booking_valid, failed_parts = self.validate_booking(data['booking'], parts)

        data.update({
            'available': available,
            'date_range_form': date_range_form,
            'booking_parts': parts, 
            'booking_is_complex': self.is_booking_complex(parts),
            'notes_form': notes_form,
            'from_date': date_range_form.cleaned_data.get('from_date', None) if date_range_form.is_valid() else None,
            'to_date': date_range_form.cleaned_data.get('to_date', None) if date_range_form.is_valid() else None,
            'booking_valid': booking_valid,
            'failed_parts': failed_parts,
        })
        return data

class HandleBookingView(ThothMixin, View):
    admin_view = AdminHandleBookingView
    public_create_view = PublicCreateBookingView
    public_watch_view = PublicViewBookingView

    def get_admin_view(self):
        return self.admin_view.as_view()

    def get_public_create_view(self):
        return self.public_create_view.as_view()

    def get_public_watch_view(self):
        return self.public_watch_view.as_view()

    # this is actually a dispatcher
    # that does "the right thing" depending on what's up
    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(m.Booking, pk=kwargs.get('pk', None))

        try_view_admin = request.GET.get('view_as_admin', 'n') == 'y'
        if self.user_is_admin() and (obj.user != request.user or try_view_admin) and (obj.user == request.user or not try_view_admin) and obj.state != 'creating':
            return self.get_admin_view()(request, *args, **kwargs)
        elif not self.user_is_admin() and obj.user != request.user:
            raise Http404("User not allowed to view that!")
        elif obj.state == 'creating':
            return self.get_public_create_view()(request, *args, **kwargs)
        else:
            return self.get_public_watch_view()(request, *args, **kwargs)
