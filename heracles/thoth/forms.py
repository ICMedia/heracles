from . import models as m
from django import forms
from django.contrib.auth import get_user_model
from bootstrap3_datetime.widgets import DateTimePicker

from django.utils import timezone

class RequestFormMixin(object):
    def __init__(self, *args, **kwargs):
       self.request = kwargs.pop('request', None)
       super(RequestFormMixin, self).__init__(*args, **kwargs)

class DateRangeForm(forms.Form):
    from_date = forms.DateTimeField(widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))
    to_date = forms.DateTimeField(widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))

    def clean(self):
        cleaned_data = super(DateRangeForm, self).clean()

        from_date, to_date = cleaned_data.get('from_date', None), cleaned_data.get('to_date', None)

        if from_date and to_date and from_date >= to_date:
            raise forms.ValidationError("'From' date must be after the 'To' date.")

        return cleaned_data

class FutureDateRangeForm(DateRangeForm):
    def clean_from_date(self):
        date = self.cleaned_data['from_date']
        if date < timezone.now():
            raise forms.ValidationError("Date must be in the future.")
        return date

    def clean_to_date(self):
        date = self.cleaned_data['to_date']
        if date < timezone.now():
            raise forms.ValidationError("Date must be in the future.")
        return date

class NotesForm(forms.Form):
    notes = forms.CharField(widget=forms.Textarea())

class BookingPartForm(forms.Form):
    item = forms.ModelChoiceField(queryset=m.Lendable.objects.all(), required=True)
    from_date = forms.DateTimeField(widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))
    to_date = forms.DateTimeField(widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))
